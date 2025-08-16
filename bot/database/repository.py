import asyncpg
import logging
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from bot.database.models import User, Chat, Message, Category, Subcategory, Product, Order, PremiumPricing, UserBalance, CryptoPayInvoice
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


class ChatRepository:
    """Repository for chat operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def create_chat(self, telegram_id: int, chat_type: str, 
                         title: str = None, username: str = None) -> Chat:
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


class CategoryRepository:
    """Repository for category operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def create_category(self, name: str, name_en: str, description: str = None, 
                            description_en: str = None, icon: str = "📦", sort_order: int = 0) -> Category:
        """Create new category"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO categories (name, name_en, description, description_en, icon, sort_order, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, name, name_en, description, description_en, icon, sort_order, is_active, created_at, updated_at
            """, name, name_en, description, description_en, icon, sort_order, datetime.now(), datetime.now())
            
            return Category(**dict(row))
    
    async def get_all_categories(self, active_only: bool = True) -> List[Category]:
        """Get all categories"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT id, name, name_en, description, description_en, icon, sort_order, is_active, created_at, updated_at
                FROM categories
            """
            if active_only:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY sort_order, name"
            
            rows = await conn.fetch(query)
            return [Category(**dict(row)) for row in rows]
    
    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name, name_en, description, description_en, icon, sort_order, is_active, created_at, updated_at
                FROM categories WHERE id = $1
            """, category_id)
            
            return Category(**dict(row)) if row else None
    
    async def update_category(self, category_id: int, **kwargs) -> Optional[Category]:
        """Update category"""
        if not kwargs:
            return None
            
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            set_parts = []
            values = []
            param_num = 1
            
            for key, value in kwargs.items():
                set_parts.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
            
            set_parts.append(f"updated_at = ${param_num}")
            values.append(datetime.now())
            param_num += 1
            values.append(category_id)
            
            query = f"""
                UPDATE categories SET {', '.join(set_parts)}
                WHERE id = ${param_num}
                RETURNING id, name, name_en, description, description_en, icon, sort_order, is_active, created_at, updated_at
            """
            
            row = await conn.fetchrow(query, *values)
            return Category(**dict(row)) if row else None
    
    async def delete_category(self, category_id: int) -> bool:
        """Delete category"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM categories WHERE id = $1", category_id)
            return result == "DELETE 1"


class SubcategoryRepository:
    """Repository for subcategory operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def create_subcategory(self, category_id: int, name: str, name_en: str, 
                               description: str = None, description_en: str = None, 
                               icon: str = "📦", sort_order: int = 0) -> Subcategory:
        """Create new subcategory"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO subcategories (category_id, name, name_en, description, description_en, icon, sort_order, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, category_id, name, name_en, description, description_en, icon, sort_order, is_active, created_at, updated_at
            """, category_id, name, name_en, description, description_en, icon, sort_order, datetime.now(), datetime.now())
            
            return Subcategory(**dict(row))
    
    async def get_subcategories_by_category(self, category_id: int, active_only: bool = True) -> List[Subcategory]:
        """Get subcategories by category ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT id, category_id, name, name_en, description, description_en, icon, sort_order, is_active, created_at, updated_at
                FROM subcategories WHERE category_id = $1
            """
            if active_only:
                query += " AND is_active = TRUE"
            query += " ORDER BY sort_order, name"
            
            rows = await conn.fetch(query, category_id)
            return [Subcategory(**dict(row)) for row in rows]
    
    async def get_subcategory_by_id(self, subcategory_id: int) -> Optional[Subcategory]:
        """Get subcategory by ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, category_id, name, name_en, description, description_en, icon, sort_order, is_active, created_at, updated_at
                FROM subcategories WHERE id = $1
            """, subcategory_id)
            
            return Subcategory(**dict(row)) if row else None
    
    async def update_subcategory(self, subcategory_id: int, **kwargs) -> Optional[Subcategory]:
        """Update subcategory"""
        if not kwargs:
            return None
            
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            set_parts = []
            values = []
            param_num = 1
            
            for key, value in kwargs.items():
                set_parts.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
            
            set_parts.append(f"updated_at = ${param_num}")
            values.append(datetime.now())
            param_num += 1
            values.append(subcategory_id)
            
            query = f"""
                UPDATE subcategories SET {', '.join(set_parts)}
                WHERE id = ${param_num}
                RETURNING id, category_id, name, name_en, description, description_en, icon, sort_order, is_active, created_at, updated_at
            """
            
            row = await conn.fetchrow(query, *values)
            return Subcategory(**dict(row)) if row else None
    
    async def delete_subcategory(self, subcategory_id: int) -> bool:
        """Delete subcategory"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM subcategories WHERE id = $1", subcategory_id)
            return result == "DELETE 1"


