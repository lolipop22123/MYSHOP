import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CryptoPayAPI:
    """Crypto Bot Crypto Pay API integration for USDT payments"""
    
    def __init__(self, api_token: str, testnet: bool = False):
        self.api_token = api_token
        self.base_url = "https://testnet-pay.crypt.bot/api" if testnet else "https://pay.crypt.bot/api"
        self.headers = {
            "Crypto-Pay-API-Token": api_token
        }
    
    async def get_me(self) -> Optional[Dict[str, Any]]:
        """Test API authentication"""
        try:
            response = requests.get(f"{self.base_url}/getMe", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result")
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error in getMe: {e}")
            return None
    
    async def create_invoice(self, amount: float, asset: str = "USDT", 
                           currency_type: str = "crypto", fiat: str = "USD",
                           description: str = "", payload: str = "") -> Optional[Dict[str, Any]]:
        """Create payment invoice"""
        try:
            payload_data = {
                "amount": str(amount),
                "asset": asset,
                "currency_type": currency_type,
                "description": description,
                "payload": payload,
                "expires_in": 3600  # 1 hour
            }
            
            if currency_type == "fiat":
                payload_data["fiat"] = fiat
                payload_data["accepted_assets"] = "USDT,TON,BTC,ETH"
            
            logger.info(f"Creating invoice with payload: {payload_data}")
            response = requests.post(f"{self.base_url}/createInvoice", 
                                  headers=self.headers, json=payload_data)
            
            logger.info(f"Create invoice response status: {response.status_code}")
            logger.info(f"Create invoice response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Create invoice response data: {data}")
                
                if data.get("ok") and data.get("result"):
                    result = data.get("result")
                    logger.info(f"Invoice created successfully: {result}")
                    return result
                else:
                    logger.error(f"API returned error: {data}")
            
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error in create_invoice: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice status"""
        try:
            logger.info(f"Getting invoice status for ID: {invoice_id}")
            response = requests.get(f"{self.base_url}/getInvoices", 
                                 headers=self.headers, params={"invoice_ids": invoice_id})
            
            logger.info(f"API response status: {response.status_code}")
            logger.info(f"API response headers: {dict(response.headers)}")
            logger.info(f"API response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response data: {data}")
                
                if data.get("ok") and data.get("result"):
                    result = data.get("result")
                    
                    # Check if result has items array
                    if "items" in result and result["items"]:
                        invoices = result["items"]
                        if invoices:
                            logger.info(f"Found invoice: {invoices[0]}")
                            return invoices[0]
                        else:
                            logger.warning("No invoices found in items array")
                    # Fallback for direct result array (old format)
                    elif isinstance(result, list) and result:
                        logger.info(f"Found invoice in direct result: {result[0]}")
                        return result[0]
                    else:
                        logger.warning("No invoices found in response")
                else:
                    logger.error(f"API returned error: {data}")
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error in get_invoice: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        return None
    
    async def get_exchange_rates(self) -> Optional[Dict[str, Any]]:
        """Get current exchange rates"""
        try:
            response = requests.get(f"{self.base_url}/getExchangeRates", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result")
            
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error in get_exchange_rates: {e}")
            return None
    
    def get_payment_url(self, invoice_data: Dict[str, Any]) -> Optional[str]:
        """Get payment URL from invoice data"""
        if invoice_data:
            return invoice_data.get("bot_invoice_url") or invoice_data.get("pay_url")
        return None 