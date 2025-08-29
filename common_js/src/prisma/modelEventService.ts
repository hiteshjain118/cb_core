import PrismaService from './client';

export interface ModelEvent {
  cbId: bigint;
  systemPrompt: string | null;
  toolCalls: any | null;
  responseContent: string | null;
  inputPrompt: any | null;
  createdAt: Date;
  threadId: bigint | null;
  senderId: bigint | null;
  modelId: string | null;
  cbProfileId: bigint | null;
  assistantMessageId: bigint | null;
}

export class ModelEventService {
  private static instance: ModelEventService;

  static getInstance(): ModelEventService {
    if (!ModelEventService.instance) {
      ModelEventService.instance = new ModelEventService();
    }
    return ModelEventService.instance;
  }

  /**
   * Create a new model event
   */
  async createModelEvent(data: {
    systemPrompt?: string;
    toolCalls?: any;
    responseContent?: string;
    inputPrompt?: any;
    threadId?: bigint;
    senderId?: bigint;
    modelId?: string;
    cbProfileId?: bigint;
    assistantMessageId?: bigint;
  }): Promise<ModelEvent> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.modelEvent.create({
        data: {
          systemPrompt: data.systemPrompt || null,
          toolCalls: data.toolCalls || null,
          responseContent: data.responseContent || null,
          inputPrompt: data.inputPrompt || null,
          threadId: data.threadId || null,
          senderId: data.senderId || null,
          modelId: data.modelId || null,
          cbProfileId: data.cbProfileId || null,
          assistantMessageId: data.assistantMessageId || null,
        },
      });
    } catch (error) {
      console.error('Error creating model event:', error);
      throw error;
    }
  }

  /**
   * Update a model event
   */
  async updateModelEvent(
    cbId: bigint,
    data: Partial<{
      systemPrompt: string;
      toolCalls: any;
      responseContent: string;
      inputPrompt: any;
      threadId: bigint;
      senderId: bigint;
      modelId: string;
      cbProfileId: bigint;
      assistantMessageId: bigint;
    }>
  ): Promise<ModelEvent> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.modelEvent.update({
        where: { cbId },
        data,
      });
    } catch (error) {
      console.error('Error updating model event:', error);
      throw error;
    }
  }

  /**
   * Get model event by ID
   */
  async getModelEvent(cbId: bigint): Promise<ModelEvent | null> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.modelEvent.findUnique({
        where: { cbId },
        include: {
          tasks: true,
        },
      });
    } catch (error) {
      console.error('Error getting model event:', error);
      throw error;
    }
  }

  /**
   * Get model events by thread ID
   */
  async getModelEventsByThreadId(threadId: bigint): Promise<ModelEvent[]> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.modelEvent.findMany({
        where: { threadId },
        orderBy: { createdAt: 'desc' },
        include: {
          tasks: true,
        },
      });
    } catch (error) {
      console.error('Error getting model events by thread ID:', error);
      throw error;
    }
  }

  /**
   * Get model events by sender ID
   */
  async getModelEventsBySenderId(senderId: bigint): Promise<ModelEvent[]> {
    const prisma = PrismaService.getInstance();
    
    try {
      return await prisma.modelEvent.findMany({
        where: { senderId },
        orderBy: { createdAt: 'desc' },
        include: {
          tasks: true,
        },
      });
    } catch (error) {
      console.error('Error getting model events by sender ID:', error);
      throw error;
    }
  }

  /**
   * Delete a model event
   */
  async deleteModelEvent(cbId: bigint): Promise<void> {
    const prisma = PrismaService.getInstance();
    
    try {
      await prisma.modelEvent.delete({
        where: { cbId },
      });
    } catch (error) {
      console.error('Error deleting model event:', error);
      throw error;
    }
  }
} 