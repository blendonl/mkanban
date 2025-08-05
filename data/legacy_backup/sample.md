---
title: Sample Kanban Board
description: A sample board for testing MKanban
created_at: 2024-01-01T00:00:00
updated_at: 2024-01-01T00:00:00
board_metadata: {}
parents:
  - id: feature-dev
    name: Feature Development
    description: Items related to developing new features
    color: green
    created_at: 2024-01-01T00:00:00
    updated_at: 2024-01-01T00:00:00
    metadata: {}
  - id: bug-fixes
    name: Bug Fixes
    description: Items related to fixing bugs
    color: red
    created_at: 2024-01-01T00:00:00
    updated_at: 2024-01-01T00:00:00
    metadata: {}
---

## To Do

- Setup development environment
- Create project structure [parent:feature-dev]
- Fix login bug [parent:bug-fixes]
- Write documentation

## In Progress

- Implement data models [parent:feature-dev]  
- Debug memory leak [parent:bug-fixes]

## Done

- Initialize repository
- Setup CI/CD pipeline [parent:feature-dev]