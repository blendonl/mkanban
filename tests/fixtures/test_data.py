from pathlib import Path
from typing import Dict, List, Any

# Sample board data for testing
SAMPLE_BOARD_MARKDOWN = """---
name: Test Board
description: A test board for unit testing
columns:
  - name: To Do
    position: 0
  - name: In Progress
    position: 1
  - name: Done
    position: 2
parents:
  - name: Epic 1
    color: blue
    description: First test epic
---

# Test Board

A test board used for unit testing the MKanban application.

## Features
- Column management
- Item tracking
- Parent grouping
"""

# Sample item data
SAMPLE_ITEM_MARKDOWN = """---
title: Test Task
description: A sample task for testing
status: To Do
tags:
  - test
  - sample
priority: medium
estimated_hours: 4
---

# Test Task

This is a sample task created for testing purposes.

## Acceptance Criteria
- [ ] Create test cases
- [ ] Implement functionality
- [ ] Update documentation

## Notes
This task is part of the test suite and should be used for validation only.
"""

# Sample item with parent
SAMPLE_ITEM_WITH_PARENT_MARKDOWN = """---
title: Feature Implementation
description: Implement new feature as part of epic
status: In Progress
tags:
  - feature
  - backend
parent_id: epic-1
priority: high
estimated_hours: 8
---

# Feature Implementation

Implement the new feature as defined in the epic requirements.

## Implementation Details
- Database schema updates
- API endpoint creation
- Business logic implementation

## Dependencies
- Epic 1 specifications
- Database migration scripts
"""

# Configuration test data
TEST_CONFIG_DATA = {
    "data_dir": "/tmp/test_mkanban",
    "log_level": "DEBUG",
    "jira": {
        "enabled": False,
        "url": "https://test.atlassian.net",
        "username": "test@example.com",
        "api_token": "fake_token_for_testing"
    },
    "git": {
        "enabled": True,
        "auto_create_tasks": True,
        "branch_patterns": [
            "feature/*",
            "bug/*",
            "hotfix/*"
        ]
    },
    "tmux": {
        "enabled": True,
        "session_prefix": "mkanban"
    }
}

# Sample file structure for testing
TEST_FILE_STRUCTURE = {
    "boards": {
        "test-board": {
            "kanban.md": SAMPLE_BOARD_MARKDOWN,
            "to-do": {
                "test-task.md": SAMPLE_ITEM_MARKDOWN,
                "another-task.md": """---
title: Another Task
description: Another sample task
status: To Do
tags: [test]
---

# Another Task

Another test task.
"""
            },
            "in-progress": {
                "feature-implementation.md": SAMPLE_ITEM_WITH_PARENT_MARKDOWN
            },
            "done": {
                "completed-task.md": """---
title: Completed Task
description: A task that was completed
status: Done
tags: [test, completed]
completed_at: 2024-01-15T10:30:00Z
---

# Completed Task

This task has been completed successfully.
"""
            }
        },
        "another-board": {
            "kanban.md": """---
name: Another Board
description: Second test board
columns:
  - name: Backlog
    position: 0
  - name: Active
    position: 1
  - name: Review
    position: 2
  - name: Complete
    position: 3
---

# Another Board

A second test board with different columns.
"""
        }
    },
    "logs": {},
    "config.json": """{
    "data_dir": "/tmp/test_mkanban",
    "log_level": "INFO"
}"""
}

# Git test data
GIT_BRANCH_PATTERNS = [
    "feature/user-authentication",
    "bug/login-validation",
    "hotfix/security-patch",
    "feature/board-sharing",
    "bug/column-ordering"
]

# JIRA test data
JIRA_TICKET_DATA = [
    {
        "key": "PROJ-123",
        "summary": "Implement user authentication",
        "description": "Add login and logout functionality",
        "status": "To Do",
        "assignee": "test@example.com",
        "priority": "High"
    },
    {
        "key": "PROJ-124",
        "summary": "Fix column ordering bug",
        "description": "Columns are not maintaining their order",
        "status": "In Progress",
        "assignee": "test@example.com",
        "priority": "Medium"
    },
    {
        "key": "PROJ-125",
        "summary": "Add board sharing feature",
        "description": "Allow users to share boards with team members",
        "status": "Done",
        "assignee": "test@example.com",
        "priority": "Low"
    }
]

# Validation test cases
VALIDATION_TEST_CASES = {
    "valid_board_names": [
        "My Board",
        "Project Alpha",
        "Sprint-1",
        "Team_Board",
        "Board123"
    ],
    "invalid_board_names": [
        "",
        "   ",
        "a" * 256,  # Too long
        "Board/With/Slashes",
        "Board\nWith\nNewlines"
    ],
    "valid_column_names": [
        "To Do",
        "In Progress",
        "Done",
        "Review",
        "Backlog"
    ],
    "invalid_column_names": [
        "",
        "   ",
        "a" * 256,  # Too long
        "Column/With/Slashes"
    ],
    "valid_item_titles": [
        "Task 1",
        "Implement feature",
        "Fix bug #123",
        "Review code",
        "Deploy to production"
    ],
    "invalid_item_titles": [
        "",
        "   ",
        "a" * 256,  # Too long
        "Title\nWith\nNewlines"
    ]
}

# Performance test data
PERFORMANCE_TEST_DATA = {
    "large_board_items": 1000,
    "many_boards_count": 50,
    "many_columns_count": 20,
    "stress_test_operations": 10000
}

# Error scenarios for testing
ERROR_SCENARIOS = {
    "file_not_found": "/nonexistent/path/to/file.md",
    "permission_denied": "/root/restricted_file.md",
    "invalid_yaml": """---
invalid: yaml: content:
  - missing quotes
  - improper indentation
---""",
    "corrupted_markdown": """---
title: Valid YAML
---

# Corrupted Content
This file has been corrupted and contains invalid characters: \x00\x01\x02
""",
    "network_timeout": "https://timeout.example.com/api",
    "jira_auth_failure": {
        "status_code": 401,
        "message": "Authentication failed"
    },
    "git_repository_error": "Not a git repository"
}

# Mock responses for external services
MOCK_RESPONSES = {
    "jira_search_success": {
        "issues": JIRA_TICKET_DATA,
        "total": len(JIRA_TICKET_DATA),
        "startAt": 0,
        "maxResults": 50
    },
    "jira_auth_error": {
        "errorMessages": ["Invalid credentials"],
        "errors": {}
    },
    "git_status_clean": "On branch main\nnothing to commit, working tree clean",
    "git_status_dirty": """On branch feature/test
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git checkout -- <file>..." to discard changes in working directory)

        modified:   src/test.py

no changes added to commit (use "git add" and/or "git commit")""",
    "tmux_list_sessions": """test-session: 1 windows (created Mon Jan 15 10:30:00 2024)
mkanban-dev: 2 windows (created Mon Jan 15 09:00:00 2024)"""
}