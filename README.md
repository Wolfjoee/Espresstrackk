# 💰 Advanced Finance Tracker Bot

A comprehensive Telegram bot for personal finance management with automated daily reports.

## ✨ Features

### 💰 Income Tracking
- Record multiple income sources (salary, freelance, business, etc.)
- Categorized income management
- Income summary reports

### 💸 Expense Management
- Track expenses by category
- 8 predefined categories: Food, Transport, Bills, Shopping, Health, Entertainment, Education, Other
- Detailed expense analysis
- Category-wise breakdown

### 🤝 Borrow & Lend System
- **Borrowed Money**: Record money you borrowed from others
- **Lent Money**: Track money you lent to friends
- **Money Received**: Mark when borrowed money is returned to you
- **Money Returned**: Mark when you return borrowed money
- Complete status tracking (Pending/Settled)
- Person-wise detailed reports

### 📊 Advanced Statements
- **Monthly Statement**: Complete month overview with category breakdown
- **Custom Date Range**: Filter by specific dates
- **Borrow & Lend Statement**: Detailed loan reports
  - Total borrowed (pending & settled)
  - Total lent (pending & settled)
  - Person-wise breakdown
- **Expense Category Report**: Category-wise spending analysis
- **Income Summary**: All income sources overview
- **Net Balance Report**: Overall financial position

### 📬 Automated Daily Reports
- Automatically sends yesterday's report every morning at **6:00 AM**
- Includes:
  - Total income
  - Total expenses
  - Category-wise expense breakdown
  - Net balance

### ⚙️ Settings
- Enable/disable daily reports
- Reset all data option
- User-specific configurations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Railway/Render/Heroku account for deployment

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd finance-tracker-bot
