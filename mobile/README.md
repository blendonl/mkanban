# MKanban Mobile

A mobile Kanban board application for iOS and Android, built with React Native and TypeScript. Fully compatible with MKanban Desktop (Python TUI version).

## Features

### Core Functionality
- ✅ **Board Management** - Create, view, edit, and delete multiple boards
- ✅ **Column-based Organization** - Organize tasks in customizable columns
- ✅ **Item Management** - Create, edit, move, and delete tasks
- ✅ **Parent Grouping** - Hierarchical task organization with color-coded parents
- ✅ **Markdown Storage** - All data stored as markdown files with YAML frontmatter
- ✅ **File Sync** - Compatible with iCloud, Dropbox, Google Drive, Syncthing
- ✅ **Desktop Compatible** - Same markdown format as Python desktop version

### User Experience
- 🎨 **Modern UI** - Clean, intuitive interface with smooth animations
- 📱 **Native Feel** - Platform-specific behaviors for iOS and Android
- ⚡ **Performance** - Virtualized lists handle thousands of items smoothly
- 🔄 **Pull-to-Refresh** - Easy data refresh with pull gesture
- 💫 **Haptic Feedback** - Tactile responses for important actions
- 🎯 **Gesture Support** - Long-press to move items, swipe navigation

### Advanced Features
- 🏷️ **Issue Types** - Task, Story, Bug, Epic, Subtask with icons
- 🎨 **Color-Coded Parents** - 7 colors for visual organization
- 📊 **Parent Grouping View** - Toggle between flat and grouped views
- ⏱️ **Timestamp Tracking** - Created, moved, and worked-on timestamps
- 📝 **Markdown Preview** - Preview formatted descriptions
- ⚙️ **Settings** - Configure storage path and app preferences

## Tech Stack

- **Framework:** React Native (Expo)
- **Language:** TypeScript
- **Navigation:** React Navigation
- **File System:** expo-file-system
- **Markdown:** gray-matter, js-yaml
- **Testing:** Jest, React Native Testing Library
- **Architecture:** Clean Architecture with Dependency Injection

## Installation

### Prerequisites
- Node.js 18+ and npm
- Expo CLI: `npm install -g expo-cli`
- For iOS: Xcode and iOS Simulator
- For Android: Android Studio and Android emulator

### Setup

```bash
# Clone repository
cd mobile

# Install dependencies
npm install

# Start development server
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

## Project Structure

```
mobile/
├── src/
│   ├── core/                   # Core types, constants, DI container
│   ├── domain/                 # Entities and repository interfaces
│   │   ├── entities/          # Board, Column, Item, Parent
│   │   └── repositories/      # Repository interfaces
│   ├── services/              # Business logic services
│   │   ├── BoardService.ts
│   │   ├── ItemService.ts
│   │   └── ValidationService.ts
│   ├── infrastructure/        # Implementation details
│   │   ├── storage/          # Markdown repositories
│   │   └── daemon/           # File change detection
│   ├── ui/                    # React Native UI
│   │   ├── screens/          # App screens
│   │   ├── components/       # Reusable components
│   │   └── navigation/       # Navigation setup
│   └── utils/                 # Utility functions
├── __tests__/                 # Test files
├── jest.config.js
├── package.json
└── README.md
```

## Usage

### Creating a Board

1. Tap the "+" button on the board list screen
2. Enter board name and optional description
3. Tap "Create"

### Adding Items

1. Open a board
2. Tap "+ Add Item" at the bottom of a column
3. Enter title, description, and optional parent
4. Select issue type (Task, Story, Bug, Epic, Subtask)
5. Tap "Save"

### Moving Items

**Method 1: Long Press**
1. Long-press on any item
2. Select target column from the modal
3. Item moves instantly

**Method 2: Edit Screen**
1. Tap on an item to edit
2. Use the move functionality (if available)

### Managing Parents

1. Tap "🏷️ Parents" button in board screen
2. Create new parents with name and color
3. Assign parents to items in item detail screen
4. Toggle "📁 Groups" to see grouped view

### Settings

1. Tap ⚙️ icon on board list screen
2. View boards directory path
3. Configure storage settings
4. View app information

## File Sync Setup

### iCloud (iOS)

1. Enable iCloud Drive on your device
2. Move MKanban boards folder to iCloud Drive
3. Update path in Settings

### Dropbox

1. Install Dropbox app
2. Move boards folder to Dropbox
3. Update path in Settings

### Syncthing

1. Install Syncthing on all devices
2. Share boards folder
3. Configure sync settings

## Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

See [TESTING.md](./TESTING.md) for detailed testing documentation.

## Development

### Code Style

- TypeScript strict mode enabled
- ESLint for linting
- Prettier for formatting
- React hooks for state management

### Architecture

The app follows Clean Architecture principles:

- **Domain Layer:** Pure business entities
- **Service Layer:** Business logic
- **Infrastructure Layer:** External dependencies
- **UI Layer:** React Native components

Dependency Injection is used throughout for testability.

### Adding New Features

1. Create entities in `domain/entities/`
2. Define service methods in `services/`
3. Implement UI in `ui/screens/` or `ui/components/`
4. Write tests for all layers
5. Update this README

## Compatibility

### Python Desktop Version

This mobile app uses the same markdown file format as the Python desktop version (MKanban TUI). You can:

- ✅ Create boards on mobile, edit on desktop
- ✅ Create tasks on desktop, view on mobile
- ✅ Use both simultaneously with file sync
- ✅ Switch between platforms seamlessly

### File Format

**Board File (kanban.md):**
```yaml
---
id: my-project
name: My Project
description: Project description
parents:
  - id: feature-x
    name: Feature X
    color: blue
    created_at: 2025-01-15T10:00:00.000Z
created_at: 2025-01-15T10:00:00.000Z
---

# My Project
```

**Item File (MKA-1-task-name.md):**
```yaml
---
id: MKA-1
title: Fix bug
parent_id: feature-x
metadata:
  issue_type: Bug
created_at: 2025-01-15T10:30:00.000Z
---

# Fix bug

Detailed description here...
```

## Performance

- **Virtualized Lists:** FlatList for smooth scrolling with 1000+ items
- **Memoization:** React.memo on all list components
- **Lazy Loading:** Load boards on demand
- **Debounced Operations:** File watcher with 3-second polling

## Troubleshooting

### App Won't Start

```bash
# Clear cache and restart
expo start -c
```

### Tests Failing

```bash
# Clear Jest cache
npm test -- --clearCache
```

### File Sync Issues

1. Check file permissions
2. Verify sync service is running
3. Check boards directory path in Settings

## Roadmap

### v1.1 (Post-MVP)
- [ ] Drag-and-drop item movement
- [ ] Rich markdown editor
- [ ] Search and filter
- [ ] Dark mode
- [ ] Custom themes

### v1.2
- [ ] Offline mode
- [ ] Push notifications
- [ ] Home screen widgets
- [ ] Share extension

### v2.0
- [ ] Cloud sync service
- [ ] Collaboration features
- [ ] Real-time updates
- [ ] Web version

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license here]

## Credits

- Built with React Native and Expo
- Icons from built-in emoji set
- Inspired by Trello and GitHub Projects

## Support

- GitHub Issues: [Link to issues]
- Email: [Your email]
- Discord: [Link to Discord]

---

**Version:** 1.0.0
**Last Updated:** 2025-10-15
**Status:** Production Ready (98% complete)
