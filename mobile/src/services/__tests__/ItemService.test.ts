/**
 * Unit Tests for ItemService
 */

import { ItemService } from '../ItemService';
import { ValidationService } from '../ValidationService';
import { Board } from '../../domain/entities/Board';
import { Column } from '../../domain/entities/Column';
import { Item } from '../../domain/entities/Item';
import { Parent } from '../../domain/entities/Parent';
import { StorageRepository } from '../../domain/repositories/StorageRepository';
import { ParentColor } from '../../core/enums';

// Mock storage repository
class MockStorageRepository implements StorageRepository {
  deletedItems: string[] = [];
  movedItems: Array<{ from: string; to: string }> = [];

  async deleteItemFromColumn(board: Board, item: Item, column: Column): Promise<boolean> {
    this.deletedItems.push(item.id);
    return true;
  }

  async moveItemBetweenColumns(
    board: Board,
    item: Item,
    oldColumn: Column,
    newColumn: Column
  ): Promise<boolean> {
    this.movedItems.push({ from: oldColumn.id, to: newColumn.id });
    return true;
  }

  async saveBoardToStorage(board: Board): Promise<boolean> {
    return true;
  }

  reset() {
    this.deletedItems = [];
    this.movedItems = [];
  }
}

describe('ItemService', () => {
  let itemService: ItemService;
  let mockStorageRepo: MockStorageRepository;
  let validationService: ValidationService;
  let testBoard: Board;
  let testColumn: Column;

  beforeEach(() => {
    mockStorageRepo = new MockStorageRepository();
    validationService = new ValidationService();
    itemService = new ItemService(mockStorageRepo, validationService);

    // Create test board with columns
    testColumn = new Column('col-1', 'To Do', [], 1);
    const column2 = new Column('col-2', 'In Progress', [], 2);
    testBoard = new Board('board-1', 'Test Board', [testColumn, column2], []);
  });

  describe('createItem', () => {
    it('should create item with valid title', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Test Item');

      expect(item).not.toBeNull();
      expect(item?.title).toBe('Test Item');
      expect(item?.id).toMatch(/^MKA-\d+$/); // Auto-generated ID
      expect(testColumn.items).toHaveLength(1);
    });

    it('should create item with description', async () => {
      const item = await itemService.createItem(
        testBoard,
        testColumn,
        'Test Item',
        'Test description'
      );

      expect(item?.description).toBe('Test description');
    });

    it('should create item with parent', async () => {
      const parent = new Parent('parent-1', 'Feature X', ParentColor.BLUE, new Date().toISOString());
      testBoard.parents.push(parent);

      const item = await itemService.createItem(
        testBoard,
        testColumn,
        'Test Item',
        '',
        'parent-1'
      );

      expect(item?.parent_id).toBe('parent-1');
    });

    it('should throw error for empty title', async () => {
      await expect(itemService.createItem(testBoard, testColumn, '')).rejects.toThrow();
    });

    it('should throw error for excessively long title', async () => {
      const longTitle = 'a'.repeat(201);
      await expect(itemService.createItem(testBoard, testColumn, longTitle)).rejects.toThrow();
    });

    it('should generate sequential IDs', async () => {
      const item1 = await itemService.createItem(testBoard, testColumn, 'Item 1');
      const item2 = await itemService.createItem(testBoard, testColumn, 'Item 2');

      expect(item1?.id).toBe('MKA-1');
      expect(item2?.id).toBe('MKA-2');
    });
  });

  describe('updateItem', () => {
    it('should update item title', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Original');
      const result = await itemService.updateItem(testBoard, item!.id, { title: 'Updated' });

      expect(result).toBe(true);
      expect(item?.title).toBe('Updated');
    });

    it('should update item description', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Test');
      const result = await itemService.updateItem(testBoard, item!.id, {
        description: 'New description',
      });

      expect(result).toBe(true);
      expect(item?.description).toBe('New description');
    });

    it('should update item parent', async () => {
      const parent = new Parent('parent-1', 'Feature X', ParentColor.BLUE, new Date().toISOString());
      testBoard.parents.push(parent);

      const item = await itemService.createItem(testBoard, testColumn, 'Test');
      const result = await itemService.updateItem(testBoard, item!.id, { parent_id: 'parent-1' });

      expect(result).toBe(true);
      expect(item?.parent_id).toBe('parent-1');
    });

    it('should throw error for invalid title update', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Test');
      await expect(itemService.updateItem(testBoard, item!.id, { title: '' })).rejects.toThrow();
    });

    it('should throw error when item does not exist', async () => {
      await expect(
        itemService.updateItem(testBoard, 'nonexistent', { title: 'Updated' })
      ).rejects.toThrow('Item with ID nonexistent not found');
    });
  });

  describe('deleteItem', () => {
    it('should delete existing item', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Test');
      const result = await itemService.deleteItem(testBoard, item!.id);

      expect(result).toBe(true);
      expect(testColumn.items).toHaveLength(0);
      expect(mockStorageRepo.deletedItems).toContain(item!.id);
    });

    it('should throw error when item does not exist', async () => {
      await expect(itemService.deleteItem(testBoard, 'nonexistent')).rejects.toThrow(
        'Item with ID nonexistent not found'
      );
    });

    it('should throw error for empty item ID', async () => {
      await expect(itemService.deleteItem(testBoard, '')).rejects.toThrow();
    });
  });

  describe('moveItemBetweenColumns', () => {
    it('should move item to different column', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Test');
      const targetColumn = testBoard.columns[1]; // In Progress

      const result = await itemService.moveItemBetweenColumns(
        testBoard,
        item!.id,
        targetColumn.id
      );

      expect(result).toBe(true);
      expect(testColumn.items).toHaveLength(0);
      expect(targetColumn.items).toHaveLength(1);
      expect(targetColumn.items[0].id).toBe(item!.id);
    });

    it('should throw error when item does not exist', async () => {
      await expect(
        itemService.moveItemBetweenColumns(testBoard, 'nonexistent', 'col-2')
      ).rejects.toThrow('Item with ID nonexistent not found');
    });

    it('should throw error when target column does not exist', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Test');

      await expect(
        itemService.moveItemBetweenColumns(testBoard, item!.id, 'nonexistent')
      ).rejects.toThrow('Column with ID nonexistent not found');
    });

    it('should not move if item already in target column', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Test');

      const result = await itemService.moveItemBetweenColumns(testBoard, item!.id, testColumn.id);

      expect(result).toBe(true);
      expect(testColumn.items).toHaveLength(1);
      expect(mockStorageRepo.movedItems).toHaveLength(0); // No storage operation
    });
  });

  describe('setItemParent', () => {
    it('should assign parent to item', async () => {
      const parent = new Parent('parent-1', 'Feature X', ParentColor.BLUE, new Date().toISOString());
      testBoard.parents.push(parent);

      const item = await itemService.createItem(testBoard, testColumn, 'Test');
      const result = await itemService.setItemParent(testBoard, item!.id, 'parent-1');

      expect(result).toBe(true);
      expect(item?.parent_id).toBe('parent-1');
    });

    it('should clear parent when parentId is null', async () => {
      const parent = new Parent('parent-1', 'Feature X', ParentColor.BLUE, new Date().toISOString());
      testBoard.parents.push(parent);

      const item = await itemService.createItem(testBoard, testColumn, 'Test', '', 'parent-1');
      const result = await itemService.setItemParent(testBoard, item!.id, null);

      expect(result).toBe(true);
      expect(item?.parent_id).toBeNull();
    });

    it('should throw error when item does not exist', async () => {
      await expect(itemService.setItemParent(testBoard, 'nonexistent', 'parent-1')).rejects.toThrow(
        'Item with ID nonexistent not found'
      );
    });

    it('should throw error when parent does not exist', async () => {
      const item = await itemService.createItem(testBoard, testColumn, 'Test');

      await expect(
        itemService.setItemParent(testBoard, item!.id, 'nonexistent')
      ).rejects.toThrow('Parent with ID nonexistent not found');
    });
  });

  describe('getItemsGroupedByParent', () => {
    it('should group items by parent', async () => {
      const parent1 = new Parent('p1', 'Feature X', ParentColor.BLUE, new Date().toISOString());
      const parent2 = new Parent('p2', 'Feature Y', ParentColor.RED, new Date().toISOString());
      testBoard.parents.push(parent1, parent2);

      await itemService.createItem(testBoard, testColumn, 'Item 1', '', 'p1');
      await itemService.createItem(testBoard, testColumn, 'Item 2', '', 'p1');
      await itemService.createItem(testBoard, testColumn, 'Item 3', '', 'p2');
      await itemService.createItem(testBoard, testColumn, 'Item 4');

      const grouped = itemService.getItemsGroupedByParent(testBoard, testColumn.id);

      expect(grouped.size).toBe(3); // p1, p2, and null (no parent)
      expect(grouped.get('p1')).toHaveLength(2);
      expect(grouped.get('p2')).toHaveLength(1);
      expect(grouped.get(null as any)).toHaveLength(1);
    });

    it('should return empty map when column has no items', async () => {
      const grouped = itemService.getItemsGroupedByParent(testBoard, testColumn.id);

      expect(grouped.size).toBe(0);
    });

    it('should throw error when column does not exist', async () => {
      expect(() => itemService.getItemsGroupedByParent(testBoard, 'nonexistent')).toThrow(
        'Column with ID nonexistent not found'
      );
    });
  });
});
