#!/usr/bin/env python3
"""
Database initialization script for CosmicPerks bot
Creates tables and adds sample data
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database import create_tables, CategoryRepository, SubcategoryRepository, ProductRepository
from bot.config import Config


async def init_database():
    """Initialize database with sample data"""
    print("🚀 Initializing CosmicPerks database...")
    
    # Create tables
    await create_tables()
    print("✅ Database tables created")
    
    config = Config()
    category_repo = CategoryRepository(config.database_url)
    subcategory_repo = SubcategoryRepository(config.database_url)
    product_repo = ProductRepository(config.database_url)
    
    # Create sample categories
    print("📂 Creating sample categories...")
    
    categories = [
        {
            "name": "Игровые товары",
            "name_en": "Gaming Products",
            "description": "Аккаунты, скины, внутриигровая валюта",
            "description_en": "Accounts, skins, in-game currency",
            "icon": "🎮"
        },
        {
            "name": "Цифровые товары",
            "name_en": "Digital Products", 
            "description": "Подписки, программы, ключи",
            "description_en": "Subscriptions, software, keys",
            "icon": "💎"
        },
        {
            "name": "Подарки",
            "name_en": "Gifts",
            "description": "Подарочные карты, сертификаты",
            "description_en": "Gift cards, certificates",
            "icon": "🎁"
        },
        {
            "name": "Услуги",
            "name_en": "Services",
            "description": "Настройка, консультации, поддержка",
            "description_en": "Setup, consultations, support",
            "icon": "🔧"
        }
    ]
    
    created_categories = []
    for cat_data in categories:
        category = await category_repo.create_category(**cat_data)
        created_categories.append(category)
        print(f"✅ Created category: {category.name}")
    
    # Create sample subcategories
    print("📂 Creating sample subcategories...")
    
    subcategories_data = [
        # Gaming subcategories
        {
            "category_id": created_categories[0].id,
            "name": "Steam аккаунты",
            "name_en": "Steam Accounts",
            "description": "Аккаунты Steam с играми",
            "description_en": "Steam accounts with games",
            "icon": "🎮"
        },
        {
            "category_id": created_categories[0].id,
            "name": "CS2 скины",
            "name_en": "CS2 Skins",
            "description": "Редкие скины для CS2",
            "description_en": "Rare skins for CS2",
            "icon": "🎯"
        },
        {
            "category_id": created_categories[0].id,
            "name": "Dota 2 предметы",
            "name_en": "Dota 2 Items",
            "description": "Эксклюзивные предметы Dota 2",
            "description_en": "Exclusive Dota 2 items",
            "icon": "🏆"
        },
        
        # Digital subcategories
        {
            "category_id": created_categories[1].id,
            "name": "Подписки",
            "name_en": "Subscriptions",
            "description": "Netflix, Spotify, YouTube Premium",
            "description_en": "Netflix, Spotify, YouTube Premium",
            "icon": "📺"
        },
        {
            "category_id": created_categories[1].id,
            "name": "Программы",
            "name_en": "Software",
            "description": "Лицензионное ПО",
            "description_en": "Licensed software",
            "icon": "💻"
        },
        {
            "category_id": created_categories[1].id,
            "name": "Ключи активации",
            "name_en": "Activation Keys",
            "description": "Ключи для игр и программ",
            "description_en": "Keys for games and software",
            "icon": "🔑"
        },
        
        # Gifts subcategories
        {
            "category_id": created_categories[2].id,
            "name": "Steam карты",
            "name_en": "Steam Cards",
            "description": "Подарочные карты Steam",
            "description_en": "Steam gift cards",
            "icon": "🎁"
        },
        {
            "category_id": created_categories[2].id,
            "name": "iTunes карты",
            "name_en": "iTunes Cards",
            "description": "Подарочные карты iTunes",
            "description_en": "iTunes gift cards",
            "icon": "💳"
        },
        {
            "category_id": created_categories[2].id,
            "name": "PlayStation карты",
            "name_en": "PlayStation Cards",
            "description": "Подарочные карты PlayStation",
            "description_en": "PlayStation gift cards",
            "icon": "🎪"
        },
        
        # Services subcategories
        {
            "category_id": created_categories[3].id,
            "name": "Настройка ПК",
            "name_en": "PC Setup",
            "description": "Оптимизация и настройка компьютеров",
            "description_en": "PC optimization and setup",
            "icon": "🔧"
        },
        {
            "category_id": created_categories[3].id,
            "name": "Дизайн",
            "name_en": "Design",
            "description": "Создание логотипов и брендинга",
            "description_en": "Logo and branding design",
            "icon": "🎨"
        },
        {
            "category_id": created_categories[3].id,
            "name": "Разработка",
            "name_en": "Development",
            "description": "Создание сайтов и приложений",
            "description_en": "Website and app development",
            "icon": "📱"
        }
    ]
    
    created_subcategories = []
    for subcat_data in subcategories_data:
        subcategory = await subcategory_repo.create_subcategory(**subcat_data)
        created_subcategories.append(subcategory)
        print(f"✅ Created subcategory: {subcategory.name}")
    
    # Create sample products
    print("📦 Creating sample products...")
    
    products_data = [
        # Gaming products
        {
            "category_id": created_categories[0].id,
            "subcategory_id": created_subcategories[0].id,  # Steam accounts
            "name": "Steam аккаунт с играми",
            "name_en": "Steam Account with Games",
            "description": "Аккаунт Steam с коллекцией популярных игр. Включает CS2, Dota 2, GTA V и другие игры.",
            "description_en": "Steam account with popular games collection. Includes CS2, Dota 2, GTA V and other games.",
            "price": 50.0
        },
        {
            "category_id": created_categories[0].id,
            "subcategory_id": created_subcategories[1].id,  # CS2 skins
            "name": "CS2 скин AWP Dragon Lore",
            "name_en": "CS2 AWP Dragon Lore Skin",
            "description": "Редкий скин AWP Dragon Lore для CS2. Один из самых дорогих скинов в игре.",
            "description_en": "Rare AWP Dragon Lore skin for CS2. One of the most expensive skins in the game.",
            "price": 1500.0
        },
        {
            "category_id": created_categories[0].id,
            "subcategory_id": created_subcategories[2].id,  # Dota 2 items
            "name": "Dota 2 Arcana набор",
            "name_en": "Dota 2 Arcana Set",
            "description": "Полный набор Arcana предметов для Dota 2. Включает все популярные Arcana скины.",
            "description_en": "Complete Arcana set for Dota 2. Includes all popular Arcana skins.",
            "price": 300.0
        },
        
        # Digital products
        {
            "category_id": created_categories[1].id,
            "subcategory_id": created_subcategories[3].id,  # Subscriptions
            "name": "Netflix Premium 1 месяц",
            "name_en": "Netflix Premium 1 Month",
            "description": "Подписка Netflix Premium на 1 месяц. 4K качество, 4 экрана одновременно.",
            "description_en": "Netflix Premium subscription for 1 month. 4K quality, 4 screens simultaneously.",
            "price": 15.0
        },
        {
            "category_id": created_categories[1].id,
            "subcategory_id": created_subcategories[3].id,  # Subscriptions
            "name": "Spotify Premium 3 месяца",
            "name_en": "Spotify Premium 3 Months",
            "description": "Подписка Spotify Premium на 3 месяца. Без рекламы, высокое качество звука.",
            "description_en": "Spotify Premium subscription for 3 months. No ads, high quality audio.",
            "price": 30.0
        },
        {
            "category_id": created_categories[1].id,
            "subcategory_id": created_subcategories[4].id,  # Software
            "name": "Adobe Creative Suite",
            "name_en": "Adobe Creative Suite",
            "description": "Полный пакет Adobe Creative Suite. Photoshop, Illustrator, Premiere Pro и другие.",
            "description_en": "Complete Adobe Creative Suite package. Photoshop, Illustrator, Premiere Pro and more.",
            "price": 500.0
        },
        
        # Gift cards
        {
            "category_id": created_categories[2].id,
            "subcategory_id": created_subcategories[6].id,  # Steam cards
            "name": "Steam карта $50",
            "name_en": "Steam Card $50",
            "description": "Подарочная карта Steam на $50. Можно использовать для покупки игр и внутриигровых предметов.",
            "description_en": "Steam gift card for $50. Can be used to buy games and in-game items.",
            "price": 50.0
        },
        {
            "category_id": created_categories[2].id,
            "subcategory_id": created_subcategories[7].id,  # iTunes cards
            "name": "iTunes карта $25",
            "name_en": "iTunes Card $25",
            "description": "Подарочная карта iTunes на $25. Для покупки музыки, фильмов и приложений.",
            "description_en": "iTunes gift card for $25. For buying music, movies and apps.",
            "price": 25.0
        },
        {
            "category_id": created_categories[2].id,
            "subcategory_id": created_subcategories[8].id,  # PlayStation cards
            "name": "PlayStation карта $100",
            "name_en": "PlayStation Card $100",
            "description": "Подарочная карта PlayStation на $100. Для покупки игр в PlayStation Store.",
            "description_en": "PlayStation gift card for $100. For buying games in PlayStation Store.",
            "price": 100.0
        },
        
        # Services
        {
            "category_id": created_categories[3].id,
            "subcategory_id": created_subcategories[9].id,  # PC Setup
            "name": "Настройка и оптимизация ПК",
            "name_en": "PC Setup and Optimization",
            "description": "Профессиональная настройка и оптимизация компьютера. Установка ОС, драйверов, программ.",
            "description_en": "Professional PC setup and optimization. OS installation, drivers, software setup.",
            "price": 100.0
        },
        {
            "category_id": created_categories[3].id,
            "subcategory_id": created_subcategories[10].id,  # Design
            "name": "Дизайн логотипа",
            "name_en": "Logo Design",
            "description": "Создание уникального логотипа для вашего бренда. Включает несколько вариантов и правки.",
            "description_en": "Creating unique logo for your brand. Includes multiple options and revisions.",
            "price": 200.0
        },
        {
            "category_id": created_categories[3].id,
            "subcategory_id": created_subcategories[11].id,  # Development
            "name": "Telegram бот разработка",
            "name_en": "Telegram Bot Development",
            "description": "Разработка и настройка Telegram бота под ваши требования. Полный цикл разработки.",
            "description_en": "Telegram bot development and setup according to your requirements. Full development cycle.",
            "price": 500.0
        }
    ]
    
    for product_data in products_data:
        product = await product_repo.create_product(**product_data)
        print(f"✅ Created product: {product.name} - ${product.price}")
    
    print("\n🎉 Database initialization completed successfully!")
    print("📊 Summary:")
    print(f"   📂 Categories: {len(created_categories)}")
    print(f"   📂 Subcategories: {len(created_subcategories)}")
    print(f"   📦 Products: {len(products_data)}")
    print("\n🚀 You can now start the bot with: python main.py")


if __name__ == "__main__":
    asyncio.run(init_database()) 