# Builder Library

A Python library for building conversational AI systems with intent classification, slot extraction, and model provider abstractions.

## Features

- **Intent Classification**: Classify user intents using various ML models
- **Slot Extraction**: Extract structured data from user utterances
- **Model Providers**: Abstract interface for different LLM providers (GPT, DS, etc.)
- **Memory Management**: Conversation memory and context management
- **Retrieval Systems**: Interface for retrieving relevant information

## Structure

```
builder/
├── core/                    # Core functionality
│   ├── intent_classifier.py # Intent classification logic
│   ├── slots.py            # Slot extraction
│   ├── memory.py           # Memory management
│   ├── intents.py          # Intent definitions
│   ├── structs.py          # Data structures
│   ├── enums.py            # Enumerations
│   ├── tod_types.py        # Type definitions
│   └── tests/              # Core tests
└── model_providers/        # Model provider implementations
    ├── gpt_provider.py     # GPT model provider
    ├── ds_provider.py      # DS model provider
    ├── llm_monitor.py      # LLM monitoring
    ├── token_util.py       # Token utilities
    └── tests/              # Provider tests
```

## Installation

```bash
pip install -e .
```

## Usage

```python
from builder.core.intent_classifier import IntentClassifier
from builder.model_providers.gpt_provider import GPTProvider

# Initialize components
provider = GPTProvider()
classifier = IntentClassifier(provider)

# Classify intent
intent = classifier.classify("What's the weather like?")
```

## Development

This library is used as a dependency by the QBO project. 