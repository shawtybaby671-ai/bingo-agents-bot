# Bingo Agents Bot

This is a Python-based Telegram bot designed to manage bingo games with OCR and cloud deployment on Render.

## Features
- Telegram bot integration
- OCR for image processing
- Cloud deployment-ready

## Setup
1. Create a virtual environment:
   ```
   python -m venv venv
   ```
2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set environment variables for secrets:
   - `TELEGRAM_TOKEN`: Your bot token from @BotFather
   - `ADMIN_ID`: Your Telegram user ID
   - `GROUP_CHAT_ID`: The group chat ID

## Deployment
1. Push the code to GitHub.
2. Connect the repository to Render.
3. Add environment variables in Render settings.
4. Deploy the bot as a background worker.

## Commands
- `/start`: Check if the bot is running.