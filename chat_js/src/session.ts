import { ChatIntentName, ChatSlotName, SenderType } from "./types/enums";
import { ChatMessage } from "./types/implementations";
import { ChatMemory } from "./types/memory";
import { INTENT_REGISTRY } from "./types/intent-registry";
import { AssistantToUserMessageSender, IntentServerInput } from "./types/intent-server";
import { WebSocket } from 'ws';
import { ModelIO } from "./types/modelio";
import { ToolCallRunner } from "./tool-call-runner";
import { QBServerSuccessPrompt } from "./qb-server-success-prompt";
import { QBServer } from "./qb-server";

class Session implements AssistantToUserMessageSender {
  private threadId: bigint;
  private userId: bigint;
  private createdAt: Date;
  private ws: WebSocket;
  // have history in DB
  public modelIO: ModelIO;
  private memory: ChatMemory;
  
  constructor(threadId: bigint, userId: bigint, createdAt: Date, ws: WebSocket) {
    this.threadId = threadId;
    this.userId = userId;
    this.memory = new ChatMemory(this.userId);
    this.createdAt = createdAt;
    this.ws = ws;
    this.modelIO = QBServer.create_model_io(this.threadId, this.userId);
  }
  
  getMemory(): ChatMemory {
    return this.memory;
  }
  
  async handleAssistantMessage(
    intent_server_cbid: bigint,
    body: string,
    sender_type: SenderType,
    intent_name: ChatIntentName,
    slots: Record<ChatSlotName, any>,
  ) : Promise<bigint> {
    // send message to user on the websocket connection

    const assistantTurn = new ChatMessage(
      BigInt(0),
      this.threadId,
      Date.now(),
      intent_server_cbid,
      this.userId,
      body,
      sender_type,
      intent_name,
      slots,
    );
    const assistant_to_user_message_cbId = await this.memory.addMessage(assistantTurn);
      
    console.log(`Sending assistant message to user ${this.userId} in thread ${this.threadId}: ${assistantTurn.body} with cbId: ${assistant_to_user_message_cbId}`);
    this.ws.send(JSON.stringify({
      type: 'chat',
      userId: this.userId.toString(),
      threadId: this.threadId.toString(),
      message: assistantTurn.body,
      timestamp: new Date().toISOString()
    }));
    return assistant_to_user_message_cbId;
  }
  
  async handleUserMessage(message: string) {
    // Send delivery receipt to client
    console.log(`Sending delivery receipt to client for thread ${this.threadId}...`);
    this.ws.send(JSON.stringify({
      type: 'message_received',
      userId: this.userId.toString(),
      threadId: this.threadId.toString(),
      messageId: Date.now().toString(),
      timestamp: new Date().toISOString()
    }));
    
    // Handle message processing in background
    setImmediate(async () => {
      // try {
      console.log(`Scheduled to handle user message for thread ${this.threadId}...`);
      await this.sendUserMessageToIntentServer(message);
    });
  }

  // Handle chat messages with intent classification and memory management
  async sendUserMessageToIntentServer(body: string) : Promise<void> {
    try {
      // Classify intent and get appropriate server
      // For now, we'll use a simple intent detection
      let detectedIntent = ChatIntentName.QB;
          
      // Get intent server
      const intentServer = INTENT_REGISTRY.server(detectedIntent);
      if (!intentServer) {
        throw new Error(`Intent server for ${detectedIntent} not found`);
      } else {
        console.log(`got here intentServer: ${intentServer.get_cbId()}, ${INTENT_REGISTRY.getAllIntents()}`);
      }
      
      // write message to db and get messageId = cbId
      const user_to_assistant_message_cbId = BigInt(123);
      const userTurn = new ChatMessage(
        user_to_assistant_message_cbId,
        this.threadId,
        Date.now(),
        this.userId,
        intentServer.get_cbId(),
        body,
        SenderType.USER,
        detectedIntent,
        {} as Record<ChatSlotName, any>,
      );
      
      // Add to memory
      await this.memory.addMessage(userTurn);
      // Create intent server input
      const inputData = new IntentServerInput(
        this.threadId,
        this.userId,
        userTurn,
        this.memory,
        this,
        this.modelIO
      );
      
      console.log(`Input data: ${inputData}, calling intent server: ${ChatIntentName.QB}, ${INTENT_REGISTRY.getAllIntents()}`);
      
      await intentServer.serve(inputData);
    } catch (error) {
      // print more info about error
      console.error('Error handling chat message:', error instanceof Error ? error.stack : error, INTENT_REGISTRY.getAllIntents());
    }
  }
}

export default Session;
