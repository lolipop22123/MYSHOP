import asyncpg
import logging
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from bot.database.models import User, Chat, Message, PremiumPricing, UserBalance, CryptoPayInvoice
from .connection import get_db_manager

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def create_user(self, telegram_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None, language: str = "ru") -> User:
        """Create new user"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO users (telegram_id, username, first_name, last_name, language, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, telegram_id, username, first_name, last_name, language, created_at, updated_at, is_active
            """, telegram_id, username, first_name, last_name, language, datetime.now(), datetime.now())
            
            return User(**dict(row))
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, telegram_id, username, first_name, last_name, language, created_at, updated_at, is_active
                FROM users WHERE telegram_id = $1
            """, telegram_id)
            
            return User(**dict(row)) if row else None
    
    async def update_user(self, telegram_id: int, **kwargs) -> Optional[User]:
        """Update user data"""
        if not kwargs:
            return None
            
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            # Build dynamic update query
            set_parts = []
            values = []
            param_num = 1
            
            for key, value in kwargs.items():
                set_parts.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
            
            # Add updated_at
            set_parts.append(f"updated_at = ${param_num}")
            values.append(datetime.now())
            param_num += 1
            
            # Add WHERE condition
            values.append(telegram_id)
            
            query = f"""
                UPDATE users SET {', '.join(set_parts)}
                WHERE telegram_id = ${param_num}
                RETURNING id, telegram_id, username, first_name, last_name, language, created_at, updated_at, is_active
            """
            
            row = await conn.fetchrow(query, *values)
            
            return User(**dict(row)) if row else None

    async def get_all_users(self) -> List[User]:
        """Get all users"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, telegram_id, username, first_name, last_name, language, created_at, updated_at, is_active
                FROM users WHERE is_active = TRUE
                ORDER BY created_at DESC
            """)
            return [User(**dict(row)) for row in rows]
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user by ID (cascade delete due to foreign keys)"""
        try:
            pool = await self.db_manager.get_pool()
            async with pool.acquire() as conn:
                # Delete user (cascade will handle related records)
                await conn.execute("DELETE FROM users WHERE id = $1", user_id)
                return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False


class ChatRepository:
    """Repository for chat operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def create_chat(self, telegram_id: int, chat_type: str, title: str = None, username: str = None) -> Chat:
        """Create new chat"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO chats (telegram_id, chat_type, title, username, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, telegram_id, chat_type, title, username, created_at, updated_at, is_active
            """, telegram_id, chat_type, title, username, datetime.now(), datetime.now())
            
            return Chat(**dict(row))
    
    async def get_chat_by_telegram_id(self, telegram_id: int) -> Optional[Chat]:
        """Get chat by telegram ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, telegram_id, chat_type, title, username, created_at, updated_at, is_active
                FROM chats WHERE telegram_id = $1
            """, telegram_id)
            
            return Chat(**dict(row)) if row else None


class MessageRepository:
    """Repository for message operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def create_message(self, telegram_id: int, user_id: int, chat_id: int, 
                           message_type: str = "text", text: str = None) -> Message:
        """Create new message"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO messages (telegram_id, user_id, chat_id, message_type, text, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, telegram_id, user_id, chat_id, message_type, text, created_at
            """, telegram_id, user_id, chat_id, message_type, text, datetime.now())
            
            return Message(**dict(row))
    
    async def get_messages_count(self, user_id: int = None, chat_id: int = None, 
                               today_only: bool = False) -> int:
        """Get messages count"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            query = "SELECT COUNT(*) FROM messages WHERE 1=1"
            params = []
            param_num = 1
            
            if user_id:
                query += f" AND user_id = ${param_num}"
                params.append(user_id)
                param_num += 1
            
            if chat_id:
                query += f" AND chat_id = ${param_num}"
                params.append(chat_id)
                param_num += 1
            
            if today_only:
                query += f" AND created_at >= ${param_num}"
                params.append(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
                param_num += 1
            
            count = await conn.fetchval(query, *params)
            return count


class PremiumPricingRepository:
    """Repository for premium pricing operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def get_price_for_months(self, months: int) -> Optional[float]:
        """Get price for given number of months"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT price_usd FROM premium_pricing 
                WHERE months = $1 AND is_active = TRUE
            """, months)
            
            return float(row['price_usd']) if row else None
    
    async def get_all_pricing(self) -> List[PremiumPricing]:
        """Get all active pricing"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, months, price_usd, is_active, created_at, updated_at
                FROM premium_pricing WHERE is_active = TRUE
                ORDER BY months
            """)
            return [PremiumPricing(**dict(row)) for row in rows]


