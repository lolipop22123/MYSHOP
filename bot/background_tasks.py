import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from bot.database.connection import get_connection
from bot.database.repository import CryptoPayInvoiceRepository, UserBalanceRepository
from bot.crypto_pay_api import CryptoPayAPI
from bot.config import Config

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manager for background tasks"""
    
    def __init__(self, bot=None):
        self.running = False
        self.check_interval = 60  # seconds - check every minute
        self.config = None  # Will be initialized when needed
        self.bot = bot  # Bot instance for sending notifications
    
    def set_bot(self, bot):
        """Set bot instance for notifications"""
        self.bot = bot
        logger.info("Bot instance set for background tasks")
    
    def _get_config(self):
        """Get config instance, initialize if needed"""
        if self.config is None:
            self.config = Config()
        return self.config
    
    async def start(self):
        """Start background tasks"""
        if self.running:
            logger.warning("Background tasks already running")
            return
        
        self.running = True
        logger.info("Starting background tasks...")
        
        # Start invoice checking task
        asyncio.create_task(self.check_pending_invoices())
        
        # Start other background tasks here if needed
        # asyncio.create_task(self.other_task())
    
    async def stop(self):
        """Stop background tasks"""
        self.running = False
        logger.info("Stopping background tasks...")
    
    async def check_pending_invoices(self):
        """Check all pending invoices for payment status"""
        logger.info("Background task: check_pending_invoices started")
        while self.running:
            try:
                logger.debug("Background task: checking pending invoices...")
                await self._check_pending_invoices_once()
                logger.debug(f"Background task: waiting {self.check_interval} seconds before next check")
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in check_pending_invoices task: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_pending_invoices_once(self):
        """Check pending invoices once"""
        config = self._get_config()
        logger.debug(f"Background task: config loaded, crypto_pay_token: {'configured' if config.crypto_pay_token else 'not configured'}")
        
        if not config.crypto_pay_token:
            logger.debug("Crypto Pay token not configured, skipping invoice check")
            return
        
        logger.info(f"Background task: using Crypto Pay API with token: {config.crypto_pay_token[:10]}...")
        logger.info(f"Background task: testnet mode: {config.crypto_pay_testnet}")
        
        try:
            logger.debug("Background task: getting database connection...")
            # Get connection to database
            pool = await get_connection(config.database_url)
            invoice_repo = CryptoPayInvoiceRepository(pool)
            balance_repo = UserBalanceRepository(pool)
            
            logger.debug("Background task: getting pending invoices...")
            # Get all pending invoices
            pending_invoices = await invoice_repo.get_pending_invoices()
            
            if not pending_invoices:
                logger.debug("No pending invoices to check")
                return
            
            logger.info(f"Checking {len(pending_invoices)} pending invoices...")
            
            # Initialize Crypto Pay API
            crypto_api = CryptoPayAPI(config.crypto_pay_token, config.crypto_pay_testnet)
            
            # Test API connection first
            logger.info("Testing Crypto Pay API connection...")
            me_info = await crypto_api.get_me()
            if me_info:
                logger.info(f"Crypto Pay API connection successful: {me_info}")
            else:
                logger.error("Crypto Pay API connection failed!")
                return
            
            # Check each pending invoice
            for invoice in pending_invoices:
                try:
                    await self._check_single_invoice(invoice, crypto_api, invoice_repo, balance_repo)
                except Exception as e:
                    logger.error(f"Error checking invoice {invoice.invoice_id}: {e}")
                    continue
                
                # Small delay between API calls to avoid rate limiting
                await asyncio.sleep(0.5)
            
            logger.info(f"Invoice check completed, processed {len(pending_invoices)} invoices")
            
        except Exception as e:
            logger.error(f"Error in _check_pending_invoices_once: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _check_single_invoice(self, invoice, crypto_api, invoice_repo, balance_repo):
        """Check single invoice status and update if paid"""
        try:
            # Check if invoice is expired (3 minutes from creation)
            from datetime import timezone
            current_time = datetime.now(timezone.utc)
            
            # Make sure created_at is timezone-aware
            created_at = invoice.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            # Set expiration to 3 minutes from creation
            expiration_time = created_at + timedelta(minutes=3)
            
            if current_time > expiration_time and invoice.status not in ["expired", "paid"]:
                logger.info(f"Invoice {invoice.invoice_id} expired, marking as expired")
                await invoice_repo.update_invoice_status(invoice.invoice_id, "expired")
                
                # Send expiration notification to user
                await self._send_expiration_notification(invoice)
                return
            
            # Get current status from Crypto Pay API
            invoice_data = await crypto_api.get_invoice(invoice.invoice_id)
            if not invoice_data:
                logger.warning(f"Could not get status for invoice {invoice.invoice_id}")
                return
            
            status = invoice_data.get("status")
            logger.debug(f"Invoice {invoice.invoice_id} status: {status}")
            
            if status == "paid" and invoice.status != "paid":
                logger.info(f"Invoice {invoice.invoice_id} paid, updating balance for user {invoice.user_id}")
                
                # Update invoice status with timezone-aware datetime
                await invoice_repo.update_invoice_status(invoice.invoice_id, "paid", current_time)
                
                # Check if this is a subscription payment invoice
                if invoice.payload and "premium_" in invoice.payload:
                    # This is a subscription payment - create Fragment order
                    await self._process_subscription_payment(invoice)
                elif invoice.payload and "stars_" in invoice.payload:
                    # This is a stars payment - create Fragment order
                    await self._process_stars_payment(invoice)
                else:
                    # Regular balance top-up
                    success = await balance_repo.add_to_balance(
                        invoice.user_id, 
                        invoice.amount_usd, 
                        0  # No USDT balance for now
                    )
                    
                    if success:
                        logger.info(f"Successfully added ${invoice.amount_usd} to user {invoice.user_id} balance")
                        
                        # Send payment success notification to user
                        await self._send_payment_success_notification(invoice, invoice.amount_usd)
                    else:
                        logger.error(f"Failed to add balance for user {invoice.user_id}")
                
            elif status in ["expired", "cancelled"] and invoice.status != status:
                logger.info(f"Invoice {invoice.invoice_id} status changed to {status}")
                await invoice_repo.update_invoice_status(invoice.invoice_id, status)
                
                if status == "expired":
                    # Send expiration notification to user
                    await self._send_expiration_notification(invoice)
                
        except Exception as e:
            logger.error(f"Error checking single invoice {invoice.invoice_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _process_subscription_payment(self, invoice):
        """Process subscription payment - create Fragment order"""
        try:
            logger.info(f"Processing subscription payment for invoice {invoice.invoice_id}")
            
            # Parse payload: user_{user_id}_premium_{months}m_{username}
            payload_parts = invoice.payload.split("_")
            if len(payload_parts) >= 4:
                user_id = int(payload_parts[1])
                months = int(payload_parts[3].replace("m", ""))
                username = payload_parts[4]
                
                logger.info(f"Creating Fragment order: {months} months for @{username}")
                
                # Get config and create Fragment API instance
                config = self._get_config()
                from bot.fragment_api import FragmentAPI
                
                fragment_api = FragmentAPI(
                    token=config.token_fragment,
                    demo_mode=not bool(config.token_fragment and config.token_fragment.strip())
                )
                
                # Create Fragment order
                order, error_info = await fragment_api.create_premium_order(username, months, show_sender=False)
                
                if order:
                    logger.info(f"Fragment order created successfully: {order.id}")
                    
                    # Send success notification to user
                    await self._send_subscription_success_notification(invoice, order, months, username)
                    
                    # Notify admins
                    await self._notify_admins_subscription_created(invoice, order, months, username)
                    
                else:
                    logger.error(f"Failed to create Fragment order: {error_info}")
                    # Send error notification to user
                    await self._send_subscription_error_notification(invoice, error_info, months, username)
                    
            else:
                logger.error(f"Invalid payload format for subscription invoice: {invoice.payload}")
                
        except Exception as e:
            logger.error(f"Error processing subscription payment: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _process_stars_payment(self, invoice):
        """Process stars payment - create Fragment order"""
        try:
            logger.info(f"Processing stars payment for invoice {invoice.invoice_id}")
            
            # Parse payload: user_{user_id}_stars_{stars_count}_{username}
            payload_parts = invoice.payload.split("_")
            if len(payload_parts) >= 4:
                user_id = int(payload_parts[1])
                stars_count = int(payload_parts[3])
                username = payload_parts[4]
                
                logger.info(f"Creating Fragment stars order: {stars_count} stars for @{username}")
                
                # Get config and create Fragment API instance
                config = self._get_config()
                from bot.fragment_api import FragmentAPI
                
                fragment_api = FragmentAPI(
                    token=config.token_fragment,
                    demo_mode=not bool(config.token_fragment and config.token_fragment.strip())
                )
                
                # Create Fragment order
                order, error_info = await fragment_api.create_stars_order(username, stars_count, show_sender=False)
                
                if order:
                    logger.info(f"Fragment stars order created successfully: {order.id}")
                    
                    # Send success notification to user
                    await self._send_stars_success_notification(invoice, order, stars_count, username)
                    
                    # Notify admins
                    await self._notify_admins_stars_created(invoice, order, stars_count, username)
                    
                else:
                    logger.error(f"Failed to create Fragment stars order: {error_info}")
                    # Send error notification to user
                    await self._send_stars_error_notification(invoice, error_info, stars_count, username)
                    
            else:
                logger.error(f"Invalid payload format for stars invoice: {invoice.payload}")
                
        except Exception as e:
            logger.error(f"Error processing stars payment: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _send_subscription_success_notification(self, invoice, order, months, username):
        """Send subscription success notification to user"""
        try:
            if not self.bot:
                logger.warning("Bot instance not available, cannot send notification")
                return
            
            message_text = (
                f"🎉 **Telegram Premium активирован!**\n\n"
                f"✅ Подписка успешно создана\n"
                f"📱 **Период:** {months} месяцев\n"
                f"👤 **Для аккаунта:** @{username}\n"
                f"💰 **Сумма:** ${invoice.amount_usd:.2f}\n"
                f"🆔 **ID заказа:** {order.id}\n\n"
                f"🎊 **Наслаждайтесь Premium возможностями!**\n\n"
                f"💡 **Что дальше:**\n"
                f"• Подписка активна в Telegram\n"
                f"• Все Premium функции доступны\n"
                f"• Срок действия: {months} месяцев"
            )
            
            try:
                # Try to send to user_id first, then try to get telegram_id from database
                chat_id = invoice.user_id
                
                # Check if we can send message to this user
                try:
                    await self.bot.send_chat_action(chat_id=chat_id, action="typing")
                except Exception:
                    # If user_id doesn't work, try to get telegram_id from database
                    logger.warning(f"Cannot send to user_id {chat_id}, trying to get telegram_id from database")
                    from bot.database.repository import get_connection
                    from bot.database.connection import get_connection as get_db_connection
                    
                    try:
                        pool = get_db_connection(config.database_url)
                        async with pool.acquire() as conn:
                            result = await conn.fetchrow(
                                "SELECT telegram_id FROM users WHERE id = $1",
                                invoice.user_id
                            )
                            if result and result['telegram_id']:
                                chat_id = result['telegram_id']
                                logger.info(f"Using telegram_id {chat_id} from database for user {invoice.user_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to get telegram_id from database: {db_error}")
                        return
                
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown"
                )
                logger.info(f"Subscription success notification sent to user {invoice.user_id} (chat_id: {chat_id})")
            except Exception as e:
                logger.error(f"Failed to send subscription success notification to user {invoice.user_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error in subscription success notification: {e}")
    
    async def _send_subscription_error_notification(self, invoice, error_info, months, username):
        """Send subscription error notification to user"""
        try:
            if not self.bot:
                logger.warning("Bot instance not available, cannot send notification")
                return
            
            message_text = (
                f"❌ **Ошибка активации Premium!**\n\n"
                f"💳 Платеж прошел успешно (${invoice.amount_usd:.2f})\n"
                f"📱 **Период:** {months} месяцев\n"
                f"👤 **Для аккаунта:** @{username}\n\n"
                f"🚨 **Проблема:** Не удалось активировать подписку\n\n"
                f"💡 **Что делать:**\n"
                f"• Обратитесь в поддержку\n"
                f"• Укажите ID счета: {invoice.invoice_id}\n"
                f"• Деньги будут возвращены"
            )
            
            try:
                # Get config for database connection
                config = self._get_config()
                chat_id = invoice.user_id
                
                # Check if we can send message to this user
                try:
                    await self.bot.send_chat_action(chat_id=chat_id, action="typing")
                except Exception:
                    # If user_id doesn't work, try to get telegram_id from database
                    logger.warning(f"Cannot send to user_id {chat_id}, trying to get telegram_id from database")
                    
                    try:
                        from bot.database.connection import get_connection as get_db_connection
                        pool = get_db_connection(config.database_url)
                        async with pool.acquire() as conn:
                            result = await conn.fetchrow(
                                "SELECT telegram_id FROM users WHERE id = $1",
                                invoice.user_id
                            )
                            if result and result['telegram_id']:
                                chat_id = result['telegram_id']
                                logger.info(f"Using telegram_id {chat_id} from database for user {invoice.user_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to get telegram_id from database: {db_error}")
                        return
                
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown"
                )
                logger.info(f"Subscription error notification sent to user {invoice.user_id} (chat_id: {chat_id})")
            except Exception as e:
                logger.error(f"Failed to send subscription error notification to user {invoice.user_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error in subscription error notification: {e}")
    
    async def _send_stars_success_notification(self, invoice, order, stars_count, username):
        """Send stars success notification to user"""
        try:
            if not self.bot:
                logger.warning("Bot instance not available, cannot send notification")
                return
            
            message_text = (
                f"🎉 **Telegram Stars отправлены!**\n\n"
                f"✅ Stars успешно отправлены\n"
                f"⭐ **Количество:** {stars_count} stars\n"
                f"👤 **Для аккаунта:** @{username}\n"
                f"💰 **Сумма:** ${invoice.amount_usd:.2f}\n"
                f"🆔 **ID заказа:** {order.id}\n\n"
                f"🎊 **Наслаждайтесь Stars!**\n\n"
                f"💡 **Что дальше:**\n"
                f"• Stars активны в Telegram\n"
                f"• Все Stars функции доступны\n"
                f"• Stars не имеют срока действия"
            )
            
            try:
                # Try to send to user_id first, then try to get telegram_id from database
                chat_id = invoice.user_id
                
                # Check if we can send message to this user
                try:
                    await self.bot.send_chat_action(chat_id=chat_id, action="typing")
                except Exception:
                    # If user_id doesn't work, try to get telegram_id from database
                    logger.warning(f"Cannot send to user_id {chat_id}, trying to get telegram_id from database")
                    
                    try:
                        from bot.database.connection import get_connection as get_db_connection
                        pool = get_db_connection(config.database_url)
                        async with pool.acquire() as conn:
                            result = await conn.fetchrow(
                                "SELECT telegram_id FROM users WHERE id = $1",
                                invoice.user_id
                            )
                            if result and result['telegram_id']:
                                chat_id = result['telegram_id']
                                logger.info(f"Using telegram_id {chat_id} from database for user {invoice.user_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to get telegram_id from database: {db_error}")
                        return
                
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown"
                )
                
                logger.info(f"Stars success notification sent to user {invoice.user_id}")
                
            except Exception as e:
                logger.error(f"Error sending stars success notification: {e}")
                
        except Exception as e:
            logger.error(f"Error sending stars success notification: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _send_stars_error_notification(self, invoice, error_info, stars_count, username):
        """Send stars error notification to user"""
        try:
            if not self.bot:
                logger.warning("Bot instance not available, cannot send notification")
                return
            
            error_message = "Неизвестная ошибка"
            if error_info and "message" in error_info:
                error_message = error_info["message"]
            
            message_text = (
                f"❌ **Ошибка при отправке Stars**\n\n"
                f"⚠️ Не удалось отправить Stars\n"
                f"⭐ **Количество:** {stars_count} stars\n"
                f"👤 **Для аккаунта:** @{username}\n"
                f"💰 **Сумма:** ${invoice.amount_usd:.2f}\n"
                f"🚫 **Ошибка:** {error_message}\n\n"
                f"💡 **Что делать:**\n"
                f"• Обратитесь в поддержку\n"
                f"• Укажите ID заказа\n"
                f"• Мы решим проблему"
            )
            
            try:
                # Try to send to user_id first, then try to get telegram_id from database
                chat_id = invoice.user_id
                
                # Check if we can send message to this user
                try:
                    await self.bot.send_chat_action(chat_id=chat_id, action="typing")
                except Exception:
                    # If user_id doesn't work, try to get telegram_id from database
                    logger.warning(f"Cannot send to user_id {chat_id}, trying to get telegram_id from database")
                    
                    try:
                        from bot.database.connection import get_connection as get_db_connection
                        pool = get_db_connection(config.database_url)
                        async with pool.acquire() as conn:
                            result = await conn.fetchrow(
                                "SELECT telegram_id FROM users WHERE id = $1",
                                invoice.user_id
                            )
                            if result and result['telegram_id']:
                                chat_id = result['telegram_id']
                                logger.info(f"Using telegram_id {chat_id} from database for user {invoice.user_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to get telegram_id from database: {db_error}")
                        return
                
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown"
                )
                
                logger.info(f"Stars error notification sent to user {invoice.user_id}")
                
            except Exception as e:
                logger.error(f"Error sending stars error notification: {e}")
                
        except Exception as e:
            logger.error(f"Error sending stars error notification: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _notify_admins_subscription_created(self, invoice, order, months, username):
        """Notify admins about successful subscription creation"""
        try:
            if not self.bot:
                return
            
            config = self._get_config()
            if not config.admin_ids:
                return
            
            admin_message = (
                f"🎉 **Новая Premium подписка активирована!**\n\n"
                f"👤 **Пользователь:** {invoice.user_id}\n"
                f"📱 **Период:** {months} месяцев\n"
                f"👤 **Для аккаунта:** @{username}\n"
                f"💰 **Сумма:** ${invoice.amount_usd:.2f}\n"
                f"🆔 **Fragment ID:** {order.id}\n"
                f"💳 **Счет:** {invoice.invoice_id}\n"
                f"⏰ **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            
            for admin_id in config.admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error notifying admins: {e}")
    
    async def _notify_admins_stars_created(self, invoice, order, stars_count, username):
        """Notify admins about successful stars creation"""
        try:
            if not self.bot:
                return
            
            config = self._get_config()
            if not config.admin_ids:
                return
            
            admin_message = (
                f"🎉 **Новые Stars отправлены!**\n\n"
                f"👤 **Пользователь:** {invoice.user_id}\n"
                f"⭐ **Количество:** {stars_count} stars\n"
                f"👤 **Для аккаунта:** @{username}\n"
                f"💰 **Сумма:** ${invoice.amount_usd:.2f}\n"
                f"🆔 **Fragment ID:** {order.id}\n"
                f"💳 **Счет:** {invoice.invoice_id}\n"
                f"⏰ **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            
            for admin_id in config.admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error notifying admins about stars: {e}")
    
    async def _send_payment_success_notification(self, invoice, amount_usd):
        """Send payment success notification to user"""
        try:
            if not self.bot:
                logger.warning("Bot instance not available, cannot send notification")
                return
            
            message_text = (
                f"✅ **Ваш баланс пополнен на ${amount_usd}!**\n\n"
                f"Теперь вы можете покупать Telegram Premium подписки.\n\n"
                f"💰 **Текущий баланс**: ${amount_usd}\n"
                f"📱 **Что дальше**: Выберите период подписки в главном меню"
            )
            
            try:
                # Get config for database connection
                config = self._get_config()
                chat_id = invoice.user_id
                
                # Check if we can send message to this user
                try:
                    await self.bot.send_chat_action(chat_id=chat_id, action="typing")
                except Exception:
                    # If user_id doesn't work, try to get telegram_id from database
                    logger.warning(f"Cannot send to user_id {chat_id}, trying to get telegram_id from database")
                    
                    try:
                        from bot.database.connection import get_connection as get_db_connection
                        pool = get_db_connection(config.database_url)
                        async with pool.acquire() as conn:
                            result = await conn.fetchrow(
                                "SELECT telegram_id FROM users WHERE id = $1",
                                invoice.user_id
                            )
                            if result and result['telegram_id']:
                                chat_id = result['telegram_id']
                                logger.info(f"Using telegram_id {chat_id} from database for user {invoice.user_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to get telegram_id from database: {db_error}")
                        return
                
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown"
                )
                logger.info(f"Payment success notification sent to user {invoice.user_id} (chat_id: {chat_id})")
            except Exception as e:
                logger.error(f"Failed to send payment success notification to user {invoice.user_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error in payment success notification: {e}")
    
    async def _send_expiration_notification(self, invoice):
        """Send expiration notification to user"""
        try:
            if not self.bot:
                logger.warning("Bot instance not available, cannot send notification")
                return
            
            message_text = (
                f"⏰ **Срок действия счета истек!**\n\n"
                f"Счет на пополнение баланса на **${invoice.amount_usd}** "
                f"больше не действителен.\n\n"
                f"💡 **Что делать**:\n"
                f"• Создайте новый счет для пополнения баланса\n"
                f"• Или выберите другую сумму\n\n"
                f"🔄 **Повторить пополнение**: /start → Профиль → 💰 Пополнить баланс"
            )
            
            try:
                # Get config for database connection
                config = self._get_config()
                chat_id = invoice.user_id
                
                # Check if we can send message to this user
                try:
                    await self.bot.send_chat_action(chat_id=chat_id, action="typing")
                except Exception:
                    # If user_id doesn't work, try to get telegram_id from database
                    logger.warning(f"Cannot send to user_id {chat_id}, trying to get telegram_id from database")
                    
                    try:
                        from bot.database.connection import get_connection as get_db_connection
                        pool = get_db_connection(config.database_url)
                        async with pool.acquire() as conn:
                            result = await conn.fetchrow(
                                "SELECT telegram_id FROM users WHERE id = $1",
                                invoice.user_id
                            )
                            if result and result['telegram_id']:
                                chat_id = result['telegram_id']
                                logger.info(f"Using telegram_id {chat_id} from database for user {invoice.user_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to get telegram_id from database: {db_error}")
                        return
                
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown"
                )
                logger.info(f"Expiration notification sent to user {invoice.user_id} (chat_id: {chat_id})")
            except Exception as e:
                logger.error(f"Failed to send expiration notification to user {invoice.user_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error in expiration notification: {e}")
    
    async def force_check_invoice(self, invoice_id: str) -> bool:
        """Force check specific invoice (for manual checks)"""
        try:
            config = self._get_config()
            if not config.crypto_pay_token:
                return False
            
            pool = await get_connection(config.database_url)
            invoice_repo = CryptoPayInvoiceRepository(pool)
            balance_repo = UserBalanceRepository(pool)
            
            invoice = await invoice_repo.get_invoice_by_id(invoice_id)
            if not invoice:
                return False
            
            crypto_api = CryptoPayAPI(config.crypto_pay_token, config.crypto_pay_testnet)
            
            await self._check_single_invoice(invoice, crypto_api, invoice_repo, balance_repo)
            return True
            
        except Exception as e:
            logger.error(f"Error in force_check_invoice: {e}")
            return False


# Global background task manager instance
background_manager = BackgroundTaskManager()


async def start_background_tasks(bot=None):
    """Start background tasks"""
    if bot:
        background_manager.set_bot(bot)
    await background_manager.start()


async def stop_background_tasks():
    """Stop background tasks"""
    await background_manager.stop()


async def force_check_invoice(invoice_id: str) -> bool:
    """Force check specific invoice"""
    return await background_manager.force_check_invoice(invoice_id) 