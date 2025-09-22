# Daemon and JIRA Integration

MKanban includes a background daemon for automatic synchronization with Git branches and JIRA tickets, providing seamless integration with development workflows.

## Overview

The daemon system provides:

- **Background Processing**: Automatic synchronization without user intervention
- **Git Integration**: Branch tracking and automatic task management
- **JIRA Integration**: Bidirectional synchronization with JIRA projects
- **Session Awareness**: tmux session-based task organization
- **Configurable Polling**: Adjustable sync intervals and behaviors

## Daemon Architecture

### Core Components

- **DaemonManager**: Main daemon orchestrator
- **GitBranchMonitor**: Git repository monitoring
- **JiraClient**: JIRA API integration
- **TaskCreator**: Automatic task creation and management
- **SessionManager**: tmux session detection and management

### Daemon Lifecycle

```python
# Daemon startup
daemon_manager = DaemonManager()
daemon_manager.start()

# Background processing loop
while daemon_manager.is_running:
    await daemon_manager.process_cycle()
    await asyncio.sleep(polling_interval)

# Graceful shutdown
daemon_manager.stop()
```

## Git Integration

### GitBranchMonitor

Monitors Git repositories for branch changes and creates corresponding tasks.

#### Configuration

```python
daemon_config = {
    "enabled": True,
    "polling_interval": 5,  # seconds
    "branch_patterns": [
        "feature/*",
        "bugfix/*",
        "hotfix/*",
        "fix/*",
        "feat/*"
    ],
    "excluded_branches": [
        "main",
        "master",
        "develop",
        "staging"
    ]
}
```

#### Branch Detection

```python
class GitBranchMonitor:
    def __init__(self, repository_path: str, config: DaemonConfiguration):
        self.repository_path = Path(repository_path)
        self.config = config
        self.logger = get_daemon_logger("git_monitor")

    async def scan_branches(self) -> List[GitBranch]:
        """Scan repository for matching branches."""
        self.logger.debug("Scanning branches", repo=str(self.repository_path))

        try:
            # Get all branches
            result = await self._run_git_command(["branch", "-a"])
            branches = self._parse_branch_output(result)

            # Filter by patterns
            filtered_branches = []
            for branch in branches:
                if self._matches_patterns(branch.name):
                    filtered_branches.append(branch)

            self.logger.info("Branches scanned",
                           repo=str(self.repository_path),
                           total=len(branches),
                           filtered=len(filtered_branches))

            return filtered_branches

        except Exception as e:
            self.logger.error("Failed to scan branches",
                            repo=str(self.repository_path),
                            error=str(e))
            return []
```

#### Branch Matching

```python
def _matches_patterns(self, branch_name: str) -> bool:
    """Check if branch matches configured patterns."""
    # Exclude system branches
    if branch_name in self.config.excluded_branches:
        return False

    # Check against patterns
    for pattern in self.config.branch_patterns:
        if fnmatch.fnmatch(branch_name, pattern):
            self.logger.debug("Branch matched pattern",
                            branch=branch_name,
                            pattern=pattern)
            return True

    return False
```

#### Task Creation from Branches

```python
async def create_task_from_branch(self, branch: GitBranch) -> Optional[Item]:
    """Create a kanban task from a Git branch."""
    self.logger.set_context(branch=branch.name)

    try:
        # Get commit information
        commit_info = await self._get_latest_commit(branch.name)

        # Create item from branch
        item = Item.from_git_branch(
            branch_name=branch.name,
            repository_path=str(self.repository_path),
            column_id=self.config.default_column,
            last_commit_hash=commit_info.get("hash"),
            last_commit_message=commit_info.get("message"),
            last_commit_author=commit_info.get("author"),
            last_commit_date=commit_info.get("date"),
            is_current=branch.is_current
        )

        self.logger.info("Task created from branch",
                        item=item.title,
                        branch=branch.name)

        return item

    except Exception as e:
        self.logger.error("Failed to create task from branch",
                         branch=branch.name,
                         error=str(e))
        return None
```

### Automatic Task Management

#### Current Branch Detection

