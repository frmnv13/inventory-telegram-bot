# /telegram-stock-bot/bot.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN, ADMIN_USER_IDS
import db

# --- Basic Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def format_product(product):
    """Formats a product dictionary into a readable string."""
    return (
        f"📦 *Name:* {product['name'].title()}\n"
        f"🔢 *Code:* `{product['code']}`\n"
        f"💲 *Price:* Rp {product['price']:,}\n"
        f"📊 *Stock:* {product['stock']} units"
    )

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! Welcome to the Inventory Bot.\n\n"
        "You can search for items by typing any keyword.\n"
        "Use /help to see all available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with all available commands."""
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot\n"
        "/list - Show a paginated list of all products\n"
        "/find `<keyword>` - Find products by name or code\n"
        "/stock `<code>` - Check stock for a specific product code\n"
        "/buy `<code>` `<quantity>` - Purchase an item\n"
        "/addstock `<code>` `<quantity>` - (Admin) Add stock for an item\n"
        "/help - Show this help message\n\n"
        "You can also just type any text to perform a quick search."
    )
    await update.message.reply_text(help_text)

async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /find command to search for products."""
    if not context.args:
        await update.message.reply_text("Please provide a keyword to search. Usage: /find <keyword>")
        return
    
    keyword = " ".join(context.args)
    await perform_search(update, keyword)

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks the stock for a specific product code."""
    if not context.args:
        await update.message.reply_text("Please provide a product code. Usage: /stock <code>")
        return
    
    code = context.args[0].upper()
    product = db.get_product_by_code(code)
    
    if product:
        response = (
            f"Stock information for `{product['code']}`:\n"
            f"📊 *Stock:* {product['stock']} units"
        )
        await update.message.reply_markdown(response)
    else:
        await update.message.reply_text(f"Product with code '{code}' not found.")

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /buy command to purchase an item and deduct stock."""
    if len(context.args) != 2:
        await update.message.reply_text("Invalid format. Usage: /buy <code> <quantity>")
        return

    code = context.args[0].upper()
    try:
        quantity = int(context.args[1])
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Quantity must be a positive number.")
        return

    success, result = db.update_stock(code, quantity)

    if success:
        product = result
        response = (
            f"✅ *Purchase Successful!*\n\n"
            f"Item: {product['name'].title()}\n"
            f"Qty: {quantity}\n"
            f"Remaining stock: {product['stock']}"
        )
        logger.info(f"Purchase: User {update.effective_user.id} bought {quantity} of {code}. New stock: {product['stock']}")
    else:
        # 'result' contains the error message from db.py
        response = f"⚠️ *Purchase Failed:*\n{result}"
        
    await update.message.reply_markdown(response)

async def add_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """(Admin) Adds stock for a specific product."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("🚫 Sorry, this command is for admins only.")
        logger.warning(f"Unauthorized /addstock attempt by user {user_id}.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Invalid format. Usage: /addstock <code> <quantity>")
        return

    code = context.args[0].upper()
    try:
        quantity = int(context.args[1])
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Quantity must be a positive number.")
        return

    success, result = db.add_stock(code, quantity)

    if success:
        product = result
        response = (
            f"✅ *Stock Added Successfully!*\n\n"
            f"Item: {product['name'].title()}\n"
            f"Added: {quantity}\n"
            f"New stock total: {product['stock']}"
        )
        logger.info(f"Restock: Admin {user_id} added {quantity} to {code}. New stock: {product['stock']}")
    else:
        response = f"⚠️ *Failed to add stock:*\n{result}"

    await update.message.reply_markdown(response)

# --- Free Text Search ---
async def free_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles non-command messages to perform a search."""
    keyword = update.message.text
    await perform_search(update, keyword)

async def perform_search(update: Update, keyword: str):
    """Shared logic for searching and replying."""
    results = db.search_products(keyword)
    
    if not results:
        await update.message.reply_text("Item not found.")
        return

    response = "🔍 *Found items matching your search:*\n\n"
    for product in results:
        response += format_product(product) + "\n\n"
        
    await update.message.reply_markdown(response.strip())

# --- Pagination for /list ---
ITEMS_PER_PAGE = 5

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the first page of the product list."""
    await send_paginated_list(update.message, context, page=0)

async def list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button clicks for paginated list."""
    query = update.callback_query
    await query.answer()
    page = int(query.data.split('_')[1])
    await send_paginated_list(query.message, context, page=page, is_edit=True)

async def send_paginated_list(message, context, page=0, is_edit=False):
    """Sends a paginated list of products."""
    products = db.get_all_products()
    if not products:
        await message.reply_text("No products found in the inventory.")
        return

    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    paginated_products = products[start_index:end_index]

    if not paginated_products:
        await message.reply_text("You've reached the end of the list.")
        return

    text = "📋 *Full Product List*\n\n"
    for p in paginated_products:
        text += format_product(p) + "\n\n"
    
    # --- Keyboard Buttons ---
    keyboard = []
    row = []
    if page > 0:
        row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"list_{page-1}"))
    if end_index < len(products):
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"list_{page+1}"))
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_edit:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await message.reply_markdown(text, reply_markup=reply_markup)

# --- Main Application ---
def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("find", find_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("addstock", add_stock_command))
    application.add_handler(CommandHandler("list", list_command))

    # Callback query handler for pagination
    application.add_handler(CallbackQueryHandler(list_callback, pattern='^list_'))

    # Message handler for free text search (must be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_text_search))

    # Log a message to the console to confirm the bot is running
    logger.info("Bot started successfully. Polling for updates...")

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
