/**
 * Dependency Injection Container for mobile app
 * Simplified from Python: src/core/dependency_container.py
 * MVP version: No logger, config manager, or daemon services
 */

import { FileSystemManager } from '../infrastructure/storage/FileSystemManager';
import { MarkdownBoardRepository } from '../infrastructure/storage/MarkdownBoardRepository';
import { MarkdownStorageRepository } from '../infrastructure/storage/MarkdownStorageRepository';
import { ValidationService } from '../services/ValidationService';
import { BoardService } from '../services/BoardService';
import { ItemService } from '../services/ItemService';
import { FileWatcher } from '../infrastructure/daemon/FileWatcher';
import { StorageConfig } from './StorageConfig';
import { ActionsConfig, getActionsConfig } from './ActionsConfig';
import { YamlActionRepository } from '../infrastructure/repositories/YamlActionRepository';
import { ActionService } from '../services/ActionService';
import { NotificationService } from '../services/NotificationService';
import { ActionEngine } from '../services/ActionEngine';
import { ActionDaemon } from '../infrastructure/daemon/ActionDaemon';
import { MissedActionsManager } from '../services/MissedActionsManager';

type Factory<T> = () => T;

/**
 * Dependency Injection Container
 * Manages service lifecycle with singleton pattern and lazy instantiation
 */
export class DependencyContainer {
  private instances: Map<any, any>;
  private factories: Map<any, Factory<any>>;

  constructor() {
    this.instances = new Map();
    this.factories = new Map();
    this._setupDefaultFactories();
  }

  /**
   * Set up default factories for all services
   */
  private _setupDefaultFactories(): void {
    // File system manager (foundation) - created first without StorageConfig
    this.factories.set(FileSystemManager, () => {
      return new FileSystemManager();
    });

    // Storage config with FileSystemManager dependency
    this.factories.set(StorageConfig, () => {
      const fsManager = this.get(FileSystemManager);
      const storageConfig = new StorageConfig(undefined, fsManager);

      // Asynchronously load and apply custom boards directory to FileSystemManager
      // This is a workaround since factory can't be async
      storageConfig.getBoardsDirectory().then((boardsDir) => {
        const defaultDir = fsManager.getDefaultBoardsDirectory();
        if (boardsDir !== defaultDir) {
          fsManager.setBoardsDirectory(boardsDir);
          console.log('Custom boards directory loaded:', boardsDir);
        }
      }).catch((error) => {
        console.error('Failed to load custom boards directory:', error);
      });

      return storageConfig;
    });

    // Repository factories with FileSystemManager dependency
    this.factories.set(
      MarkdownBoardRepository,
      () => new MarkdownBoardRepository(this.get(FileSystemManager))
    );
    this.factories.set(
      MarkdownStorageRepository,
      () => new MarkdownStorageRepository(this.get(FileSystemManager))
    );

    // Service factories with dependencies
    this.factories.set(ValidationService, () => new ValidationService());

    this.factories.set(
      BoardService,
      () =>
        new BoardService(
          this.get(MarkdownBoardRepository),
          this.get(ValidationService)
        )
    );

    this.factories.set(
      ItemService,
      () =>
        new ItemService(
          this.get(MarkdownStorageRepository),
          this.get(ValidationService)
        )
    );

    // File watcher factory with FileSystemManager dependency
    this.factories.set(
      FileWatcher,
      () => new FileWatcher(this.get(FileSystemManager))
    );

    // Actions Config (singleton)
    this.factories.set(ActionsConfig, () => getActionsConfig());

    // Action Repository with FileSystemManager dependency
    this.factories.set(
      YamlActionRepository,
      () => {
        const repo = new YamlActionRepository(this.get(FileSystemManager));
        // Initialize asynchronously
        repo.initialize().catch((error) => {
          console.error('Failed to initialize ActionRepository:', error);
        });
        return repo;
      }
    );

    // Action Service
    this.factories.set(
      ActionService,
      () =>
        new ActionService(
          this.get(YamlActionRepository),
          this.get(MarkdownBoardRepository),
          this.get(ActionsConfig)
        )
    );

    // Notification Service
    this.factories.set(
      NotificationService,
      () => {
        const service = new NotificationService(this.get(ActionsConfig));
        // Initialize asynchronously
        service.initialize().catch((error) => {
          console.error('Failed to initialize NotificationService:', error);
        });
        return service;
      }
    );

    // Action Engine
    this.factories.set(
      ActionEngine,
      () =>
        new ActionEngine(
          this.get(ActionService),
          this.get(ItemService),
          this.get(BoardService),
          this.get(NotificationService)
        )
    );

    // Missed Actions Manager
    this.factories.set(
      MissedActionsManager,
      () =>
        new MissedActionsManager(
          this.get(ActionService),
          this.get(ActionsConfig)
        )
    );

    // Action Daemon
    this.factories.set(
      ActionDaemon,
      () =>
        new ActionDaemon(
          this.get(ActionEngine),
          this.get(ActionService),
          this.get(ActionsConfig)
        )
    );
  }

