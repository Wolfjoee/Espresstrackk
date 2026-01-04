# 💰 Telegram Salary Tracker Bot

A simple and efficient Telegram bot to track your salary, expenses, and savings.

## 🚀 Features

- ✅ Track salary credits
- ✅ Record daily expenses with notes
- ✅ Track savings
- ✅ Automatic date tracking
- ✅ Today's summary report
- ✅ Monthly summary report with savings rate
- ✅ SQLite database (persistent storage)
- ✅ Multi-user support

## 📝 Commands

- `salary credited <amount>` - Record salary
- `spend <amount> [note]` - Record expense
- `credit savings <amount>` - Record savings
- `today report` - View today's summary
- `month report` - View monthly summary
- `help` - Show help message

## 🛠️ Local Setup

```bash
# Clone repository
git clone https://github.com/yourusername/salary-tracker-bot.git
cd salary-tracker-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN

# Run bot
python bot.py
