import { ChatIntentName, ChatSlotName, SenderType } from "./types/enums";
import { ChatMessage } from "./types/implementations";
import { ChatMemory } from "./types/memory";
import { INTENT_REGISTRY } from "./types/intent-registry";
import { IntentServerInput } from "./types/intent-server";

class Session {
  private threadId: bigint;
  private userId: bigint;
  private memory: ChatMemory;
  private createdAt: Date;
  
  constructor(threadId: bigint, userId: bigint, createdAt: Date) {
    this.threadId = threadId;
    this.userId = userId;
    this.memory = new ChatMemory(this.userId);
    this.createdAt = createdAt;
  }
  
  getMemory(): ChatMemory {
    return this.memory;
  }
  
  // Handle chat messages with intent classification and memory management
  async handleUserMessage(body: string) {
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
      const assistant_to_user_message_cbId = BigInt(456);
      const userTurn = new ChatMessage(
        user_to_assistant_message_cbId,
        this.threadId,
        Date.now(),
        this.userId,
        intentServer.get_cbId(),
        body,
        SenderType.USER,
        detectedIntent,
        {} as Record<ChatSlotName, any>
      );
      
      // Add to memory
      this.memory.addMessage(userTurn);
      // Create intent server input
      const inputData = new IntentServerInput(
        this.threadId,
        this.userId,
        userTurn,
        this.memory
      );
      
      console.log(`Input data: ${inputData}, calling intent server: ${ChatIntentName.QB}, ${INTENT_REGISTRY.getAllIntents()}`);
      
      const intent_server_output = await intentServer.serve(inputData);
      console.log(`Response: ${intent_server_output}, ${INTENT_REGISTRY.getAllIntents()}`);
        
      
      this.memory.addMessage(intent_server_output.assistantTurn);
      
      return intent_server_output.assistantTurn.body;
    } catch (error) {
      // print more info about error
      console.error('Error handling chat message:', error instanceof Error ? error.stack : error, INTENT_REGISTRY.getAllIntents());
      return null;
    }
  }
}

export default Session;
