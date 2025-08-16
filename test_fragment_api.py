#!/usr/bin/env python3
"""
Test script for Fragment API authentication
"""

import os
import asyncio
import sys
sys.path.append('.')

# Load environment variables directly
from dotenv import load_dotenv
load_dotenv()

from bot.fragment_api import FragmentAPI

async def test_fragment_api():
    """Test Fragment API connection and authentication"""
    print("🔍 Testing Fragment API Authentication...")
    
    # Get token directly from environment
    token = os.getenv("TOKEN_FRAGMENT")
    if not token:
        print("❌ No Fragment API token found in environment")
        print("💡 Set TOKEN_FRAGMENT environment variable")
        return
    
    print(f"✅ Token loaded successfully")
    print(f"📝 Token length: {len(token)}")
    print(f"🔑 Token preview: {token[:20]}...")
    
    # Test the correct authentication method
    print(f"\n🧪 Testing Fragment API with JWT Authorization header")
    
    # Create API instance
    api = FragmentAPI(token=token, demo_mode=False)
    
    print(f"📤 Headers: {api.headers}")
    print(f"🔑 JWT Token: {token[:20]}...")
    
    # Test connection (which now uses the Authorization header)
    try:
        print("🔗 Testing API connection...")
        connection_ok = await api.test_connection()
        if connection_ok:
            print(f"✅ Connection successful!")
            
            # Try to create a test order
            print("📝 Testing order creation...")
            order, error_info = await api.create_premium_order("test_user", 3, show_sender=False)
            if order:
                print(f"✅ Order created successfully: {order.id}")
            else:
                print("❌ Order creation failed")
                if error_info:
                    # Check if it's a wallet balance error
                    if api.is_wallet_balance_error(error_info):
                        print("💰 Wallet balance error detected!")
                        print("💡 This means the Fragment API wallet needs funding")
                    else:
                        error_message = api.get_error_message(error_info, "en")
                        print(f"🔍 Error details: {error_message}")
        else:
            print("❌ Connection failed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🔍 Authentication test completed")

if __name__ == "__main__":
    asyncio.run(test_fragment_api()) 