```python
async def update_current_branch_task(self, current_branch: str) -> None:
    """Update task status based on current branch."""
    self.logger.debug("Updating current branch task", branch=current_branch)

    # Find task for current branch
    task = await self._find_task_for_branch(current_branch)
    if not task:
        return

    # Mark as current and move to in-progress if configured
    task.set_current_branch(True)

    if (self.config.auto_activate_on_session_switch and
        task.should_auto_activate()):

        await self._move_task_to_column(task, self.config.in_progress_column)
        self.logger.info("Task auto-activated",
                        task=task.title,
                        branch=current_branch)
```

#### Branch Deletion Handling

```python
async def handle_deleted_branch(self, branch_name: str) -> None:
    """Handle tasks for deleted branches."""
    self.logger.debug("Handling deleted branch", branch=branch_name)

    task = await self._find_task_for_branch(branch_name)
    if not task:
        return

    # Mark branch as deleted
    task.mark_branch_deleted()

    # Auto-complete if configured
    if (self.config.auto_complete_on_session_switch and
        task.should_auto_complete()):

        await self._move_task_to_column(task, self.config.done_column)
        self.logger.info("Task auto-completed",
                        task=task.title,
                        branch=branch_name)
```

## JIRA Integration

### JiraClient

Handles all JIRA API interactions with authentication and error handling.

#### Configuration

```python
jira_config = {
    "enabled": True,
    "api_url": "https://company.atlassian.net",
    "username": "user@company.com",
    "api_token": "secret_token",
    "project_keys": ["PROJ", "DEV"],
    "polling_interval": 300,  # 5 minutes
    "bidirectional_sync": True,
    "status_mapping": {
        "To Do": "to-do",
        "In Progress": "in-progress",
        "Done": "done",
        "Backlog": "backlog"
    },
    "jql_filter": "project = PROJ AND assignee = currentUser()",
    "board_name": "jira-tickets"
}
```

#### Authentication

```python
class JiraClient:
    def __init__(self, config: JiraConfiguration):
        self.config = config
        self.logger = get_daemon_logger("jira_client")
        self._session = None

    async def authenticate(self) -> bool:
        """Authenticate with JIRA API."""
        try:
            auth = HTTPBasicAuth(self.config.username, self.config.api_token)

            # Test authentication with user info endpoint
            response = await self._make_request(
                "GET",
                f"{self.config.api_url}/rest/api/3/myself",
                auth=auth
            )

            if response.status_code == 200:
                user_info = response.json()
                self.logger.info("JIRA authentication successful",
                               user=user_info.get("displayName"))
                return True
            else:
                self.logger.error("JIRA authentication failed",
                                status=response.status_code)
                return False

        except Exception as e:
            self.logger.error("JIRA authentication error", error=str(e))
            return False
```

#### Ticket Fetching

```python
async def fetch_tickets(self) -> List[Dict[str, Any]]:
    """Fetch tickets based on JQL filter."""
    try:
        jql = self.config.jql_filter or self._build_default_jql()

        params = {
            "jql": jql,
            "maxResults": self.config.backlog_limit,
            "fields": "summary,description,status,assignee,priority,labels,components",
            "expand": "changelog"
        }

        self.logger.debug("Fetching JIRA tickets", jql=jql)

        response = await self._make_request(
            "GET",
            f"{self.config.api_url}/rest/api/3/search",
            params=params
        )

        if response.status_code == 200:
            data = response.json()
            tickets = data.get("issues", [])

            self.logger.info("JIRA tickets fetched", count=len(tickets))
            return tickets
        else:
            self.logger.error("Failed to fetch JIRA tickets",
                            status=response.status_code)
            return []

    except Exception as e:
        self.logger.error("Error fetching JIRA tickets", error=str(e))
        return []

def _build_default_jql(self) -> str:
    """Build default JQL filter from configuration."""
    project_filter = " OR ".join([f"project = {key}" for key in self.config.project_keys])
    return f"({project_filter}) AND assignee = currentUser() ORDER BY updated DESC"
```

#### Task Creation from JIRA

