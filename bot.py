import asyncio
import random
import threading
import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler

TOKEN = "8864441821:AAEvsjEETpSNggfVVJONvjaCoUUe-drg0mA"
OWNER_ID = 1869599187

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"

def run_server():
    # Render ke according port dynamically set hoga
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

GAME_STATE = {'mode': 'random', 'roll_mode': 'normal', 'custom_cards_1': [], 'custom_cards_2': []}
SUITS = ['♠️', '♥️', '♣️', '♦️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

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

def get_random_hand():
    deck = [f"{r}{s}" for r in RANKS for s in SUITS]
    return random.sample(deck, 3)

def is_owner(update: Update) -> bool: return update.effective_user.id == OWNER_ID

async def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == 'private': return True
    try:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if bot_member.status == 'administrator': return True
    except: pass
    return False

async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or not await is_bot_admin(update, context): return
    if not context.args: return
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
    else: return
    for card in cards:
        await update.message.reply_text(f"{player} cards {card}")
        await asyncio.sleep(0.3)

async def cmd_111(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or not await is_bot_admin(update, context): return
    GAME_STATE['roll_mode'] = 'odd'
    await update.message.reply_text("🚫You should try /roll")

async def cmd_222(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or not await is_bot_admin(update, context): return
    GAME_STATE['roll_mode'] = 'even'
    await update.message.reply_text("🚫Try /roll")

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or not await is_bot_admin(update, context): return
    if GAME_STATE['roll_mode'] == 'odd': res = random.choice([1, 3, 5])
    elif GAME_STATE['roll_mode'] == 'even': res = random.choice([2, 4, 6])
    else: res = random.randint(1, 6)
    await update.message.reply_text(str(res))

async def win11_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or not await is_bot_admin(update, context): return
    if len(context.args) == 3:
        GAME_STATE['mode'] = 'custom_win11'
        GAME_STATE['custom_cards_1'] = context.args
        await update.message.reply_text("✅ Custom Mode Win11 set.")
    else:
        GAME_STATE['mode'] = 'win11'
        await update.message.reply_text("✅ Win11 Active.")

async def win22_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or not await is_bot_admin(update, context): return
    if len(context.args) == 3:
        GAME_STATE['mode'] = 'custom_win22'
        GAME_STATE['custom_cards_2'] = context.args
        await update.message.reply_text("✅ Custom Mode Win22 set.")
    else:
        GAME_STATE['mode'] = 'win22'
        await update.message.reply_text("✅ Win22 Active.")

async def mode45_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or not await is_bot_admin(update, context): return
    GAME_STATE['mode'] = 'random'
    GAME_STATE['roll_mode'] = 'normal'
    await update.message.reply_text("✅ Random Mode Active.")

async def main():
    threading.Thread(target=run_server, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handlers([
        CommandHandler("show", show_command), CommandHandler("roll", roll_command),
        CommandHandler("111", cmd_111), CommandHandler("222", cmd_222),
        CommandHandler("win11", win11_command), CommandHandler("win22", win22_command),
        CommandHandler("45", mode45_command)
    ])
    application.run_polling()

if __name__ == '__main__': asyncio.run(main())
