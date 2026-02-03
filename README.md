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

### Game Flow Commands (Automated Progression)
- `/newgame`: Create a new bingo game (anyone can create)
- `/card`: Get your bingo card and join the game
- `/ready`: Mark yourself as ready to start playing
- `/startcalling`: Begin auto-calling numbers every 10 seconds
- `/pause`: Pause the auto-calling
- `/resume`: Resume the auto-calling
- `/endgame`: End the current game

### Manual Control
- `/call <number>`: Manually call a specific number (1-75)

### Player Commands
- `/lastcall`: Replay last called number with its ball image
- `/check`: Check if you have won
- `/numbers`: View all called numbers
- `/players`: View list of players and their card counts
- `/status`: View game status and flow state

## Game Flow States

The game automatically progresses through these states:

1. **🏁 IDLE** - No game active
2. **📝 SETUP** - Game created, players joining with `/card`
3. **✅ READY** - Minimum players joined, waiting for ready confirmations
4. **🎲 CALLING** - Auto-calling numbers at 10-second intervals
5. **⏸️ PAUSED** - Game temporarily paused
6. **🏁 ENDED** - Game completed

### Automatic Transitions
- IDLE → SETUP: When someone uses `/newgame`
- SETUP → READY: When minimum players (1+) join with `/card`
- READY → CALLING: When players mark ready and someone uses `/startcalling`
- CALLING → PAUSED: When someone uses `/pause`
- PAUSED → CALLING: When someone uses `/resume`
- CALLING → ENDED: When all 75 numbers called or someone uses `/endgame`

## Multimedia Features
- **Visual Ball Display**: When numbers are called, a colorful bingo ball image is automatically sent showing the letter and number
- **Ball Colors**: Each column has a distinct color (B=Red, I=Teal, N=Yellow, G=Green, O=Pink)
- **Last Call Replay**: Players can use `/lastcall` to see the most recent call again
- **Real-time Updates**: All players see the ball image immediately when a number is called

## How to Play

### Quick Start (Automated Game Flow)
1. Anyone creates a game: `/newgame`
2. Players join by getting cards: `/card` 
3. Players mark themselves ready: `/ready`
4. When ready, start auto-calling: `/startcalling`
5. Numbers are called automatically every 10 seconds with visual ball images
6. Players check for wins: `/check`
7. Use `/pause` and `/resume` to control the flow
8. Game ends when someone wins or all numbers called

### Classic Mode (Manual Control)
- Create game with `/newgame`
- Players get cards with `/card`
- Manually call numbers: `/call 42`
- Players check wins: `/check`

Win conditions: Complete row, column, or diagonal

## Features
- **Automated Game Flow** with state-based progression
- **No Admin Required** - anyone can create/control games
- **Auto-calling** numbers at configurable intervals (default 10s)
- **Player Ready System** for coordinated starts
- **Pause/Resume** controls for flexible gameplay
- Standard 5x5 bingo cards (B-I-N-G-O format)
- Free space in the center
- Multiple players can join the same game
- Win detection for rows, columns, and diagonals
- **Visual ball images** with color-coded display for each column
- **Player list** showing all active players and their cards
- **Last call replay** for players who missed a call
- Real-time game state tracking and display