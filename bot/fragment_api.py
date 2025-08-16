import requests
import json
import logging
import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FragmentProduct:
    """Fragment product model"""
    id: str
    name: str
    description: str
    price: float
    currency: str
    months: int
    is_active: bool

@dataclass
class FragmentOrder:
    """Fragment order model"""
    id: str
    username: str
    months: int
    status: str
    price: float
    currency: str
    created_at: str
    completed_at: Optional[str] = None
    show_sender: bool = False

class FragmentAPI:
    """Fragment API client with JWT token authentication"""
    
    def __init__(self, token: str = "", base_url: str = "https://api.fragment-api.com/v1", demo_mode: bool = False):
        self.token = token.strip() if token else ""
        self.base_url = base_url
        self.demo_mode = demo_mode  # Don't auto-switch to demo mode
        
        logger.info(f"FragmentAPI initialized: token={bool(self.token)}, demo_mode={self.demo_mode}")
        
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add JWT authorization header if token is provided
        if self.token:
            self.headers["Authorization"] = f"JWT {self.token}"
        
        logger.info(f"Headers set: {self.headers}")
        logger.info(f"Authorization header: JWT {self.token[:20] if self.token else 'None'}...")
        
        # Demo products
        self.demo_products = [
            FragmentProduct(
                id="premium_3m",
                name="Telegram Premium 3 месяца",
                description="Премиум подписка на 3 месяца",
                price=12.99,
                currency="USD",
                months=3,
                is_active=True
            ),
            FragmentProduct(
                id="premium_9m",
                name="Telegram Premium 9 месяцев",
                description="Премиум подписка на 9 месяцев",
                price=29.99,
                currency="USD",
                months=9,
                is_active=True
            ),
            FragmentProduct(
                id="premium_12m",
                name="Telegram Premium 12 месяцев",
                description="Премиум подписка на 12 месяцев",
                price=39.99,
                currency="USD",
                months=12,
                is_active=True
            )
        ]
    
    def _get_price_for_months(self, months: int) -> float:
        """Get price for given number of months from database or fallback to default"""
        try:
            # Try to get price from database
            import asyncio
            from bot.database.connection import get_connection
            from bot.database.repository import PremiumPricingRepository
            from bot.config import Config
            
            config = Config()
            
            # Create event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Get price from database
            async def get_db_price():
                try:
                    pool = await get_connection(config.database_url)
                    pricing_repo = PremiumPricingRepository(pool)
                    pricing = await pricing_repo.get_pricing_by_months(months)
                    if pricing and pricing.is_active:
                        return pricing.price_usd
                except Exception as e:
                    logger.error(f"Error getting price from database: {e}")
                return None
            
            # Run async function
            if loop.is_running():
                # If loop is running, schedule the coroutine
                future = asyncio.create_task(get_db_price())
                # Wait for result (this might not work in all contexts)
                try:
                    price = loop.run_until_complete(future)
                    if price is not None:
                        return price
                except:
                    pass
            else:
                # If no loop is running, run the coroutine
                price = loop.run_until_complete(get_db_price())
                if price is not None:
                    return price
            
        except Exception as e:
            logger.error(f"Error in _get_price_for_months: {e}")
        
        # Fallback to default prices
        if months == 3:
            return 12.99
        elif months == 9:
            return 29.99
        elif months == 12:
            return 39.99
        else:
            return 12.99  # Default to 3 months price

    async def test_authentication(self) -> bool:
        """Test API authentication using the auth endpoint"""
        if self.demo_mode:
            logger.info("Demo mode: Authentication test passed")
            return True
        
        try:
            logger.info("Testing API authentication using auth endpoint...")
            
            # Use the authentication endpoint
            auth_url = f"{self.base_url}/auth/authenticate/"
            
            # For authentication test, we need to provide required fields
            # Based on test.py, it seems to require phone_number and mnemonics
            # But for API key validation, we might just need the api_key
            payload = {
                "api_key": self.token
            }
            
            response = requests.post(auth_url, headers=self.headers, json=payload)
            
            logger.info(f"Authentication test response status: {response.status_code}")
            logger.info(f"Authentication test response: {response.text}")
            
            if response.status_code == 200:
                logger.info("API authentication test successful")
                return True
            elif response.status_code in [401, 403]:
                logger.error("API authentication test failed: Invalid API key")
                return False
            else:
                logger.warning(f"Authentication test returned unexpected status: {response.status_code}")
                # If the endpoint requires additional fields, we might get a different error
                # but the API key format might still be correct
                return True
                
        except Exception as e:
            logger.error(f"Error testing API authentication: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test API connection and authentication"""
        if self.demo_mode:
            logger.info("Demo mode: Connection test passed")
            return True
        
        try:
            # Try a simple GET request to test authentication
            logger.info("Testing API connection and authentication...")
            
            # For Fragment API, we need to test with an endpoint that accepts authentication
            # Let's try the orders endpoint which should require authentication
            test_url = f"{self.base_url}/orders"
            
            response = requests.get(test_url, headers=self.headers)
            
            logger.info(f"Connection test response status: {response.status_code}")
            logger.info(f"Connection test response: {response.text}")
            
            if response.status_code == 200:
                logger.info("API connection test successful")
                return True
            elif response.status_code in [401, 403]:
                logger.error("API connection test failed: Authentication error")
                return False
            else:
                logger.warning(f"API connection test returned unexpected status: {response.status_code}")
                return True  # Might still work for specific endpoints
                
        except Exception as e:
            logger.error(f"Error testing API connection: {e}")
            return False

    async def create_premium_order(self, username: str, months: int, show_sender: bool = False) -> tuple[Optional[FragmentOrder], Optional[dict]]:
        """Create a new premium order using the simple token. Returns (order, error_info)"""
        logger.info(f"Creating premium order: username={username}, months={months}, demo_mode={self.demo_mode}")
        
        if self.demo_mode:
            logger.info("Demo mode: Creating demo premium order")
            
            # Calculate demo price based on months
            price = self._get_price_for_months(months)
            
            # Create demo order
            order = FragmentOrder(
                id=f"demo_premium_order_{username}_{datetime.datetime.now().timestamp()}",
                username=username,
                months=months,
                status="pending",
                price=price,
                currency="USD",
                created_at=datetime.datetime.now().isoformat(),
                show_sender=show_sender
            )
            
            logger.info(f"Demo order created: {order}")
            return order, None
        
        # Real API mode with token
        try:
            payload = {
                "username": username,
                "months": int(months),  # Ensure months is an integer
                "show_sender": show_sender
            }
            
            logger.info(f"Sending request to {self.base_url}/order/premium/ with payload: {payload}")
            logger.info(f"Using headers: {self.headers}")
            
            response = requests.post(
                f"{self.base_url}/order/premium/", 
                headers=self.headers,
                json=payload
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response: {data}")
                
                order = FragmentOrder(
                    id=data.get("id", f"order_{username}_{months}m"),
                    username=data.get("username", username),
                    months=data.get("months", months),
                    status=data.get("status", "pending"),
                    price=float(data.get("price", self._get_price_for_months(months))),
                    currency=data.get("currency", "USD"),
                    created_at=data.get("created_at", datetime.datetime.now().isoformat()),
                    show_sender=data.get("show_sender", show_sender)
                )
                
                logger.info(f"Real order created: {order}")
                return order, None
            else:
                # Handle different error codes
                error_info = self._parse_error_response(response)
                logger.error(f"API error: {response.status_code} - {error_info}")
                return None, error_info
            
        except Exception as e:
            logger.error(f"Error creating premium order: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            error_info = {
                "type": "exception",
                "code": "exception",
                "message": str(e),
                "raw_response": str(e)
            }
            return None, error_info
    
    def _parse_error_response(self, response) -> dict:
        """Parse error response from Fragment API and return structured error info"""
        try:
            error_data = response.json()
            logger.info(f"Error response data: {error_data}")
            
            # Handle different error response formats
            if "errors" in error_data and isinstance(error_data["errors"], list):
                # Multiple errors format
                errors = []
                for error in error_data["errors"]:
                    error_info = {
                        "code": error.get("code", "unknown"),
                        "message": error.get("error", "Unknown error"),
                        "details": error.get("details", "")
                    }
                    errors.append(error_info)
                
                return {
                    "type": "multiple_errors",
                    "errors": errors,
                    "raw_response": error_data
                }
            elif "detail" in error_data:
                # Single error format
                return {
                    "type": "single_error",
                    "code": "unknown",
                    "message": error_data["detail"],
                    "raw_response": error_data
                }
            else:
                # Unknown error format
                return {
                    "type": "unknown",
                    "code": "unknown",
                    "message": str(error_data),
                    "raw_response": error_data
                }
                
        except Exception as e:
            logger.error(f"Error parsing error response: {e}")
            return {
                "type": "parse_error",
                "code": "unknown",
                "message": response.text,
                "raw_response": response.text
            }
    
    def get_error_message(self, error_info: dict, language: str = "ru") -> str:
        """Get user-friendly error message based on error code and language"""
        if error_info["type"] == "multiple_errors":
            # Handle multiple errors
            messages = []
            for error in error_info["errors"]:
                message = self._get_single_error_message(error, language)
                messages.append(message)
            return "\n".join(messages)
        else:
            # Handle single error
            return self._get_single_error_message(error_info, language)
    
    def _get_single_error_message(self, error: dict, language: str) -> str:
        """Get user-friendly message for a single error"""
        code = error.get("code", "unknown")
        message = error.get("message", "")
        
        # Check for insufficient funds error (code 0 with specific message)
        if code == "0" and self._is_insufficient_funds_error(message):
            if language == "ru":
                return "Недостаточно средств в кошельке Fragment API"
            else:
                return "Insufficient funds in Fragment API wallet"
        
        if language == "ru":
            error_messages = {
                "0": "Общая ошибка системы",
                "10": "Ошибка сети TON",
                "11": "Требуется KYC для указанного аккаунта",
                "12": "Ошибка подключения к сети TON",
                "13": "Общая ошибка TON/Telegram",
                "20": "Пользователь не найден на Fragment",
                "unknown": "Неизвестная ошибка"
            }
        else:
            error_messages = {
                "0": "General system error",
                "10": "TON Network error",
                "11": "KYC is needed for specified account",
                "12": "TON Network connection error",
                "13": "General TON/Telegram error",
                "20": "Recipient username was not found on Fragment",
                "unknown": "Unknown error"
            }
        
        # Get base message
        base_message = error_messages.get(str(code), error_messages["unknown"])
        
        # Add specific details if available
        if message and message != base_message:
            if language == "ru":
                return f"{base_message}: {message}"
            else:
                return f"{base_message}: {message}"
        
        return base_message
    
    def _is_insufficient_funds_error(self, message: str) -> bool:
        """Check if the error message indicates insufficient funds"""
        message_lower = message.lower()
        
        # Check for the exact error message you're getting
        if "not enough funds for wallet" in message_lower and "balance: '0 ton'" in message_lower:
            return True
        
        insufficient_indicators = [
            "not enough funds",
            "insufficient funds",
            "balance: '0 ton",
            "balance: 0 ton",
            "transaction total:",
            "wallet",
            "insufficient",
            "balance"
        ]
        
        # Check for specific patterns
        if "balance: '0 ton" in message_lower or "balance: 0 ton" in message_lower:
            return True
        
        if "transaction total:" in message_lower and "balance:" in message_lower:
            return True
        
        # Check for general indicators
        return any(indicator in message_lower for indicator in insufficient_indicators)
    
    def is_wallet_balance_error(self, error_info: dict) -> bool:
        """Check if the error is related to wallet balance"""
        if error_info["type"] == "multiple_errors":
            return any(self._is_insufficient_funds_error(error.get("error", "")) 
                      for error in error_info["errors"])
        else:
            return self._is_insufficient_funds_error(error_info.get("message", ""))
    
    async def get_order_status(self, order_id: str) -> Optional[str]:
        """Get order status"""
        if self.demo_mode:
            return "pending"
        
        try:
            response = requests.get(f"{self.base_url}/orders/{order_id}", headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("status")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching order status: {e}")
            return None
    
    async def get_user_orders(self, user_id: int) -> List[FragmentOrder]:
        """Get user orders"""
        if self.demo_mode:
            return []
        
        try:
            response = requests.get(f"{self.base_url}/users/{user_id}/orders", headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            orders = []
            
            for order_data in data.get("orders", []):
                order = FragmentOrder(
                    id=order_data["id"],
                    username=order_data.get("username", ""),
                    months=order_data.get("months", 1),
                    status=order_data["status"],
                    price=float(order_data["price"]),
                    currency=order_data["currency"],
                    created_at=order_data["created_at"],
                    completed_at=order_data.get("completed_at"),
                    show_sender=order_data.get("show_sender", False)
                )
                orders.append(order)
            
            return orders
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user orders: {e}")
            return []
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if self.demo_mode:
            return True
        
        try:
            response = requests.delete(f"{self.base_url}/orders/{order_id}", headers=self.headers)
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error canceling order: {e}")
            return False 