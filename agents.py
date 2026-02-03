import os
import random
import io
import asyncio
from enum import Enum
from typing import Dict, List, Set, Optional, Tuple
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont

# Game flow states
class GameState(Enum):
    IDLE = "idle"           # No active game
    SETUP = "setup"         # Game created, waiting for players
    READY = "ready"         # Players ready, can start calling
    CALLING = "calling"     # Auto-calling numbers
    PAUSED = "paused"       # Game paused
    ENDED = "ended"         # Game completed

# Environment variables for secrets
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', '-1001234567890'))

# Game state storage
class BingoGame:
    def __init__(self):
        self.called_numbers: Set[int] = set()
        self.player_cards: Dict[int, List[List[int]]] = {}  # user_id -> card
        self.player_names: Dict[int, str] = {}  # user_id -> display name
        self.player_ready: Set[int] = set()  # user_ids who are ready
        self.active = False
        self.state: GameState = GameState.IDLE
        self.last_call: Optional[Tuple[int, str]] = None  # (number, letter)
        self.auto_call_interval: int = 10  # seconds between auto-calls
        self.auto_call_task: Optional[asyncio.Task] = None
        self.min_players: int = 1  # Minimum players to start
        self.chat_id: Optional[int] = None  # Store chat ID for broadcasting
    
    def reset(self):
        """Reset game state for a new game."""
        self.called_numbers.clear()
        self.player_cards.clear()
        self.player_names.clear()
        self.player_ready.clear()
        self.last_call = None
        self.active = False
        self.state = GameState.IDLE
        if self.auto_call_task and not self.auto_call_task.done():
            self.auto_call_task.cancel()
        self.auto_call_task = None
    
    def can_start_calling(self) -> bool:
        """Check if game can start calling numbers."""
        return (
            self.state == GameState.READY and
            len(self.player_cards) >= self.min_players and
            len(self.player_ready) >= self.min_players
        )
    
    def get_next_number(self) -> Optional[int]:
        """Get a random uncalled number, or None if all called."""
        available = set(range(1, 76)) - self.called_numbers
        if not available:
            return None
        return random.choice(list(available))
    
    def get_state_description(self) -> str:
        """Get human-readable state description."""
        state_desc = {
            GameState.IDLE: "No active game",
            GameState.SETUP: "Setting up - players joining",
            GameState.READY: "Ready to start - waiting for players to be ready",
            GameState.CALLING: "Game in progress - auto-calling numbers",
            GameState.PAUSED: "Game paused",
            GameState.ENDED: "Game ended"
        }
        return state_desc.get(self.state, "Unknown")
    
    def generate_card(self) -> List[List[int]]:
        """Generate a 5x5 bingo card with random numbers.
        
        Card is stored in column-major order: card[col_idx][row_idx]
        This matches the B-I-N-G-O layout where each letter represents a column.
        """
        card = []
        # B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
        ranges = [(1, 15), (16, 30), (31, 45), (46, 60), (61, 75)]
        
        for col_idx, (start, end) in enumerate(ranges):
            column = random.sample(range(start, end + 1), 5)
            card.append(column)
        
        # Make center a free space (N column, middle row)
        card[2][2] = 0  # Free space
        
        return card
    
    def call_number(self, number: int) -> bool:
        """Call a number in the game."""
        if 1 <= number <= 75 and number not in self.called_numbers:
            self.called_numbers.add(number)
            return True
        return False
    
    def check_win(self, card: List[List[int]]) -> bool:
        """Check if a card has a winning pattern.
        
        Since card is stored as card[col][row], we need to transpose to check rows.
        """
        # Transpose to convert columns to rows for easier row checking
        transposed = list(zip(*card))
        
        # Check rows (each row from the transposed data)
        for row in transposed:
            if all(num == 0 or num in self.called_numbers for num in row):
                return True
        
        # Check columns (original card structure is already column-major)
        for col in card:
            if all(num == 0 or num in self.called_numbers for num in col):
                return True
        
        # Check diagonals
        diagonal1 = [card[i][i] for i in range(5)]
        diagonal2 = [card[i][4-i] for i in range(5)]
        
        if all(num == 0 or num in self.called_numbers for num in diagonal1):
            return True
        if all(num == 0 or num in self.called_numbers for num in diagonal2):
            return True
        
        return False
    
    def format_card(self, card: List[List[int]]) -> str:
        """Format card for display."""
        header = "  B   I   N   G   O\n"
        rows = []
        for row_idx in range(5):
            row = []
            for col_idx in range(5):
                num = card[col_idx][row_idx]
                if num == 0:
                    row.append("FREE")
                elif num in self.called_numbers:
                    row.append(f"[{num:2d}]")
                else:
                    row.append(f" {num:2d} ")
            rows.append(" ".join(row))
        return header + "\n".join(rows)

