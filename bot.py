import asyncio
import random
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler

# --- CONFIGURATION ---
TOKEN = "YOUR_BOT_TOKEN_HERE" # Apna Token daalein
OWNER_ID = 1869599187

# --- FLASK SERVER (24/7 ALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_server():
    app.run(host="0.0.0.0", port=8080)

# --- GAME STATE ---
GAME_STATE = {
    'mode': 'random',       
    'roll_mode': 'normal',   
    'custom_cards_1': [],
    'custom_cards_2': []
}

SUITS = ['♠️', '♥️', '♣️', '♦️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# --- HELPER FUNCTIONS ---
def get_strong_hand():
    # Ab sirf Trail nahi, balki Pure Sequence aur Color bhi aayega
    hand_type = random.choice(['trail', 'pure_seq', 'color'])
    if hand_type == 'trail':
        rank = random.choice(['J', 'Q', 'K', 'A'])
        suits = random.sample(SUITS, 3)
        return [f"{rank}{s}" for s in suits]
    elif hand_type == 'pure_seq':
        suit = random.choice(SUITS)
        return [f"A{suit}", f"K{suit}", f"Q{suit}"]
    else: # Color
        suit = random.choice(SUITS)
        ranks = random.sample(['10', 'J', 'Q', 'K', 'A'], 3)
        return [f"{r}{suit}" for r in ranks]

def get_weak_hand():
    ranks = random.sample(['2', '3', '4', '5', '7', '8'], 3)
    suits = random.sample(SUITS, 3)
    return [f"{r}{s}" for r, s in zip(ranks, suits)]

def get_random_hand():
    deck = [f"{r}{s}" for r in RANKS for s in SUITS]
    return random.sample(deck, 3)

# --- AUTHENTICATION & BOT ADMIN CHECK ---
def is_owner(update: Update) -> bool:
    return update.effective_user.id == OWNER_ID

async def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == 'private': return True
    try:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if bot_member.status == 'administrator': return True
    except: pass
    return False

# --- COMMAND HANDLERS ---
async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not await is_bot_admin(update, context): return

    if not context.args:
        await update.message.reply_text("⚠️ Please pass a username also.")
        return

    player = context.args[0]
    
    if player == "1":
        if GAME_STATE['mode'] == 'custom_win11': cards = GAME_STATE['custom_cards_1']
        elif GAME_STATE['mode'] == 'win11': cards = get_strong_hand()
        elif GAME_STATE['mode'] in ['win22', 'custom_win22']: cards = get_weak_hand()
        else: cards = get_random_hand()
            
    elif player == "2":
        if GAME_STATE['mode'] == 'custom_win22': cards = GAME_STATE['custom_cards_2']
        elif GAME_STATE['mode'] == 'win22': cards = get_strong_hand()
        elif GAME_STATE['mode'] in ['win11', 'custom_win11']: cards = get_weak_hand()
        else: cards = get_random_hand()
    else:
        return

    for card in cards:
        await update.message.reply_text(f"{player} cards {card}")
        await asyncio.sleep(0.3) 

async def cmd_111(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not await is_bot_admin(update, context): return
    GAME_STATE['roll_mode'] = 'odd'
    await update.message.reply_text("🚫You should try /roll")

async def cmd_222(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not await is_bot_admin(update, context): return
    GAME_STATE['roll_mode'] = 'even'
    await update.message.reply_text("🚫Try /roll")

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not await is_bot_admin(update, context): return
    
    if GAME_STATE['roll_mode'] == 'odd': res = random.choice([1, 3, 5])
    elif GAME_STATE['roll_mode'] == 'even': res = random.choice([2, 4, 6])
    else: res = random.randint(1, 6)
        
    await update.message.reply_text(str(res))

# --- WIN COMMANDS WITH CUSTOM CARD SUPPORT ---
async def win11_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not await is_bot_admin(update, context): return
    
    # Check if 3 cards are provided manually
    if len(context.args) == 3:
        GAME_STATE['mode'] = 'custom_win11'
        GAME_STATE['custom_cards_1'] = [context.args[0], context.args[1], context.args[2]]
        await update.message.reply_text(f"✅ Custom Mode: Cards set to {context.args[0]}, {context.args[1]}, {context.args[2]}")
    else:
        GAME_STATE['mode'] = 'win11'
        await update.message.reply_text("✅ Mode Changed: Win 11 Active (Random Heavy Cards)")

async def win22_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not await is_bot_admin(update, context): return
    
    if len(context.args) == 3:
        GAME_STATE['mode'] = 'custom_win22'
        GAME_STATE['custom_cards_2'] = [context.args[0], context.args[1], context.args[2]]
        await update.message.reply_text(f"✅ Custom Mode: Cards set to {context.args[0]}, {context.args[1]}, {context.args[2]}")
    else:
        GAME_STATE['mode'] = 'win22'
        await update.message.reply_text("✅ Mode Changed: Win 22 Active (Random Heavy Cards)")

async def mode45_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not await is_bot_admin(update, context): return
    
    GAME_STATE['mode'] = 'random'
    GAME_STATE['roll_mode'] = 'normal'
    await update.message.reply_text("✅ Mode Changed: Random Mode Active")

async def sps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not await is_bot_admin(update, context): return
    await update.message.reply_text(random.choice(['Stone', 'Paper', 'Scissors']))

# --- GROUP JOIN/LEAVE LOGIC ---
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    chat_id = update.effective_chat.id
    if result.new_chat_member.user.id == context.bot.id:
        if result.from_user.id != OWNER_ID:
            await context.bot.send_message(chat_id, "⚠️ I can only be added by my Owner. Leaving chat.")
            await context.bot.leave_chat(chat_id)
            return

    if result.new_chat_member.user.id == OWNER_ID and result.new_chat_member.status in ['left', 'kicked']:
        await context.bot.leave_chat(chat_id)

# --- MAIN SETUP ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("show", show_command))
    application.add_handler(CommandHandler("roll", roll_command))
    application.add_handler(CommandHandler("111", cmd_111))
    application.add_handler(CommandHandler("222", cmd_222))
    application.add_handler(CommandHandler("win11", win11_command))
    application.add_handler(CommandHandler("win22", win22_command))
    application.add_handler(CommandHandler("45", mode45_command))
    application.add_handler(CommandHandler("sps", sps_command))
    
    application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.CHAT_MEMBER))
    application.run_polling()

if __name__ == '__main__':
    main()
