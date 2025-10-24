import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import { Board } from '../../domain/entities/Board';
import { Item } from '../../domain/entities/Item';
import { getBoardService, getItemService } from '../../core/DependencyContainer';
import ColumnCard from '../components/ColumnCard';
import EmptyState from '../components/EmptyState';
import MoveToColumnModal from '../components/MoveToColumnModal';
import ParentManagementModal from '../components/ParentManagementModal';
import ParentFormModal from '../components/ParentFormModal';
import { Parent } from '../../domain/entities/Parent';
import { ParentColor } from '../../core/enums';
import { generateIdFromName, now } from '../../utils';
import theme from '../theme';
import alertService from '../../services/AlertService';
import logger from '../../utils/logger';

type BoardScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Board'>;
type BoardScreenRouteProp = RouteProp<RootStackParamList, 'Board'>;

interface Props {
  navigation: BoardScreenNavigationProp;
  route: BoardScreenRouteProp;
}

export default function BoardScreen({ navigation, route }: Props) {
  const [board, setBoard] = useState<Board | null>(null);
  const [loading, setLoading] = useState(true);
  const [showParentGroups, setShowParentGroups] = useState(false);
  const [selectedColumnId, setSelectedColumnId] = useState<string | null>(null);
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);
  const [showParentManagement, setShowParentManagement] = useState(false);
  const [showParentForm, setShowParentForm] = useState(false);
  const [editingParent, setEditingParent] = useState<Parent | null>(null);

  const boardService = getBoardService();
  const itemService = getItemService();
  const boardId = route.params.boardId;

  // Load board on mount
  useEffect(() => {
    const loadBoard = async () => {
      try {
        const loadedBoard = await boardService.getBoardById(boardId);
        if (loadedBoard) {
          setBoard(loadedBoard);
          // Update navigation title
          navigation.setOptions({ title: loadedBoard.name });
        } else {
          alertService.showError('Board not found');
          navigation.goBack();
        }
      } catch (error) {
        logger.error('Failed to load board', error, { boardId });
        alertService.showError('Failed to load board');
        navigation.goBack();
      } finally {
        setLoading(false);
      }
    };

    loadBoard();
  }, [boardId, boardService, navigation]);

  // Set up header right buttons for parent management and grouping toggle
  useEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <View style={styles.headerButtonContainer}>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setShowParentManagement(true)}
          >
            <Text style={styles.headerButtonText}>🏷️ Parents</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setShowParentGroups(!showParentGroups)}
          >
            <Text style={styles.headerButtonText}>
              {showParentGroups ? '📋 List' : '📁 Groups'}
            </Text>
          </TouchableOpacity>
        </View>
      ),
    });
  }, [navigation, showParentGroups]);

  const refreshBoard = useCallback(async () => {
    if (!board) return;

    try {
      const updatedBoard = await boardService.getBoardById(board.id);
      if (updatedBoard) {
        setBoard(updatedBoard);
      }
    } catch (error) {
      logger.error('Failed to refresh board', error, { boardId: board.id });
      alertService.showError('Failed to refresh board');
    }
  }, [board, boardService]);

  const handleItemPress = (item: Item) => {
    if (!board) return;
    navigation.navigate('ItemDetail', { boardId: board.id, itemId: item.id });
  };

  const handleItemLongPress = async (item: Item) => {
    // Trigger haptic feedback
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setSelectedItem(item);
    setShowMoveModal(true);
  };

  const handleMoveToColumn = async (targetColumnId: string) => {
    if (!selectedItem) return;

    try {
      // Find target column
      const targetColumn = board.columns.find((col) => col.id === targetColumnId);
      if (!targetColumn) {
        alertService.showError('Target column not found');
        return;
      }

      // Move item
      await itemService.moveItemBetweenColumns(board, selectedItem.id, targetColumnId);

      // Save board
      await boardService.saveBoard(board);

      // Trigger success haptic
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      // Refresh board
      await refreshBoard();

      // Close modal
      setShowMoveModal(false);
      setSelectedItem(null);
    } catch (error) {
      logger.error('Failed to move item', error, { itemId: selectedItem.id, targetColumnId });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      alertService.showError('Failed to move item');
    }
  };

  const handleAddItem = (columnId: string) => {
    if (!board) return;
    // Navigate to ItemDetail in create mode with the column ID
    setSelectedColumnId(columnId);
    navigation.navigate('ItemDetail', { boardId: board.id, columnId });
  };

  // Parent Management Handlers
  const handleCreateParent = () => {
    setEditingParent(null);
    setShowParentManagement(false);
    setShowParentForm(true);
  };

  const handleEditParent = (parent: Parent) => {
    setEditingParent(parent);
    setShowParentManagement(false);
    setShowParentForm(true);
  };

  const handleDeleteParent = async (parentId: string) => {
    try {
      // Remove parent from board
      board.parents = board.parents.filter((p) => p.id !== parentId);

      // Clear parent from items that have this parent
      board.columns.forEach((column) => {
        column.items.forEach((item) => {
          if (item.parent_id === parentId) {
            item.parent_id = undefined;
          }
        });
      });

      // Save board
      await boardService.saveBoard(board);

      // Refresh board
      await refreshBoard();

      alertService.showSuccess('Parent deleted successfully');
    } catch (error) {
      logger.error('Failed to delete parent', error, { parentId });
      alertService.showError('Failed to delete parent');
    }
  };

  const handleSaveParent = async (
    name: string,
    color: ParentColor,
    parentId?: string
  ) => {
    try {
      if (parentId) {
        // Update existing parent
        const parent = board.parents.find((p) => p.id === parentId);
        if (parent) {
          parent.name = name;
          parent.color = color;
        }
      } else {
        // Create new parent
        const newParent = new Parent(
          generateIdFromName(name),
          name,
          color,
          now()
        );
        board.parents.push(newParent);
      }

      // Save board
      await boardService.saveBoard(board);

      // Refresh board
      await refreshBoard();

      alertService.showSuccess(`Parent ${parentId ? 'updated' : 'created'} successfully`);
    } catch (error) {
      logger.error('Failed to save parent', error, { parentId, name });
      throw error; // Re-throw to be handled by the form modal
    }
  };

  // Listen for navigation changes to refresh board
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      refreshBoard();
    });

    return unsubscribe;
  }, [navigation, refreshBoard]);

  if (loading || !board) {
    return (
      <View style={styles.container}>
        <View style={styles.centerContainer}>
          <Text style={styles.loadingText}>Loading board...</Text>
        </View>
      </View>
    );
  }

  if (board.columns.length === 0) {
    return (
      <EmptyState
        title="No Columns"
        message="This board doesn't have any columns yet. Add columns through the desktop app."
      />
    );
  }

  return (
    <View style={styles.container}>
      {/* Board Info */}
      {board.description && (
        <View style={styles.descriptionContainer}>
          <Text style={styles.description}>{board.description}</Text>
        </View>
      )}

      {/* Kanban Columns */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.columnsContainer}
      >
        {board.columns.map((column) => (
          <ColumnCard
            key={column.id}
            column={column}
            parents={board.parents}
            showParentGroups={showParentGroups}
            onItemPress={handleItemPress}
            onItemLongPress={handleItemLongPress}
            onAddItem={() => handleAddItem(column.id)}
          />
        ))}
      </ScrollView>

      {/* Move to Column Modal */}
      {selectedItem && (
        <MoveToColumnModal
          visible={showMoveModal}
          columns={board.columns}
          currentColumnId={selectedItem.column_id}
          onSelectColumn={handleMoveToColumn}
          onClose={() => {
            setShowMoveModal(false);
            setSelectedItem(null);
          }}
        />
      )}

      {/* Parent Management Modal */}
      <ParentManagementModal
        visible={showParentManagement}
        parents={board.parents}
        onClose={() => setShowParentManagement(false)}
        onEdit={handleEditParent}
        onDelete={handleDeleteParent}
        onCreate={handleCreateParent}
      />

      {/* Parent Form Modal */}
      <ParentFormModal
        visible={showParentForm}
        parent={editingParent}
        onSave={handleSaveParent}
        onClose={() => {
          setShowParentForm(false);
          setEditingParent(null);
        }}
      />
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
  },
  loadingText: {
    ...theme.typography.textStyles.body,
    color: theme.text.secondary,
  },
  descriptionContainer: {
    backgroundColor: theme.background.elevated,
    padding: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.border.primary,
  },
  description: {
    ...theme.typography.textStyles.body,
    color: theme.text.secondary,
  },
  columnsContainer: {
    paddingVertical: theme.spacing.lg,
    paddingHorizontal: theme.spacing.sm,
  },
  headerButtonContainer: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  headerButton: {
    marginRight: theme.spacing.lg,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: theme.radius.button,
  },
  headerButtonText: {
    color: theme.header.text,
    ...theme.typography.textStyles.body,
    fontWeight: theme.typography.fontWeights.semibold,
  },
});