# Helper functions for multimedia
def generate_ball_image(number: int, letter: str) -> io.BytesIO:
    """Generate a bingo ball image with the called number."""
    # Create image
    size = 400
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw ball (circle)
    margin = 50
    ball_color = {
        'B': '#FF6B6B',  # Red
        'I': '#4ECDC4',  # Teal
        'N': '#FFE66D',  # Yellow
        'G': '#95E1D3',  # Light green
        'O': '#F38181'   # Pink
    }.get(letter, '#CCCCCC')
    
    draw.ellipse([margin, margin, size-margin, size-margin], fill=ball_color, outline='black', width=5)
    
    # Try to load a font, fall back to default if not available
    try:
        # Try common font locations
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except (IOError, OSError):
        # Fall back to default font if TrueType font not available
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw letter at top
    letter_text = letter
    letter_bbox = draw.textbbox((0, 0), letter_text, font=font_small)
    letter_width = letter_bbox[2] - letter_bbox[0]
    letter_x = (size - letter_width) // 2
    draw.text((letter_x, 80), letter_text, fill='black', font=font_small)
    
    # Draw number in center
    number_text = str(number)
    number_bbox = draw.textbbox((0, 0), number_text, font=font_large)
    number_width = number_bbox[2] - number_bbox[0]
    number_x = (size - number_width) // 2
    draw.text((number_x, 180), number_text, fill='black', font=font_large)
    
    # Save to BytesIO
    bio = io.BytesIO()
    bio.name = f'ball_{letter}_{number}.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

def generate_tts_audio(text: str) -> Optional[io.BytesIO]:
    """Generate text-to-speech audio for the called number.
    
    Note: This is a placeholder. For production, integrate with:
    - Google Cloud Text-to-Speech API
    - Amazon Polly
    - gTTS (Google Text-to-Speech) library
    - Or other TTS service
    
    Returns None for now as TTS requires additional setup.
    """
    # Placeholder - would implement actual TTS here
    # For now, we'll just send the image and text
    return None

# Global game instance
game = BingoGame()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - shows available commands."""
    help_text = (
        "🎲 *Bingo Game Bot* 🎲\n\n"
        "Game Flow Commands:\n"
        "/newgame - Create a new bingo game\n"
        "/card - Get your bingo card and join the game\n"
        "/ready - Mark yourself as ready to play\n"
        "/startcalling - Begin auto-calling numbers\n"
        "/pause - Pause the game\n"
        "/resume - Resume the game\n"
        "/call <number> - Manually call a specific number\n"
        "\n"
        "Player Commands:\n"
        "/lastcall - Replay last called number\n"
        "/check - Check if you won\n"
        "/numbers - View all called numbers\n"
        "/players - View player list\n"
        "/status - View game status and flow state"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def newgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new bingo game (anyone can create)."""
    if game.state != GameState.IDLE:
        await update.message.reply_text(
            f"⚠️ Game already active in state: {game.get_state_description()}\n"
            "Use /endgame to end the current game first."
        )
        return
    
    # Reset and setup new game
    game.reset()
    game.active = True
    game.state = GameState.SETUP
    game.chat_id = update.effective_chat.id
    
    await update.message.reply_text(
        "🎉 *New Bingo Game Created!*\n\n"
        "📝 Game Flow:\n"
        "1. Players join with `/card`\n"
        "2. Players mark ready with `/ready`\n"
        f"3. When {game.min_players}+ players ready, use `/startcalling`\n"
        "4. Numbers will auto-call every 10 seconds\n"
        "5. Use `/pause` and `/resume` to control flow\n\n"
        "Let's play! 🎲",
        parse_mode='Markdown'
    )

