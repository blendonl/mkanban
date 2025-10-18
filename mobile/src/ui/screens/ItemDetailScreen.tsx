import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
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
          Alert.alert('Error', 'Board not found');
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
            Alert.alert('Error', 'Item not found');
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
        console.error('Failed to load data:', error);
        Alert.alert('Error', 'Failed to load data');
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
      Alert.alert('Error', 'Board not loaded');
      return;
    }

    if (!title.trim()) {
      Alert.alert('Error', 'Item title is required');
      return;
    }

    if (!targetColumn) {
      Alert.alert('Error', 'Could not determine target column');
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

        Alert.alert('Success', 'Item created successfully');
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

        Alert.alert('Success', 'Item updated successfully');
        navigation.goBack();
      }
    } catch (error) {
      console.error('Failed to save item:', error);
      Alert.alert('Error', 'Failed to save item');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (isCreateMode || !item || !board) {
      return;
    }

    Alert.alert(
      'Delete Item',
      'Are you sure you want to delete this item? This action cannot be undone.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await itemService.deleteItem(board, item.id);
              await boardService.saveBoard(board);

              Alert.alert('Success', 'Item deleted successfully');
              navigation.goBack();
            } catch (error) {
              console.error('Failed to delete item:', error);
              Alert.alert('Error', 'Failed to delete item');
            }
          },
        },
      ]
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

  // Helper function to get issue type icon
  const getIssueTypeIcon = (issueType: string): string => {
    switch (issueType) {
      case IssueType.EPIC:
        return '📚';
      case IssueType.STORY:
        return '📖';
      case IssueType.BUG:
        return '🐛';
      case IssueType.SUBTASK:
        return '☑️';
      case IssueType.TASK:
      default:
        return '📋';
    }
  };

  // Helper function to format timestamp
  const formatTimestamp = (timestamp: Date | string | null): string => {
    if (!timestamp) return 'N/A';
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return date.toLocaleString();
  };

  // All available issue types
  const issueTypes = [
    IssueType.TASK,
    IssueType.STORY,
    IssueType.BUG,
    IssueType.EPIC,
    IssueType.SUBTASK,
  ];

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
    backgroundColor: '#fff',
  },
  centerContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
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
    color: '#374151',
    marginBottom: 8,
  },
  titleInput: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  textArea: {
    height: 120,
    textAlignVertical: 'top',
  },
  parentSelector: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    backgroundColor: '#fff',
  },
  parentPlaceholder: {
    fontSize: 16,
    color: '#9ca3af',
  },
  infoSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    padding: 12,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
    marginRight: 8,
  },
  infoValue: {
    fontSize: 14,
    color: '#1f2937',
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
    backgroundColor: '#2563eb',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  deleteButton: {
    backgroundColor: '#ef4444',
  },
  deleteButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  pickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  pickerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  pickerClose: {
    fontSize: 16,
    color: '#2563eb',
    fontWeight: '600',
  },
  parentOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  parentOptionText: {
    fontSize: 16,
    color: '#6b7280',
  },
  checkmark: {
    fontSize: 20,
    color: '#2563eb',
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
    backgroundColor: '#e5e7eb',
    borderRadius: 6,
  },
  previewToggleText: {
    fontSize: 12,
    color: '#374151',
    fontWeight: '600',
  },
  preview: {
    backgroundColor: '#f9fafb',
  },
  previewText: {
    fontSize: 14,
    color: '#1f2937',
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
    color: '#1f2937',
  },
  metadataContainer: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  metadataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  metadataLabel: {
    fontSize: 13,
    color: '#6b7280',
    fontWeight: '500',
  },
  metadataValue: {
    fontSize: 13,
    color: '#1f2937',
  },
});
