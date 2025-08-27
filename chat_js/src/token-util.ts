/**
 * Token counting utilities for LLM models
 */

/**
 * Estimate the number of LLM tokens in a string.
 * 
 * @param text - The text to count tokens for
 * @param model - The model to use for tokenization (default: gpt-3.5-turbo)
 * @returns Estimated number of tokens
 */
export function countTokens(text: string | null | undefined, model: string = "gpt-3.5-turbo"): number {
  if (text === null || text === undefined) {
    return 0;
  }
  
  if (typeof text !== 'string') {
    text = String(text);
  }

  try {
    // For now, use heuristic approach since tiktoken is not available in browser/Node.js easily
    // In a real implementation, you might want to use a package like @dqbd/tiktoken
    return estimateTokensHeuristic(text);
  } catch (error) {
    console.debug(`Using heuristic token counting (tiktoken failed: ${error})`);
    return estimateTokensHeuristic(text);
  }
}

/**
 * Heuristic token estimation: ~4 characters per token for English text
 */
function estimateTokensHeuristic(text: string): number {
  const charCount = text.length;
  
  // Count whitespace and punctuation for adjustment
  const whitespaceChars = (text.match(/[ \n\t]/g) || []).length;
  const punctuationChars = (text.match(/[.,!?;:]/g) || []).length;
  
  // Adjust for whitespace and punctuation
  const adjustedChars = charCount - (whitespaceChars * 0.5) - (punctuationChars * 0.3);
  
  return Math.max(1, Math.floor(adjustedChars / 4));
}

/**
 * Log the token count for a given text with optional context.
 * 
 * @param text - The text to count tokens for
 * @param context - Optional context for the log message
 * @returns Number of tokens
 */
export function logTokenCount(text: string, context: string = ""): number {
  const tokenCount = countTokens(text);
  const contextMsg = context ? ` (${context})` : "";
  
  console.debug(
    `Token count: ${tokenCount}${contextMsg} - Text length: ${text.length} chars`
  );
  
  return tokenCount;
} 