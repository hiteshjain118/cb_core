import { QBServer } from "../qb-server";
import { ChatIntentName } from "./enums";
import { GPTProvider } from "../gpt-provider";
import { IIntentServer } from "./intent-server";

export class IntentRegistry {
  private intentsToHandlers: Map<ChatIntentName, IIntentServer>;
  private initialized: boolean = false;

  constructor() {
    this.intentsToHandlers = new Map();
    this.ensureInitialized();
  }

  register(intent: ChatIntentName, server: IIntentServer): void {
    console.log(`registering intent: ${intent}, ${server.get_cbId()}`);
    this.intentsToHandlers.set(intent, server);
  }

  server(intent: ChatIntentName): IIntentServer | undefined {
    // Ensure registry is initialized before serving
    this.ensureInitialized();
    console.log(`getting server for intent: ${intent}, ${this.intentsToHandlers.get(intent)?.get_cbId()}`);
    return this.intentsToHandlers.get(intent);
  }

  hasIntent(intent: ChatIntentName): boolean {
    this.ensureInitialized();
    return this.intentsToHandlers.has(intent);
  }

  getAllIntents(): ChatIntentName[] {
    this.ensureInitialized();
    return Array.from(this.intentsToHandlers.keys());
  }

  getIntentServerCount(): number {
    this.ensureInitialized();
    return this.intentsToHandlers.size;
  }

  // Additional utility methods
  unregister(intent: ChatIntentName): boolean {
    this.ensureInitialized();
    return this.intentsToHandlers.delete(intent);
  }

  // Lazy initialization method
  private ensureInitialized(): void {
    if (this.initialized) {
      return;
    }

        // In Node.js environment
    const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
    if (OPENAI_API_KEY) {
      this.register(ChatIntentName.QB, new QBServer(new GPTProvider(OPENAI_API_KEY)));
      console.log('Successfully registered QB intent server in Node.js environment');
    } else {
      throw new Error('OPENAI_API_KEY is not set');
    }
    
    this.initialized = true;
  }
}

// Global intent registry instance
export const INTENT_REGISTRY = new IntentRegistry();