```python
async def create_task_from_ticket(self, ticket_data: Dict[str, Any]) -> Optional[Item]:
    """Create a kanban task from JIRA ticket."""
    ticket_key = ticket_data["key"]
    fields = ticket_data["fields"]

    self.logger.set_context(jira_ticket=ticket_key)

    try:
        # Map JIRA status to column
        jira_status = fields["status"]["name"]
        column_id = self.config.status_mapping.get(jira_status, self.config.default_column)

        # Extract ticket information
        processed_ticket = {
            "id": ticket_data["id"],
            "url": f"{self.config.api_url}/browse/{ticket_key}",
            "project_key": fields["project"]["key"],
            "issue_type": fields["issuetype"]["name"],
            "summary": fields["summary"],
            "description": fields.get("description", ""),
            "status": jira_status,
            "priority": fields.get("priority", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("emailAddress"),
            "reporter": fields.get("reporter", {}).get("emailAddress"),
            "labels": [label for label in fields.get("labels", [])],
            "components": [comp["name"] for comp in fields.get("components", [])]
        }

        # Create item
        item = Item.from_jira_ticket(ticket_key, processed_ticket, column_id)

        self.logger.info("Task created from JIRA ticket",
                        item=item.title,
                        jira_ticket=ticket_key,
                        status=jira_status)

        return item

    except Exception as e:
        self.logger.error("Failed to create task from JIRA ticket",
                         jira_ticket=ticket_key,
                         error=str(e))
        return None
```

### Bidirectional Synchronization

#### Status Sync to JIRA

```python
async def sync_status_to_jira(self, item: Item) -> bool:
    """Sync item status back to JIRA."""
    if not item.should_sync_to_jira():
        return True

    jira_ticket = item.get_jira_ticket_key()
    self.logger.set_context(jira_ticket=jira_ticket)

    try:
        # Map column to JIRA status
        local_column = item.column_id
        jira_status = self._map_column_to_jira_status(local_column)

        if not jira_status:
            self.logger.warning("No JIRA status mapping for column", column=local_column)
            return False

        # Update JIRA ticket
        transition_data = {
            "transition": {
                "id": await self._get_transition_id(jira_ticket, jira_status)
            }
        }

        response = await self._make_request(
            "POST",
            f"{self.config.api_url}/rest/api/3/issue/{jira_ticket}/transitions",
            json=transition_data
        )

        if response.status_code in [200, 204]:
            self.logger.info("Status synced to JIRA",
                           jira_ticket=jira_ticket,
                           status=jira_status)

            # Update sync timestamp
            item.update_jira_metadata(last_sync=now())
            return True
        else:
            self.logger.error("Failed to sync status to JIRA",
                            jira_ticket=jira_ticket,
                            status=response.status_code)
            return False

    except Exception as e:
        self.logger.error("Error syncing status to JIRA",
                         jira_ticket=jira_ticket,
                         error=str(e))
        return False
```

#### Comment Synchronization

```python
async def sync_comments_to_jira(self, item: Item, comment: str) -> bool:
    """Add comment to JIRA ticket."""
    jira_ticket = item.get_jira_ticket_key()

    try:
        comment_data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"[MKanban] {comment}"
                            }
                        ]
                    }
                ]
            }
        }

        response = await self._make_request(
            "POST",
            f"{self.config.api_url}/rest/api/3/issue/{jira_ticket}/comment",
            json=comment_data
        )

        if response.status_code == 201:
            self.logger.info("Comment synced to JIRA", jira_ticket=jira_ticket)
            return True
        else:
            self.logger.error("Failed to sync comment to JIRA",
                            jira_ticket=jira_ticket,
                            status=response.status_code)
            return False

    except Exception as e:
        self.logger.error("Error syncing comment to JIRA",
                         jira_ticket=jira_ticket,
                         error=str(e))
        return False
```

## Session Management

### TmuxSessionManager

Handles tmux session detection and session-specific board organization.

#### Session Detection

```python
class TmuxSessionManager:
    def __init__(self):
        self.logger = get_daemon_logger("tmux_manager")

    def get_current_session(self) -> Optional[TmuxSession]:
        """Get current tmux session information."""
        try:
            # Check if we're in tmux
            if not os.environ.get("TMUX"):
                self.logger.debug("Not in tmux session")
                return None

            # Get session information
            result = subprocess.run(
                ["tmux", "display-message", "-p", "#{session_name}:#{session_path}"],
                capture_output=True,
                text=True,
                check=True
            )

            session_info = result.stdout.strip().split(":")
            if len(session_info) >= 2:
                session = TmuxSession(
                    name=session_info[0],
                    path=session_info[1]
                )

                self.logger.debug("Current tmux session detected",
                                session=session.name,
                                path=session.path)
                return session

        except subprocess.CalledProcessError as e:
            self.logger.debug("Failed to get tmux session", error=str(e))
        except Exception as e:
            self.logger.error("Error detecting tmux session", error=str(e))

        return None
```

