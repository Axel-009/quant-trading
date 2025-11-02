"""
Configuration module for Quant Trading project
Manages paths, constants, and environment variables securely
"""

import os
from pathlib import Path

# Base directory - automatically detects the project root
BASE_DIR = Path(__file__).parent.resolve()

# Data directories - now relative to project root
DATA_DIR = os.getenv('QUANT_DATA_DIR', BASE_DIR / 'data')
PREVIEW_DIR = os.getenv('QUANT_PREVIEW_DIR', BASE_DIR / 'preview')

# Smart Farmers project paths
SMART_FARMERS_DIR = BASE_DIR / 'Smart Farmers project'
SMART_FARMERS_DATA_DIR = SMART_FARMERS_DIR / 'data'

# Oil Money project paths
OIL_MONEY_DIR = BASE_DIR / 'Oil Money project'
OIL_MONEY_DATA_DIR = OIL_MONEY_DIR / 'data'

# Ore Money project paths
ORE_MONEY_DIR = BASE_DIR / 'Ore Money project'

# Monte Carlo project paths
MONTE_CARLO_DIR = BASE_DIR / 'Monte Carlo project'

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        DATA_DIR,
        PREVIEW_DIR,
        SMART_FARMERS_DATA_DIR,
        OIL_MONEY_DATA_DIR,
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Trading constants
TRADING_DAYS_PER_YEAR = 250
TRADING_HOURS_PER_DAY = 6.5  # US market

# Statistical thresholds
COINTEGRATION_P_VALUE_THRESHOLD = 0.05
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
BOLLINGER_BANDS_SIGMA = 2

# Risk management
DEFAULT_INITIAL_CAPITAL = 20000
MAX_POSITION_SIZE = 0.2  # 20% of capital per position
STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss

# Data source configuration
YAHOO_FINANCE_MAX_RETRIES = 3
DATA_CACHE_EXPIRY_HOURS = 24

# API Configuration (if needed in future)
# Note: Never commit API keys to git! Use environment variables
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
QUANDL_API_KEY = os.getenv('QUANDL_API_KEY', '')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = BASE_DIR / 'quant_trading.log'

def get_data_path(filename):
    """
    Get the full path for a data file

    Args:
        filename (str): Name of the data file

    Returns:
        Path: Full path to the data file
    """
    return Path(DATA_DIR) / filename

def get_preview_path(filename):
    """
    Get the full path for a preview/chart file

    Args:
        filename (str): Name of the preview file

    Returns:
        Path: Full path to the preview file
    """
    return Path(PREVIEW_DIR) / filename

# Initialize directories on import
ensure_directories()

# Configuration validation
def validate_config():
    """Validate that all required paths and settings are correct"""
    errors = []

    if not BASE_DIR.exists():
        errors.append(f"Base directory does not exist: {BASE_DIR}")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))

# Run validation
validate_config()
