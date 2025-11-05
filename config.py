"""
Configuration module for invoice processing service.
Loads environment variables and provides centralized configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for the invoice processing service."""

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = "gpt-4o"  # Using GPT-4 with vision for invoice processing

    # File paths
    INVOICES_DIR = "Invoices"
    TAX_RATES_FILE = "tax_rate_by_category.csv"
    OUTPUT_DIR = "output"

    # Processing settings
    MAX_TOKENS = 4000
    TEMPERATURE = 0.0  # Zero temperature for maximum consistency and deterministic outputs

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return True
