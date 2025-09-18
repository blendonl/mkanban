# MKanban Git Daemon Usage Guide

The MKanban Git Daemon automatically creates and manages kanban tasks based on your git branches, focusing on the active tmux session.

## Features

- **Tmux Integration**: Only monitors the git repository in your current tmux session
- **Automatic Task Creation**: Creates tasks for each feature branch
- **Branch-based Status**: Tasks move to "in-progress" when you switch to that branch
- **Configurable Data Path**: Uses `$MKANBAN_PATH` environment variable or `~/.mkanban` by default
- **Branch Filtering**: Supports include/exclude patterns for branch names

## Quick Start

### 1. Install Dependencies
```bash
# Ensure you have tmux and git installed
sudo apt install tmux git  # Ubuntu/Debian
# or
brew install tmux git      # macOS
```

### 2. Set Environment (Optional)
```bash
# Set custom data directory
export MKANBAN_PATH="/path/to/your/kanban/data"
```

### 3. Start the Daemon
```bash
# Start daemon
mkanban --daemon start

# Check status
mkanban --daemon status

# Stop daemon
mkanban --daemon stop
```

### 4. Use MKanban Normally
```bash
# View your boards (now includes auto-created git-branches board)
mkanban

# Open specific board
mkanban --board git-branches
```

## How It Works

1. **Session Detection**: The daemon detects your current tmux session
2. **Repository Monitoring**: It monitors the git repository in your current working directory
3. **Branch Tracking**: When you create a new branch (e.g., `feature/new-login`), a task is automatically created
4. **Status Sync**: When you switch to a branch (`git checkout feature/new-login`), that task moves to "in-progress"
5. **Completion**: When you delete a branch (after merging), the task moves to "done"

## Branch Patterns

By default, these branch patterns are tracked:
- `feature/*`
- `bugfix/*` 
- `hotfix/*`
- `fix/*`
- `feat/*`

These branches are excluded:
- `main`
- `master`
- `develop`
- `staging`
- `production`

## Advanced Usage

### Custom Configuration
```bash
# Start with custom settings
mkanban-daemon \
  --board-name "my-git-tasks" \
  --default-column "backlog" \
  --in-progress-column "working" \
  --done-column "completed" \
  --branch-patterns "feature/*,bug/*" \
  --excluded-branches "main,develop,staging"
```

### Systemd Service (Linux)
```bash
# Install systemd service
sudo cp src/scripts/mkanban.service /etc/systemd/user/
systemctl --user daemon-reload
systemctl --user enable mkanban.service
systemctl --user start mkanban.service
```

### Manual Sync
If you want to manually trigger a sync:
```bash
# This will be implemented via IPC
mkanban --sync
```

## File Structure

The daemon creates the following structure:

```
$MKANBAN_PATH/  (or ~/.mkanban/)
├── boards/
│   └── git-branches/
│       ├── kanban.md          # Board metadata
│       ├── to-do/             # Tasks for inactive branches
│       ├── in-progress/       # Task for current branch
│       └── done/              # Tasks for deleted/merged branches
├── logs/
│   └── daemon.log             # Daemon logs
├── daemon.pid                 # Daemon process ID
└── daemon.sock               # IPC socket
```

## Troubleshooting

### Daemon Won't Start
```bash
# Check if tmux is running
echo $TMUX

# Check if in a git repository
git status

# Check logs
tail -f ~/.mkanban/logs/daemon.log
```

### Tasks Not Creating
- Ensure you're in a tmux session
- Ensure your current directory is a git repository
- Check that your branch names match the patterns
- Verify daemon is running: `mkanban --daemon status`

### Permission Issues
```bash
# Ensure data directory is writable
ls -la $MKANBAN_PATH  # or ~/.mkanban
```

## Integration Examples

### With Git Hooks
Create a post-checkout hook to trigger immediate sync:
```bash
#!/bin/bash
# .git/hooks/post-checkout
if command -v mkanban >/dev/null 2>&1; then
    mkanban --sync 2>/dev/null || true
fi
```

### With Shell Aliases
```bash
# Add to your .bashrc or .zshrc
alias gco='git checkout'
alias gcb='git checkout -b'
alias gbd='git branch -d'

# Auto-sync after branch operations
function gco() { git checkout "$@" && mkanban --sync; }
```

## Configuration

All configuration is done via command-line arguments to the daemon. Future versions may support configuration files.

## Limitations

- Currently only supports one repository per tmux session
- Requires tmux (doesn't work in regular terminal sessions)
- Limited to local git repositories (no remote-only branch tracking)

## Future Enhancements

- Support for multiple repositories
- Integration with GitHub/GitLab/Bitbucket APIs
- Jira/Trello/Linear integration
- Configuration file support
- Web dashboard for monitoring