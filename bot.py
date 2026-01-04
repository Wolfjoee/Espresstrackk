import os
import logging
from datetime import datetime, time as dt_time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    filters, ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()
scheduler = AsyncIOScheduler()

# Conversation states
(AWAIT_INCOME, AWAIT_EXPENSE, AWAIT_BORROW_AMOUNT, AWAIT_BORROW_PERSON,
 AWAIT_BORROW_PURPOSE, AWAIT_LEND_AMOUNT, AWAIT_LEND_PERSON, AWAIT_LEND_PURPOSE) = range(8)

# ========== Keyboard Layouts ==========

def main_keyboard():
    """Enhanced main menu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Add Income", callback_data="add_income"),
            InlineKeyboardButton("💸 Add Expense", callback_data="add_expense")
        ],
        [
            InlineKeyboardButton("🤝 Borrow & Lend", callback_data="menu_borrow_lend"),
            InlineKeyboardButton("📊 Statements", callback_data="menu_statements")
        ],
        [
            InlineKeyboardButton("📝 Mini Statement", callback_data="mini_statement"),
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        ]
    ])

def borrow_lend_keyboard():
    """Borrow & Lend main menu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 Borrowed Money", callback_data="borrowed_money"),
            InlineKeyboardButton("📤 Lent Money", callback_data="lent_money")
        ],
        [
            InlineKeyboardButton("🔄 Money Received", callback_data="money_received"),
            InlineKeyboardButton("🔁 Money Returned", callback_data="money_returned")
        ],
        [
            InlineKeyboardButton("📜 Borrow & Lend Summary", callback_data="bl_summary")
        ],
        [
            InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
        ]
    ])

def statements_keyboard():
    """Statements menu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 Monthly Statement", callback_data="monthly_statement"),
            InlineKeyboardButton("📆 Custom Date Range", callback_data="custom_date")
        ],
        [
            InlineKeyboardButton("🤝 Borrow & Lend Statement", callback_data="bl_statement"),
            InlineKeyboardButton("💸 Expense Category Report", callback_data="expense_category")
        ],
        [
            InlineKeyboardButton("💰 Income Summary", callback_data="income_summary"),
            InlineKeyboardButton("📈 Net Balance Report", callback_data="net_balance")
        ],
        [
            InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
        ]
    ])

def borrow_lend_statement_keyboard():
    """Advanced Borrow & Lend statement options."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 Total Borrowed", callback_data="total_borrowed"),
            InlineKeyboardButton("📤 Total Lent", callback_data="total_lent")
        ],
        [
            InlineKeyboardButton("⏳ Pending Amount", callback_data="pending_amount"),
            InlineKeyboardButton("✅ Settled Amount", callback_data="settled_amount")
        ],
        [
            InlineKeyboardButton("👤 Person-wise Report", callback_data="person_wise")
        ],
        [
            InlineKeyboardButton("🔙 Statements", callback_data="menu_statements")
        ]
    ])

def settings_keyboard():
    """Settings menu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📬 Daily Reports: ON", callback_data="toggle_daily_report"),
        ],
        [
            InlineKeyboardButton("🔄 Reset All Data", callback_data="confirm_reset")
        ],
        [
            InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
        ]
    ])

def cancel_keyboard():
    """Cancel button."""
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
    """Back to main menu."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
    ]])

def back_to_statements():
    """Back to statements menu."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Statements", callback_data="menu_statements")
    ]])

def back_to_borrow_lend():
    """Back to borrow/lend menu."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Borrow & Lend", callback_data="menu_borrow_lend")
    ]])

# ========== Command Handlers ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    message = """👋 *Welcome to Advanced Finance Tracker!*

Your complete financial management solution:

