/**
 * Logger utility for structured logging
 * Replaces console.log with environment-aware logging
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

interface LogContext {
  [key: string]: any;
}

class Logger {
  private isDevelopment: boolean;
  private minLevel: LogLevel;

  constructor() {
    this.isDevelopment = __DEV__;
    // In production, only log warnings and errors
    this.minLevel = this.isDevelopment ? LogLevel.DEBUG : LogLevel.WARN;
  }

  /**
   * Check if a log level should be printed
   */
  private shouldLog(level: LogLevel): boolean {
    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
    const currentIndex = levels.indexOf(level);
    const minIndex = levels.indexOf(this.minLevel);
    return currentIndex >= minIndex;
  }

  /**
   * Format log message with context
   */
  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const contextStr = context ? ` ${JSON.stringify(context)}` : '';
    return `[${timestamp}] ${level} ${message}${contextStr}`;
  }

  /**
   * Log debug message (development only)
   */
  debug(message: string, context?: LogContext): void {
    if (this.shouldLog(LogLevel.DEBUG)) {
      console.log(this.formatMessage(LogLevel.DEBUG, message, context));
    }
  }

  /**
   * Log info message
   */
  info(message: string, context?: LogContext): void {
    if (this.shouldLog(LogLevel.INFO)) {
      console.log(this.formatMessage(LogLevel.INFO, message, context));
    }
  }

  /**
   * Log warning message
   */
  warn(message: string, context?: LogContext): void {
    if (this.shouldLog(LogLevel.WARN)) {
      console.warn(this.formatMessage(LogLevel.WARN, message, context));
    }
  }

  /**
   * Log error message
   */
  error(message: string, error?: Error | unknown, context?: LogContext): void {
    if (this.shouldLog(LogLevel.ERROR)) {
      const errorContext = error instanceof Error
        ? { ...context, error: error.message, stack: error.stack }
        : { ...context, error };

      console.error(this.formatMessage(LogLevel.ERROR, message, errorContext));
    }
  }

  /**
   * Log with custom level
   */
  log(level: LogLevel, message: string, context?: LogContext): void {
    switch (level) {
      case LogLevel.DEBUG:
        this.debug(message, context);
        break;
      case LogLevel.INFO:
        this.info(message, context);
        break;
      case LogLevel.WARN:
        this.warn(message, context);
        break;
      case LogLevel.ERROR:
        this.error(message, undefined, context);
        break;
    }
  }

  /**
   * Create a scoped logger with context
   */
  scope(scopeName: string): ScopedLogger {
    return new ScopedLogger(this, scopeName);
  }
}

/**
 * Scoped logger that automatically includes scope context
 */
class ScopedLogger {
  constructor(
    private logger: Logger,
    private scopeName: string
  ) {}

  debug(message: string, context?: LogContext): void {
    this.logger.debug(message, { ...context, scope: this.scopeName });
  }

  info(message: string, context?: LogContext): void {
    this.logger.info(message, { ...context, scope: this.scopeName });
  }

  warn(message: string, context?: LogContext): void {
    this.logger.warn(message, { ...context, scope: this.scopeName });
  }

  error(message: string, error?: Error | unknown, context?: LogContext): void {
    this.logger.error(message, error, { ...context, scope: this.scopeName });
  }
}

// Export singleton instance
export const logger = new Logger();

// Export default for convenience
export default logger;

// Usage examples:
// logger.debug('Debug message');
// logger.info('Info message', { userId: 123 });
// logger.warn('Warning message', { board: 'my-board' });
// logger.error('Error occurred', error, { operation: 'saveBoard' });
//
// const boardLogger = logger.scope('BoardService');
// boardLogger.info('Board loaded', { boardId: 'my-board' });
