import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    filters, ContextTypes
)
from database import Database
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# Conversation states
(AWAIT_SALARY, AWAIT_EXPENSE, AWAIT_SAVINGS,
 AWAIT_BORROW, AWAIT_LEND, AWAIT_RETURN) = range(6)

# ========== Keyboard Layouts ==========

def main_keyboard():
    """Primary navigation menu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➡️ Salary Credited", callback_data="add_salary"),
            InlineKeyboardButton("➡️ Add Expense", callback_data="add_expense")
        ],
        [
            InlineKeyboardButton("➡️ Add to Savings", callback_data="add_savings"),
            InlineKeyboardButton("📊 Reports", callback_data="show_reports")
        ],
        [
            InlineKeyboardButton("🤝 Borrow & Lend", callback_data="show_borrow"),
            InlineKeyboardButton("📝 Mini Statement", callback_data="mini_statement")
        ],
        [
            InlineKeyboardButton("🔄 Reset All Data", callback_data="confirm_reset"),
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        ]
    ])

def reports_keyboard():
    """Reports submenu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 Today Report", callback_data="report_today"),
            InlineKeyboardButton("📆 Month Report", callback_data="report_month")
        ],
        [
            InlineKeyboardButton("💸 Daily Expenses", callback_data="daily_expenses"),
            InlineKeyboardButton("📈 Spending Analysis", callback_data="spending_analysis")
        ],
        [
            InlineKeyboardButton("📅 Complete Month Report", callback_data="complete_report")
        ],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ])

def borrow_keyboard():
    """Borrow & Lend submenu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 Borrowed Money", callback_data="borrowed"),
            InlineKeyboardButton("📤 Money Given", callback_data="lent")
        ],
        [
            InlineKeyboardButton("🔁 Money Received", callback_data="returned"),
            InlineKeyboardButton("📒 Borrow/Lend Report", callback_data="borrow_report")
        ],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ])

def cancel_keyboard():
    """Cancel operation button."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel", callback_data="main_menu")
    ]])

def confirm_reset_keyboard():
    """Reset confirmation."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Delete Everything", callback_data="execute_reset"),
            InlineKeyboardButton("❌ No, Go Back", callback_data="main_menu")
        ]
    ])

def back_to_menu():
    """Single back button."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
    ]])

def back_to_borrow():
    """Back to borrow menu."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Borrow & Lend", callback_data="show_borrow")
    ]])

def back_to_reports():
    """Back to reports menu."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Reports", callback_data="show_reports")
    ]])

# ========== Command Handlers ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    message = """👋 *Welcome to Advanced Finance Tracker!*

Track all your finances in one place:

💰 *Income & Salary*
💸 *Expenses by Category*
🏦 *Savings Tracking*
🤝 *Borrow & Lend Money*
📊 *Detailed Reports*

Choose an option below to get started!"""
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            message, parse_mode='Markdown', reply_markup=main_keyboard()
        )
    else:
        await update.message.reply_text(
            message, parse_mode='Markdown', reply_markup=main_keyboard()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information."""
    help_text = """📖 *How to Use This Bot*

*💰 Salary / Income:*
Click "Salary Credited" and enter amount.

*💸 Expenses:*
Click "Add Expense" then enter:
`<amount> <category> <description>`

*Categories:* food, transport, bills, shopping, health, entertainment, education, other

*Example:* `500 food Lunch at restaurant`

*🏦 Savings:*
Click "Add to Savings" and enter amount.

*🤝 Borrow & Lend:*
Track money borrowed from or lent to others.

*📊 Reports:*
• Today Report - Today's activity
• Month Report - Monthly summary
• Daily Expenses - Day-by-day view
• Spending Analysis - Category breakdown
• Complete Month Report - Full details
• Mini Statement - Last 30 days

*Quick Commands:*
• `salary 50000`
• `spend 500 food lunch`
• `save 5000`"""
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            help_text, parse_mode='Markdown', reply_markup=back_to_menu()
        )
    else:
        await update.message.reply_text(help_text, parse_mode='Markdown')

