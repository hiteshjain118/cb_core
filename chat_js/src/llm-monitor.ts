import { countTokens } from './token-util';
import { ChatIntentName } from './types/enums';

/**
 * Interface for token usage statistics
 */
interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
}

/**
 * Interface for intent-specific statistics
 */
interface IntentStats {
  input_tokens: number;
  output_tokens: number;
  llm_calls: number;
}

/**
 * Interface for usage statistics summary
 */
interface UsageStatistics {
  summary: {
    total_input_tokens: number;
    total_output_tokens: number;
    total_tokens: number;
    total_llm_calls: number;
    estimated_app_cost: number;
    estimated_total_cost: number;
  };
  breakdown_by_intent: Record<string, {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    llm_calls: number;
    estimated_cost: number;
  }>;
  tools_token_usage: {
    input_tokens: number;
    output_tokens: number;
    estimated_cost: number;
  };
}

/**
 * LLM Monitor class for tracking token usage and API calls
 */
export class LLMMonitor {
  private model: string;
  private name: string;
  private toolsTokenUsage: TokenUsage;
  private totalInputTokens: number = 0;
  private totalOutputTokens: number = 0;
  private totalLlmCalls: number = 0;
  private intentTokenUsage: Map<string, IntentStats> = new Map();
  
  private estimatedCosts: Record<string, { input: number; output: number }> = {
    'gpt-4o-mini': { input: 0.6 * 1e-6, output: 2.4 * 1e-6 }, // per token
    'gpt-4o': { input: 5 * 1e-6, output: 20 * 1e-6 }, // per token
    'deepseek-ai/DeepSeek-R1-Distill-Llama-70B': { input: 0.1 * 1e-6, output: 0.4 * 1e-6 }, // per token
    'deepseek-ai/DeepSeek-V3': { input: 0.38 * 1e-6, output: 0.89 * 1e-6 } // per token
  };

  constructor(model: string = "gpt-4o", name: string = "LLMMonitor") {
    this.model = model;
    this.name = name;
    this.toolsTokenUsage = {
      input_tokens: 0,
      output_tokens: 0
    };
    
    console.info(`LLM Monitor '${name}' initialized with model: ${model}`);
  }

  /**
   * Calculate token count for input messages only.
   */
  calculateInputTokens(messages: Array<{ role: string; content: string }>, intent: ChatIntentName): number {
    if (!messages || messages.length === 0) {
      return 0;
    }

    // Validate that the last message is not from the assistant
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) {
      throw new Error(`No messages provided for intent: ${intent}`);
    }
    if (lastMessage.role === 'assistant') {
      throw new Error(
        `Last message in input messages should not be from assistant. ` +
        `Intent: ${intent}, Last message role: ${lastMessage.role}`
      );
    }

    let inputTokens = 0;

