# MKanban Mobile MVP - Implementation Plan

**Target Platform:** React Native (iOS + Android)
**Architecture:** Keep Python desktop app, build separate mobile app with shared markdown file format
**Timeline:** 10-12 weeks to production-ready MVP
**Status:** Planning Phase

---

## 🎯 MVP Scope

### Core Principles
- **No server/API** - direct file system operations only
- **Shared markdown format** - desktop and mobile use identical file structure
- **Feature separation** - mobile doesn't need tmux/git/JIRA (desktop-only)
- **Clean architecture** - port domain/service layers from Python
- **File-based sync** - users handle via iCloud/Dropbox/Syncthing

### ✅ MVP Features (Must Have)

**Board Management**
- View list of all boards
- Create new board
- Delete board
- Switch between boards

**Column Management**
- Display columns horizontally
- Default columns: To Do, In Progress, Done
- Reorder columns (optional for MVP)

**Item Management**
- Create item in column
- Edit item (title, description, parent)
- Delete item
- Move item between columns (drag-and-drop)

**Parent Grouping**
- Create parent/project
- Assign items to parents
- Toggle parent grouping view
- Color-coded parent badges

**Storage**
- Read/write markdown files with YAML frontmatter
- Maintain identical file structure to desktop app
- Validate markdown format

**Daemon/Sync**
- Background file watcher
- Detect external file changes
- Auto-reload when files modified
- Conflict detection (basic)

### ❌ Deferred Features (Post-MVP)

**Desktop-Only Features**
- Git branch monitoring
- Tmux session integration
- JIRA bidirectional sync (for now)

**Advanced Features**
- Cloud sync configuration
- Custom themes
- Rich markdown editor
- Item attachments
- Search/filter
- Column WIP limits
- Task reminders
- Home screen widgets
- Work duration tracking
- Auto-save intervals (mobile saves immediately)

---

## 📁 Project Structure

```
mkanban-mobile/
├── src/
│   ├── domain/              # Core entities (ported from Python)
│   │   ├── entities/
│   │   │   ├── Board.ts
│   │   │   ├── Column.ts
│   │   │   ├── Item.ts
│   │   │   └── Parent.ts
│   │   └── repositories/    # Repository interfaces
│   │       ├── BoardRepository.ts
│   │       └── StorageRepository.ts
│   │
│   ├── services/            # Business logic (ported from Python)
│   │   ├── BoardService.ts
│   │   ├── ItemService.ts
│   │   └── ValidationService.ts
│   │
│   ├── infrastructure/      # Implementation details
│   │   ├── storage/
│   │   │   ├── MarkdownBoardRepository.ts
│   │   │   ├── MarkdownStorageRepository.ts
│   │   │   ├── MarkdownParser.ts
│   │   │   └── FileSystemManager.ts
│   │   └── daemon/
│   │       └── FileWatcher.ts
│   │
│   ├── ui/                  # React Native UI
│   │   ├── screens/
│   │   │   ├── BoardListScreen.tsx
│   │   │   ├── BoardScreen.tsx
│   │   │   └── ItemDetailScreen.tsx
│   │   ├── components/
│   │   │   ├── ColumnCard.tsx
│   │   │   ├── ItemCard.tsx
│   │   │   └── ParentGroup.tsx
│   │   └── navigation/
│   │       └── AppNavigator.tsx
│   │
│   ├── core/                # Container, types, utils
│   │   ├── DependencyContainer.ts
│   │   ├── types.ts
│   │   └── constants.ts
│   │
│   └── utils/               # Helper functions
│       ├── stringUtils.ts
│       ├── dateUtils.ts
│       └── fileUtils.ts
│
├── __tests__/
├── package.json
└── README.md
```

---

## 🔄 Python → TypeScript Migration Map

### File Structure (Identical Between Platforms)

```
{boards_path}/
└── {board-name}/
    ├── kanban.md                 # Board metadata
    ├── to-do/
    │   ├── column.md            # Column metadata
    │   ├── MKA-1-fix-bug.md     # Item file
    │   └── MKA-2-feature.md
    ├── in-progress/
    │   └── column.md
    └── done/
        └── column.md
```

### Markdown Format (Same)

**Board file (kanban.md):**
```markdown
---
id: my-project
name: My Project
description: Project description
parents:
  - id: feature-x
    name: Feature X
    color: blue
    created_at: 2025-01-15T10:00:00Z
created_at: 2025-01-15T10:00:00Z
---

# My Project
```

