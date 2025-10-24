import React, { useEffect, useState, useCallback, useLayoutEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  TextInput,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { Board } from '../../domain/entities/Board';
import { getBoardService } from '../../core/DependencyContainer';
import EmptyState from '../components/EmptyState';
import theme from '../theme';
import alertService from '../../services/AlertService';
import logger from '../../utils/logger';

type BoardListScreenNavigationProp = StackNavigationProp<RootStackParamList, 'BoardList'>;

interface Props {
  navigation: BoardListScreenNavigationProp;
}

export default function BoardListScreen({ navigation }: Props) {
  const [boards, setBoards] = useState<Board[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newBoardName, setNewBoardName] = useState('');
  const [newBoardDescription, setNewBoardDescription] = useState('');

  const boardService = getBoardService();

  // Add settings button to header
  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity
          onPress={() => navigation.navigate('Settings')}
          style={{ marginRight: 16 }}
        >
          <Text style={{ fontSize: 20, color: theme.header.text }}>⚙️</Text>
        </TouchableOpacity>
      ),
    });
  }, [navigation]);

  const loadBoards = useCallback(async () => {
    try {
      const allBoards = await boardService.getAllBoards();
      setBoards(allBoards);
    } catch (error) {
      logger.error('Failed to load boards', error);
      alertService.showError('Failed to load boards');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [boardService]);

  useEffect(() => {
    loadBoards();
  }, [loadBoards]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadBoards();
  }, [loadBoards]);

  const handleCreateBoard = async () => {
    if (!newBoardName.trim()) {
      alertService.showValidationError('Board name is required');
      return;
    }

    try {
      const newBoard = await boardService.createBoard(
        newBoardName.trim(),
        newBoardDescription.trim() || undefined
      );

      if (newBoard) {
        // Add default columns: to-do, in-progress, done
        await boardService.addColumnToBoard(newBoard, 'to-do');
        await boardService.addColumnToBoard(newBoard, 'in-progress');
        await boardService.addColumnToBoard(newBoard, 'done');

        // Save the board with the new columns
        await boardService.saveBoard(newBoard);

        setShowCreateDialog(false);
        setNewBoardName('');
        setNewBoardDescription('');
        await loadBoards();
        // Navigate to the new board
        navigation.navigate('Board', { boardId: newBoard.id });
      }
    } catch (error) {
      logger.error('Failed to create board', error, { name: newBoardName });
      alertService.showError('Failed to create board');
    }
  };

  const handleBoardPress = (board: Board) => {
    navigation.navigate('Board', { boardId: board.id });
  };

  const getTotalItemCount = (board: Board): number => {
    return board.columns.reduce((total, column) => total + column.items.length, 0);
  };

  const renderBoardCard = ({ item: board }: { item: Board }) => (
    <TouchableOpacity
      style={styles.boardCard}
      onPress={() => handleBoardPress(board)}
      activeOpacity={theme.ui.PRESSED_OPACITY}
    >
      <Text style={styles.boardName}>{board.name}</Text>
      {board.description && (
        <Text style={styles.boardDescription} numberOfLines={2}>
          {board.description}
        </Text>
      )}
      <View style={styles.boardFooter}>
        <Text style={styles.boardStats}>
          {board.columns.length} columns • {getTotalItemCount(board)} items
        </Text>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.loadingText}>Loading boards...</Text>
      </View>
    );
  }

  if (showCreateDialog) {
    return (
      <View style={styles.container}>
        <View style={styles.dialogContainer}>
          <Text style={styles.dialogTitle}>Create New Board</Text>

          <TextInput
            style={styles.input}
            placeholder="Board Name *"
            value={newBoardName}
            onChangeText={setNewBoardName}
            autoFocus
          />

          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Description (optional)"
            value={newBoardDescription}
            onChangeText={setNewBoardDescription}
            multiline
            numberOfLines={4}
          />

          <View style={styles.dialogButtons}>
            <TouchableOpacity
              style={[styles.dialogButton, styles.cancelButton]}
              onPress={() => {
                setShowCreateDialog(false);
                setNewBoardName('');
                setNewBoardDescription('');
              }}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.dialogButton, styles.createButton]}
              onPress={handleCreateBoard}
            >
              <Text style={styles.createButtonText}>Create</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {boards.length === 0 ? (
        <EmptyState
          title="No Boards Yet"
          message="Create your first board to start organizing your tasks"
          actionLabel="Create Board"
          onAction={() => setShowCreateDialog(true)}
        />
      ) : (
        <FlatList
          data={boards}
          renderItem={renderBoardCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}

      {/* Floating Action Button */}
      {boards.length > 0 && (
        <TouchableOpacity
          style={styles.fab}
          onPress={() => setShowCreateDialog(true)}
        >
          <Text style={styles.fabText}>+</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background.primary,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.background.primary,
  },
  loadingText: {
    ...theme.typography.textStyles.body,
    color: theme.text.secondary,
  },
  listContent: {
    padding: theme.spacing.lg,
  },
  boardCard: {
    backgroundColor: theme.card.background,
    borderRadius: theme.radius.card,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.card.border,
    ...theme.shadows.card,
  },
  boardName: {
    ...theme.typography.textStyles.h3,
    color: theme.text.primary,
    marginBottom: theme.spacing.xs,
  },
  boardDescription: {
    ...theme.typography.textStyles.body,
    color: theme.text.secondary,
    marginBottom: theme.spacing.md,
  },
  boardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  boardStats: {
    ...theme.typography.textStyles.bodySmall,
    color: theme.text.tertiary,
  },
  fab: {
    position: 'absolute',
    right: theme.spacing.xl,
    bottom: theme.spacing.xl,
    width: theme.ui.FAB_SIZE,
    height: theme.ui.FAB_SIZE,
    borderRadius: theme.radius.fab,
    backgroundColor: theme.accent.primary,
    justifyContent: 'center',
    alignItems: 'center',
    ...theme.shadows.fab,
  },
  fabText: {
    color: theme.button.primary.text,
    fontSize: theme.typography.fontSizes.display,
    fontWeight: theme.typography.fontWeights.light,
  },
  dialogContainer: {
    flex: 1,
    padding: theme.spacing.xl,
    backgroundColor: theme.modal.background,
  },
  dialogTitle: {
    ...theme.typography.textStyles.h1,
    color: theme.text.primary,
    marginBottom: theme.spacing.xl,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.input.border,
    borderRadius: theme.radius.input,
    padding: theme.spacing.md,
    fontSize: theme.typography.fontSizes.lg,
    marginBottom: theme.spacing.lg,
    backgroundColor: theme.input.background,
    color: theme.input.text,
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  dialogButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: theme.spacing.xl,
  },
  dialogButton: {
    paddingHorizontal: theme.spacing.buttonPadding.horizontal,
    paddingVertical: theme.spacing.buttonPadding.vertical,
    borderRadius: theme.radius.button,
    marginLeft: theme.spacing.md,
  },
  cancelButton: {
    backgroundColor: theme.button.secondary.background,
  },
  cancelButtonText: {
    color: theme.button.secondary.text,
    ...theme.typography.textStyles.button,
  },
  createButton: {
    backgroundColor: theme.button.primary.background,
  },
  createButtonText: {
    color: theme.button.primary.text,
    ...theme.typography.textStyles.button,
  },
});
