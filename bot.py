import asyncio
import random
import threading
import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8864441821:AAEvsjEETpSNggfVVJONvjaCoUUe-drg0mA"
OWNER_ID = 1869599187

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Game State
GAME_STATE = {'mode': 'random', 'roll_mode': 'normal', 'custom_cards_1': [], 'custom_cards_2': []}
SUITS = ['♠️', '♥️', '♣️', '♦️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# --- HELPER FUNCTIONS ---
def get_strong_hand():
    hand_type = random.choice(['trail', 'pure_seq', 'color'])
    if hand_type == 'trail':
        rank = random.choice(['J', 'Q', 'K', 'A'])
        suits = random.sample(SUITS, 3)
        return [f"{rank}{s}" for s in suits]
    elif hand_type == 'pure_seq':
        suit = random.choice(SUITS)
        return [f"A{suit}", f"K{suit}", f"Q{suit}"]
    else:
        suit = random.choice(SUITS)
        ranks = random.sample(['10', 'J', 'Q', 'K', 'A'], 3)
        return [f"{r}{suit}" for r in ranks]

def get_weak_hand():
    ranks = random.sample(['2', '3', '4', '5', '7', '8'], 3)
    suits = random.sample(SUITS, 3)
    return [f"{r}{s}" for r, s in zip(ranks, suits)]

# --- AUTH: Owner + Group Admins ---
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == OWNER_ID: return True
    if update.effective_chat.type == 'private': return False
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if member.status in ['administrator', 'creator']: return True
    except: pass
    return False

# --- COMMANDS ---
async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context) or not context.args: return
    player = context.args[0]
    
    if player == "1":
        if GAME_STATE['mode'] == 'custom_win11': cards = GAME_STATE['custom_cards_1']
        elif GAME_STATE['mode'] == 'win11': cards = get_strong_hand()
        elif GAME_STATE['mode'] in ['win22', 'custom_win22']: cards = get_weak_hand()
        else: cards = random.sample([f"{r}{s}" for r in RANKS for s in SUITS], 3)
    else:
        if GAME_STATE['mode'] == 'custom_win22': cards = GAME_STATE['custom_cards_2']
        elif GAME_STATE['mode'] == 'win22': cards = get_strong_hand()
        elif GAME_STATE['mode'] in ['win11', 'custom_win11']: cards = get_weak_hand()
        else: cards = random.sample([f"{r}{s}" for r in RANKS for s in SUITS], 3)

    for card in cards:
        await update.message.reply_text(f"{player} cards {card}")
        await asyncio.sleep(0.3)

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context): return
    if GAME_STATE['roll_mode'] == 'odd_bias':
        res = random.choices([1, 3, 5, 2, 4, 6], weights=[23, 23, 23, 10, 10, 11])[0]
    elif GAME_STATE['roll_mode'] == 'even_bias':
        res = random.choices([2, 4, 6, 1, 3, 5], weights=[23, 23, 23, 10, 10, 11])[0]
    else:
        res = random.randint(1, 6)
    await update.message.reply_text(str(res))

async def win_cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context): return
    cmd = update.message.text
    if "/win11" in cmd:
        if len(context.args) == 3:
            GAME_STATE['mode'] = 'custom_win11'; GAME_STATE['custom_cards_1'] = context.args
        else: GAME_STATE['mode'] = 'win11'
    else:
        if len(context.args) == 3:
            GAME_STATE['mode'] = 'custom_win22'; GAME_STATE['custom_cards_2'] = context.args
        else: GAME_STATE['mode'] = 'win22'
    await update.message.reply_text("✅ Mode Updated.")

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context): return
    GAME_STATE.update({'mode': 'random', 'roll_mode': 'normal'})
    await update.message.reply_text("✅ Random Mode Active.")

async def bias_cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context): return
    GAME_STATE['roll_mode'] = 'odd_bias' if "33" in update.message.text else 'even_bias'
    await update.message.reply_text(f"✅ {'Odd' if '33' in update.message.text else 'Even'} Bias Active.")

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handlers([
        CommandHandler("show", show_command), CommandHandler("roll", roll_command),
        CommandHandler("win11", win_cmds), CommandHandler("win22", win_cmds),
        CommandHandler("33", bias_cmds), CommandHandler("44", bias_cmds),
        CommandHandler("45", reset_cmd), CommandHandler("sps", lambda u, c: u.message.reply_text(random.choice(['Stone 🪨', 'Paper 📄', 'Scissors ✂️'])))
    ])
    app.run_polling()

if __name__ == '__main__': main()
