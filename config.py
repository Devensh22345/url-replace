import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8283288287:AAGaDDCBX_rCF638Oztf2dt1mVChJ26Dg9g')
DEFAULT_USERNAME = os.getenv('DEFAULT_USERNAME', '@DK_ANIMES')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://10:10@cluster0.rbnwfqt.mongodb.net/?appName=Cluster0')
DB_NAME = os.getenv('DB_NAME', 'telegram_bot_db')

# Admin IDs (optional)
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '6872968794').split(',') if id]

# Global Settings (applied to all channels)
GLOBAL_WHITELIST = [
    '@DK_ANIMES'
    
    # Add more whitelisted usernames here
]

# Whitelisted URLs/domains (these won't be replaced)
WHITELISTED_URLS = [
    'telegram.org',
    
    # Add more whitelisted domains here
]