class ProductRepository:
    """Repository for product operations"""
    
    def __init__(self, database_url: str):
        self.db_manager = get_db_manager(database_url)
    
    async def create_product(self, category_id: int, name: str, name_en: str, 
                           description: str, description_en: str, price: float,
                           subcategory_id: int = None, image_url: str = None,
                           sort_order: int = 0) -> Product:
        """Create new product"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO products (category_id, name, name_en, description, description_en, 
                                   price, subcategory_id, image_url, sort_order, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id, category_id, name, name_en, description, description_en, 
                         price, subcategory_id, currency, image_url, is_active, sort_order, created_at, updated_at
            """, category_id, name, name_en, description, description_en, 
                 price, subcategory_id, image_url, sort_order, datetime.now(), datetime.now())
            
            return Product(**dict(row))
    
    async def get_products_by_category(self, category_id: int, active_only: bool = True) -> List[Product]:
        """Get products by category ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT id, category_id, name, name_en, description, description_en, 
                       price, subcategory_id, currency, image_url, is_active, sort_order, created_at, updated_at
                FROM products WHERE category_id = $1
            """
            if active_only:
                query += " AND is_active = TRUE"
            query += " ORDER BY sort_order, name"
            
            rows = await conn.fetch(query, category_id)
            return [Product(**dict(row)) for row in rows]
    
    async def get_products_by_subcategory(self, subcategory_id: int, active_only: bool = True) -> List[Product]:
        """Get products by subcategory ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT id, category_id, name, name_en, description, description_en, 
                       price, subcategory_id, currency, image_url, is_active, sort_order, created_at, updated_at
                FROM products WHERE subcategory_id = $1
            """
            if active_only:
                query += " AND is_active = TRUE"
            query += " ORDER BY sort_order, name"
            
            rows = await conn.fetch(query, subcategory_id)
            return [Product(**dict(row)) for row in rows]
    
    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, category_id, name, name_en, description, description_en, 
                       price, subcategory_id, currency, image_url, is_active, sort_order, created_at, updated_at
                FROM products WHERE id = $1
            """, product_id)
            
            return Product(**dict(row)) if row else None
    
    async def update_product(self, product_id: int, **kwargs) -> Optional[Product]:
        """Update product"""
        if not kwargs:
            return None
            
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            set_parts = []
            values = []
            param_num = 1
            
            for key, value in kwargs.items():
                set_parts.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
            
            set_parts.append(f"updated_at = ${param_num}")
            values.append(datetime.now())
            param_num += 1
            values.append(product_id)
            
            query = f"""
                UPDATE products SET {', '.join(set_parts)}
                WHERE id = ${param_num}
                RETURNING id, category_id, name, name_en, description, description_en, 
                         price, subcategory_id, currency, image_url, is_active, sort_order, created_at, updated_at
            """
            
            row = await conn.fetchrow(query, *values)
            return Product(**dict(row)) if row else None
    
    async def delete_product(self, product_id: int) -> bool:
        """Delete product"""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM products WHERE id = $1", product_id)
            return result == "DELETE 1"


class OrderRepository:
    """Repository for order operations"""
    
    def __init__(self, connection):
        self.connection = connection
    
    async def create_order(self, user_id: int, product_id: int, quantity: int = 1,
                          total_price: float = 0.0, payment_method: str = None) -> Order:
        """Create new order"""
        try:
            row = await self.connection.fetchrow("""
                INSERT INTO orders (user_id, product_id, quantity, total_price, payment_method, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                RETURNING id, user_id, product_id, quantity, total_price, currency, status, payment_method, created_at, updated_at
            """, user_id, product_id, quantity, total_price, payment_method)
            
            return Order(**dict(row))
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    async def get_orders_by_user(self, user_id: int) -> List[Order]:
        """Get orders by user ID"""
        try:
            rows = await self.connection.fetch("""
                SELECT id, user_id, product_id, quantity, total_price, currency, status, payment_method, created_at, updated_at
                FROM orders WHERE user_id = $1 ORDER BY created_at DESC
            """, user_id)
            
            return [Order(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting orders by user: {e}")
            return []
    
    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        try:
            row = await self.connection.fetchrow("""
                SELECT id, user_id, product_id, quantity, total_price, currency, status, payment_method, created_at, updated_at
                FROM orders WHERE id = $1
            """, order_id)
            
            return Order(**dict(row)) if row else None
        except Exception as e:
            logger.error(f"Error getting order by id: {e}")
            return None
    
    async def update_order_status(self, order_id: int, status: str) -> Optional[Order]:
        """Update order status"""
        try:
            row = await self.connection.fetchrow("""
                UPDATE orders SET status = $1, updated_at = NOW()
                WHERE id = $3
                RETURNING id, user_id, product_id, quantity, total_price, currency, status, payment_method, created_at, updated_at
            """, status, order_id)
            
            return Order(**dict(row)) if row else None
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return None


class PremiumPricingRepository:
    """Repository for Telegram Premium pricing"""
    
    def __init__(self, connection):
        self.connection = connection
    
    async def get_all_pricing(self) -> List[PremiumPricing]:
        """Get all premium pricing"""
        try:
            rows = await self.connection.fetch("""
                SELECT id, months, price_usd, is_active, created_at, updated_at
                FROM premium_pricing 
                ORDER BY months
            """)
            
            pricing_list = []
            for row in rows:
                pricing = PremiumPricing(
                    id=row[0],
                    months=row[1],
                    price_usd=float(row[2]),
                    is_active=row[3],
                    created_at=row[4],
                    updated_at=row[5]
                )
                pricing_list.append(pricing)
            
            return pricing_list
        except Exception as e:
            logger.error(f"Error getting all premium pricing: {e}")
            return []
    
    async def get_pricing_by_months(self, months: int) -> Optional[PremiumPricing]:
        """Get pricing for specific months"""
        try:
            row = await self.connection.fetchrow("""
                SELECT id, months, price_usd, is_active, created_at, updated_at
                FROM premium_pricing 
                WHERE months = $1
            """, months)
            
            if row:
                return PremiumPricing(
                    id=row[0],
                    months=row[1],
                    price_usd=float(row[2]),
                    is_active=row[3],
                    created_at=row[4],
                    updated_at=row[5]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting pricing for {months} months: {e}")
            return None
    
    async def update_pricing(self, months: int, price_usd: float) -> bool:
        """Update pricing for specific months"""
        try:
            await self.connection.execute("""
                UPDATE premium_pricing 
                SET price_usd = $1, updated_at = NOW()
                WHERE months = $2
            """, price_usd, months)
            
            return True
        except Exception as e:
            logger.error(f"Error updating pricing for {months} months: {e}")
            return False
    
    async def toggle_pricing_status(self, months: int) -> bool:
        """Toggle pricing active status"""
        try:
            await self.connection.execute("""
                UPDATE premium_pricing 
                SET is_active = NOT is_active, updated_at = NOW()
                WHERE months = $1
            """, months)
            
            return True
        except Exception as e:
            logger.error(f"Error toggling pricing status for {months} months: {e}")
            return False 


class UserBalanceRepository:
    """Repository for user balance management"""
    
    def __init__(self, connection):
        self.connection = connection
    
    async def get_user_balance(self, user_id: int) -> Optional[UserBalance]:
        """Get user balance by user_id"""
        try:
            row = await self.connection.fetchrow("""
                SELECT id, user_id, balance_usd, balance_usdt, created_at, updated_at
                FROM user_balance 
                WHERE user_id = $1
            """, user_id)
            
            if row:
                return UserBalance(
                    id=row[0],
                    user_id=row[1],
                    balance_usd=float(row[2]),
                    balance_usdt=float(row[3]),
                    created_at=row[4],
                    updated_at=row[5]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return None
    
    async def create_user_balance(self, user_id: int) -> bool:
        """Create user balance record"""
        try:
            await self.connection.execute("""
                INSERT INTO user_balance (user_id, balance_usd, balance_usdt)
                VALUES ($1, 0.00, 0.00)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id)
            return True
        except Exception as e:
            logger.error(f"Error creating user balance: {e}")
            return False
    
    async def update_balance(self, user_id: int, balance_usd: float, balance_usdt: float) -> bool:
        """Update user balance"""
        try:
            await self.connection.execute("""
                UPDATE user_balance 
                SET balance_usd = $1, balance_usdt = $2, updated_at = NOW()
                WHERE user_id = $1
            """, balance_usd, balance_usdt, user_id)
            return True
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            return False
    
    async def add_to_balance(self, user_id: int, amount_usd: float, amount_usdt: float) -> bool:
        """Add amount to user balance"""
        try:
            await self.connection.execute("""
                UPDATE user_balance 
                SET balance_usd = balance_usd + $1, 
                    balance_usdt = balance_usdt + $2, 
                    updated_at = NOW()
                WHERE user_id = $3
            """, amount_usd, amount_usdt, user_id)
            return True
        except Exception as e:
            logger.error(f"Error adding to user balance: {e}")
            return False


