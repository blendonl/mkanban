/**
 * TimeTriggerEvaluator - Evaluates time-based triggers
 */

import { Cron } from 'croner';
import {
  TimeTrigger,
  ScheduleType,
  TriggerType,
} from '../../domain/entities/Trigger';
import { Action } from '../../domain/entities/Action';

export class TimeTriggerEvaluator {
  /**
   * Check if a time-based action should be triggered
   */
  shouldTrigger(action: Action, now: Date = new Date()): boolean {
    const timeTriggers = action.triggers.filter(
      (t) => t.type === TriggerType.TIME
    ) as TimeTrigger[];

    if (timeTriggers.length === 0) {
      return false;
    }

    // Check each time trigger
    for (const trigger of timeTriggers) {
      if (this.evaluateTrigger(trigger, action, now)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Evaluate a single time trigger
   */
  private evaluateTrigger(trigger: TimeTrigger, action: Action, now: Date): boolean {
    const { schedule } = trigger;

    switch (schedule.type) {
      case ScheduleType.ONCE:
        return this.evaluateOnce(schedule, action, now);

      case ScheduleType.DAILY:
        return this.evaluateDaily(schedule, now);

      case ScheduleType.WEEKLY:
        return this.evaluateWeekly(schedule, now);

      case ScheduleType.MONTHLY:
        return this.evaluateMonthly(schedule, now);

      case ScheduleType.CRON:
        return this.evaluateCron(schedule, action, now);

      default:
        return false;
    }
  }

  /**
   * Evaluate ONCE schedule
   */
  private evaluateOnce(schedule: any, action: Action, now: Date): boolean {
    if (!schedule.datetime) {
      return false;
    }

    const targetTime = new Date(schedule.datetime);

    // Has it been triggered before?
    if (action.execution?.lastTriggered) {
      return false; // One-time trigger, already executed
    }

    // Is it time?
    return now >= targetTime;
  }

  /**
   * Evaluate DAILY schedule
   */
  private evaluateDaily(schedule: any, now: Date): boolean {
    if (!schedule.time) {
      return false;
    }

    // Check day of week filter
    if (schedule.daysOfWeek && schedule.daysOfWeek.length > 0) {
      const dayOfWeek = now.getDay() === 0 ? 7 : now.getDay(); // Convert Sunday from 0 to 7
      if (!schedule.daysOfWeek.includes(dayOfWeek)) {
        return false;
      }
    }

    return this.isTimeMatch(schedule.time, now);
  }

  /**
   * Evaluate WEEKLY schedule
   */
  private evaluateWeekly(schedule: any, now: Date): boolean {
    if (!schedule.time || !schedule.daysOfWeek || schedule.daysOfWeek.length === 0) {
      return false;
    }

    const dayOfWeek = now.getDay() === 0 ? 7 : now.getDay();
    if (!schedule.daysOfWeek.includes(dayOfWeek)) {
      return false;
    }

    return this.isTimeMatch(schedule.time, now);
  }

  /**
   * Evaluate MONTHLY schedule
   */
  private evaluateMonthly(schedule: any, now: Date): boolean {
    if (!schedule.time || schedule.dayOfMonth === undefined) {
      return false;
    }

    if (now.getDate() !== schedule.dayOfMonth) {
      return false;
    }

    return this.isTimeMatch(schedule.time, now);
  }

  /**
   * Evaluate CRON schedule
   */
  private evaluateCron(schedule: any, action: Action, now: Date): boolean {
    if (!schedule.cronExpression) {
      return false;
    }

    try {
      const cron = new Cron(schedule.cronExpression);
      const nextRun = cron.next();

      if (!nextRun) {
        return false;
      }

      // Check if we're within the trigger window (within polling interval)
      const timeDiff = Math.abs(nextRun.getTime() - now.getTime());
      const pollingInterval = 30000; // 30 seconds default
      return timeDiff <= pollingInterval;
    } catch (error) {
      console.error('Invalid cron expression:', schedule.cronExpression, error);
      return false;
    }
  }

  /**
   * Check if current time matches the scheduled time (within 1 minute tolerance)
   */
  private isTimeMatch(timeStr: string, now: Date): boolean {
    const [hours, minutes] = timeStr.split(':').map(Number);

    if (isNaN(hours) || isNaN(minutes)) {
      return false;
    }

    const nowHours = now.getHours();
    const nowMinutes = now.getMinutes();

    // Exact match or within 1 minute tolerance
    return nowHours === hours && Math.abs(nowMinutes - minutes) <= 1;
  }

  /**
   * Get next trigger time for an action
   */
  getNextTriggerTime(action: Action): Date | null {
    const timeTriggers = action.triggers.filter(
      (t) => t.type === TriggerType.TIME
    ) as TimeTrigger[];

    if (timeTriggers.length === 0) {
      return null;
    }

    let nextTime: Date | null = null;

    for (const trigger of timeTriggers) {
      const time = this.getNextTriggerTimeForTrigger(trigger);
      if (time && (!nextTime || time < nextTime)) {
        nextTime = time;
      }
    }

    return nextTime;
  }

  /**
   * Get next trigger time for a specific trigger
   */
  private getNextTriggerTimeForTrigger(trigger: TimeTrigger): Date | null {
    const { schedule } = trigger;

    switch (schedule.type) {
      case ScheduleType.ONCE:
        return schedule.datetime ? new Date(schedule.datetime) : null;

      case ScheduleType.CRON:
        if (schedule.cronExpression) {
          try {
            const cron = new Cron(schedule.cronExpression);
            return cron.next() || null;
          } catch (error) {
            return null;
          }
        }
        return null;

      default:
        // For DAILY, WEEKLY, MONTHLY, calculate next occurrence
        return this.calculateNextOccurrence(schedule);
    }
  }

  /**
   * Calculate next occurrence for DAILY/WEEKLY/MONTHLY schedules
   */
  private calculateNextOccurrence(schedule: any): Date | null {
    if (!schedule.time) {
      return null;
    }

    const [hours, minutes] = schedule.time.split(':').map(Number);
    const now = new Date();
    let next = new Date(now);

    next.setHours(hours, minutes, 0, 0);

    // If time has passed today, move to tomorrow
    if (next <= now) {
      next.setDate(next.getDate() + 1);
    }

    // Handle day-of-week filters
    if (schedule.daysOfWeek && schedule.daysOfWeek.length > 0) {
      while (true) {
        const dayOfWeek = next.getDay() === 0 ? 7 : next.getDay();
        if (schedule.daysOfWeek.includes(dayOfWeek)) {
          break;
        }
        next.setDate(next.getDate() + 1);
      }
    }

    // Handle day-of-month (for MONTHLY)
    if (schedule.dayOfMonth !== undefined) {
      next.setDate(schedule.dayOfMonth);
      if (next <= now) {
        next.setMonth(next.getMonth() + 1);
      }
    }

    return next;
  }
}