  /**
   * Register a custom factory for a service type
   */
  registerFactory<T>(serviceType: any, factory: Factory<T>): void {
    this.factories.set(serviceType, factory);
  }

  /**
   * Register a singleton instance for a service type
   */
  registerInstance<T>(serviceType: any, instance: T): void {
    this.instances.set(serviceType, instance);
  }

  /**
   * Get an instance of the requested service type
   * Uses singleton pattern - creates instance once and reuses it
   */
  get<T>(serviceType: any): T {
    // Return existing instance if already created
    if (this.instances.has(serviceType)) {
      return this.instances.get(serviceType);
    }

    // Create instance using factory
    if (this.factories.has(serviceType)) {
      const factory = this.factories.get(serviceType);
      if (!factory) {
        throw new Error(`Factory is undefined for ${serviceType.name || serviceType}`);
      }
      const instance = factory();
      this.instances.set(serviceType, instance);
      return instance;
    }

    throw new Error(`No factory registered for ${serviceType.name || serviceType}`);
  }

  /**
   * Clear all singleton instances (useful for testing)
   */
  clearInstances(): void {
    this.instances.clear();
  }

  /**
   * Set up container for testing with mock dependencies
   */
  setupForTesting(): void {
    this.clearInstances();
    // Test-specific setup can be added here
  }
}

// Global container instance
let _container: DependencyContainer | null = null;

/**
 * Get the global dependency container
 */
export function getContainer(): DependencyContainer {
  if (_container === null) {
    _container = new DependencyContainer();
  }
  return _container;
}

/**
 * Set the global dependency container (useful for testing)
 */
export function setContainer(container: DependencyContainer): void {
  _container = container;
}

/**
 * Reset the global container (useful for testing)
 */
export function resetContainer(): void {
  _container = null;
}

// Convenience functions for getting services
// These provide backward compatibility and simpler API

/**
 * Get the validation service
 */
export function getValidationService(): ValidationService {
  return getContainer().get(ValidationService);
}

/**
 * Get the board service
 */
export function getBoardService(): BoardService {
  return getContainer().get(BoardService);
}

/**
 * Get the item service
 */
export function getItemService(): ItemService {
  return getContainer().get(ItemService);
}

/**
 * Get the board repository
 */
export function getBoardRepository(): MarkdownBoardRepository {
  return getContainer().get(MarkdownBoardRepository);
}

/**
 * Get the storage repository
 */
export function getStorageRepository(): MarkdownStorageRepository {
  return getContainer().get(MarkdownStorageRepository);
}

/**
 * Get the file watcher
 */
export function getFileWatcher(): FileWatcher {
  return getContainer().get(FileWatcher);
}

/**
 * Get the storage config
 */
export function getStorageConfig(): StorageConfig {
  return getContainer().get(StorageConfig);
}

/**
 * Get the file system manager
 */
export function getFileSystemManager(): FileSystemManager {
  return getContainer().get(FileSystemManager);
}

/**
 * Get the actions config
 */
export function getActionsConfigFromContainer(): ActionsConfig {
  return getContainer().get(ActionsConfig);
}

/**
 * Get the action repository
 */
export function getActionRepository(): YamlActionRepository {
  return getContainer().get(YamlActionRepository);
}

/**
 * Get the action service
 */
export function getActionService(): ActionService {
  return getContainer().get(ActionService);
}

/**
 * Get the notification service
 */
export function getNotificationService(): NotificationService {
  return getContainer().get(NotificationService);
}

/**
 * Get the action engine
 */
export function getActionEngine(): ActionEngine {
  return getContainer().get(ActionEngine);
}

/**
 * Get the missed actions manager
 */
export function getMissedActionsManager(): MissedActionsManager {
  return getContainer().get(MissedActionsManager);
}

/**
 * Get the action daemon
 */
export function getActionDaemon(): ActionDaemon {
  return getContainer().get(ActionDaemon);
}
