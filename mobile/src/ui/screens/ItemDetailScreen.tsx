import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Platform,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
import { Board } from '../../domain/entities/Board';
import { Item } from '../../domain/entities/Item';
import { Parent } from '../../domain/entities/Parent';
import { IssueType } from '../../core/enums';
import { getItemService, getBoardService } from '../../core/DependencyContainer';
import ParentBadge from '../components/ParentBadge';
import theme from '../theme';
import { getIssueTypeIcon, getAllIssueTypes } from '../../utils/issueTypeUtils';
import alertService from '../../services/AlertService';
import { uiConstants } from '../theme';

type ItemDetailScreenNavigationProp = StackNavigationProp<RootStackParamList, 'ItemDetail'>;
type ItemDetailScreenRouteProp = RouteProp<RootStackParamList, 'ItemDetail'>;

interface Props {
  navigation: ItemDetailScreenNavigationProp;
  route: ItemDetailScreenRouteProp;
}

export default function ItemDetailScreen({ navigation, route }: Props) {
  const { boardId, itemId, columnId } = route.params;
  const isCreateMode = !itemId;

  const [board, setBoard] = useState<Board | null>(null);
  const [item, setItem] = useState<Item | null>(null);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedParentId, setSelectedParentId] = useState<string | null>(null);
  const [selectedIssueType, setSelectedIssueType] = useState<string>(IssueType.TASK);
  const [saving, setSaving] = useState(false);
  const [showParentPicker, setShowParentPicker] = useState(false);
  const [showIssueTypePicker, setShowIssueTypePicker] = useState(false);
  const [showMarkdownPreview, setShowMarkdownPreview] = useState(false);

  const itemService = getItemService();
  const boardService = getBoardService();

  // Load board and item on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const loadedBoard = await boardService.getBoardById(boardId);
        if (!loadedBoard) {
          alertService.showError('Board not found');
          navigation.goBack();
          return;
        }

        setBoard(loadedBoard);

        if (!isCreateMode && itemId) {
          // Find the item in the board
          let foundItem: Item | null = null;
          for (const column of loadedBoard.columns) {
            foundItem = column.items.find((i) => i.id === itemId) || null;
            if (foundItem) break;
          }

          if (!foundItem) {
            alertService.showError('Item not found');
            navigation.goBack();
            return;
          }

          setItem(foundItem);
          setTitle(foundItem.title);
          setDescription(foundItem.description || '');
          setSelectedParentId(foundItem.parent_id || null);
          setSelectedIssueType(foundItem.getIssueType());
        }
      } catch (error) {
        alertService.showError('Failed to load data');
        navigation.goBack();
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [boardId, itemId, isCreateMode, boardService, navigation]);

  // Get current column for create mode
  const targetColumn = board
    ? columnId
      ? board.columns.find((col) => col.id === columnId)
      : item
      ? board.columns.find((col) => col.items.some((i) => i.id === item.id))
      : null
    : null;

  const handleSave = async () => {
    if (!board) {
      alertService.showError('Board not loaded');
      return;
    }

    if (!title.trim()) {
      alertService.showValidationError('Item title is required');
      return;
    }

    if (!targetColumn) {
      alertService.showError('Could not determine target column');
      return;
    }

    setSaving(true);

    try {
      if (isCreateMode) {
        // Create new item
        const newItem = await itemService.createItem(
          board,
          targetColumn.id,
          title.trim(),
          description.trim() || undefined,
          selectedParentId || undefined
        );

        // Set issue type on the newly created item
        if (newItem) {
          newItem.setIssueType(selectedIssueType);
        }

        // Save the board
        await boardService.saveBoard(board);

        alertService.showSuccess('Item created successfully');
        navigation.goBack();
      } else {
        // Update existing item
        if (!item) {
          throw new Error('Item is null in edit mode');
        }

        await itemService.updateItem(board, item.id, {
          title: title.trim(),
          description: description.trim() || undefined,
          parent_id: selectedParentId || undefined,
        });

        // Update issue type
        item.setIssueType(selectedIssueType);

        // Save the board
        await boardService.saveBoard(board);

        alertService.showSuccess('Item updated successfully');
        navigation.goBack();
      }
    } catch (error) {
      alertService.showError('Failed to save item');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (isCreateMode || !item || !board) {
      return;
    }

    alertService.showDestructiveConfirm(
      'Are you sure you want to delete this item? This action cannot be undone.',
      async () => {
        try {
          await itemService.deleteItem(board, item.id);
          await boardService.saveBoard(board);

          alertService.showSuccess('Item deleted successfully');
          navigation.goBack();
        } catch (error) {
          alertService.showError('Failed to delete item');
        }
      },
      undefined,
      'Delete Item'
    );
  };

  const selectedParent = selectedParentId && board
    ? board.parents.find((p) => p.id === selectedParentId)
    : null;

  // Show loading state
  if (loading || !board) {
    return (
      <View style={[styles.container, styles.centerContainer]}>
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }


  // Helper function to format timestamp
  const formatTimestamp = (timestamp: Date | string | null): string => {
    if (!timestamp) return 'N/A';
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return date.toLocaleString();
  };

  // All available issue types
  const issueTypes = getAllIssueTypes();

  // Issue Type Picker Modal
  if (showIssueTypePicker) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.pickerHeader}>
          <Text style={styles.pickerTitle}>Select Issue Type</Text>
          <TouchableOpacity onPress={() => setShowIssueTypePicker(false)}>
            <Text style={styles.pickerClose}>Done</Text>
          </TouchableOpacity>
        </View>

        {issueTypes.map((issueType) => (
          <TouchableOpacity
            key={issueType}
            style={styles.parentOption}
            onPress={() => {
              setSelectedIssueType(issueType);
              setShowIssueTypePicker(false);
            }}
          >
            <View style={styles.issueTypeOption}>
              <Text style={styles.issueTypeIcon}>{getIssueTypeIcon(issueType)}</Text>
              <Text style={styles.issueTypeText}>{issueType}</Text>
            </View>
            {selectedIssueType === issueType && <Text style={styles.checkmark}>✓</Text>}
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  }

  // Parent Picker Modal
  if (showParentPicker) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.pickerHeader}>
          <Text style={styles.pickerTitle}>Select Parent</Text>
          <TouchableOpacity onPress={() => setShowParentPicker(false)}>
            <Text style={styles.pickerClose}>Done</Text>
          </TouchableOpacity>
        </View>

        {/* None option */}
        <TouchableOpacity
          style={styles.parentOption}
          onPress={() => {
            setSelectedParentId(null);
            setShowParentPicker(false);
          }}
        >
          <Text style={styles.parentOptionText}>None</Text>
          {selectedParentId === null && <Text style={styles.checkmark}>✓</Text>}
        </TouchableOpacity>

        {/* Parent options */}
        {board.parents.map((parent) => (
          <TouchableOpacity
            key={parent.id}
            style={styles.parentOption}
            onPress={() => {
              setSelectedParentId(parent.id);
              setShowParentPicker(false);
            }}
          >
            <ParentBadge name={parent.name} color={parent.color} size="medium" />
            {selectedParentId === parent.id && <Text style={styles.checkmark}>✓</Text>}
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Title Input */}
      <View style={styles.section}>
        <Text style={styles.label}>Title *</Text>
        <TextInput
          style={styles.titleInput}
          placeholder="Enter item title"
          value={title}
          onChangeText={setTitle}
          autoFocus={isCreateMode}
        />
      </View>

      {/* Description Input with Preview Toggle */}
      <View style={styles.section}>
        <View style={styles.labelRow}>
          <Text style={styles.label}>Description</Text>
          <TouchableOpacity
            style={styles.previewToggle}
            onPress={() => setShowMarkdownPreview(!showMarkdownPreview)}
          >
            <Text style={styles.previewToggleText}>
              {showMarkdownPreview ? '✏️ Edit' : '👁 Preview'}
            </Text>
          </TouchableOpacity>
        </View>

        {showMarkdownPreview ? (
          <View style={[styles.input, styles.textArea, styles.preview]}>
            <Text style={styles.previewText}>{description || 'No description'}</Text>
          </View>
        ) : (
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Enter item description (supports Markdown)"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={8}
            textAlignVertical="top"
          />
        )}
      </View>

      {/* Issue Type Selector */}
      <View style={styles.section}>
        <Text style={styles.label}>Issue Type</Text>
        <TouchableOpacity
          style={styles.parentSelector}
          onPress={() => setShowIssueTypePicker(true)}
        >
          <View style={styles.issueTypeDisplay}>
            <Text style={styles.issueTypeIcon}>{getIssueTypeIcon(selectedIssueType)}</Text>
            <Text style={styles.issueTypeText}>{selectedIssueType}</Text>
          </View>
        </TouchableOpacity>
      </View>

      {/* Parent Selector */}
      <View style={styles.section}>
        <Text style={styles.label}>Parent / Project</Text>
        <TouchableOpacity
          style={styles.parentSelector}
          onPress={() => setShowParentPicker(true)}
        >
          {selectedParent ? (
            <ParentBadge name={selectedParent.name} color={selectedParent.color} />
          ) : (
            <Text style={styles.parentPlaceholder}>Select a parent (optional)</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Target Column Info */}
      {targetColumn && (
        <View style={styles.infoSection}>
          <Text style={styles.infoLabel}>Column:</Text>
          <Text style={styles.infoValue}>{targetColumn.name}</Text>
        </View>
      )}

      {/* Timestamp Display (Edit Mode Only) */}
      {!isCreateMode && item && (
        <View style={styles.section}>
          <Text style={styles.label}>Metadata</Text>
          <View style={styles.metadataContainer}>
            <View style={styles.metadataRow}>
              <Text style={styles.metadataLabel}>Created:</Text>
              <Text style={styles.metadataValue}>{formatTimestamp(item.created_at)}</Text>
            </View>
            {item.moved_in_progress_at && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Moved to In Progress:</Text>
                <Text style={styles.metadataValue}>{formatTimestamp(item.moved_in_progress_at)}</Text>
              </View>
            )}
            {item.moved_in_done_at && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Moved to Done:</Text>
                <Text style={styles.metadataValue}>{formatTimestamp(item.moved_in_done_at)}</Text>
              </View>
            )}
            {item.worked_on_for && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Work Duration:</Text>
                <Text style={styles.metadataValue}>{item.worked_on_for}</Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.button, styles.saveButton]}
          onPress={handleSave}
          disabled={saving}
        >
          <Text style={styles.saveButtonText}>
            {saving ? 'Saving...' : isCreateMode ? 'Create Item' : 'Save Changes'}
          </Text>
        </TouchableOpacity>

        {!isCreateMode && (
          <TouchableOpacity
            style={[styles.button, styles.deleteButton]}
            onPress={handleDelete}
            disabled={saving}
          >
            <Text style={styles.deleteButtonText}>Delete Item</Text>
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background.secondary,
  },
  centerContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: theme.text.secondary,
  },
  content: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.text.primary,
    marginBottom: 8,
  },
  titleInput: {
    borderWidth: 1,
    borderColor: theme.input.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: theme.input.background,
    color: theme.input.text,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.input.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: theme.input.background,
    color: theme.input.text,
  },
  textArea: {
    height: 120,
    textAlignVertical: 'top',
  },
  parentSelector: {
    borderWidth: 1,
    borderColor: theme.input.border,
    borderRadius: 8,
    padding: 12,
    backgroundColor: theme.input.background,
  },
  parentPlaceholder: {
    fontSize: 16,
    color: theme.input.placeholder,
  },
  infoSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    padding: 12,
    backgroundColor: theme.background.elevated,
    borderRadius: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.text.secondary,
    marginRight: 8,
  },
  infoValue: {
    fontSize: 14,
    color: theme.text.primary,
  },
  buttonContainer: {
    marginTop: 8,
  },
  button: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  saveButton: {
    backgroundColor: theme.button.primary.background,
  },
  saveButtonText: {
    color: theme.button.primary.text,
    fontSize: 16,
    fontWeight: '600',
  },
  deleteButton: {
    backgroundColor: theme.button.danger.background,
  },
  deleteButtonText: {
    color: theme.button.danger.text,
    fontSize: 16,
    fontWeight: '600',
  },
  pickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.border.primary,
  },
  pickerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.text.primary,
  },
  pickerClose: {
    fontSize: 16,
    color: theme.accent.primary,
    fontWeight: '600',
  },
  parentOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.border.primary,
  },
  parentOptionText: {
    fontSize: 16,
    color: theme.text.secondary,
  },
  checkmark: {
    fontSize: 20,
    color: theme.accent.primary,
    fontWeight: 'bold',
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  previewToggle: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: theme.background.elevated,
    borderRadius: 6,
  },
  previewToggleText: {
    fontSize: 12,
    color: theme.text.primary,
    fontWeight: '600',
  },
  preview: {
    backgroundColor: theme.background.elevated,
  },
  previewText: {
    fontSize: 14,
    color: theme.text.primary,
    lineHeight: 20,
  },
  issueTypeDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  issueTypeOption: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  issueTypeIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  issueTypeText: {
    fontSize: 16,
    color: theme.text.primary,
  },
  metadataContainer: {
    backgroundColor: theme.background.elevated,
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: theme.border.primary,
  },
  metadataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  metadataLabel: {
    fontSize: 13,
    color: theme.text.secondary,
    fontWeight: '500',
  },
  metadataValue: {
    fontSize: 13,
    color: theme.text.primary,
  },
});