#### Session-based Board Management

```python
def get_session_board_name(self, session: TmuxSession) -> str:
    """Get board name for a tmux session."""
    # Use session name as board name
    board_name = session.name

    # Sanitize for filesystem
    safe_name = re.sub(r'[^\w\-_]', '-', board_name)

    self.logger.debug("Session board name determined",
                     session=session.name,
                     board=safe_name)

    return safe_name

async def setup_session_board(self, session: TmuxSession) -> Optional[Board]:
    """Set up a board for the current session."""
    board_name = self.get_session_board_name(session)

    try:
        board_service = get_container().get(BoardService)

        # Try to load existing board
        board = board_service.load_board(board_name)

        if not board:
            # Create new board for session
            board = board_service.create_board(
                name=board_name,
                columns=["to-do", "in-progress", "done"]
            )

            self.logger.info("Session board created",
                           session=session.name,
                           board=board_name)
        else:
            self.logger.debug("Session board loaded",
                            session=session.name,
                            board=board_name)

        return board

    except Exception as e:
        self.logger.error("Failed to setup session board",
                         session=session.name,
                         error=str(e))
        return None
```

## Daemon Process Management

### Daemon Startup

```python
class DaemonManager:
    def __init__(self):
        self.config = get_container().get(ConfigurationManager).config.daemon
        self.logger = get_daemon_logger("daemon_manager")
        self.is_running = False
        self.tasks = []

    async def start(self) -> None:
        """Start the daemon process."""
        if not self.config.enabled:
            self.logger.info("Daemon disabled in configuration")
            return

        self.logger.info("Starting MKanban daemon",
                        polling_interval=self.config.polling_interval)

        try:
            # Initialize components
            await self._initialize_components()

            # Start background tasks
            self.is_running = True
            self.tasks = [
                asyncio.create_task(self._git_monitor_loop()),
                asyncio.create_task(self._jira_sync_loop()),
                asyncio.create_task(self._session_monitor_loop())
            ]

            # Wait for shutdown signal
            await self._wait_for_shutdown()

        except Exception as e:
            self.logger.error("Daemon startup failed", error=str(e))
            raise
```

### Processing Loops

```python
async def _git_monitor_loop(self) -> None:
    """Main Git monitoring loop."""
    while self.is_running:
        try:
            await self._process_git_changes()
            await asyncio.sleep(self.config.polling_interval)
        except Exception as e:
            self.logger.error("Git monitor loop error", error=str(e))
            await asyncio.sleep(self.config.polling_interval)

async def _jira_sync_loop(self) -> None:
    """Main JIRA synchronization loop."""
    if not self.config.jira.enabled:
        return

    while self.is_running:
        try:
            await self._process_jira_sync()
            await asyncio.sleep(self.config.jira.polling_interval)
        except Exception as e:
            self.logger.error("JIRA sync loop error", error=str(e))
            await asyncio.sleep(self.config.jira.polling_interval)

async def _session_monitor_loop(self) -> None:
    """Monitor tmux session changes."""
    current_session = None

    while self.is_running:
        try:
            session = self.session_manager.get_current_session()

            if session != current_session:
                self.logger.info("Session changed",
                               old_session=current_session.name if current_session else None,
                               new_session=session.name if session else None)

                await self._handle_session_change(current_session, session)
                current_session = session

            await asyncio.sleep(2)  # Check session more frequently

        except Exception as e:
            self.logger.error("Session monitor error", error=str(e))
            await asyncio.sleep(2)
```

### Graceful Shutdown

```python
async def stop(self) -> None:
    """Stop the daemon gracefully."""
    self.logger.info("Stopping MKanban daemon")

    self.is_running = False

    # Cancel all tasks
    for task in self.tasks:
        task.cancel()

    # Wait for tasks to complete
    await asyncio.gather(*self.tasks, return_exceptions=True)

    # Cleanup resources
    await self._cleanup()

    self.logger.info("MKanban daemon stopped")

def _setup_signal_handlers(self) -> None:
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        self.logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(self.stop())

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
```