💰 *Income Tracking*
💸 *Expense Management*
🤝 *Borrow & Lend Records*
📊 *Detailed Statements*
📬 *Automated Daily Reports*

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
    help_text = """📖 *Complete User Guide*

*💰 Add Income:*
Record salary, freelance, or any income source.

*💸 Add Expense:*
Track expenses with categories:
• Food, Transport, Bills, Shopping
• Health, Entertainment, Education, Other

*🤝 Borrow & Lend:*
• Record money borrowed from others
• Track money lent to friends
• Mark received/returned amounts
• Get detailed summaries

*📊 Statements:*
• Monthly financial statements
• Custom date range reports
• Category-wise expense analysis
• Person-wise borrow/lend report
• Net balance overview

*⚙️ Settings:*
• Enable/disable daily reports
• Daily reports sent at 6:00 AM
• Reset all data option

*Quick Commands:*
• `income 50000 salary`
• `spend 500 food lunch`

*📬 Daily Automation:*
Yesterday's report automatically sent every morning at 6 AM!"""
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            help_text, parse_mode='Markdown', reply_markup=back_to_menu()
        )
    else:
        await update.message.reply_text(help_text, parse_mode='Markdown')

# ========== Entry Point Handlers ==========

async def start_income_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start income entry conversation."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "💰 *Add Income*\n\n"
        "Enter income details in this format:\n"
        "`<amount> <category> <description>`\n\n"
        "*Examples:*\n"
        "• `50000 salary Monthly salary`\n"
        "• `15000 freelance Project payment`\n"
        "• `5000 bonus Performance bonus`\n\n"
        "*Categories:* salary, freelance, business, investment, bonus, other",
        parse_mode='Markdown', reply_markup=cancel_keyboard()
    )
    return AWAIT_INCOME

async def start_expense_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start expense entry conversation."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "💸 *Add Expense*\n\n"
        "Enter expense details in this format:\n"
        "`<amount> <category> <description>`\n\n"
        "*Examples:*\n"
        "• `500 food Lunch at restaurant`\n"
        "• `1500 bills Electricity bill`\n"
        "• `200 transport Auto fare`\n\n"
        "*Categories:* food, transport, bills, shopping, health, entertainment, education, other",
        parse_mode='Markdown', reply_markup=cancel_keyboard()
    )
    return AWAIT_EXPENSE

async def start_borrowed_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start borrowed money entry."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "📥 *Borrowed Money*\n\n"
        "➕ *Add New Borrow*\n\n"
        "Enter details in this format:\n"
        "`<amount> <from_whom> <purpose>`\n\n"
        "*Example:*\n"
        "`5000 John Emergency medical expense`",
        parse_mode='Markdown', reply_markup=cancel_keyboard()
    )
    return AWAIT_BORROW_AMOUNT

async def start_lent_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start lent money entry."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "📤 *Lent Money*\n\n"
        "➕ *Add New Lend*\n\n"
        "Enter details in this format:\n"
        "`<amount> <to_whom> <purpose>`\n\n"
        "*Example:*\n"
        "`2000 Sarah Business startup help`",
        parse_mode='Markdown', reply_markup=cancel_keyboard()
    )
    return AWAIT_LEND_AMOUNT