# ========== Button Callback Handler ==========

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data
    
    # Navigation
    if action == "main_menu":
        await start_command(update, context)
        return ConversationHandler.END
    
    elif action == "show_help":
        await help_command(update, context)
    
    # Add transactions
    elif action == "add_salary":
        await query.message.edit_text(
            "💰 *Salary Credited*\n\n✅ Enter the salary amount:\n\n*Example:* `50000`",
            parse_mode='Markdown', reply_markup=cancel_keyboard()
        )
        return AWAIT_SALARY
    
    elif action == "add_expense":
        await query.message.edit_text(
            "💸 *Add Expense*\n\n🧾 Enter in this format:\n"
            "`<amount> <category> <description>`\n\n"
            "*Examples:*\n"
            "• `500 food Lunch at cafe`\n"
            "• `1500 bills Electricity bill`\n"
            "• `200 transport Auto fare`\n\n"
            "*Categories:* food, transport, bills, shopping, health, entertainment, education, other",
            parse_mode='Markdown', reply_markup=cancel_keyboard()
        )
        return AWAIT_EXPENSE
    
    elif action == "add_savings":
        await query.message.edit_text(
            "🏦 *Add to Savings*\n\n💾 Enter the amount to move to savings:\n\n*Example:* `5000`",
            parse_mode='Markdown', reply_markup=cancel_keyboard()
        )
        return AWAIT_SAVINGS
    
    # Reports
    elif action == "show_reports":
        await query.message.edit_text("📊 *Select Report Type*", reply_markup=reports_keyboard())
    
    elif action == "report_today":
        report = db.get_today_summary(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', reply_markup=back_to_reports())
    
    elif action == "report_month":
        report = db.get_monthly_overview(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', reply_markup=back_to_reports())
    
    elif action == "complete_report":
        report = db.get_complete_monthly_report(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', reply_markup=back_to_reports())
    
    elif action == "daily_expenses":
        report = db.get_daily_expense_breakdown(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', reply_markup=back_to_reports())
    
    elif action == "spending_analysis":
        report = db.get_category_analysis(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', reply_markup=back_to_reports())
    
    elif action == "mini_statement":
        statement = db.get_last_30_days_statement(user_id)
        await query.message.edit_text(statement, parse_mode='Markdown', reply_markup=back_to_menu())
    
    # Borrow & Lend
    elif action == "show_borrow":
        await query.message.edit_text("🤝 *Borrow & Lend Money*\n\nManage your loans:",
                                       reply_markup=borrow_keyboard())
    
    elif action == "borrowed":
        await query.message.edit_text(
            "📥 *Borrowed Money*\n\n"
            "Enter details in this format:\n"
            "`<amount> <from_whom> <purpose>`\n\n"
            "*Example:* `5000 John For bike repair`",
            parse_mode='Markdown', reply_markup=cancel_keyboard()
        )
        return AWAIT_BORROW
    
    elif action == "lent":
        await query.message.edit_text(
            "📤 *Money Given to Friend*\n\n"
            "Enter details in this format:\n"
            "`<amount> <friend_name> <purpose>`\n\n"
            "*Example:* `2000 Sarah Emergency help`",
            parse_mode='Markdown', reply_markup=cancel_keyboard()
        )
        return AWAIT_LEND
    
    elif action == "returned":
        await query.message.edit_text(
            "🔁 *Money Received Back*\n\n"
            "Enter details in this format:\n"
            "`<amount> <friend_name> <note>`\n\n"
            "*Example:* `2000 Sarah Loan repayment`",
            parse_mode='Markdown', reply_markup=cancel_keyboard()
        )
        return AWAIT_RETURN
    
    elif action == "borrow_report":
        report = db.get_borrow_lend_summary(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', reply_markup=back_to_borrow())
    
    # Reset
    elif action == "confirm_reset":
        await query.message.edit_text(
            "⚠️ *WARNING: Reset All Data*\n\n"
            "This will permanently delete:\n"
            "• All salary records\n"
            "• All expenses\n"
            "• All savings\n"
            "• All borrow/lend records\n\n"
            "❗ *This action CANNOT be undone!*\n\n"
            "Are you absolutely sure?",
            parse_mode='Markdown', reply_markup=confirm_reset_keyboard()
        )
    
    elif action == "execute_reset":
        db.wipe_user_data(user_id)
        await query.message.edit_text(
            "✅ *All Data Deleted Successfully!*\n\n"
            "Your account has been reset to zero.\n"
            "You can start adding new transactions now.",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )

# ========== Conversation Input Handlers ==========

async def receive_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process salary input."""
    try:
        amount = float(update.message.text.strip())
        user_id = update.effective_user.id
        
        db.record_salary(user_id, amount)
        
        await update.message.reply_text(
            f"✅ *Salary Credited Successfully!*\n\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"Your balance has been updated.",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a valid number.",
            reply_markup=cancel_keyboard()
        )
        return AWAIT_SALARY

async def receive_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process expense input."""
    try:
        text = update.message.text.strip()
        parts = text.split(None, 2)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n`<amount> <category> <description>`\n\n"
                "Example: `500 food Lunch`",
                parse_mode='Markdown', reply_markup=cancel_keyboard()
            )
            return AWAIT_EXPENSE
        
        amount = float(parts[0])
        category = parts[1].lower()
        description = parts[2] if len(parts) > 2 else ""
        
        # Validate category
        valid_categories = ['food', 'transport', 'bills', 'shopping', 'health', 'entertainment', 'education', 'other']
        if category not in valid_categories:
            category = 'other'
        
        user_id = update.effective_user.id
        db.record_expense(user_id, amount, category, description)
        
        # Category emojis
        category_icons = {
            'food': '🍔', 'transport': '🚗', 'bills': '🏠',
            'shopping': '🛍️', 'health': '💊', 'entertainment': '🎬',
            'education': '📚', 'other': '📦'
        }
        icon = category_icons.get(category, '💸')
        
        await update.message.reply_text(
            f"✅ *Expense Recorded!*\n\n"
            f"{icon} Category: {category.title()}\n"
            f"💸 Amount: ₹{amount:,.2f}\n"
            f"📝 Note: {description if description else 'No note'}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please try again.",
            reply_markup=cancel_keyboard()
        )
        return AWAIT_EXPENSE

async def receive_savings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process savings input."""
    try:
        amount = float(update.message.text.strip())
        user_id = update.effective_user.id
        
        db.record_savings(user_id, amount)
        
        await update.message.reply_text(
            f"✅ *Amount Added to Savings!*\n\n"
            f"🏦 Savings: ₹{amount:,.2f}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"💾 Amount moved to your savings account.",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a valid number.",
            reply_markup=cancel_keyboard()
        )
        return AWAIT_SAVINGS

async def receive_borrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process borrowed money input."""
    try:
        text = update.message.text.strip()
        parts = text.split(None, 2)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n`<amount> <from_whom> <purpose>`",
                parse_mode='Markdown', reply_markup=cancel_keyboard()
            )
            return AWAIT_BORROW
        
        amount = float(parts[0])
        person = parts[1]
        purpose = parts[2] if len(parts) > 2 else ""
        
        user_id = update.effective_user.id
        db.record_borrowed(user_id, amount, person, purpose)
        
        await update.message.reply_text(
            f"📥 *Borrowed Money Recorded!*\n\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
            f"👤 From: {person}\n"
            f"📝 Purpose: {purpose if purpose else 'No note'}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y')}",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Please try again.",
            reply_markup=cancel_keyboard()
        )
        return AWAIT_BORROW

async def receive_lent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process money lent input."""
    try:
        text = update.message.text.strip()
        parts = text.split(None, 2)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n`<amount> <friend_name> <purpose>`",
                parse_mode='Markdown', reply_markup=cancel_keyboard()
            )
            return AWAIT_LEND
        
        amount = float(parts[0])
        person = parts[1]
        purpose = parts[2] if len(parts) > 2 else ""
        
        user_id = update.effective_user.id
        db.record_lent(user_id, amount, person, purpose)
        
        await update.message.reply_text(
            f"📤 *Money Given Recorded!*\n\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
            f"👤 To: {person}\n"
            f"📝 Purpose: {purpose if purpose else 'No note'}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y')}",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Please try again.",
            reply_markup=cancel_keyboard()
        )
        return AWAIT_LEND

async def receive_returned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process money received back input."""
    try:
        text = update.message.text.strip()
        parts = text.split(None, 2)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n`<amount> <friend_name> <note>`",
                parse_mode='Markdown', reply_markup=cancel_keyboard()
            )
            return AWAIT_RETURN
        
        amount = float(parts[0])
        person = parts[1]
        note = parts[2] if len(parts) > 2 else ""
        
        user_id = update.effective_user.id
        db.record_debt_settlement(user_id, amount, person, note)
        
        await update.message.reply_text(
            f"🔁 *Money Received Back!*\n\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
            f"👤 From: {person}\n"
            f"📝 Note: {note if note else 'No note'}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y')}\n\n"
            f"✅ Balance updated successfully.",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Please try again.",
            reply_markup=cancel_keyboard()
        )
        return AWAIT_RETURN

# ========== Quick Text Commands ==========

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick text commands."""
    user_id = update.effective_user.id
    text = update.message.text.lower().strip()
    
    try:
        # Quick salary
        if text.startswith('salary'):
            amount = float(text.split('salary')[1].strip())
            db.record_salary(user_id, amount)
            await update.message.reply_text(
                f"✅ Salary: ₹{amount:,.2f} credited!",
                reply_markup=main_keyboard()
            )
        
        # Quick spend
        elif text.startswith('spend'):
            parts = text.split('spend')[1].strip().split(None, 2)
            amount = float(parts[0])
            category = parts[1] if len(parts) > 1 else 'other'
            description = parts[2] if len(parts) > 2 else ''
            db.record_expense(user_id, amount, category, description)
            await update.message.reply_text(
                f"✅ Expense: ₹{amount:,.2f} ({category}) recorded!",
                reply_markup=main_keyboard()
            )
        
        # Quick save
        elif text.startswith('save'):
            amount = float(text.split('save')[1].strip())
            db.record_savings(user_id, amount)
            await update.message.reply_text(
                f"✅ Savings: ₹{amount:,.2f} added!",
                reply_markup=main_keyboard()
            )
        
        else:
            await update.message.reply_text(
                "❌ Unknown command. Use buttons or:\n"
                "• `salary 50000`\n"
                "• `spend 500 food lunch`\n"
                "• `save 5000`",
                reply_markup=main_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ Invalid format. Use buttons for guided input.",
            reply_markup=main_keyboard()
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

# ========== Main Function ==========

def main():
    """Initialize and start the bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
    
    app = Application.builder().token(token).build()
    
    # Conversation handlers
    salary_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^add_salary$")],
        states={AWAIT_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_salary)]},
        fallbacks=[CallbackQueryHandler(button_callback, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    expense_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^add_expense$")],
        states={AWAIT_EXPENSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expense)]},
        fallbacks=[CallbackQueryHandler(button_callback, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    savings_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^add_savings$")],
        states={AWAIT_SAVINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_savings)]},
        fallbacks=[CallbackQueryHandler(button_callback, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    borrow_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^borrowed$")],
        states={AWAIT_BORROW: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_borrow)]},
        fallbacks=[CallbackQueryHandler(button_callback, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    lend_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^lent$")],
        states={AWAIT_LEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_lent)]},
        fallbacks=[CallbackQueryHandler(button_callback, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    return_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^returned$")],
        states={AWAIT_RETURN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_returned)]},
        fallbacks=[CallbackQueryHandler(button_callback, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    # Add all handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(salary_conv)
    app.add_handler(expense_conv)
    app.add_handler(savings_conv)
    app.add_handler(borrow_conv)
    app.add_handler(lend_conv)
    app.add_handler(return_conv)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    
    logger.info("🚀 Finance Tracker Bot Started Successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