class UserBalanceRepository:
    """Repository for user balance operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def get_user_balance(self, user_id: int) -> Optional[UserBalance]:
        """Get user balance"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, user_id, balance_usd, balance_usdt, created_at, updated_at
                FROM user_balance WHERE user_id = $1
            """, user_id)
            
            return UserBalance(**dict(row)) if row else None
    
    async def create_user_balance(self, user_id: int) -> UserBalance:
        """Create user balance record"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO user_balance (user_id, balance_usd, balance_usdt, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, user_id, balance_usd, balance_usdt, created_at, updated_at
            """, user_id, 0.0, 0.0, datetime.now(), datetime.now())
            
            return UserBalance(**dict(row))
    
    async def add_to_balance(self, user_id: int, amount: float) -> bool:
        """Add amount to user balance"""
        try:
            pool = await self.db_manager.get_pool()
            async with pool.acquire() as conn:
                # First, ensure user has a balance record
                balance = await self.get_user_balance(user_id)
                if not balance:
                    await self.create_user_balance(user_id)
                
                await conn.execute("""
                    UPDATE user_balance 
                    SET balance_usd = balance_usd + $1, updated_at = $2
                    WHERE user_id = $3
                """, amount, datetime.now(), user_id)
                
                return True
        except Exception as e:
            logger.error(f"Error adding to balance: {e}")
            return False
    
    async def subtract_from_balance(self, user_id: int, amount: float) -> bool:
        """Subtract amount from user balance"""
        try:
            pool = await self.db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE user_balance 
                    SET balance_usd = balance_usd - $1, updated_at = $2
                    WHERE user_id = $3 AND balance_usd >= $1
                """, amount, datetime.now(), user_id)
                
                return True
        except Exception as e:
            logger.error(f"Error subtracting from balance: {e}")
            return False


class CryptoPayInvoiceRepository:
    """Repository for crypto pay invoice operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def create_invoice(self, invoice_id: str, user_id: int, amount_usd: float,
                           amount_crypto: float, asset: str, payload: str = None) -> CryptoPayInvoice:
        """Create new crypto pay invoice"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            expires_at = datetime.now() + timedelta(hours=1)
            
            row = await conn.fetchrow("""
                INSERT INTO crypto_pay_invoices (invoice_id, user_id, amount_usd, amount_crypto, 
                                               asset, payload, expires_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, invoice_id, user_id, amount_usd, amount_crypto, asset, status, 
                         crypto_pay_url, payload, created_at, updated_at, paid_at, expires_at
            """, invoice_id, user_id, amount_usd, amount_crypto, asset, payload, expires_at, 
                 datetime.now(), datetime.now())
            
            return CryptoPayInvoice(**dict(row))
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[CryptoPayInvoice]:
        """Get invoice by ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, invoice_id, user_id, amount_usd, amount_crypto, asset, status, 
                       crypto_pay_url, payload, created_at, updated_at, paid_at, expires_at
                FROM crypto_pay_invoices WHERE invoice_id = $1
            """, invoice_id)
            
            return CryptoPayInvoice(**dict(row)) if row else None
    
    async def update_invoice_status(self, invoice_id: str, status: str, 
                                  crypto_pay_url: str = None) -> bool:
        """Update invoice status"""
        try:
            pool = await self.db_manager.get_pool()
            async with pool.acquire() as conn:
                update_fields = ["status = $1", "updated_at = $2"]
                params = [status, datetime.now()]
                param_num = 3
                
                if crypto_pay_url:
                    update_fields.append(f"crypto_pay_url = ${param_num}")
                    params.append(crypto_pay_url)
                    param_num += 1
                
                if status == "paid":
                    update_fields.append(f"paid_at = ${param_num}")
                    params.append(datetime.now())
                    param_num += 1
                
                params.append(invoice_id)
                
                query = f"""
                    UPDATE crypto_pay_invoices 
                    SET {', '.join(update_fields)}
                    WHERE invoice_id = ${param_num}
                """
                
                await conn.execute(query, *params)
                return True
        except Exception as e:
            logger.error(f"Error updating invoice status: {e}")
            return False
    
    async def get_pending_invoices(self) -> List[CryptoPayInvoice]:
        """Get all pending invoices"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, invoice_id, user_id, amount_usd, amount_crypto, asset, status, 
                       crypto_pay_url, payload, created_at, updated_at, paid_at, expires_at
                FROM crypto_pay_invoices 
                WHERE status = 'pending' AND expires_at > NOW()
                ORDER BY created_at ASC
            """)
            return [CryptoPayInvoice(**dict(row)) for row in rows] 