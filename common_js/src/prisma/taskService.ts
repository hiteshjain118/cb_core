import PrismaService from './client';

export interface Task {
  cbId: bigint;
  threadId: bigint;
  createdAt: Date;
  toolCallId: string;
  toolCallName: string;
  toolCallArgs: any;
  handleForModel: string;
  requestModelEventId: bigint;
}

export interface TaskWithDependencies extends Task {
  deps: Task[];
  dependents: Task[];
}

export class TaskService {
  private static instance: TaskService;

  static getInstance(): TaskService {
    if (!TaskService.instance) {
      TaskService.instance = new TaskService();
    }
    return TaskService.instance;
  }

  /**
   * Create a new task
   */
  async createTask(data: {
    threadId: bigint;
    toolCallId: string;
    toolCallName: string;
    toolCallArgs: any;
    handleForModel: string;
    requestModelEventId: bigint;
  }): Promise<Task> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.task.create({
        data: {
          threadId: data.threadId,
          toolCallId: data.toolCallId,
          toolCallName: data.toolCallName,
          toolCallArgs: data.toolCallArgs,
          handleForModel: data.handleForModel,
          requestModelEventId: data.requestModelEventId,
        },
      });
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    }
  }

  /**
   * Update a task
   */
  async updateTask(
    cbId: bigint,
    data: Partial<{
      threadId: bigint;
      toolCallId: string;
      toolCallName: string;
      toolCallArgs: any;
      handleForModel: string;
      requestModelEventId: bigint;
    }>
  ): Promise<Task> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.task.update({
        where: { cbId },
        data,
      });
    } catch (error) {
      console.error('Error updating task:', error);
      throw error;
    }
  }

  /**
   * Get task by ID
   */
  async getTask(cbId: bigint): Promise<TaskWithDependencies | null> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.task.findUnique({
        where: { cbId },
        include: {
          deps: true,
          dependents: true,
          requestModelEvent: true,
        },
      });
    } catch (error) {
      console.error('Error getting task:', error);
      throw error;
    }
  }

  /**
   * Get tasks by thread ID
   */
  async getTasksByThreadId(threadId: bigint): Promise<TaskWithDependencies[]> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.task.findMany({
        where: { threadId },
        include: {
          deps: true,
          dependents: true,
          requestModelEvent: true,
        },
        orderBy: { createdAt: 'desc' },
      });
    } catch (error) {
      console.error('Error getting tasks by thread ID:', error);
      throw error;
    }
  }

  /**
   * Get tasks by model event ID
   */
  async getTasksByModelEventId(requestModelEventId: bigint): Promise<TaskWithDependencies[]> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.task.findMany({
        where: { requestModelEventId },
        include: {
          deps: true,
          dependents: true,
          requestModelEvent: true,
        },
        orderBy: { createdAt: 'asc' },
      });
    } catch (error) {
      console.error('Error getting tasks by model event ID:', error);
      throw error;
    }
  }

  /**
   * Add task dependency
   */
  async addTaskDependency(taskId: bigint, dependsOnTaskId: bigint): Promise<void> {
    const prisma = PrismaService.getInstance();
    
    try {
      await prisma.task.update({
        where: { cbId: taskId },
        data: {
          deps: {
            connect: { cbId: dependsOnTaskId },
          },
        },
      });
    } catch (error) {
      console.error('Error adding task dependency:', error);
      throw error;
    }
  }

  /**
   * Remove task dependency
   */
  async removeTaskDependency(taskId: bigint, dependsOnTaskId: bigint): Promise<void> {
    const prisma = PrismaService.getInstance();
    
    try {
      await prisma.task.update({
        where: { cbId: taskId },
        data: {
          deps: {
            disconnect: { cbId: dependsOnTaskId },
          },
        },
      });
    } catch (error) {
      console.error('Error removing task dependency:', error);
      throw error;
    }
  }

  /**
   * Get task dependencies tree
   */
  async getTaskDependenciesTree(taskId: bigint): Promise<TaskWithDependencies[]> {
    const prisma = PrismaService.getInstance();
    
    try {
      // Get the task with all its dependencies recursively
      const task = await prisma.task.findUnique({
        where: { cbId: taskId },
        include: {
          deps: {
            include: {
              deps: true,
              dependents: true,
            },
          },
          dependents: {
            include: {
              deps: true,
              dependents: true,
            },
          },
        },
      });

      if (!task) {
        return [];
      }

      // Flatten the dependency tree
      const allTasks = new Map<bigint, TaskWithDependencies>();
      
      function addTaskToMap(t: any) {
        allTasks.set(t.cbId, t);
        if (t.deps) {
          t.deps.forEach(addTaskToMap);
        }
        if (t.dependents) {
          t.dependents.forEach(addTaskToMap);
        }
      }

      addTaskToMap(task);
      return Array.from(allTasks.values());
    } catch (error) {
      console.error('Error getting task dependencies tree:', error);
      throw error;
    }
  }

  /**
   * Delete a task
   */
  async deleteTask(cbId: bigint): Promise<void> {
    const prisma = PrismaService.getInstance();
    
    try {
      await prisma.task.delete({
        where: { cbId },
      });
    } catch (error) {
      console.error('Error deleting task:', error);
      throw error;
    }
  }

  /**
   * Get pending tasks (tasks without dependencies or with completed dependencies)
   */
  async getPendingTasksByThreadId(threadId: bigint): Promise<TaskWithDependencies[]> {
    const prisma = PrismaService.getInstance();
    
    try {
      // Get all tasks for the thread with their dependencies
      const allTasks = await this.getTasksByThreadId(threadId);
      
      // Filter tasks that have no dependencies or all dependencies are completed
      // This is a simple implementation - you might want to add a 'status' field to tasks
      return allTasks.filter(task => task.deps.length === 0);
    } catch (error) {
      console.error('Error getting pending tasks:', error);
      throw error;
    }
  }
} 