async def get_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get or view player's bingo card.
    
    Note: Cards are randomly generated. While the probability of duplicate cards
    is low given ~111 quadrillion possible combinations, duplicates are theoretically
    possible with enough players.
    """
    if not game.active:
        await update.message.reply_text("❌ No active game. Create one with /newgame")
        return
    
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Store player name for display purposes
    is_new_player = user_id not in game.player_names
    if is_new_player:
        # Prefer username, fall back to first_name, then to user_id
        if user.username:
            game.player_names[user_id] = f"@{user.username}"
        elif user.first_name:
            game.player_names[user_id] = user.first_name
        else:
            game.player_names[user_id] = f"User {user_id}"
    
    if user_id not in game.player_cards:
        game.player_cards[user_id] = game.generate_card()
        player_count = len(game.player_cards)
        await update.message.reply_text(
            f"🎴 Your new bingo card:\n\n"
            f"You are player #{player_count}\n"
            f"Use /ready when you're ready to play!"
        )
        
        # Auto-transition to READY state when minimum players join
        if game.state == GameState.SETUP and player_count >= game.min_players:
            game.state = GameState.READY
            await update.message.reply_text(
                f"✅ {player_count} players joined!\n"
                f"Game is READY. Players can mark themselves ready with /ready\n"
                f"Once ready, use /startcalling to begin!"
            )
    else:
        await update.message.reply_text("🎴 Your bingo card:\n")
    
    card_text = f"```\n{game.format_card(game.player_cards[user_id])}\n```"
    await update.message.reply_text(card_text, parse_mode='Markdown')

async def call_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually call a specific number with visual ball image."""
    if not game.active:
        await update.message.reply_text("❌ No active game. Create one with /newgame")
        return
    
    if not context.args:
        await update.message.reply_text("Please provide a number: /call <number>")
        return
    
    try:
        number = int(context.args[0])
        if game.call_number(number):
            # Map number to letter explicitly
            if 1 <= number <= 15:
                letter = 'B'
            elif 16 <= number <= 30:
                letter = 'I'
            elif 31 <= number <= 45:
                letter = 'N'
            elif 46 <= number <= 60:
                letter = 'G'
            else:  # 61-75
                letter = 'O'
            
            # Store last call
            game.last_call = (number, letter)
            
            # Generate and send ball image
            ball_image = generate_ball_image(number, letter)
            await update.message.reply_photo(
                photo=ball_image,
                caption=f"📢 *{letter}-{number}* manually called!\n\nTotal called: {len(game.called_numbers)}/75",
                parse_mode='Markdown'
            )
            
            # Generate and send audio (if available)
            audio = generate_tts_audio(f"{letter} {number}")
            if audio:
                await update.message.reply_voice(voice=audio)
            
        else:
            await update.message.reply_text(
                "❌ Invalid number or already called. Must be 1-75."
            )
    except ValueError:
        await update.message.reply_text("❌ Invalid number format.")

