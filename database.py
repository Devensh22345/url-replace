from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI, DB_NAME
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URI)
            self.db = self.client[DB_NAME]
            
            # Create indexes
            await self.db.channels.create_index("channel_id", unique=True)
            await self.db.settings.create_index("key", unique=True)
            
            # Initialize global settings if not exists
            await self.init_global_settings()
            
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def init_global_settings(self):
        """Initialize global settings in database"""
        settings = await self.db.settings.find_one({"key": "global"})
        if not settings:
            from config import GLOBAL_WHITELIST, WHITELISTED_URLS, DEFAULT_USERNAME
            await self.db.settings.insert_one({
                "key": "global",
                "username": DEFAULT_USERNAME,
                "whitelist_usernames": GLOBAL_WHITELIST,
                "whitelist_urls": WHITELISTED_URLS,
                "settings": {
                    "add_username_to_all": True,
                    "replace_links": True,
                    "replace_usernames": True
                }
            })
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
    
    async def add_channel(self, channel_id: int, channel_title: str, added_by: int = None):
        """Add channel to database when bot is added"""
        channel_data = {
            "channel_id": channel_id,
            "channel_title": channel_title,
            "added_by": added_by,
            "added_at": datetime.utcnow(),
            "is_active": True
        }
        
        await self.db.channels.update_one(
            {"channel_id": channel_id},
            {"$set": channel_data},
            upsert=True
        )
        logger.info(f"Channel {channel_title} ({channel_id}) added to database")
        return channel_data
    
    async def remove_channel(self, channel_id: int):
        """Remove channel when bot is removed"""
        await self.db.channels.delete_one({"channel_id": channel_id})
        logger.info(f"Channel {channel_id} removed from database")
    
    async def get_channel(self, channel_id: int):
        """Get channel information"""
        return await self.db.channels.find_one({"channel_id": channel_id})
    
    async def get_all_channels(self):
        """Get all active channels"""
        cursor = self.db.channels.find({"is_active": True})
        return await cursor.to_list(length=None)
    
    async def update_channel_activity(self, channel_id: int, is_active: bool):
        """Update channel active status"""
        await self.db.channels.update_one(
            {"channel_id": channel_id},
            {"$set": {"is_active": is_active}}
        )
    
    # Global settings methods
    async def get_global_settings(self):
        """Get global settings"""
        settings = await self.db.settings.find_one({"key": "global"})
        if not settings:
            await self.init_global_settings()
            settings = await self.db.settings.find_one({"key": "global"})
        return settings
    
    async def update_global_username(self, username: str):
        """Update global username"""
        await self.db.settings.update_one(
            {"key": "global"},
            {"$set": {"username": username}}
        )
    
    async def add_to_whitelist_usernames(self, username: str):
        """Add username to global whitelist"""
        await self.db.settings.update_one(
            {"key": "global"},
            {"$addToSet": {"whitelist_usernames": username}}
        )
    
    async def remove_from_whitelist_usernames(self, username: str):
        """Remove username from global whitelist"""
        await self.db.settings.update_one(
            {"key": "global"},
            {"$pull": {"whitelist_usernames": username}}
        )
    
    async def get_whitelist_usernames(self):
        """Get global whitelisted usernames"""
        settings = await self.get_global_settings()
        return settings.get("whitelist_usernames", [])
    
    async def add_to_whitelist_urls(self, url: str):
        """Add URL to global whitelist"""
        await self.db.settings.update_one(
            {"key": "global"},
            {"$addToSet": {"whitelist_urls": url}}
        )
    
    async def remove_from_whitelist_urls(self, url: str):
        """Remove URL from global whitelist"""
        await self.db.settings.update_one(
            {"key": "global"},
            {"$pull": {"whitelist_urls": url}}
        )
    
    async def get_whitelist_urls(self):
        """Get global whitelisted URLs"""
        settings = await self.get_global_settings()
        return settings.get("whitelist_urls", [])
    
    async def update_global_settings(self, settings_dict: dict):
        """Update global settings"""
        await self.db.settings.update_one(
            {"key": "global"},
            {"$set": {"settings": settings_dict}}
        )

# Create database instance
db = Database()
