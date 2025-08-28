from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User model"""
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True
    language: str = "ru"


@dataclass
class Chat:
    """Chat model"""
    id: int
    telegram_id: int
    chat_type: str  # 'private', 'group', 'supergroup', 'channel'
    title: Optional[str] = None
    username: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True


@dataclass
class Message:
    """Message model"""
    id: int
    telegram_id: int
    user_id: int
    chat_id: int
    message_type: str  # 'text', 'photo', 'document', etc.
    text: Optional[str] = None
    created_at: datetime = None


@dataclass
class PremiumPricing:
    """Telegram Premium pricing model"""
    id: int
    months: int  # 3, 9, 12 months
    price_usd: float
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class UserBalance:
    """User balance model"""
    id: int
    user_id: int
    balance_usd: float = 0.0
    balance_usdt: float = 0.0
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class CryptoPayInvoice:
    """Crypto Pay invoice model"""
    id: int
    invoice_id: str
    user_id: int
    amount_usd: float
    amount_crypto: float
    asset: str
    status: str = "pending"
    crypto_pay_url: Optional[str] = None
    payload: Optional[str] = None  # Additional data for subscription payments
    created_at: datetime = None
    updated_at: datetime = None
    paid_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None 