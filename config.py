"""
Configuration file for the Telegram bot.
Contains configuration settings and loads sensitive data from environment variables.
"""

import os
import dotenv
from typing import List

# Load environment variables from .env file
dotenv.load_dotenv()

# Bot token loaded from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin user IDs loaded from environment variable
ADMIN_USER_IDS_STR = os.getenv("ADMIN_USER_IDS", "")
ADMIN_USER_IDS: List[int] = []
if ADMIN_USER_IDS_STR:
    try:
        ADMIN_USER_IDS = [int(user_id.strip()) for user_id in ADMIN_USER_IDS_STR.split(",")]
    except ValueError:
        print("Warning: Invalid format for ADMIN_USER_IDS in .env file")

# Database configuration
DATABASE_FILE = "bot_database.json"

# Payment configuration
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# Bot settings
BOT_USERNAME = ""  # Will be filled when bot starts
