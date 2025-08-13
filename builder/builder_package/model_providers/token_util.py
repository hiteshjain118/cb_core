import logging


def count_tokens(text, model="gpt-3.5-turbo"):
    """
    Estimate the number of LLM tokens in a string.

    Args:
        text (str): The text to count tokens for
        model (str): The model to use for tokenization (default: gpt-3.5-turbo)

    Returns:
        int: Estimated number of tokens
    """
    if text is None:
        return 0
    if not isinstance(text, str):
        text = str(text)

    try:
        # Try to use tiktoken for accurate tokenization
        import tiktoken

        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except (ImportError, KeyError, Exception) as e:
        # Fallback to simple heuristic: ~4 characters per token for English text
        logging.debug(f"Using heuristic token counting (tiktoken failed: {e})")
        # Rough estimate: 1 token ≈ 4 characters for English text
        # Adjust for whitespace and special characters
        char_count = len(text)
        # Reduce count for whitespace and punctuation
        whitespace_chars = text.count(" ") + text.count("\n") + text.count("\t")
        punctuation_chars = sum(1 for c in text if c in ".,!?;:")
        adjusted_chars = (
            char_count - (whitespace_chars * 0.5) - (punctuation_chars * 0.3)
        )
        return max(1, int(adjusted_chars / 4))


def log_token_count(text, context=""):
    """
    Log the token count for a given text with optional context.

    Args:
        text (str): The text to count tokens for
        context (str): Optional context for the log message

    Returns:
        int: Number of tokens
    """
    token_count = count_tokens(text)
    context_msg = f" ({context})" if context else ""
    logging.debug(
        f"Token count: {token_count}{context_msg} - Text length: {len(text)} chars"
    )
    return token_count


def main():
    """Main function to analyze token count for agoda_example.json"""
    import json

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        # Read the agoda example JSON file
        with open("agoda_example.json", "r") as f:
            data = json.load(f)

        # Convert to string for token counting
        json_str = json.dumps(data, indent=2)

        # Count tokens
        token_count = count_tokens(json_str)
        char_count = len(json_str)

        print(f"Agoda Example JSON Analysis:")
        print(f"Character count: {char_count:,}")
        print(f"Token count (GPT-3.5-turbo): {token_count:,}")
        print(f"Token count (GPT-4): {count_tokens(json_str, 'gpt-4'):,}")
        print(
            f"Token count (Claude): {count_tokens(json_str, 'claude-3-sonnet'):,}"
        )

        # Also analyze just the properties section
        if "data" in data and "properties" in data["data"]:
            properties = data["data"]["properties"]
            properties_str = json.dumps(properties, indent=2)
            properties_tokens = count_tokens(properties_str)
            print(f"\nProperties section only:")
            print(f"Character count: {len(properties_str):,}")
            print(f"Token count: {properties_tokens:,}")
            print(f"Number of properties: {len(properties)}")

    except FileNotFoundError:
        print("Error: agoda_example.json not found in current directory")
    except Exception as e:
        print(f"Error analyzing file: {e}")


if __name__ == "__main__":
    main()