class CryptoPayInvoiceRepository:
    """Repository for Crypto Pay invoices"""
    
    def __init__(self, connection):
        self.connection = connection
    
    async def create_invoice(self, invoice_id: str, user_id: int, amount_usd: float, 
                           amount_crypto: float, asset: str, crypto_pay_url: str, payload: str = None) -> bool:
        """Create new crypto pay invoice"""
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            
            await self.connection.execute("""
                INSERT INTO crypto_pay_invoices 
                (invoice_id, user_id, amount_usd, amount_crypto, asset, crypto_pay_url, payload, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, str(invoice_id), int(user_id), float(amount_usd), float(amount_crypto), str(asset), str(crypto_pay_url), payload, expires_at)
            return True
        except Exception as e:
            logger.error(f"Error creating crypto pay invoice: {e}")
            return False
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[CryptoPayInvoice]:
        """Get invoice by invoice_id"""
        try:
            row = await self.connection.fetchrow("""
                SELECT id, invoice_id, user_id, amount_usd, amount_crypto, asset, 
                       status, crypto_pay_url, created_at, updated_at, paid_at, expires_at
                FROM crypto_pay_invoices 
                WHERE invoice_id = $1
            """, str(invoice_id))
            
            if row:
                return CryptoPayInvoice(
                    id=row[0],
                    invoice_id=row[1],
                    user_id=row[2],
                    amount_usd=float(row[3]),
                    amount_crypto=float(row[4]),
                    asset=row[5],
                    status=row[6],
                    crypto_pay_url=row[7],
                    created_at=row[8],
                    updated_at=row[9],
                    paid_at=row[10],
                    expires_at=row[11]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting invoice: {e}")
            return None
    
    async def update_invoice_status(self, invoice_id: str, status: str, paid_at: datetime = None) -> bool:
        """Update invoice status"""
        try:
            if paid_at:
                await self.connection.execute("""
                    UPDATE crypto_pay_invoices 
                    SET status = $1, paid_at = $2, updated_at = NOW()
                    WHERE invoice_id = $3
                """, str(status), paid_at, str(invoice_id))
            else:
                await self.connection.execute("""
                    UPDATE crypto_pay_invoices 
                    SET status = $1, updated_at = NOW()
                    WHERE invoice_id = $2
                """, str(status), str(invoice_id))
            return True
        except Exception as e:
            logger.error(f"Error updating invoice status: {e}")
            return False
    
    async def get_user_invoices(self, user_id: int) -> List[CryptoPayInvoice]:
        """Get all invoices for user"""
        try:
            rows = await self.connection.fetch("""
                SELECT id, invoice_id, user_id, amount_usd, amount_crypto, asset, 
                       status, crypto_pay_url, created_at, updated_at, paid_at, expires_at
                FROM crypto_pay_invoices 
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, int(user_id))
            
            invoices = []
            for row in rows:
                invoice = CryptoPayInvoice(
                    id=row[0],
                    invoice_id=row[1],
                    user_id=row[2],
                    amount_usd=float(row[3]),
                    amount_crypto=float(row[4]),
                    asset=row[5],
                    status=row[6],
                    crypto_pay_url=row[7],
                    created_at=row[8],
                    updated_at=row[9],
                    paid_at=row[10],
                    expires_at=row[11]
                )
                invoices.append(invoice)
            
            return invoices
        except Exception as e:
            logger.error(f"Error getting user invoices: {e}")
            return []
    
    async def get_pending_invoices(self) -> List[CryptoPayInvoice]:
        """Get all pending invoices"""
        try:
            rows = await self.connection.fetch("""
                SELECT id, invoice_id, user_id, amount_usd, amount_crypto, asset, 
                       status, crypto_pay_url, created_at, updated_at, paid_at, expires_at
                FROM crypto_pay_invoices 
                WHERE status = 'pending'
                ORDER BY created_at ASC
            """)
            
            invoices = []
            for row in rows:
                invoice = CryptoPayInvoice(
                    id=row[0],
                    invoice_id=row[1],
                    user_id=row[2],
                    amount_usd=float(row[3]),
                    amount_crypto=float(row[4]),
                    asset=row[5],
                    status=row[6],
                    crypto_pay_url=row[7],
                    created_at=row[8],
                    updated_at=row[9],
                    paid_at=row[10],
                    expires_at=row[11]
                )
                invoices.append(invoice)
            
            return invoices
        except Exception as e:
            logger.error(f"Error getting pending invoices: {e}")
            return [] 