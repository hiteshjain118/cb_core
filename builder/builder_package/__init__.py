"""
Builder - A Python library for building conversational AI systems
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com" 

# Re-export core modules for easier importing
from . import core
from . import model_providers
from . import qbo

# Make core, model_providers, and qbo available at the top level
__all__ = ['core', 'model_providers', 'qbo'] 