## Error Handling and Resilience

### Retry Logic

```python
async def _with_retry(self, operation: Callable, max_retries: int = 3) -> Any:
    """Execute operation with retry logic."""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt  # Exponential backoff
            self.logger.warning("Operation failed, retrying",
                              attempt=attempt + 1,
                              wait_time=wait_time,
                              error=str(e))

            await asyncio.sleep(wait_time)
```

### Connection Recovery

```python
async def _ensure_jira_connection(self) -> bool:
    """Ensure JIRA connection is active."""
    if not hasattr(self, '_jira_authenticated') or not self._jira_authenticated:
        self.logger.debug("Re-authenticating with JIRA")
        self._jira_authenticated = await self.jira_client.authenticate()

    return self._jira_authenticated

async def _handle_jira_error(self, error: Exception) -> None:
    """Handle JIRA API errors gracefully."""
    if isinstance(error, HTTPError):
        if error.response.status_code == 401:
            self.logger.warning("JIRA authentication expired, re-authenticating")
            self._jira_authenticated = False
        elif error.response.status_code == 429:
            self.logger.warning("JIRA rate limit hit, backing off")
            await asyncio.sleep(60)  # Wait 1 minute
    else:
        self.logger.error("Unexpected JIRA error", error=str(error))
```

## Monitoring and Observability

### Health Checks

```python
async def health_check(self) -> Dict[str, Any]:
    """Perform daemon health check."""
    health_status = {
        "daemon_running": self.is_running,
        "git_monitor": False,
        "jira_sync": False,
        "session_manager": False,
        "last_git_sync": None,
        "last_jira_sync": None
    }

    try:
        # Check Git monitoring
        if hasattr(self, 'git_monitor'):
            health_status["git_monitor"] = True
            health_status["last_git_sync"] = self.git_monitor.last_sync_time

        # Check JIRA sync
        if self.config.jira.enabled and hasattr(self, 'jira_client'):
            health_status["jira_sync"] = await self.jira_client.test_connection()
            health_status["last_jira_sync"] = getattr(self.jira_client, 'last_sync_time', None)

        # Check session manager
        session = self.session_manager.get_current_session()
        health_status["session_manager"] = session is not None
        health_status["current_session"] = session.name if session else None

    except Exception as e:
        self.logger.error("Health check failed", error=str(e))

    return health_status
```

### Metrics Collection

```python
class DaemonMetrics:
    def __init__(self):
        self.git_syncs = 0
        self.jira_syncs = 0
        self.tasks_created = 0
        self.tasks_updated = 0
        self.errors = 0
        self.start_time = datetime.now()

    def record_git_sync(self):
        self.git_syncs += 1

    def record_jira_sync(self):
        self.jira_syncs += 1

    def record_task_created(self):
        self.tasks_created += 1

    def record_error(self):
        self.errors += 1

    def get_summary(self) -> Dict[str, Any]:
        uptime = datetime.now() - self.start_time
        return {
            "uptime_seconds": uptime.total_seconds(),
            "git_syncs": self.git_syncs,
            "jira_syncs": self.jira_syncs,
            "tasks_created": self.tasks_created,
            "tasks_updated": self.tasks_updated,
            "errors": self.errors
        }
```

## Best Practices

### Configuration

1. **Environment Variables**: Use environment variables for sensitive data
2. **Validation**: Validate configuration on startup
3. **Defaults**: Provide sensible defaults for all settings
4. **Documentation**: Document all configuration options

### Error Handling

1. **Graceful Degradation**: Continue operation when one component fails
2. **Retry Logic**: Implement exponential backoff for transient failures
3. **Circuit Breakers**: Disable failing components temporarily
4. **Monitoring**: Log all errors with appropriate context

### Performance

1. **Batch Operations**: Group related operations together
2. **Rate Limiting**: Respect API rate limits
3. **Caching**: Cache expensive operations when appropriate
4. **Selective Sync**: Only sync changed items

### Security

1. **Token Storage**: Store API tokens securely
2. **Minimal Permissions**: Use least-privilege access
3. **Input Validation**: Validate all external input
4. **Secure Communication**: Use HTTPS for all API calls

The daemon and JIRA integration provide seamless automation for development workflows, keeping Kanban boards synchronized with Git activity and JIRA projects automatically.