**Item file (MKA-1-fix-bug.md):**
```markdown
---
id: MKA-1
title: Fix login bug
parent_id: feature-x
created_at: 2025-01-15T10:30:00Z
---

# Fix login bug

Detailed description here...
```

### Code Mapping

| Python Component | TypeScript Equivalent | Notes |
|-----------------|----------------------|-------|
| `src/domain/entities/board.py` | `src/domain/entities/Board.ts` | Pydantic → TypeScript classes |
| `src/domain/entities/column.py` | `src/domain/entities/Column.ts` | |
| `src/domain/entities/item.py` | `src/domain/entities/Item.ts` | Skip git_metadata |
| `src/domain/entities/parent.py` | `src/domain/entities/Parent.ts` | |
| `src/services/board_service.py` | `src/services/BoardService.ts` | |
| `src/services/item_service.py` | `src/services/ItemService.ts` | |
| `src/services/validation_service.py` | `src/services/ValidationService.ts` | |
| `src/infrastructure/storage/markdown_board_repository.py` | `src/infrastructure/storage/MarkdownBoardRepository.ts` | |
| `src/infrastructure/storage/markdown_parser.py` | `src/infrastructure/storage/MarkdownParser.ts` | |
| `src/utils/string_utils.py` | `src/utils/stringUtils.ts` | |
| `src/utils/date_utils.py` | `src/utils/dateUtils.ts` | |
| `src/utils/file_utils.py` | `src/utils/fileUtils.ts` | |

### Library Mapping

| Python Library | React Native Equivalent | Purpose |
|---------------|------------------------|---------|
| `frontmatter` | `gray-matter` | YAML frontmatter parsing |
| `pathlib.Path` | `react-native-fs` | File system operations |
| `pydantic` | TypeScript interfaces + classes | Data validation |
| `textual` | React Native UI | **Not ported** - different UI paradigm |

---

## 📋 Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Setup & Core Types**
- [ ] Initialize React Native project (Expo or bare)
- [ ] Install dependencies (react-native-fs, gray-matter, js-yaml)
- [ ] Set up TypeScript configuration
- [ ] Create folder structure

**Domain Entities**
- [ ] Port Board entity from Python
- [ ] Port Column entity from Python
- [ ] Port Item entity from Python (skip git-specific fields)
- [ ] Port Parent entity from Python
- [ ] Define repository interfaces

**Utils**
- [ ] Port string utils: `generateIdFromName`, `getSafeFilename`, `getBoardPrefix`, `generateManualItemId`
- [ ] Port date utils: `now()`, timestamp formatting
- [ ] Define constants: file names, default paths

### Phase 2: Storage Layer (Week 3-4)

**File System Manager**
- [ ] Implement FileSystemManager.ts
- [ ] ensureDirectoryExists
- [ ] readFile, writeFile, deleteFile, renameFile
- [ ] listFiles with pattern matching
- [ ] getBoardsDirectory, getBoardDirectory, getColumnDirectory

**Markdown Parser**
- [ ] Implement MarkdownParser.ts
- [ ] parseBoardMetadata using gray-matter
- [ ] parseItemMetadata
- [ ] parseColumnMetadata
- [ ] saveBoardMetadata
- [ ] saveItemWithMetadata

**Repositories**
- [ ] Implement MarkdownBoardRepository
- [ ] loadAllBoards() - scan boards directory
- [ ] loadBoardByName(name)
- [ ] saveBoard(board) - persist all data
- [ ] deleteBoard(boardId)
- [ ] Implement MarkdownStorageRepository
- [ ] saveItemToColumn
- [ ] deleteItemFromColumn
- [ ] moveItemBetweenColumns

### Phase 3: Business Logic (Week 5)

**Services**
- [ ] Implement ValidationService
- [ ] validateBoardName, validateColumnName, validateItemTitle
- [ ] validateBoard, validateColumnCapacity
- [ ] Implement BoardService
- [ ] getAllBoards, getBoardByName, createBoard, saveBoard
- [ ] addColumnToBoard, removeColumnFromBoard
- [ ] Implement ItemService
- [ ] createItem, updateItem, deleteItem
- [ ] moveItemBetweenColumns, setItemParent
- [ ] getItemsGroupedByParent

**Dependency Injection**
- [ ] Implement DependencyContainer
- [ ] Register repositories and services
- [ ] Lazy instantiation
- [ ] get(ServiceType) method

### Phase 4: File Watcher (Week 5)

**Background Daemon**
- [ ] Implement FileWatcher.ts
- [ ] Poll boards directory (every 2-5 seconds)
- [ ] Detect file changes (timestamp comparison)
- [ ] Emit events: onBoardChanged, onItemChanged
- [ ] Start/stop lifecycle management
- [ ] React Native background task integration

