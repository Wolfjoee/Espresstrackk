import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Tuple, Optional

class Database:
    def __init__(self, db_name='finance_tracker.db'):
        self.db_name = db_name
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create all necessary tables."""
        with self.get_connection() as conn:
            # Income/Expense transactions
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    trans_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Borrow/Lend tracking with enhanced fields
            conn.execute('''
                CREATE TABLE IF NOT EXISTS debt_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    debt_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    contact_name TEXT NOT NULL,
                    purpose TEXT,
                    status TEXT DEFAULT 'pending',
                    borrow_date DATE,
                    return_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User settings for notifications
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    daily_report BOOLEAN DEFAULT 1,
                    report_time TEXT DEFAULT '06:00',
                    timezone TEXT DEFAULT 'Asia/Kolkata',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_trans_user_date ON transactions(user_id, created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_debt_user_status ON debt_tracking(user_id, status)')
    
    # ========== Transaction Operations ==========
    
    def record_income(self, user_id: int, amount: float, category: str = 'salary', description: str = '') -> None:
        """Record any type of income."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO transactions (user_id, trans_type, amount, category, description) VALUES (?, ?, ?, ?, ?)',
                (user_id, 'income', amount, category, description)
            )
    
    def record_expense(self, user_id: int, amount: float, category: str, description: str = '') -> None:
        """Record an expense."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO transactions (user_id, trans_type, amount, category, description) VALUES (?, ?, ?, ?, ?)',
                (user_id, 'expense', amount, category, description)
            )
    
    # ========== Enhanced Borrow/Lend Operations ==========
    
    def add_borrowed_money(self, user_id: int, amount: float, from_person: str, purpose: str = '', 
                          borrow_date: str = None) -> int:
        """Record money borrowed from someone."""
        if not borrow_date:
            borrow_date = datetime.now().date().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                '''INSERT INTO debt_tracking (user_id, debt_type, amount, contact_name, purpose, 
                   status, borrow_date) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (user_id, 'borrowed', amount, from_person, purpose, 'pending', borrow_date)
            )
            return cursor.lastrowid
    
    def add_lent_money(self, user_id: int, amount: float, to_person: str, purpose: str = '',
                      lend_date: str = None) -> int:
        """Record money lent to someone."""
        if not lend_date:
            lend_date = datetime.now().date().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                '''INSERT INTO debt_tracking (user_id, debt_type, amount, contact_name, purpose, 
                   status, borrow_date) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (user_id, 'lent', amount, to_person, purpose, 'pending', lend_date)
            )
            return cursor.lastrowid
    
    def mark_money_received(self, user_id: int, debt_id: int, received_date: str = None) -> bool:
        """Mark borrowed money as received back."""
        if not received_date:
            received_date = datetime.now().date().isoformat()
        
        with self.get_connection() as conn:
            conn.execute(
                '''UPDATE debt_tracking SET status = ?, return_date = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ? AND debt_type = 'lent' ''',
                ('settled', received_date, debt_id, user_id)
            )
            return True
    
    def mark_money_returned(self, user_id: int, debt_id: int, return_date: str = None) -> bool:
        """Mark lent money as returned."""
        if not return_date:
            return_date = datetime.now().date().isoformat()
        
        with self.get_connection() as conn:
            conn.execute(
                '''UPDATE debt_tracking SET status = ?, return_date = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ? AND debt_type = 'borrowed' ''',
                ('settled', return_date, debt_id, user_id)
            )
            return True
    
    def get_pending_borrows(self, user_id: int) -> List[sqlite3.Row]:
        """Get all pending borrowed money entries."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                '''SELECT * FROM debt_tracking 
                   WHERE user_id = ? AND debt_type = 'borrowed' AND status = 'pending'
                   ORDER BY borrow_date DESC''',
                (user_id,)
            )
            return cursor.fetchall()
    
    def get_pending_lends(self, user_id: int) -> List[sqlite3.Row]:
        """Get all pending lent money entries."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                '''SELECT * FROM debt_tracking 
                   WHERE user_id = ? AND debt_type = 'lent' AND status = 'pending'
                   ORDER BY borrow_date DESC''',
                (user_id,)
            )
            return cursor.fetchall()
    
    # ========== Advanced Reports ==========
    
    def get_today_summary(self, user_id: int) -> str:
        """Get today's financial summary."""
        today = datetime.now().date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT trans_type, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND DATE(created_at) = ?
                GROUP BY trans_type
            ''', (user_id, today))
            
            data = {row['trans_type']: {'total': row['total'], 'count': row['count']} for row in cursor.fetchall()}
        
        if not data:
            return "📅 *Today's Summary*\n\n❌ No transactions recorded yet today."
        
        income = data.get('income', {}).get('total', 0)
        expenses = data.get('expense', {}).get('total', 0)
        expense_count = data.get('expense', {}).get('count', 0)
        
        net_balance = income - expenses
        
        return f"""📅 *Today's Summary*
📆 {today.strftime('%d %B %Y')}

💰 Income: ₹{income:,.2f}
💸 Expenses: ₹{expenses:,.2f} ({expense_count} transactions)
{'━' * 25}
💵 Net: ₹{net_balance:,.2f}"""
    
    def get_yesterday_report(self, user_id: int) -> str:
        """Get yesterday's complete report."""
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT trans_type, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND DATE(created_at) = ?
                GROUP BY trans_type
            ''', (user_id, yesterday))
            
            data = {row['trans_type']: {'total': row['total'], 'count': row['count']} for row in cursor.fetchall()}
            
            # Get expense details
            cursor = conn.execute('''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND DATE(created_at) = ? AND trans_type = 'expense'
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id, yesterday))
            
            categories = cursor.fetchall()
        
        if not data:
            return f"📅 *Yesterday's Report*\n📆 {yesterday.strftime('%d %B %Y')}\n\n❌ No transactions recorded."
        
        income = data.get('income', {}).get('total', 0)
        expenses = data.get('expense', {}).get('total', 0)
        expense_count = data.get('expense', {}).get('count', 0)
        
        net = income - expenses
        
        report = f"""📅 *Yesterday's Report*
📆 {yesterday.strftime('%d %B %Y')}

💰 Total Income: ₹{income:,.2f}
💸 Total Expenses: ₹{expenses:,.2f} ({expense_count} items)
{'━' * 25}
💵 Net Balance: ₹{net:,.2f}
"""
        
        if categories:
            report += "\n📊 *Expense Breakdown:*\n"
            for cat in categories:
                category = cat['category'] or 'other'
                report += f"  • {category.title()}: ₹{cat['total']:,.2f}\n"
        
        return report.strip()
    
    def get_monthly_statement(self, user_id: int, month: int = None, year: int = None) -> str:
        """Get monthly financial statement."""
        if not month or not year:
            today = datetime.now()
            month, year = today.month, today.year
        
        month_start = datetime(year, month, 1).date()
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date()
        else:
            month_end = datetime(year, month + 1, 1).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT trans_type, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND DATE(created_at) >= ? AND DATE(created_at) < ?
                GROUP BY trans_type
            ''', (user_id, month_start, month_end))
            
            data = {row['trans_type']: {'total': row['total'], 'count': row['count']} for row in cursor.fetchall()}
            
            # Category breakdown
            cursor = conn.execute('''
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND trans_type = 'expense' 
                AND DATE(created_at) >= ? AND DATE(created_at) < ?
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id, month_start, month_end))
            
            categories = cursor.fetchall()
        
        if not data:
            return f"📊 *Monthly Statement - {month_start.strftime('%B %Y')}*\n\n❌ No data available."
        
        income = data.get('income', {}).get('total', 0)
        expenses = data.get('expense', {}).get('total', 0)
        expense_count = data.get('expense', {}).get('count', 0)
        
        net = income - expenses
        savings_rate = (net / income * 100) if income > 0 else 0
        
        report = f"""📊 *Monthly Statement*
📆 {month_start.strftime('%B %Y')}

💰 Total Income: ₹{income:,.2f}
💸 Total Expenses: ₹{expenses:,.2f} ({expense_count} items)
{'━' * 25}
💵 Net Savings: ₹{net:,.2f}
📈 Savings Rate: {savings_rate:.1f}%

📊 *Category-wise Expenses:*
"""
        
        category_icons = {
            'food': '🍔', 'transport': '🚗', 'bills': '🏠',
            'shopping': '🛍️', 'health': '💊', 'entertainment': '🎬',
            'education': '📚', 'other': '📦'
        }
        
        for cat in categories:
            category = cat['category'] or 'other'
            icon = category_icons.get(category, '📦')
            percentage = (cat['total'] / expenses * 100) if expenses > 0 else 0
            report += f"{icon} {category.title()}: ₹{cat['total']:,.2f} ({percentage:.1f}%)\n"
        
        return report.strip()
    
    def get_borrow_lend_summary(self, user_id: int) -> str:
        """Complete borrow/lend summary with detailed breakdown."""
        with self.get_connection() as conn:
            # Total borrowed (pending)
            cursor = conn.execute('''
                SELECT SUM(amount) as total FROM debt_tracking
                WHERE user_id = ? AND debt_type = 'borrowed' AND status = 'pending'
            ''', (user_id,))
            total_borrowed = cursor.fetchone()['total'] or 0
            
            # Total lent (pending)
            cursor = conn.execute('''
                SELECT SUM(amount) as total FROM debt_tracking
                WHERE user_id = ? AND debt_type = 'lent' AND status = 'pending'
            ''', (user_id,))
            total_lent = cursor.fetchone()['total'] or 0
            
            # Settled borrowed
            cursor = conn.execute('''
                SELECT SUM(amount) as total FROM debt_tracking
                WHERE user_id = ? AND debt_type = 'borrowed' AND status = 'settled'
            ''', (user_id,))
            settled_borrowed = cursor.fetchone()['total'] or 0
            
            # Settled lent
            cursor = conn.execute('''
                SELECT SUM(amount) as total FROM debt_tracking
                WHERE user_id = ? AND debt_type = 'lent' AND status = 'settled'
            ''', (user_id,))
            settled_lent = cursor.fetchone()['total'] or 0
            
            # Pending borrowed entries
            cursor = conn.execute('''
                SELECT contact_name, amount, borrow_date, purpose
                FROM debt_tracking
                WHERE user_id = ? AND debt_type = 'borrowed' AND status = 'pending'
                ORDER BY borrow_date DESC
                LIMIT 5
            ''', (user_id,))
            pending_borrows = cursor.fetchall()
            
            # Pending lent entries
            cursor = conn.execute('''
                SELECT contact_name, amount, borrow_date, purpose
                FROM debt_tracking
                WHERE user_id = ? AND debt_type = 'lent' AND status = 'pending'
                ORDER BY borrow_date DESC
                LIMIT 5
            ''', (user_id,))
            pending_lends = cursor.fetchall()
        
        report = f"""📒 *Borrow & Lend Summary*

💰 *Outstanding Balances:*
📥 You Owe: ₹{total_borrowed:,.2f}
📤 Others Owe You: ₹{total_lent:,.2f}
💵 Net Position: ₹{total_lent - total_borrowed:,.2f}

✅ *Settled:*
🔄 Borrowed & Returned: ₹{settled_borrowed:,.2f}
🔁 Lent & Received: ₹{settled_lent:,.2f}
"""
        
        if pending_borrows:
            report += f"\n{'━' * 30}\n\n📥 *Money You Owe:*\n\n"
            for rec in pending_borrows:
                date_str = datetime.fromisoformat(rec['borrow_date']).strftime('%d %b %Y')
                report += f"👤 {rec['contact_name']}: ₹{rec['amount']:,.2f}\n"
                report += f"   📅 {date_str} | 📝 {rec['purpose'] or 'No note'}\n\n"
        
        if pending_lends:
            report += f"{'━' * 30}\n\n📤 *Money Others Owe You:*\n\n"
            for rec in pending_lends:
                date_str = datetime.fromisoformat(rec['borrow_date']).strftime('%d %b %Y')
                report += f"👤 {rec['contact_name']}: ₹{rec['amount']:,.2f}\n"
                report += f"   📅 {date_str} | 📝 {rec['purpose'] or 'No note'}\n\n"
        
        return report.strip()
    
    def get_person_wise_report(self, user_id: int) -> str:
        """Get person-wise borrow/lend report."""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT contact_name, debt_type, status, SUM(amount) as total, COUNT(*) as count
                FROM debt_tracking
                WHERE user_id = ?
                GROUP BY contact_name, debt_type, status
                ORDER BY contact_name, debt_type
            ''', (user_id,))
            
            records = cursor.fetchall()
        
        if not records:
            return "👤 *Person-wise Report*\n\n❌ No borrow/lend records found."
        
        # Group by person
        from collections import defaultdict
        person_data = defaultdict(lambda: {'borrowed_pending': 0, 'borrowed_settled': 0,
                                           'lent_pending': 0, 'lent_settled': 0})
        
        for rec in records:
            person = rec['contact_name']
            key = f"{rec['debt_type']}_{rec['status']}"
            person_data[person][key] += rec['total']
        
        report = "👤 *Person-wise Report*\n\n"
        
        for person, data in sorted(person_data.items()):
            report += f"*{person}*\n"
            if data['borrowed_pending'] > 0:
                report += f"  📥 You owe: ₹{data['borrowed_pending']:,.2f}\n"
            if data['lent_pending'] > 0:
                report += f"  📤 They owe: ₹{data['lent_pending']:,.2f}\n"
            if data['borrowed_settled'] > 0:
                report += f"  ✅ Returned: ₹{data['borrowed_settled']:,.2f}\n"
            if data['lent_settled'] > 0:
                report += f"  ✅ Received: ₹{data['lent_settled']:,.2f}\n"
            report += "\n"
        
        return report.strip()
    
    # ========== User Settings ==========
    
    def get_users_for_daily_report(self) -> List[int]:
        """Get all user IDs who have daily reports enabled."""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT user_id FROM user_settings WHERE daily_report = 1
                UNION
                SELECT DISTINCT user_id FROM transactions
            ''')
            return [row['user_id'] for row in cursor.fetchall()]
    
    def update_user_settings(self, user_id: int, daily_report: bool = True) -> None:
        """Update user settings."""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO user_settings (user_id, daily_report) 
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET daily_report = ?
            ''', (user_id, daily_report, daily_report))
    
    def wipe_user_data(self, user_id: int) -> None:
        """Delete all data for a user."""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM debt_tracking WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM user_settings WHERE user_id = ?', (user_id,))
