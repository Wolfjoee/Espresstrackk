import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from collections import defaultdict

class Database:
    def __init__(self, db_name='salary_tracker.db'):
        self.db_name = db_name
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    note TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_date 
                ON transactions(user_id, date)
            ''')
    
    def add_transaction(self, user_id, transaction_type, amount, note=''):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO transactions (user_id, type, amount, note) VALUES (?, ?, ?, ?)',
                (user_id, transaction_type, amount, note)
            )
    
    def get_today_report(self, user_id):
        today = datetime.now().date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT type, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND DATE(date) = ?
                GROUP BY type
            ''', (user_id, today))
            
            results = cursor.fetchall()
        
        if not results:
            return "📊 *Today's Report*\n\n❌ No transactions recorded today."
        
        salary = expenses = savings = 0
        expense_count = 0
        
        for row in results:
            if row['type'] == 'salary':
                salary = row['total']
            elif row['type'] == 'expense':
                expenses = row['total']
                expense_count = row['count']
            elif row['type'] == 'savings':
                savings = row['total']
        
        balance = salary - expenses - savings
        
        report = f"""
📊 *Today's Report*
📅 {today.strftime('%d %B %Y')}

💰 Salary: ₹{salary:,.2f}
💸 Expenses: ₹{expenses:,.2f} ({expense_count} items)
🏦 Savings: ₹{savings:,.2f}
━━━━━━━━━━━━━━━━━
💵 Balance: ₹{balance:,.2f}
        """
        
        return report.strip()
    
    def get_month_report(self, user_id):
        today = datetime.now()
        first_day = today.replace(day=1).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT type, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND DATE(date) >= ?
                GROUP BY type
            ''', (user_id, first_day))
            
            results = cursor.fetchall()
        
        if not results:
            return f"📊 *Monthly Report*\n\n❌ No transactions this month."
        
        salary = expenses = savings = 0
        expense_count = 0
        
        for row in results:
            if row['type'] == 'salary':
                salary = row['total']
            elif row['type'] == 'expense':
                expenses = row['total']
                expense_count = row['count']
            elif row['type'] == 'savings':
                savings = row['total']
        
        balance = salary - expenses - savings
        savings_rate = (savings / salary * 100) if salary > 0 else 0
        expense_rate = (expenses / salary * 100) if salary > 0 else 0
        
        report = f"""
📊 *Monthly Report*
📅 {today.strftime('%B %Y')}

💰 Total Salary: ₹{salary:,.2f}
💸 Total Expenses: ₹{expenses:,.2f} ({expense_count} items)
🏦 Total Savings: ₹{savings:,.2f}
━━━━━━━━━━━━━━━━━
💵 Net Balance: ₹{balance:,.2f}

📈 Savings Rate: {savings_rate:.1f}%
📉 Expense Rate: {expense_rate:.1f}%
        """
        
        return report.strip()
    
    def get_daily_expenses(self, user_id):
        """Get day-by-day expense breakdown for current month."""
        today = datetime.now()
        first_day = today.replace(day=1).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DATE(date) as day, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND type = 'expense' AND DATE(date) >= ?
                GROUP BY DATE(date)
                ORDER BY DATE(date) DESC
                LIMIT 15
            ''', (user_id, first_day))
            
            results = cursor.fetchall()
        
        if not results:
            return f"💸 *Daily Expenses*\n\n❌ No expenses recorded this month."
        
        report = f"💸 *Daily Expenses - {today.strftime('%B %Y')}*\n\n"
        
        total = 0
        for row in results:
            day = datetime.strptime(row['day'], '%Y-%m-%d')
            report += f"📅 {day.strftime('%d %b')}: ₹{row['total']:,.2f} ({row['count']} items)\n"
            total += row['total']
        
        report += f"\n━━━━━━━━━━━━━━━━━\n"
        report += f"💰 Total: ₹{total:,.2f}"
        
        return report
    
    def get_spending_analysis(self, user_id):
        """Get category-wise spending analysis based on notes."""
        today = datetime.now()
        first_day = today.replace(day=1).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT note, amount, date
                FROM transactions
                WHERE user_id = ? AND type = 'expense' AND DATE(date) >= ?
                ORDER BY amount DESC
            ''', (user_id, first_day))
            
            results = cursor.fetchall()
        
        if not results:
            return f"📈 *Spending Analysis*\n\n❌ No expenses this month."
        
        # Categorize expenses
        categories = defaultdict(float)
        for row in results:
            note = row['note'].lower() if row['note'] else 'other'
            
            # Simple categorization based on keywords
            if any(word in note for word in ['food', 'lunch', 'dinner', 'breakfast', 'groceries', 'restaurant']):
                categories['🍔 Food'] += row['amount']
            elif any(word in note for word in ['transport', 'fuel', 'petrol', 'taxi', 'uber', 'bus', 'metro']):
                categories['🚗 Transport'] += row['amount']
            elif any(word in note for word in ['bill', 'electricity', 'water', 'rent', 'internet']):
                categories['🏠 Bills'] += row['amount']
            elif any(word in note for word in ['shopping', 'clothes', 'shoes', 'fashion']):
                categories['🛍️ Shopping'] += row['amount']
            elif any(word in note for word in ['medicine', 'doctor', 'hospital', 'health']):
                categories['💊 Health'] += row['amount']
            elif any(word in note for word in ['movie', 'entertainment', 'game', 'party']):
                categories['🎬 Entertainment'] += row['amount']
            else:
                categories['📦 Other'] += row['amount']
        
        # Sort categories by amount
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        total = sum(categories.values())
        
        report = f"📈 *Spending Analysis - {today.strftime('%B %Y')}*\n\n"
        
        for category, amount in sorted_categories:
            percentage = (amount / total * 100) if total > 0 else 0
            report += f"{category}: ₹{amount:,.2f} ({percentage:.1f}%)\n"
        
        report += f"\n━━━━━━━━━━━━━━━━━\n"
        report += f"💰 Total Expenses: ₹{total:,.2f}"
        
        return report
    
    def get_mini_statement(self, user_id):
        """Get last 10 transactions."""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT type, amount, note, date
                FROM transactions
                WHERE user_id = ?
                ORDER BY date DESC
                LIMIT 10
            ''', (user_id,))
            
            results = cursor.fetchall()
        
        if not results:
            return "📝 *Mini Statement*\n\n❌ No transactions yet."
        
        report = "📝 *Mini Statement*\n_Last 10 Transactions_\n\n"
        
        for row in results:
            trans_date = datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S')
            
            if row['type'] == 'salary':
                emoji = "💰"
                type_text = "Salary"
            elif row['type'] == 'expense':
                emoji = "💸"
                type_text = "Expense"
            else:
                emoji = "🏦"
                type_text = "Savings"
            
            note_text = f" - {row['note']}" if row['note'] else ""
            
            report += f"{emoji} *{type_text}*: ₹{row['amount']:,.2f}{note_text}\n"
            report += f"   _{trans_date.strftime('%d %b, %I:%M %p')}_\n\n"
        
        return report.strip()
    
    def reset_user_data(self, user_id):
        """Delete all transactions for a user."""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