### Phase 5: UI Foundation (Week 6-7)

**Navigation**
- [ ] Set up React Navigation
- [ ] Create stack navigator: BoardList → Board → ItemDetail
- [ ] Configure screen options

**Board List Screen**
- [ ] Display all boards as cards
- [ ] "New Board" FAB button
- [ ] Pull-to-refresh
- [ ] Empty state UI

**Board Screen (Kanban View)**
- [ ] Horizontal ScrollView for columns
- [ ] Render columns with items
- [ ] Column header with name
- [ ] "New Item" FAB
- [ ] Parent filter toggle button

**Components**
- [ ] ColumnCard component
- [ ] ItemCard component (title, parent badge, description preview)
- [ ] ParentBadge component (color-coded)

### Phase 6: Item Management (Week 8)

**Item Detail Screen**
- [ ] Editable title input
- [ ] Markdown description editor
- [ ] Parent selector dropdown
- [ ] Save button
- [ ] Delete button with confirmation

**New Item Dialog**
- [ ] Form with title (required), description, parent
- [ ] Column selector
- [ ] Create & close
- [ ] Validation errors display

**Drag & Drop**
- [ ] Implement item drag between columns
- [ ] Visual feedback during drag
- [ ] Drop validation
- [ ] Auto-save after move

### Phase 7: Parent Management (Week 8)

**Parent Features**
- [ ] Create new parent dialog
- [ ] Color picker for parent
- [ ] Assign parent to item
- [ ] Filter items by parent (toggle view)
- [ ] Group items by parent visually

### Phase 8: Polish & Testing (Week 9-10)

**Error Handling**
- [ ] File I/O error handling
- [ ] Validation error display
- [ ] Network/offline state handling

**Settings Screen**
- [ ] Configure boards directory path
- [ ] Reset to default
- [ ] About/version info

**Performance**
- [ ] Lazy load boards
- [ ] Virtualized lists for items
- [ ] Debounce file watcher
- [ ] Memoize renders

**Testing**
- [ ] Unit tests: services, validation, utils
- [ ] Repository tests with mock files
- [ ] Integration tests: create board → add items → move items
- [ ] Cross-platform testing (iOS + Android)
- [ ] Compatibility test: same markdown files work in Python

---

## 🛠️ Technical Stack

### Core Dependencies
```json
{
  "dependencies": {
    "react-native": "^0.75.0",
    "react-native-fs": "^2.20.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/stack": "^6.4.0",
    "gray-matter": "^4.0.3",
    "js-yaml": "^4.1.0",
    "zustand": "^4.5.0",
    "react-native-gesture-handler": "^2.18.0",
    "react-native-reanimated": "^3.15.0"
  },
  "devDependencies": {
    "@types/react-native": "^0.75.0",
    "typescript": "^5.6.0",
    "jest": "^29.7.0",
    "@testing-library/react-native": "^12.8.0"
  }
}
```

---

## 📊 Code Estimates

| Layer | Python LOC | TypeScript LOC (Est.) | Complexity |
|-------|------------|----------------------|------------|
| Domain Entities | ~400 | ~300 | Low |
| Services | ~600 | ~400 | Medium |
| Storage/Repositories | ~800 | ~600 | Medium |
| Utils | ~300 | ~200 | Low |
| File Watcher | 0 (daemon) | ~150 | Medium |
| UI Components | 0 (TUI) | ~1500 | High |
| **Total** | **~2100** | **~3150** | **Medium** |

**Timeline:** 10-12 weeks (1 developer, full-time)

---

## 🧪 Testing Strategy

### Shared Test Fixtures
- Create sample markdown boards in `test/fixtures/`
- Both Python and React Native tests use same files
- Ensures 100% format compatibility

### Test Coverage
1. **Unit Tests** - utils, validation, entity methods
2. **Service Tests** - mock repositories
3. **Repository Tests** - temp directories with sample markdown
4. **Integration Tests** - end-to-end file operations
5. **Compatibility Tests** - verify Python and TypeScript can read each other's files
6. **UI Tests** - React Testing Library

---

## 🚀 Next Steps

1. ✅ Create mvp-plan.md and progress.md
2. [ ] Initialize React Native project
3. [ ] Port domain entities (Board, Column, Item, Parent)
4. [ ] Implement file system utilities
5. [ ] Build storage layer (markdown parser + repositories)

---

**Last Updated:** 2025-10-15
