# Jira Integration Implementation

This document describes the Jira integration implementation for MKanban.

## Overview

The Jira integration allows MKanban to automatically synchronize with Jira tickets, creating a unified workflow between project management and task tracking.

## Features Implemented

### 1. Core Jira Integration Components

#### **JiraClient** (`src/daemon/jira/jira_client.py`)
- Handles Jira REST API communication
- Supports authentication via username/API token
- Provides methods for:
  - Searching tickets with JQL
  - Getting individual tickets
  - Updating ticket status
  - Adding comments
  - Extracting ticket keys from text

#### **JiraConfig** (`src/daemon/core/configuration_service.py`)
- Configuration dataclass for Jira settings
- Supports:
  - API URL and authentication
  - Project filtering
  - Status mapping between Jira and MKanban
  - Polling intervals
  - Bidirectional sync settings

#### **JiraEventProcessor** (`src/daemon/jira/jira_event_processor.py`)
- Processes Jira ticket changes
- Generates events for:
  - Ticket creation
  - Status changes
  - Updates
  - Deletions
- Maps Jira statuses to MKanban columns

#### **JiraSyncCoordinator** (`src/daemon/jira/jira_sync_coordinator.py`)
- Orchestrates synchronization between Jira and MKanban
- Handles:
  - Creating items from tickets
  - Updating existing items
  - Moving items between columns
  - Bidirectional sync back to Jira

#### **JiraDaemon** (`src/daemon/jira/jira_daemon.py`)
- Main daemon service for Jira integration
- Manages polling intervals and error handling
- Integrates with existing ServiceManager

### 2. Data Model Extensions

#### **JiraMetadata** (`src/domain/entities/item.py`)
- Extended Item model with Jira-specific metadata
- Includes:
  - Ticket key, ID, URL
  - Project information
  - Priority, assignee, reporter
  - Labels and components
  - Sync timestamps

#### **Storage Integration**
- Updated MarkdownStorageImpl to handle Jira metadata
- Maintains backward compatibility with existing items

### 3. Branch-Ticket Linking

#### **BranchTicketLinker** (`src/daemon/jira/branch_ticket_linker.py`)
- Automatically links git branches to Jira tickets
- Features:
  - Extracts ticket keys from branch names (e.g., `feature/PROJ-123-login`)
  - Creates bidirectional links between git and Jira items
  - Updates status when branches change
  - Cleanup of orphaned links

### 4. Service Integration

#### **ServiceManager Extensions**
- Integrated Jira daemon into existing service lifecycle
- Added methods for Jira-specific operations
- Supports running git and Jira daemons simultaneously

#### **CLI Extensions**
- Extended mkanban-daemon script with Jira options
- Supports configuration via command line or environment variables

## Usage

### Installation

1. Install dependencies:
```bash
pip install aiohttp python-dotenv
```

2. Set up Jira credentials:
```bash
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

### Basic Usage

```bash
# Start daemon with Jira integration
mkanban-daemon \
  --enable-jira \
  --jira-url "https://company.atlassian.net" \
  --jira-projects "PROJ,FEAT" \
  --jira-board-name "jira-tickets" \
  --jira-polling-interval 300 \
  --jira-bidirectional-sync
```

### Configuration Options

- `--enable-jira`: Enable Jira integration
- `--jira-url`: Jira instance URL
- `--jira-username`: Jira username (or JIRA_USERNAME env var)
- `--jira-api-token`: Jira API token (or JIRA_API_TOKEN env var)
- `--jira-projects`: Comma-separated project keys
- `--jira-board-name`: MKanban board name for Jira tickets
- `--jira-polling-interval`: Polling interval in seconds
- `--jira-bidirectional-sync`: Enable bidirectional sync
- `--jira-jql-filter`: Additional JQL filter

## Architecture

### Data Flow

1. **Jira → MKanban**:
   - JiraDaemon polls Jira API for changes
   - JiraEventProcessor analyzes changes
   - JiraSyncCoordinator updates MKanban items

2. **Git → Jira Linking**:
   - Git events trigger branch analysis
   - BranchTicketLinker extracts ticket keys
   - Creates links between git branches and Jira tickets

3. **MKanban → Jira** (if bidirectional sync enabled):
   - Column changes trigger Jira status updates
   - Comments added with git commit references

### File Structure

```
src/daemon/jira/
├── __init__.py                 # Module exports
├── jira_client.py             # Jira API client
├── jira_daemon.py             # Main daemon service
├── jira_sync_coordinator.py   # Sync orchestration
├── jira_event_processor.py    # Event processing
└── branch_ticket_linker.py    # Branch-ticket linking
```

## Configuration Examples

### Environment Variables
```bash
export JIRA_URL="https://company.atlassian.net"
export JIRA_USERNAME="user@company.com"
export JIRA_API_TOKEN="ATATT3xFfGF0..."
```

### Status Mapping
The default status mapping is:
- Jira "To Do" → MKanban "to-do"
- Jira "In Progress" → MKanban "in-progress"
- Jira "Done" → MKanban "done"

### Branch Patterns
Branch names are automatically scanned for ticket keys:
- `feature/PROJ-123-login-fix` → Links to PROJ-123
- `bugfix/FEAT-456` → Links to FEAT-456
- `PROJ-789/new-feature` → Links to PROJ-789

## Future Enhancements

Potential improvements for Linear and other PM tools:

1. **Linear Integration**: Similar structure with GraphQL client
2. **Multiple PM Apps**: Support running multiple PM daemons simultaneously
3. **Webhook Support**: Real-time updates instead of polling
4. **Custom Field Mapping**: Map additional Jira fields to MKanban metadata
5. **Advanced Linking**: Support multiple tickets per branch
6. **Conflict Resolution**: Handle conflicts when both systems are updated

## Testing

To test the implementation:

1. Install dependencies: `pip install -r requirements.txt`
2. Set up Jira credentials
3. Run syntax check: `python -m py_compile src/daemon/jira/*.py`
4. Start daemon with `--enable-jira` flag

The implementation follows the existing patterns in the MKanban codebase and provides a solid foundation for extending to other project management tools.