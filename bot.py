import asyncio
import random
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler

# --- CONFIGURATION ---
TOKEN = "YOUR_BOT_TOKEN_HERE" # Apna bot token yahan daalein
OWNER_ID = 1869599187

# --- FLASK SERVER (24/7 ALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_server():
    app.run(host="0.0.0.0", port=8080)

# --- GAME STATE ---
# mode can be: 'random', 'win11', 'win22'
GAME_STATE = {'mode': 'random'}

SUITS = ['♠️', '♥️', '♣️', '♦️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# --- HELPER FUNCTIONS ---
def get_strong_hand():
    # Returns a strong hand (Trail/Trio)
    rank = random.choice(['J', 'Q', 'K', 'A'])
    suits = random.sample(SUITS, 3)
    return [f"{rank}{s}" for s in suits]

def get_weak_hand():
    # Returns a weak hand (Low High-Card)
    ranks = random.sample(['2', '3', '4', '5', '7', '8'], 3)
    suits = random.sample(SUITS, 3)
    return [f"{r}{s}" for r, s in zip(ranks, suits)]

def get_random_hand():
    # Returns a pure random hand
    deck = [f"{r}{s}" for r in RANKS for s in SUITS]
    return random.sample(deck, 3)

# --- AUTHENTICATION ---
def is_owner(update: Update) -> bool:
    return update.effective_user.id == OWNER_ID

# --- COMMAND HANDLERS ---
async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please pass a username also.")
        return

    player = context.args[0]
    
    if player == "1":
        if GAME_STATE['mode'] == 'win11':
            cards = get_strong_hand()
        elif GAME_STATE['mode'] == 'win22':
            cards = get_weak_hand()
        else:
            cards = get_random_hand()
            
        reply_text = f"1 cards {cards[0]}\n1 cards {cards[1]}\n1 cards {cards[2]}"
        await update.message.reply_text(reply_text)
        
    elif player == "2":
        if GAME_STATE['mode'] == 'win22':
            cards = get_strong_hand()
        elif GAME_STATE['mode'] == 'win11':
            cards = get_weak_hand()
        else:
            cards = get_random_hand()
            
        reply_text = f"2 cards {cards[0]}\n2 cards {cards[1]}\n2 cards {cards[2]}"
        await update.message.reply_text(reply_text)

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(str(random.randint(1, 6)))

async def cmd_111(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(str(random.choice([1, 3, 5])))

async def cmd_222(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(str(random.choice([2, 4, 6])))

async def win11_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    GAME_STATE['mode'] = 'win11'
    await update.message.reply_text("✅ Mode Changed: Player 1 will now get heavy cards (Winner mode).")

async def win22_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    GAME_STATE['mode'] = 'win22'
    await update.message.reply_text("✅ Mode Changed: Player 2 will now get heavy cards (Winner mode).")

async def mode45_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    GAME_STATE['mode'] = 'random'
    await update.message.reply_text("✅ Mode Changed: Random cards will be generated now.")

async def sps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(random.choice(['Stone 🪨', 'Paper 📄', 'Scissors ✂️']))

# --- GROUP JOIN/LEAVE LOGIC ---
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    chat_id = update.effective_chat.id
    
    # Check if bot was added to a group
    if result.new_chat_member.user.id == context.bot.id:
        if result.from_user.id != OWNER_ID:
            await context.bot.send_message(chat_id, "⚠️ I can only be added by my Owner. Leaving chat.")
            await context.bot.leave_chat(chat_id)
            return

    # Check if the Owner leaves the group
    if result.new_chat_member.user.id == OWNER_ID and result.new_chat_member.status in ['left', 'kicked']:
        await context.bot.leave_chat(chat_id)

# --- MAIN SETUP ---
def main():
    # Start Flask in a background thread for UptimeRobot
    threading.Thread(target=run_server, daemon=True).start()

    # Initialize Bot
    application = Application.builder().token(TOKEN).build()

    # Add Command Handlers
    application.add_handler(CommandHandler("show", show_command))
    application.add_handler(CommandHandler("roll", roll_command))
    application.add_handler(CommandHandler("111", cmd_111))
    application.add_handler(CommandHandler("222", cmd_222))
    application.add_handler(CommandHandler("win11", win11_command))
    application.add_handler(CommandHandler("win22", win22_command))
    application.add_handler(CommandHandler("45", mode45_command))
    application.add_handler(CommandHandler("sps", sps_command))

    # Add Chat Member Handler for Anti-Add and Auto-Leave
    application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.CHAT_MEMBER))

    # Run polling
    application.run_polling()

if __name__ == '__main__':
    main()
