import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Tuple

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
            # Main transactions table
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
            
            # Borrow/Lend tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS debt_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    debt_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    contact_name TEXT NOT NULL,
                    purpose TEXT,
                    is_settled INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_trans_user_date ON transactions(user_id, created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_debt_user_status ON debt_tracking(user_id, is_settled)')
    
    # ========== Transaction Operations ==========
    
    def record_salary(self, user_id: int, amount: float) -> None:
        """Record salary income."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO transactions (user_id, trans_type, amount) VALUES (?, ?, ?)',
                (user_id, 'salary', amount)
            )
    
    def record_expense(self, user_id: int, amount: float, category: str, description: str = '') -> None:
        """Record an expense with category."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO transactions (user_id, trans_type, amount, category, description) VALUES (?, ?, ?, ?, ?)',
                (user_id, 'expense', amount, category, description)
            )
    
    def record_savings(self, user_id: int, amount: float) -> None:
        """Record money moved to savings."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO transactions (user_id, trans_type, amount) VALUES (?, ?, ?)',
                (user_id, 'savings', amount)
            )
    
    # ========== Borrow/Lend Operations ==========
    
    def record_borrowed(self, user_id: int, amount: float, from_person: str, purpose: str = '') -> None:
        """Record money borrowed from someone."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO debt_tracking (user_id, debt_type, amount, contact_name, purpose) VALUES (?, ?, ?, ?, ?)',
                (user_id, 'borrowed', amount, from_person, purpose)
            )
    
    def record_lent(self, user_id: int, amount: float, to_person: str, purpose: str = '') -> None:
        """Record money lent to someone."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO debt_tracking (user_id, debt_type, amount, contact_name, purpose) VALUES (?, ?, ?, ?, ?)',
                (user_id, 'lent', amount, to_person, purpose)
            )
    
    def record_debt_settlement(self, user_id: int, amount: float, contact: str, purpose: str = '') -> None:
        """Record money received back or debt repayment."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO debt_tracking (user_id, debt_type, amount, contact_name, purpose, is_settled) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, 'settlement', amount, contact, purpose, 1)
            )
    
    # ========== Report Generation ==========
    
    def get_today_summary(self, user_id: int) -> str:
        """Generate today's financial summary."""
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
        
        salary = data.get('salary', {}).get('total', 0)
        expenses = data.get('expense', {}).get('total', 0)
        savings = data.get('savings', {}).get('total', 0)
        expense_count = data.get('expense', {}).get('count', 0)
        
        net_balance = salary - expenses - savings
        
        return f"""📅 *Today's Summary*
📆 {today.strftime('%d %B %Y')}

💰 Income: ₹{salary:,.2f}
💸 Expenses: ₹{expenses:,.2f} ({expense_count} transactions)
🏦 Savings: ₹{savings:,.2f}
{'━' * 25}
💵 Net Balance: ₹{net_balance:,.2f}"""
    
    def get_monthly_overview(self, user_id: int) -> str:
        """Generate current month's overview."""
        today = datetime.now()
        month_start = today.replace(day=1).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT trans_type, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND DATE(created_at) >= ?
                GROUP BY trans_type
            ''', (user_id, month_start))
            
            data = {row['trans_type']: {'total': row['total'], 'count': row['count']} for row in cursor.fetchall()}
        
        if not data:
            return f"📊 *Monthly Overview - {today.strftime('%B %Y')}*\n\n❌ No transactions this month."
        
        salary = data.get('salary', {}).get('total', 0)
        expenses = data.get('expense', {}).get('total', 0)
        savings = data.get('savings', {}).get('total', 0)
        expense_count = data.get('expense', {}).get('count', 0)
        
        net_balance = salary - expenses - savings
        savings_rate = (savings / salary * 100) if salary > 0 else 0
        
        return f"""📊 *Monthly Overview*
📆 {today.strftime('%B %Y')}

💰 Total Income: ₹{salary:,.2f}
💸 Total Expenses: ₹{expenses:,.2f} ({expense_count} items)
🏦 Total Savings: ₹{savings:,.2f}
{'━' * 25}
💵 Net Balance: ₹{net_balance:,.2f}
📈 Savings Rate: {savings_rate:.1f}%"""
    
    def get_complete_monthly_report(self, user_id: int) -> str:
        """Comprehensive monthly report with date-wise and category-wise breakdown."""
        today = datetime.now()
        month_start = today.replace(day=1).date()
        
        with self.get_connection() as conn:
            # Overall totals
            cursor = conn.execute('''
                SELECT trans_type, SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND DATE(created_at) >= ?
                GROUP BY trans_type
            ''', (user_id, month_start))
            totals = {row['trans_type']: row['total'] for row in cursor.fetchall()}
            
            # Daily expenses
            cursor = conn.execute('''
                SELECT DATE(created_at) as day, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND trans_type = 'expense' AND DATE(created_at) >= ?
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) DESC
            ''', (user_id, month_start))
            daily_expenses = cursor.fetchall()
            
            # Category breakdown
            cursor = conn.execute('''
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND trans_type = 'expense' AND DATE(created_at) >= ?
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id, month_start))
            categories = cursor.fetchall()
        
        if not totals:
            return f"📅 *Complete Monthly Report*\n\n❌ No data available for {today.strftime('%B %Y')}."
        
        salary = totals.get('salary', 0)
        total_expenses = totals.get('expense', 0)
        savings = totals.get('savings', 0)
        remaining = salary - total_expenses - savings
        
        report = f"""📅 *Monthly Expense Report*
📆 {today.strftime('%B %Y')}

💰 Total Income: ₹{salary:,.2f}
💸 Total Spent: ₹{total_expenses:,.2f}
🏦 Savings: ₹{savings:,.2f}
💵 Remaining: ₹{remaining:,.2f}

{'━' * 30}

📊 *Date-wise Spending*
"""
        
        for row in daily_expenses[:10]:  # Show last 10 days
            day_obj = datetime.strptime(row['day'], '%Y-%m-%d')
            report += f"\n📅 {day_obj.strftime('%d %b')}: ₹{row['total']:,.2f} ({row['count']} items)"
        
        report += f"\n\n{'━' * 30}\n\n📈 *Category-wise Expenses*\n"
        
        category_icons = {
            'food': '🍔', 'transport': '🚗', 'bills': '🏠',
            'shopping': '🛍️', 'health': '💊', 'entertainment': '🎬',
            'education': '📚', 'other': '📦'
        }
        
        for row in categories:
            cat = row['category'] or 'other'
            icon = category_icons.get(cat, '📦')
            percentage = (row['total'] / total_expenses * 100) if total_expenses > 0 else 0
            report += f"\n{icon} {cat.title()}: ₹{row['total']:,.2f} ({percentage:.1f}%)"
        
        return report
    
    def get_last_30_days_statement(self, user_id: int) -> str:
        """Mini statement showing last 30 days of transactions."""
        cutoff_date = (datetime.now() - timedelta(days=30)).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT trans_type, amount, category, description, created_at
                FROM transactions
                WHERE user_id = ? AND DATE(created_at) >= ?
                ORDER BY created_at DESC
                LIMIT 30
            ''', (user_id, cutoff_date))
            
            transactions = cursor.fetchall()
        
        if not transactions:
            return "📝 *Mini Statement (Last 30 Days)*\n\n❌ No transactions found."
        
        report = "📝 *Mini Statement*\n_Last 30 Days Activity_\n\n"
        
        type_icons = {'salary': '💰', 'expense': '💸', 'savings': '🏦'}
        
        for trans in transactions:
            trans_time = datetime.strptime(trans['created_at'], '%Y-%m-%d %H:%M:%S')
            icon = type_icons.get(trans['trans_type'], '💵')
            
            if trans['trans_type'] == 'expense' and trans['category']:
                detail = f" ({trans['category']})"
            else:
                detail = ""
            
            desc = f" - {trans['description']}" if trans['description'] else ""
            
            report += f"{icon} *{trans['trans_type'].title()}*: ₹{trans['amount']:,.2f}{detail}{desc}\n"
            report += f"   _{trans_time.strftime('%d %b, %I:%M %p')}_\n\n"
        
        return report.strip()
    
    def get_daily_expense_breakdown(self, user_id: int) -> str:
        """Show daily expenses for current month."""
        month_start = datetime.now().replace(day=1).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DATE(created_at) as day, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND trans_type = 'expense' AND DATE(created_at) >= ?
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) DESC
            ''', (user_id, month_start))
            
            daily_data = cursor.fetchall()
        
        if not daily_data:
            return "💸 *Daily Expenses*\n\n❌ No expenses recorded this month."
        
        report = f"💸 *Daily Expenses*\n📆 {datetime.now().strftime('%B %Y')}\n\n"
        
        total_spent = 0
        for row in daily_data:
            day_obj = datetime.strptime(row['day'], '%Y-%m-%d')
            report += f"📅 {day_obj.strftime('%d %b (%a)')}: ₹{row['total']:,.2f} ({row['count']} items)\n"
            total_spent += row['total']
        
        avg_daily = total_spent / len(daily_data) if daily_data else 0
        
        report += f"\n{'━' * 25}\n"
        report += f"💰 Total: ₹{total_spent:,.2f}\n"
        report += f"📊 Avg/Day: ₹{avg_daily:,.2f}"
        
        return report
    
    def get_category_analysis(self, user_id: int) -> str:
        """Analyze spending by category."""
        month_start = datetime.now().replace(day=1).date()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT category, SUM(amount) as total, COUNT(*) as count, AVG(amount) as avg
                FROM transactions
                WHERE user_id = ? AND trans_type = 'expense' AND DATE(created_at) >= ?
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id, month_start))
            
            categories = cursor.fetchall()
        
        if not categories:
            return "📈 *Spending Analysis*\n\n❌ No expense data available."
        
        total_expenses = sum(row['total'] for row in categories)
        
        report = f"📈 *Spending Analysis*\n📆 {datetime.now().strftime('%B %Y')}\n\n"
        
        icons = {
            'food': '🍔', 'transport': '🚗', 'bills': '🏠',
            'shopping': '🛍️', 'health': '💊', 'entertainment': '🎬',
            'education': '📚', 'other': '📦'
        }
        
        for row in categories:
            cat = row['category'] or 'other'
            icon = icons.get(cat, '📦')
            share = (row['total'] / total_expenses * 100) if total_expenses > 0 else 0
            
            report += f"{icon} *{cat.title()}*\n"
            report += f"   Total: ₹{row['total']:,.2f} ({share:.1f}%)\n"
            report += f"   Count: {row['count']} | Avg: ₹{row['avg']:,.2f}\n\n"
        
        report += f"{'━' * 25}\n💰 Total Expenses: ₹{total_expenses:,.2f}"
        
        return report
    
    def get_borrow_lend_summary(self, user_id: int) -> str:
        """Complete borrow/lend tracking report."""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT debt_type, contact_name, amount, purpose, created_at, is_settled
                FROM debt_tracking
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            
            records = cursor.fetchall()
        
        if not records:
            return "📒 *Borrow & Lend Summary*\n\n❌ No records found."
        
        borrowed_total = lent_total = settled_total = 0
        borrowed_list = []
        lent_list = []
        
        for rec in records:
            if rec['debt_type'] == 'borrowed' and not rec['is_settled']:
                borrowed_total += rec['amount']
                borrowed_list.append(rec)
            elif rec['debt_type'] == 'lent' and not rec['is_settled']:
                lent_total += rec['amount']
                lent_list.append(rec)
            elif rec['debt_type'] == 'settlement':
                settled_total += rec['amount']
        
        report = "📒 *Borrow & Lend Summary*\n\n"
        
        report += f"💰 *Outstanding Balances*\n"
        report += f"📥 You Owe: ₹{borrowed_total:,.2f}\n"
        report += f"📤 Others Owe You: ₹{lent_total:,.2f}\n"
        report += f"✅ Settled: ₹{settled_total:,.2f}\n\n"
        
        if borrowed_list:
            report += f"{'━' * 30}\n\n📥 *Money You Borrowed*\n\n"
            for rec in borrowed_list[:5]:
                date_obj = datetime.strptime(rec['created_at'], '%Y-%m-%d %H:%M:%S')
                report += f"👤 {rec['contact_name']}: ₹{rec['amount']:,.2f}\n"
                report += f"   📝 {rec['purpose'] or 'No note'}\n"
                report += f"   📅 {date_obj.strftime('%d %b %Y')}\n\n"
        
        if lent_list:
            report += f"{'━' * 30}\n\n📤 *Money You Lent*\n\n"
            for rec in lent_list[:5]:
                date_obj = datetime.strptime(rec['created_at'], '%Y-%m-%d %H:%M:%S')
                report += f"👤 {rec['contact_name']}: ₹{rec['amount']:,.2f}\n"
                report += f"   📝 {rec['purpose'] or 'No note'}\n"
                report += f"   📅 {date_obj.strftime('%d %b %Y')}\n\n"
        
        return report.strip()
    
    def wipe_user_data(self, user_id: int) -> None:
        """Delete all data for a specific user."""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM debt_tracking WHERE user_id = ?', (user_id,))
