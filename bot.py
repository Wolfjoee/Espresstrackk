import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters, 
    ContextTypes
)
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# ===== INLINE KEYBOARDS =====

def main_menu_keyboard():
    """Main menu with inline buttons."""
    keyboard = [
        [
            InlineKeyboardButton("💰 Add Salary", callback_data="menu_salary"),
            InlineKeyboardButton("💸 Add Expense", callback_data="menu_expense")
        ],
        [
            InlineKeyboardButton("🏦 Add Savings", callback_data="menu_savings"),
            InlineKeyboardButton("📊 Reports", callback_data="menu_reports")
        ],
        [
            InlineKeyboardButton("📝 Mini Statement", callback_data="mini_statement"),
            InlineKeyboardButton("🔄 Reset All", callback_data="reset_confirm")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def reports_keyboard():
    """Reports submenu."""
    keyboard = [
        [
            InlineKeyboardButton("📅 Today Report", callback_data="report_today"),
            InlineKeyboardButton("📆 Month Report", callback_data="report_month")
        ],
        [
            InlineKeyboardButton("💸 Daily Expenses", callback_data="daily_expenses"),
            InlineKeyboardButton("📈 Spending Analysis", callback_data="spending_analysis")
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def reset_confirm_keyboard():
    """Confirmation for reset."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Reset All", callback_data="reset_confirmed"),
            InlineKeyboardButton("❌ Cancel", callback_data="back_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button_keyboard():
    """Single back button."""
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]]
    return InlineKeyboardMarkup(keyboard)

# ===== COMMAND HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with inline buttons."""
    welcome_message = """
👋 *Welcome to Salary Tracker Bot!*

Use the buttons below or type commands:

*Quick Commands:*
• `salary credited 50000`
• `spend 500 groceries`
• `credit savings 5000`

*Choose an option:*
    """
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    help_text = """
📖 *Help - How to Use*

*📝 Text Commands:*
• `salary credited <amount>`
  Example: `salary credited 50000`

• `spend <amount> [note]`
  Example: `spend 500 groceries`

• `credit savings <amount>`
  Example: `credit savings 5000`

*🔘 Button Features:*
• *Add Salary* - Record your salary
• *Add Expense* - Track spending
• *Add Savings* - Log savings
• *Reports* - View summaries
• *Mini Statement* - Last 10 transactions
• *Reset All* - Clear all data

*📊 Reports:*
• *Today Report* - Today's summary
• *Month Report* - Monthly overview
• *Daily Expenses* - Day-by-day breakdown
• *Spending Analysis* - Category-wise view

Type commands or use buttons! 😊
    """
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    else:
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )

# ===== CALLBACK QUERY HANDLER =====

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Main menu buttons
    if data == "back_menu":
        await start(update, context)
    
    elif data == "menu_salary":
        await query.message.edit_text(
            "💰 *Add Salary*\n\n"
            "Type: `salary credited <amount>`\n"
            "Example: `salary credited 50000`",
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    
    elif data == "menu_expense":
        await query.message.edit_text(
            "💸 *Add Expense*\n\n"
            "Type: `spend <amount> [note]`\n"
            "Examples:\n"
            "• `spend 500 groceries`\n"
            "• `spend 200 transport`\n"
            "• `spend 1500 electricity bill`",
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    
    elif data == "menu_savings":
        await query.message.edit_text(
            "🏦 *Add Savings*\n\n"
            "Type: `credit savings <amount>`\n"
            "Example: `credit savings 5000`",
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    
    elif data == "menu_reports":
        await query.message.edit_text(
            "📊 *Select Report Type*",
            reply_markup=reports_keyboard()
        )
    
    elif data == "help":
        await help_command(update, context)
    
    # Reports
    elif data == "report_today":
        report = db.get_today_report(user_id)
        await query.message.edit_text(
            report,
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    
    elif data == "report_month":
        report = db.get_month_report(user_id)
        await query.message.edit_text(
            report,
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    
    elif data == "daily_expenses":
        report = db.get_daily_expenses(user_id)
        await query.message.edit_text(
            report,
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    
    elif data == "spending_analysis":
        report = db.get_spending_analysis(user_id)
        await query.message.edit_text(
            report,
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    
    elif data == "mini_statement":
        statement = db.get_mini_statement(user_id)
        await query.message.edit_text(
            statement,
            parse_mode='Markdown',
            reply_markup=back_button_keyboard()
        )
    
    # Reset functionality
    elif data == "reset_confirm":
        await query.message.edit_text(
            "⚠️ *Reset All Data*\n\n"
            "This will delete ALL your transactions:\n"
            "• All salary records\n"
            "• All expenses\n"
            "• All savings\n\n"
            "❗ This action cannot be undone!\n\n"
            "Are you sure?",
            parse_mode='Markdown',
            reply_markup=reset_confirm_keyboard()
        )
    
    elif data == "reset_confirmed":
        db.reset_user_data(user_id)
        await query.message.edit_text(
            "✅ *All Data Reset Successfully!*\n\n"
            "Your account is now clean.\n"
            "Start fresh by adding new transactions.",
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )

# ===== TEXT MESSAGE HANDLER =====

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
                f"✅ *Salary Credited*\n\n"
                f"💰 Amount: ₹{amount:,.2f}\n"
                f"📅 Date: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
        
        # Spend
        elif text.startswith('spend'):
            parts = text.split('spend')[1].strip().split(None, 1)
            amount = float(parts[0])
            note = parts[1] if len(parts) > 1 else ""
            db.add_transaction(user_id, 'expense', amount, note)
            await update.message.reply_text(
                f"✅ *Expense Recorded*\n\n"
                f"💸 Amount: ₹{amount:,.2f}\n"
                f"📝 Note: {note if note else 'No note'}\n"
                f"📅 Date: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
        
        # Credit savings
        elif text.startswith('credit savings'):
            amount = float(text.split('credit savings')[1].strip())
            db.add_transaction(user_id, 'savings', amount)
            await update.message.reply_text(
                f"✅ *Savings Credited*\n\n"
                f"🏦 Amount: ₹{amount:,.2f}\n"
                f"📅 Date: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
        
        # Today report
        elif 'today report' in text:
            report = db.get_today_report(user_id)
            await update.message.reply_text(
                report,
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
        
        # Month report
        elif 'month report' in text:
            report = db.get_month_report(user_id)
            await update.message.reply_text(
                report,
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
        
        # Mini statement
        elif 'mini statement' in text or 'statement' in text:
            statement = db.get_mini_statement(user_id)
            await update.message.reply_text(
                statement,
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
        
        else:
            await update.message.reply_text(
                "❌ Unknown command.\n\n"
                "Use buttons below or type:\n"
                "• `salary credited 5000`\n"
                "• `spend 500 lunch`\n"
                "• `credit savings 2000`",
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
    
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid Amount*\n\n"
            "Please enter a valid number.\n\n"
            "*Examples:*\n"
            "• `spend 500`\n"
            "• `salary credited 50000`",
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=main_menu_keyboard()
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Bot started with inline buttons...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