    try {
      // Calculate input tokens (all messages since none should be from assistant)
      for (const message of messages) {
        const content = message.content || '';
        inputTokens += countTokens(content, this.model);
      }

      return inputTokens;
    } catch (error) {
      console.error(`Error calculating input tokens: ${error}`);
      return 0;
    }
  }

  /**
   * Calculate token count for both input and output messages.
   */
  calculateInputAndOutputTokens(
    messages: Array<{ role: string; content: string }>, 
    intent: ChatIntentName
  ): { input_tokens: number; output_tokens: number } {
    if (!messages || messages.length === 0) {
      return { input_tokens: 0, output_tokens: 0 };
    }

    // Validate that the last message is from the assistant
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) {
      throw new Error(`No messages provided for intent: ${intent}`);
    }
    if (lastMessage.role !== 'assistant') {
      throw new Error(
        `Last message in input and output messages should be from assistant. ` +
        `Intent: ${intent}, Last message role: ${lastMessage.role}`
      );
    }

    try {
      // Get input messages (all except the last assistant message)
      const inputMessages = messages.slice(0, -1);

      // Calculate input tokens using the existing method
      const inputTokens = this.calculateInputTokens(inputMessages, intent);

      // Calculate output tokens (last message from assistant)
      const content = lastMessage.content || '';
      const outputTokens = countTokens(content, this.model);

      console.debug(
        `Token calculation for ${intent}: input=${inputTokens}, output=${outputTokens}`
      );

      return {
        input_tokens: inputTokens,
        output_tokens: outputTokens
      };
    } catch (error) {
      console.error(`Error calculating input and output tokens: ${error}`);
      return { input_tokens: 0, output_tokens: 0 };
    }
  }

  /**
   * Record an LLM call with token usage and metadata.
   */
  recordLlmCall(
    messages: Array<{ role: string; content: string }>,
    intent: ChatIntentName,
    responseContent: string,
    toolCallsInResponse: Array<{ function: { name: string; arguments: string } }> = [],
    toolsInPrompt: string = ""
  ): void {
    // Calculate input tokens
    const inputTokens = this.calculateInputTokens(messages, intent);
    const outputTokens = countTokens(responseContent, this.model);

    // Calculate output tokens for tool calls
    let toolsOutputTokens = 0;
    if (toolCallsInResponse) {
      for (const toolCall of toolCallsInResponse) {
        toolsOutputTokens += countTokens(toolCall.function.name, this.model);
        toolsOutputTokens += countTokens(toolCall.function.arguments, this.model);
      }
    }

    const toolInputTokens = countTokens(toolsInPrompt, this.model);
    this.toolsTokenUsage.input_tokens += toolInputTokens;
    this.toolsTokenUsage.output_tokens += toolsOutputTokens;

    // Update totals
    this.totalInputTokens += (inputTokens + toolInputTokens);
    this.totalOutputTokens += (outputTokens + toolsOutputTokens);
    this.totalLlmCalls += 1;

    // Update per-intent statistics
    const intentKey = intent || "Unknown";
    if (!this.intentTokenUsage.has(intentKey)) {
      this.intentTokenUsage.set(intentKey, {
        input_tokens: 0,
        output_tokens: 0,
        llm_calls: 0
      });
    }

    const intentStats = this.intentTokenUsage.get(intentKey)!;
    intentStats.input_tokens += (inputTokens + toolInputTokens);
    intentStats.output_tokens += (outputTokens + toolsOutputTokens);
    intentStats.llm_calls += 1;
  }

  /**
   * Get comprehensive usage statistics including totals and breakdown by intent.
   */
  getUsageStatistics(): UsageStatistics {
    // Calculate total costs
    const totalAppCost = this.calculateAppCost();

    // Prepare per-intent breakdown
    const intentBreakdown: Record<string, any> = {};
    this.intentTokenUsage.forEach((stats, intent) => {
      const intentCost = this.calculateCost(stats.input_tokens, stats.output_tokens);
      intentBreakdown[intent] = {
        input_tokens: stats.input_tokens,
        output_tokens: stats.output_tokens,
        total_tokens: stats.input_tokens + stats.output_tokens,
        llm_calls: stats.llm_calls,
        estimated_cost: intentCost
      };
    });

    return {
      summary: {
        total_input_tokens: this.totalInputTokens,
        total_output_tokens: this.totalOutputTokens,
        total_tokens: this.totalInputTokens + this.totalOutputTokens,
        total_llm_calls: this.totalLlmCalls,
        estimated_app_cost: totalAppCost,
        estimated_total_cost: this.calculateToolsCost() + totalAppCost
      },
      breakdown_by_intent: intentBreakdown,
      tools_token_usage: {
        input_tokens: this.toolsTokenUsage.input_tokens,
        output_tokens: this.toolsTokenUsage.output_tokens,
        estimated_cost: this.calculateToolsCost()
      }
    };
  }

  /**
   * Reset all statistics to zero
   */
  resetStatistics(): void {
    this.totalInputTokens = 0;
    this.totalOutputTokens = 0;
    this.totalLlmCalls = 0;
    this.intentTokenUsage.clear();
    this.toolsTokenUsage = { input_tokens: 0, output_tokens: 0 };
    console.info(`LLM usage statistics reset for ${this.name}`);
  }

  /**
   * Print usage summary for this monitor
   */
  printUsageSummary(): void {
    const stats = this.getUsageStatistics();
    const summary = stats.summary;
    const toolsTokenUsage = stats.tools_token_usage;

    let toolsTokenUsageStr = "";
    if (toolsTokenUsage.input_tokens > 0 || toolsTokenUsage.output_tokens > 0) {
      const overheadCostFraction = toolsTokenUsage.estimated_cost / summary.estimated_total_cost;
      toolsTokenUsageStr = (
        `Tools input tokens: ${toolsTokenUsage.input_tokens}, ` +
        `Tools output tokens: ${toolsTokenUsage.output_tokens}, ` +
        `Overhead cost: $${toolsTokenUsage.estimated_cost.toFixed(6)} (${(overheadCostFraction * 100).toFixed(2)}%)`
      );
    }

    console.debug(
      `${this.name} Usage Summary: ` +
      `Total calls: ${summary.total_llm_calls}, ` +
      `Input tokens: ${summary.total_input_tokens}, ` +
      `Output tokens: ${summary.total_output_tokens}, ` +
      `Estimated cost: $${summary.estimated_total_cost.toFixed(6)} ` +
      toolsTokenUsageStr
    );

    // Log breakdown by intent if there are any
    if (Object.keys(stats.breakdown_by_intent).length > 0) {
      const intentDetails: string[] = [];
      for (const [intentName, intentStats] of Object.entries(stats.breakdown_by_intent)) {
        intentDetails.push(
          `${intentName}: ${intentStats.llm_calls} calls, ` +
          `${intentStats.total_tokens} tokens, ` +
          `$${intentStats.estimated_cost.toFixed(6)}`
        );
      }
      console.debug(`${this.name} Breakdown: ${intentDetails.join(', ')}`);
    }
  }

  /**
   * Export usage statistics to a JSON file.
   */
  async exportStatistics(filepath: string): Promise<void> {
    try {
      const stats = this.getUsageStatistics();
      const statsJson = JSON.stringify(stats, null, 2);
      
      // In Node.js environment, you would use fs.writeFileSync
      // For browser environment, you might trigger a download
      console.info(`Usage statistics would be exported to ${filepath}`);
      console.debug('Statistics:', statsJson);
    } catch (error) {
      console.error(`Error exporting statistics: ${error}`);
    }
  }

  /**
   * Get usage statistics for a specific intent.
   */
  getIntentUsage(intent: ChatIntentName): {
    intent: string;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    llm_calls: number;
    estimated_cost: number;
  } {
    const intentKey = intent;
    const stats = this.intentTokenUsage.get(intentKey) || {
      input_tokens: 0,
      output_tokens: 0,
      llm_calls: 0
    };

    return {
      intent: intentKey,
      input_tokens: stats.input_tokens,
      output_tokens: stats.output_tokens,
      total_tokens: stats.input_tokens + stats.output_tokens,
      llm_calls: stats.llm_calls,
      estimated_cost: this.calculateCost(stats.input_tokens, stats.output_tokens)
    };
  }

  /**
   * Calculate estimated cost for token usage.
   */
  private calculateCost(inputTokens: number, outputTokens: number): number {
    const model = this.estimatedCosts[this.model] ? this.model : "gpt-4o"; // Default to gpt-4o pricing
    const pricing = this.estimatedCosts[model];
    if (!pricing) {
      throw new Error(`No pricing information available for model: ${model}`);
    }
    const inputCost = inputTokens * pricing.input;
    const outputCost = outputTokens * pricing.output;

    return Math.round((inputCost + outputCost) * 1000000) / 1000000; // Round to 6 decimal places
  }

  /**
   * Calculate total estimated cost across all calls
   */
  private calculateAppCost(): number {
    let totalCost = 0.0;

    this.intentTokenUsage.forEach((stats) => {
      const cost = this.calculateCost(stats.input_tokens, stats.output_tokens);
      totalCost += cost;
    });

    return Math.round(totalCost * 1000000) / 1000000; // Round to 6 decimal places
  }

  /**
   * Calculate total estimated cost for tools
   */
  private calculateToolsCost(): number {
    const cost = this.calculateCost(
      this.toolsTokenUsage.input_tokens,
      this.toolsTokenUsage.output_tokens
    );
    return Math.round(cost * 1000000) / 1000000; // Round to 6 decimal places
  }
} 