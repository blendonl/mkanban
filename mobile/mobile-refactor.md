# Mobile App Refactoring Plan

## Overview
Comprehensive refactoring to eliminate code duplicates, remove hard-coded values, implement design patterns, and improve maintainability.

---

## 1. **Create UI Design System** (Foundation)

### 1.1 Create `src/ui/theme/spacing.ts`
- Extract all magic numbers for spacing (4, 8, 12, 16, 24, etc.)
- Define semantic spacing scale (xs, sm, md, lg, xl, xxl)

### 1.2 Create `src/ui/theme/typography.ts`
- Centralize font sizes (10, 12, 13, 14, 16, 18, 20, 24)
- Define font weights (300, 400, 500, 600, bold)
- Define line heights

### 1.3 Create `src/ui/theme/radius.ts`
- Extract border radius values (6, 8, 12, 28)
- Define semantic radius scale (sm, md, lg, pill)

### 1.4 Create `src/ui/theme/shadows.ts`
- Centralize shadow definitions
- Platform-specific shadow configurations

### 1.5 Update `src/ui/theme/index.ts`
- Export unified theme object combining colors, spacing, typography, radius, shadows

---

## 2. **Eliminate Code Duplication**

### 2.1 Create Base Modal Component
**New file:** `src/ui/components/BaseModal.tsx`
- Shared overlay pattern
- Shared header with close button
- Configurable footer
- Reusable by ParentManagementModal, MoveToColumnModal, ParentFormModal

### 2.2 Create Centralized Alert Service
**New file:** `src/services/AlertService.ts`
- Replace 39 instances of `Alert.alert`
- Methods: showError, showSuccess, showConfirm, showInfo
- Consistent messaging and styling
- Testable and mockable

### 2.3 Create Loading State Hook
**New file:** `src/ui/hooks/useLoadingState.ts`
- Shared loading/error/data state management
- Used by BoardScreen, BoardListScreen, ItemDetailScreen
- Reduces boilerplate by ~50 lines per screen

### 2.4 Create Shared Button Components
**New file:** `src/ui/components/Button.tsx`
- PrimaryButton, SecondaryButton, DangerButton, SuccessButton
- Consistent styling and behavior
- Loading state support

### 2.5 Create Shared Input Components
**New file:** `src/ui/components/Input.tsx`
- TextInput wrapper with consistent styling
- TextArea component
- Form validation integration

### 2.6 Centralize Issue Type Icons
**New file:** `src/utils/issueTypeUtils.ts`
- Single source of truth for ISSUE_TYPE_ICONS mapping
- getIssueTypeIcon() utility function
- Remove duplication from ItemCard.tsx and ItemDetailScreen.tsx

---

## 3. **Remove Hard-Coded Values**

### 3.1 Fix App.tsx Hard-Coded Colors
- Line 36: Replace `'#1a1a1a'` with `theme.background.primary`
- Line 36: Replace `'#007AFF'` with `theme.accent.primary`

### 3.2 Fix BoardScreen Inline Styles
- Line 79: Replace inline `gap: 8` with styled component

### 3.3 Create Constants File for UI
**New file:** `src/ui/theme/uiConstants.ts`
- DESCRIPTION_PREVIEW_LENGTH = 100
- PARENT_NAME_MAX_LENGTH = 100
- DEFAULT_COLUMN_WIDTH = 280
- FAB_SIZE = 56
- etc.

### 3.4 Replace Magic Numbers Throughout
- Update all 17 files using StyleSheet.create
- Replace hard-coded values with theme tokens
- Use semantic naming (spacing.md instead of 12)

---

## 4. **Implement Better Patterns**

### 4.1 Create Logger Utility
**New file:** `src/utils/logger.ts`
- Replace 206 console.log statements
- Support log levels (debug, info, warn, error)
- Environment-aware (dev vs production)
- Structured logging with context

### 4.2 Create Custom Hooks Library
**New files in:** `src/ui/hooks/`
- `useBoards.ts` - Board data fetching and caching
- `useBoardById.ts` - Single board fetching
- `useItems.ts` - Item operations
- `useRefresh.ts` - Pull-to-refresh logic
- `useDebounce.ts` - Debouncing utility
- `usePermissions.ts` - Permission checking

### 4.3 Create Error Boundary Service
**New file:** `src/services/ErrorHandlingService.ts`
- Centralized error handling
- Error reporting and logging
- User-friendly error messages

### 4.4 Create Form Validation Utilities
**New file:** `src/utils/validation.ts`
- Reusable validation functions
- Integration with ValidationService
- Form-level validation helpers

### 4.5 Implement Higher-Order Components
**New file:** `src/ui/hoc/withLoading.tsx`
- HOC for loading state wrapper
- Reduces boilerplate in screens

---

## 5. **Address TODOs and Technical Debt**

### 5.1 Fix ActionService.ts
- Implement task existence check
- Integrate with ItemService

### 5.2 Fix ActionEngine.ts
- Implement property checking condition
- Implement inactivity checking for all tasks

### 5.3 Fix MissedActionsManager.ts
- Implement action execution through ActionEngine

### 5.4 Fix MarkCompleteExecutorImpl.ts
- Make 'done' column name configurable
- Use constant from configuration

---

## 6. **Improve Type Safety**

### 6.1 Create Centralized Type Definitions
**New file:** `src/ui/types/index.ts`
- Navigation prop types
- Component prop types
- Shared interface definitions

### 6.2 Create Utility Types
**New file:** `src/core/utilityTypes.ts`
- Common type utilities
- Type guards
- Type predicates

---

## 7. **Style Consolidation**

### 7.1 Create Shared Style Utilities
**New file:** `src/ui/styles/commonStyles.ts`
- Common style objects (centerContainer, flexRow, etc.)
- Shared component styles

### 7.2 Refactor Component Styles
- Extract duplicate styles across components
- Use theme tokens consistently
- Remove inline styles where possible

---

## 8. **Testing Infrastructure Improvements**

### 8.1 Create Test Utilities
**New file:** `src/__tests__/testUtils.ts`
- Mock factories for entities
- Test data generators
- Common test helpers

### 8.2 Add Component Test Coverage
- Add tests for new shared components
- Test custom hooks
- Test utilities

---

## Implementation Order (Priority-based)

### Phase 1: Foundation (Week 1)
1. Create theme system (spacing, typography, radius, shadows)
2. Create logger utility
3. Create AlertService
4. Create issueTypeUtils

### Phase 2: Component Library (Week 2)
5. Create BaseModal component
6. Create Button components
7. Create Input components
8. Create custom hooks (useLoadingState, useBoards, etc.)

### Phase 3: Refactor Existing Code (Week 3)
9. Update all screens to use new theme tokens
10. Replace Alert.alert with AlertService
11. Replace console.log with Logger
12. Update modals to use BaseModal

### Phase 4: Technical Debt (Week 4)
13. Address all TODOs
14. Add test coverage
15. Update documentation

---

## Expected Benefits

- **Code Reduction:** ~30% reduction in component code
- **Maintainability:** Single source of truth for styles and patterns
- **Type Safety:** Better type coverage and compile-time checks
- **Developer Experience:** Easier to build new features
- **Consistency:** Unified UI/UX across the app
- **Testability:** Better separation of concerns and testable utilities
- **Performance:** Reduced re-renders with proper memoization in base components

---

## Breaking Changes
None - all changes are backward compatible refactorings

## Testing Strategy
- Unit tests for all new utilities and services
- Integration tests for refactored screens
- Visual regression testing for UI components
- Manual QA on Android and iOS devices
