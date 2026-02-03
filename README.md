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
- `/start`: Show help message with available commands
- `/newgame`: Start a new bingo game (admin only)
- `/card`: Get or view your bingo card
- `/call <number>`: Call a number with visual ball image (1-75, admin only)
- `/lastcall`: Replay last called number with its ball image
- `/check`: Check if you have won
- `/numbers`: View all called numbers
- `/players`: View list of players and their card counts
- `/status`: View current game status

## Multimedia Features
- **Visual Ball Display**: When numbers are called, a colorful bingo ball image is automatically sent showing the letter and number
- **Ball Colors**: Each column has a distinct color (B=Red, I=Teal, N=Yellow, G=Green, O=Pink)
- **Last Call Replay**: Players can use `/lastcall` to see the most recent call again
- **Real-time Updates**: All players see the ball image immediately when a number is called

## How to Play
1. Admin starts a new game with `/newgame`
2. Players get their bingo cards with `/card`
3. Admin calls numbers with `/call <number>` (e.g., `/call 42`)
4. Players can view called numbers with `/numbers`
5. Players check for wins with `/check`
6. Win conditions: Complete row, column, or diagonal

## Features
- Standard 5x5 bingo cards (B-I-N-G-O format)
- Free space in the center
- Multiple players can join the same game
- Win detection for rows, columns, and diagonals
- Admin-controlled number calling
- Card persistence during active game
- **Visual ball images** with color-coded display for each column
- **Player list** showing all active players and their cards
- **Last call replay** for players who missed a call