async def check_win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if player has won."""
    if not game.active:
        await update.message.reply_text("❌ No active game.")
        return
    
    user_id = update.effective_user.id
    
    if user_id not in game.player_cards:
        await update.message.reply_text("❌ You don't have a card. Use /card to get one.")
        return
    
    card = game.player_cards[user_id]
    if game.check_win(card):
        await update.message.reply_text(
            "🎉🎊 *BINGO!* 🎊🎉\n\n"
            "Congratulations! You won!",
            parse_mode='Markdown'
        )
        # Show winning card
        card_text = f"```\n{game.format_card(card)}\n```"
        await update.message.reply_text(card_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Not yet! Keep playing.")

async def show_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all called numbers."""
    if not game.active:
        await update.message.reply_text("❌ No active game.")
        return
    
    if not game.called_numbers:
        await update.message.reply_text("No numbers called yet.")
        return
    
    sorted_numbers = sorted(game.called_numbers)
    numbers_text = ", ".join(str(n) for n in sorted_numbers)
    
    await update.message.reply_text(
        f"📋 *Called Numbers* ({len(sorted_numbers)}):\n\n{numbers_text}",
        parse_mode='Markdown'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show game status and flow state."""
    if game.active:
        state_emoji = {
            GameState.SETUP: "📝",
            GameState.READY: "✅",
            GameState.CALLING: "🎲",
            GameState.PAUSED: "⏸️",
            GameState.ENDED: "🏁"
        }
        emoji = state_emoji.get(game.state, "❓")
        
        status_text = (
            f"🎮 *Game Status*\n\n"
            f"State: {emoji} {game.get_state_description()}\n"
            f"Players: {len(game.player_cards)}\n"
            f"Ready: {len(game.player_ready)}/{len(game.player_cards)}\n"
            f"Numbers called: {len(game.called_numbers)}/75\n"
            f"Auto-call interval: {game.auto_call_interval}s\n"
        )
        
        # Add state-specific info
        if game.state == GameState.SETUP:
            status_text += f"\n💡 Waiting for players to join with /card"
        elif game.state == GameState.READY:
            status_text += f"\n💡 Players can mark ready with /ready\n💡 Start with /startcalling"
        elif game.state == GameState.CALLING:
            status_text += f"\n💡 Auto-calling in progress\n💡 Use /pause to pause"
        elif game.state == GameState.PAUSED:
            status_text += f"\n💡 Game paused\n💡 Use /resume to continue"
            
    else:
        status_text = "🎮 *Game Status*\n\nNo active game.\n\nUse /newgame to create one!"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of players and their card counts."""
    if not game.active:
        await update.message.reply_text("❌ No active game.")
        return
    
    if not game.player_cards:
        await update.message.reply_text("👥 No players have joined yet.\n\nUse /card to get your bingo card!")
        return
    
    # Build player list
    # Note: Currently the system stores one card per user_id in player_cards dict
    # If multi-card support is added, this would need to count cards differently
    player_list = []
    for user_id in sorted(game.player_cards.keys()):
        player_name = game.player_names.get(user_id, f"User {user_id}")
        # Each user_id maps to one card in the current implementation
        card_count = 1
        player_list.append(f"• {player_name}: {card_count} card")
    
    players_text = (
        f"👥 *Players in Game* ({len(game.player_cards)}):\n\n"
        + "\n".join(player_list)
    )
    
    await update.message.reply_text(players_text, parse_mode='Markdown')

async def player_ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark player as ready to start the game."""
    if not game.active:
        await update.message.reply_text("❌ No active game. Create one with /newgame")
        return
    
    user_id = update.effective_user.id
    
    if user_id not in game.player_cards:
        await update.message.reply_text("❌ You need a card first! Use /card to join.")
        return
    
    if user_id in game.player_ready:
        await update.message.reply_text("✅ You're already marked as ready!")
        return
    
    game.player_ready.add(user_id)
    player_name = game.player_names.get(user_id, f"User {user_id}")
    
    ready_count = len(game.player_ready)
    total_count = len(game.player_cards)
    
    await update.message.reply_text(
        f"✅ {player_name} is ready!\n\n"
        f"Ready: {ready_count}/{total_count} players\n\n"
        + (f"🎮 All players ready! Use /startcalling to begin!" if ready_count == total_count else
           f"Waiting for {total_count - ready_count} more player(s)...")
    )

async def start_calling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start auto-calling numbers at regular intervals."""
    if not game.active:
        await update.message.reply_text("❌ No active game.")
        return
    
    if game.state == GameState.CALLING:
        await update.message.reply_text("⚠️ Already calling numbers! Use /pause to pause.")
        return
    
    if game.state not in [GameState.READY, GameState.PAUSED]:
        await update.message.reply_text(
            f"⚠️ Cannot start calling from state: {game.get_state_description()}"
        )
        return
    
    if len(game.player_ready) < game.min_players:
        await update.message.reply_text(
            f"⚠️ Need at least {game.min_players} ready player(s). "
            f"Currently {len(game.player_ready)} ready.\n"
            f"Players use /ready to mark themselves ready!"
        )
        return
    
    game.state = GameState.CALLING
    
    # Start auto-calling task
    app = context.application
    game.auto_call_task = asyncio.create_task(auto_call_loop(app.bot))
    
    await update.message.reply_text(
        f"🎲 *Game Started!*\n\n"
        f"Auto-calling numbers every {game.auto_call_interval} seconds.\n"
        f"Use /pause to pause the game.",
        parse_mode='Markdown'
    )

async def pause_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pause the game."""
    if not game.active:
        await update.message.reply_text("❌ No active game.")
        return
    
    if game.state != GameState.CALLING:
        await update.message.reply_text(
            f"⚠️ Game is not calling. Current state: {game.get_state_description()}"
        )
        return
    
    game.state = GameState.PAUSED
    if game.auto_call_task and not game.auto_call_task.done():
        game.auto_call_task.cancel()
    
    await update.message.reply_text(
        "⏸️ *Game Paused*\n\nUse /resume to continue.",
        parse_mode='Markdown'
    )

async def resume_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resume the paused game."""
    if not game.active:
        await update.message.reply_text("❌ No active game.")
        return
    
    if game.state != GameState.PAUSED:
        await update.message.reply_text(
            f"⚠️ Game is not paused. Current state: {game.get_state_description()}"
        )
        return
    
    game.state = GameState.CALLING
    
    # Restart auto-calling
    app = context.application
    game.auto_call_task = asyncio.create_task(auto_call_loop(app.bot))
    
    await update.message.reply_text(
        "▶️ *Game Resumed*\n\nContinuing auto-calls.",
        parse_mode='Markdown'
    )

async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End the current game."""
    if not game.active:
        await update.message.reply_text("❌ No active game.")
        return
    
    game.state = GameState.ENDED
    if game.auto_call_task and not game.auto_call_task.done():
        game.auto_call_task.cancel()
    
    summary = (
        f"🏁 *Game Ended*\n\n"
        f"Players: {len(game.player_cards)}\n"
        f"Numbers called: {len(game.called_numbers)}/75\n\n"
        f"Thanks for playing! Use /newgame to start another."
    )
    
    await update.message.reply_text(summary, parse_mode='Markdown')
    game.reset()

async def auto_call_loop(bot):
    """Background task that auto-calls numbers at intervals."""
    try:
        while game.state == GameState.CALLING:
            # Get next number
            number = game.get_next_number()
            if number is None:
                # All numbers called
                game.state = GameState.ENDED
                if game.chat_id:
                    await bot.send_message(
                        chat_id=game.chat_id,
                        text="🎊 All 75 numbers have been called! Game complete!",
                        parse_mode='Markdown'
                    )
                break
            
            # Call the number
            game.call_number(number)
            
            # Map number to letter
            if 1 <= number <= 15:
                letter = 'B'
            elif 16 <= number <= 30:
                letter = 'I'
            elif 31 <= number <= 45:
                letter = 'N'
            elif 46 <= number <= 60:
                letter = 'G'
            else:  # 61-75
                letter = 'O'
            
            game.last_call = (number, letter)
            
            # Send to chat
            if game.chat_id:
                ball_image = generate_ball_image(number, letter)
                await bot.send_photo(
                    chat_id=game.chat_id,
                    photo=ball_image,
                    caption=f"📢 *{letter}-{number}* called!\n\nTotal: {len(game.called_numbers)}/75",
                    parse_mode='Markdown'
                )
            
            # Wait for next call
            await asyncio.sleep(game.auto_call_interval)
            
    except asyncio.CancelledError:
        # Task was cancelled (paused or stopped)
        pass

async def lastcall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the last called number with its ball image."""
    if not game.active:
        await update.message.reply_text("❌ No active game.")
        return
    
    if not game.last_call:
        await update.message.reply_text("🔇 No numbers have been called yet.")
        return
    
    number, letter = game.last_call
    
    # Generate and send ball image
    ball_image = generate_ball_image(number, letter)
    await update.message.reply_photo(
        photo=ball_image,
        caption=f"🔊 Last call: *{letter}-{number}*\n\nTotal called: {len(game.called_numbers)}/75",
        parse_mode='Markdown'
    )
    
    # Generate and send audio (if available)
    audio = generate_tts_audio(f"{letter} {number}")
    if audio:
        await update.message.reply_voice(voice=audio)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newgame", newgame))
    application.add_handler(CommandHandler("card", get_card))
    application.add_handler(CommandHandler("ready", player_ready))
    application.add_handler(CommandHandler("startcalling", start_calling))
    application.add_handler(CommandHandler("pause", pause_game))
    application.add_handler(CommandHandler("resume", resume_game))
    application.add_handler(CommandHandler("endgame", end_game))
    application.add_handler(CommandHandler("call", call_number))
    application.add_handler(CommandHandler("lastcall", lastcall))
    application.add_handler(CommandHandler("check", check_win))
    application.add_handler(CommandHandler("numbers", show_numbers))
    application.add_handler(CommandHandler("players", players))
    application.add_handler(CommandHandler("status", status))

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()