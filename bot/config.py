import os
from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    """Configuration class for bot settings"""
    bot_token: str
    database_url: str
    redis_url: str = None
    log_level: str = "INFO"
    admin_ids: List[int] = None
    default_language: str = "ru"
    token_fragment: str = ""
    
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is not set in environment variables")
        
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL is not set in environment variables")
        
        self.redis_url = os.getenv("REDIS_URL")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Admin IDs from environment variable
        admin_ids_str = os.getenv("ADMIN_IDS", "6956440009")  # Ваш ID
        self.admin_ids = [int(x.strip()) for x in admin_ids_str.split(",")]
        
        self.default_language = os.getenv("DEFAULT_LANGUAGE", "ru")
        
        # Fragment API token
        self.token_fragment = os.getenv("TOKEN_FRAGMENT", "")
        
        # Crypto Bot API token
        self.crypto_pay_token = os.getenv("CRYPTO_PAY_TOKEN", "")
        self.crypto_pay_testnet = os.getenv("CRYPTO_PAY_TESTNET", "false").lower() == "true" 