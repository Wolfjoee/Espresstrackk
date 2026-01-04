import os
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import Database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    welcome_message = """
👋 *Welcome to Salary Tracker Bot!*

📝 *Commands:*
• `salary credited <amount>` - Record salary
• `spend <amount> [note]` - Record expense
• `credit savings <amount>` - Record savings
• `today report` - View today's summary
• `month report` - View monthly summary
• `help` - Show this message

💡 *Examples:*
• `salary credited 50000`
• `spend 500 groceries`
• `credit savings 5000`
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages."""
    user_id = update.effective_user.id
    text = update.message.text.lower().strip()
    
    try:
        # Salary credited
        if text.startswith('salary credited'):
            amount = float(text.split('salary credited')[1].strip())
            db.add_transaction(user_id, 'salary', amount)
            await update.message.reply_text(
                f"✅ Salary credited: ₹{amount:,.2f}\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        
        # Spend
        elif text.startswith('spend'):
            parts = text.split('spend')[1].strip().split(None, 1)
            amount = float(parts[0])
            note = parts[1] if len(parts) > 1 else ""
            db.add_transaction(user_id, 'expense', amount, note)
            await update.message.reply_text(
                f"✅ Expense recorded: ₹{amount:,.2f}\n"
                f"📝 Note: {note if note else 'No note'}\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        
        # Credit savings
        elif text.startswith('credit savings'):
            amount = float(text.split('credit savings')[1].strip())
            db.add_transaction(user_id, 'savings', amount)
            await update.message.reply_text(
                f"✅ Savings credited: ₹{amount:,.2f}\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        
        # Today report
        elif 'today report' in text:
            report = db.get_today_report(user_id)
            await update.message.reply_text(report, parse_mode='Markdown')
        
        # Month report
        elif 'month report' in text:
            report = db.get_month_report(user_id)
            await update.message.reply_text(report, parse_mode='Markdown')
        
        else:
            await update.message.reply_text(
                "❌ Unknown command. Type 'help' to see available commands."
            )
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a valid number.\n"
            "Example: `spend 500` or `salary credited 50000`",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again or contact support."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    # Get token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()