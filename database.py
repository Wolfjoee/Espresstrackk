import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager

class Database:
    def __init__(self, db_name='salary_tracker.db'):
        self.db_name = db_name
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
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
        """Initialize database tables."""
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
        """Add a new transaction."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO transactions (user_id, type, amount, note) VALUES (?, ?, ?, ?)',
                (user_id, transaction_type, amount, note)
            )
    
    def get_today_report(self, user_id):
        """Get today's summary report."""
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
            return "📊 *Today's Report*\n\nNo transactions recorded today."
        
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
📅 Date: {today.strftime('%d %B %Y')}

💰 Salary Credited: ₹{salary:,.2f}
💸 Total Expenses: ₹{expenses:,.2f} ({expense_count} transactions)
🏦 Savings: ₹{savings:,.2f}
━━━━━━━━━━━━━━━━━
💵 Balance: ₹{balance:,.2f}
        """
        
        return report.strip()
    
    def get_month_report(self, user_id):
        """Get monthly summary report."""
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
            return f"📊 *Monthly Report - {today.strftime('%B %Y')}*\n\nNo transactions recorded this month."
        
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
📊 *Monthly Report*
📅 Month: {today.strftime('%B %Y')}

💰 Total Salary: ₹{salary:,.2f}
💸 Total Expenses: ₹{expenses:,.2f} ({expense_count} transactions)
🏦 Total Savings: ₹{savings:,.2f}
━━━━━━━━━━━━━━━━━
💵 Net Balance: ₹{balance:,.2f}

📈 Savings Rate: {(savings/salary*100) if salary > 0 else 0:.1f}%
        """
        
        return report.strip()