async def handle_money_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle money received back."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    pending_lends = db.get_pending_lends(user_id)
    
    if not pending_lends:
        await query.message.edit_text(
            "🔄 *Money Received*\n\n"
            "❌ No pending lent money records found.\n\n"
            "You need to lend money first before marking it as received.",
            parse_mode='Markdown',
            reply_markup=back_to_borrow_lend()
        )
        return
    
    # Create buttons for each pending lend
    keyboard = []
    for lend in pending_lends[:10]:  # Show max 10
        button_text = f"👤 {lend['contact_name']}: ₹{lend['amount']:,.2f}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"receive_{lend['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Borrow & Lend", callback_data="menu_borrow_lend")])
    
    await query.message.edit_text(
        "🔄 *Money Received Back*\n\n"
        "✅ Select the person who returned the money:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_money_returned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle money returned."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    pending_borrows = db.get_pending_borrows(user_id)
    
    if not pending_borrows:
        await query.message.edit_text(
            "🔁 *Money Returned*\n\n"
            "❌ No pending borrowed money records found.\n\n"
            "You need to borrow money first before marking it as returned.",
            parse_mode='Markdown',
            reply_markup=back_to_borrow_lend()
        )
        return
    
    # Create buttons for each pending borrow
    keyboard = []
    for borrow in pending_borrows[:10]:  # Show max 10
        button_text = f"👤 {borrow['contact_name']}: ₹{borrow['amount']:,.2f}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"return_{borrow['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Borrow & Lend", callback_data="menu_borrow_lend")])
    
    await query.message.edit_text(
        "🔁 *Money Returned*\n\n"
        "✅ Select the person you returned money to:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel operation."""
    query = update.callback_query
    await query.answer()
    await start_command(update, context)
    return ConversationHandler.END

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
    
    elif action == "show_help":
        await help_command(update, context)
    
    # Menus
    elif action == "menu_borrow_lend":
        await query.message.edit_text(
            "🤝 *Borrow & Lend Money*\n\n"
            "Complete loan management system:",
            reply_markup=borrow_lend_keyboard()
        )
    
    elif action == "menu_statements":
        await query.message.edit_text(
            "📊 *Financial Statements*\n\n"
            "Select statement type:",
            reply_markup=statements_keyboard()
        )
    
    elif action == "menu_settings":
        await query.message.edit_text(
            "⚙️ *Settings*\n\n"
            "Configure your preferences:",
            reply_markup=settings_keyboard()
        )
    
    # Statements
    elif action == "monthly_statement":
        report = db.get_monthly_statement(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', reply_markup=back_to_statements())
    
    elif action == "bl_statement":
        await query.message.edit_text(
            "🤝 *Borrow & Lend Statement*\n\n"
            "Select report type:",
            reply_markup=borrow_lend_statement_keyboard()
        )
    
    elif action == "bl_summary":
        report = db.get_borrow_lend_summary(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', reply_markup=back_to_borrow_lend())
    
    elif action == "person_wise":
        report = db.get_person_wise_report(user_id)
        await query.message.edit_text(report, parse_mode='Markdown', 
                                       reply_markup=InlineKeyboardMarkup([[
                                           InlineKeyboardButton("🔙 Back", callback_data="bl_statement")
                                       ]]))
    
    elif action == "total_borrowed":
        pending_borrows = db.get_pending_borrows(user_id)
        total = sum(b['amount'] for b in pending_borrows)
        report = f"📥 *Total Borrowed (Pending)*\n\n💰 Amount: ₹{total:,.2f}\n📊 Count: {len(pending_borrows)} entries"
        await query.message.edit_text(report, parse_mode='Markdown',
                                       reply_markup=InlineKeyboardMarkup([[
                                           InlineKeyboardButton("🔙 Back", callback_data="bl_statement")
                                       ]]))
    
    elif action == "total_lent":
        pending_lends = db.get_pending_lends(user_id)
        total = sum(l['amount'] for l in pending_lends)
        report = f"📤 *Total Lent (Pending)*\n\n💰 Amount: ₹{total:,.2f}\n📊 Count: {len(pending_lends)} entries"
        await query.message.edit_text(report, parse_mode='Markdown',
                                       reply_markup=InlineKeyboardMarkup([[
                                           InlineKeyboardButton("🔙 Back", callback_data="bl_statement")
                                       ]]))
            # Mini Statement
    elif action == "mini_statement":
        await query.message.edit_text(
            "⏳ *Generating Mini Statement...*\n\nPlease wait...",
            parse_mode='Markdown'
        )
        
        try:
            statement = db.get_last_30_days_statement(user_id)
            
            # Split into chunks if too long (Telegram limit: 4096 chars)
            max_length = 4000
            if len(statement) > max_length:
                chunks = [statement[i:i+max_length] for i in range(0, len(statement), max_length)]
                
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await query.message.edit_text(
                            chunk,
                            parse_mode='Markdown',
                            reply_markup=back_to_menu() if i == len(chunks)-1 else None
                        )
                    else:
                        await query.message.reply_text(
                            chunk,
                            parse_mode='Markdown',
                            reply_markup=back_to_menu() if i == len(chunks)-1 else None
                        )
            else:
                await query.message.edit_text(
                    statement,
                    parse_mode='Markdown',
                    reply_markup=back_to_menu()
                )
        except Exception as e:
            logger.error(f"Mini statement error: {e}")
            await query.message.edit_text(
                "❌ Error generating statement. Please try again.",
                parse_mode='Markdown',
                reply_markup=back_to_menu()
            )
    # Settings
    elif action == "toggle_daily_report":
        db.update_user_settings(user_id, True)
        await query.message.edit_text(
            "✅ *Daily Reports Enabled*\n\n"
            "📬 You will receive yesterday's report every morning at 6:00 AM.\n\n"
            "The report includes:\n"
            "• Income summary\n"
            "• Expense breakdown\n"
            "• Net balance",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Settings", callback_data="menu_settings")
            ]])
        )
    
    # Reset
    elif action == "confirm_reset":
        await query.message.edit_text(
            "⚠️ *WARNING: Reset All Data*\n\n"
            "This will permanently delete:\n"
            "• All income records\n"
            "• All expense records\n"
            "• All borrow/lend records\n"
            "• All statements\n\n"
            "❗ *This action CANNOT be undone!*\n\n"
            "Are you absolutely sure?",
            parse_mode='Markdown',
            reply_markup=confirm_reset_keyboard()
        )
    
    elif action == "execute_reset":
        db.wipe_user_data(user_id)
        await query.message.edit_text(
            "✅ *All Data Deleted Successfully!*\n\n"
            "Your account has been reset.\n"
            "You can start adding new records now.",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )
    
    # Handle receive/return callbacks
    elif action.startswith("receive_"):
        debt_id = int(action.split("_")[1])
        db.mark_money_received(user_id, debt_id)
        await query.message.edit_text(
            "✅ *Money Received Marked!*\n\n"
            "The lent amount has been marked as received.\n"
            "Your balance has been updated.",
            parse_mode='Markdown',
            reply_markup=back_to_borrow_lend()
        )
    
    elif action.startswith("return_"):
        debt_id = int(action.split("_")[1])
        db.mark_money_returned(user_id, debt_id)
        await query.message.edit_text(
            "✅ *Money Returned Marked!*\n\n"
            "The borrowed amount has been marked as returned.\n"
            "Your balance has been updated.",
            parse_mode='Markdown',
            reply_markup=back_to_borrow_lend()
        )

# ========== Conversation Input Handlers ==========

async def receive_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process income input."""
    try:
        text = update.message.text.strip()
        parts = text.split(None, 2)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n`<amount> <category> <description>`",
                parse_mode='Markdown', reply_markup=cancel_keyboard()
            )
            return AWAIT_INCOME
        
        amount = float(parts[0])
        category = parts[1].lower()
        description = parts[2] if len(parts) > 2 else ""
        
        user_id = update.effective_user.id
        db.record_income(user_id, amount, category, description)
        
        category_icons = {
            'salary': '💰', 'freelance': '💼', 'business': '🏢',
            'investment': '📈', 'bonus': '🎁', 'other': '💵'
        }
        icon = category_icons.get(category, '💰')
        
        await update.message.reply_text(
            f"✅ *Income Recorded!*\n\n"
            f"{icon} Category: {category.title()}\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
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
        return AWAIT_INCOME

async def receive_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process expense input."""
    try:
        text = update.message.text.strip()
        parts = text.split(None, 2)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n`<amount> <category> <description>`",
                parse_mode='Markdown', reply_markup=cancel_keyboard()
            )
            return AWAIT_EXPENSE
        
        amount = float(parts[0])
        category = parts[1].lower()
        description = parts[2] if len(parts) > 2 else ""
        
        valid_categories = ['food', 'transport', 'bills', 'shopping', 'health', 
                          'entertainment', 'education', 'other']
        if category not in valid_categories:
            category = 'other'
        
        user_id = update.effective_user.id
        db.record_expense(user_id, amount, category, description)
        
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
            return AWAIT_BORROW_AMOUNT
        
        amount = float(parts[0])
        person = parts[1]
        purpose = parts[2] if len(parts) > 2 else ""
        
        user_id = update.effective_user.id
        db.add_borrowed_money(user_id, amount, person, purpose)
        
        await update.message.reply_text(
            f"📥 *Borrowed Money Recorded!*\n\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
            f"👤 From: {person}\n"
            f"📝 Purpose: {purpose if purpose else 'No note'}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y')}\n\n"
            f"⏳ Status: Pending",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Please try again.",
            reply_markup=cancel_keyboard()
        )
        return AWAIT_BORROW_AMOUNT

async def receive_lend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process lent money input."""
    try:
        text = update.message.text.strip()
        parts = text.split(None, 2)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n`<amount> <to_whom> <purpose>`",
                parse_mode='Markdown', reply_markup=cancel_keyboard()
            )
            return AWAIT_LEND_AMOUNT
        
        amount = float(parts[0])
        person = parts[1]
        purpose = parts[2] if len(parts) > 2 else ""
        
        user_id = update.effective_user.id
        db.add_lent_money(user_id, amount, person, purpose)
        
        await update.message.reply_text(
            f"📤 *Lent Money Recorded!*\n\n"
            f"💰 Amount: ₹{amount:,.2f}\n"
            f"👤 To: {person}\n"
            f"📝 Purpose: {purpose if purpose else 'No note'}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y')}\n\n"
            f"⏳ Status: Pending",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Please try again.",
            reply_markup=cancel_keyboard()
        )
        return AWAIT_LEND_AMOUNT

# ========== Quick Text Commands ==========

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick text commands."""
    user_id = update.effective_user.id
    text = update.message.text.lower().strip()
    
    try:
        if text.startswith('income'):
            parts = text.split('income')[1].strip().split(None, 2)
            amount = float(parts[0])
            category = parts[1] if len(parts) > 1 else 'other'
            description = parts[2] if len(parts) > 2 else ''
            db.record_income(user_id, amount, category, description)
            await update.message.reply_text(
                f"✅ Income: ₹{amount:,.2f} ({category}) recorded!",
                reply_markup=main_keyboard()
            )
        
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
        
        else:
            await update.message.reply_text(
                "❌ Unknown command. Use buttons or:\n"
                "• `income 50000 salary`\n"
                "• `spend 500 food lunch`",
                reply_markup=main_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ Invalid format. Use buttons for guided input.",
            reply_markup=main_keyboard()
        )

# ========== Automated Daily Report ==========

async def send_daily_reports(application: Application):
    """Send yesterday's report to all users at 6 AM."""
    logger.info("Starting daily report distribution...")
    
    user_ids = db.get_users_for_daily_report()
    
    for user_id in user_ids:
        try:
            report = db.get_yesterday_report(user_id)
            
            await application.bot.send_message(
                chat_id=user_id,
                text=f"🌅 *Good Morning!*\n\n{report}",
                parse_mode='Markdown',
                reply_markup=main_keyboard()
            )
            logger.info(f"Daily report sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send report to user {user_id}: {e}")
    
    logger.info(f"Daily reports sent to {len(user_ids)} users")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

# ========== Main Function ==========

def main():
    """Initialize and start the bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not found!")
    
    app = Application.builder().token(token).build()
        # ========== Conversation Handlers ==========
    
    income_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_income_entry, pattern="^add_income$")],
        states={AWAIT_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_income)]},
        fallbacks=[CallbackQueryHandler(cancel_operation, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    expense_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_expense_entry, pattern="^add_expense$")],
        states={AWAIT_EXPENSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expense)]},
        fallbacks=[CallbackQueryHandler(cancel_operation, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    borrow_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_borrowed_entry, pattern="^borrowed_money$")],
        states={AWAIT_BORROW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_borrow)]},
        fallbacks=[CallbackQueryHandler(cancel_operation, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    lend_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_lent_entry, pattern="^lent_money$")],
        states={AWAIT_LEND_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_lend)]},
        fallbacks=[CallbackQueryHandler(cancel_operation, pattern="^main_menu$")],
        allow_reentry=True
    )
    
    # Add handlers in correct order
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Conversation handlers
    app.add_handler(income_conv)
    app.add_handler(expense_conv)
    app.add_handler(borrow_conv)
    app.add_handler(lend_conv)
    
    # Special handlers for money received/returned
    app.add_handler(CallbackQueryHandler(handle_money_received, pattern="^money_received$"))
    app.add_handler(CallbackQueryHandler(handle_money_returned, pattern="^money_returned$"))
    
    # General callback handler
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Text handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # ========== Setup Daily Report Scheduler ==========
    
    # Schedule daily report at 6:00 AM IST
    scheduler.add_job(
        send_daily_reports,
        CronTrigger(hour=6, minute=0, timezone='Asia/Kolkata'),
        args=[app],
        id='daily_report',
        name='Send Yesterday Report',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("📅 Daily report scheduler started (6:00 AM IST)")
    
    # Start bot
    logger.info("🚀 Advanced Finance Tracker Bot Started Successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
