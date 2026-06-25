import asyncio
import random
import threading
import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8864441821:AAHhRh8bjA6H7pYnfDYpvc_3OZNBDTZD8HY"
OWNER_ID = 1869599187

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Game State
GAME_STATE = {
    'mode': 'random', 
    'roll_mode': 'normal', 
    'custom_cards_1': [], 
    'custom_cards_2': [],
    'prepared_hands': None,
    'shown_players': set()
}
SUITS = ['♠️', '♥️', '♣️', '♦️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_MAP = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':11, 'Q':12, 'K':13, 'A':14}

# --- TEEN PATTI REAL EVALUATOR ---
def evaluate_hand(cards):
    """Yeh function har card ka exact score nikalega (Trail > Pure Seq > Seq > Color > Pair > High Card)"""
    parsed = []
    for c in cards:
        for s in SUITS:
            if s in c:
                rank_str = c.replace(s, '')
                parsed.append((RANK_MAP[rank_str], s))
                break
                
    ranks = sorted([p[0] for p in parsed], reverse=True)
    suits = [p[1] for p in parsed]
    
    is_flush = len(set(suits)) == 1
    is_straight = (ranks[0] - ranks[1] == 1 and ranks[1] - ranks[2] == 1) or (ranks == [14, 3, 2])
    is_trail = len(set(ranks)) == 1
    is_pair = len(set(ranks)) == 2

    if is_trail: return 600000 + ranks[0]
    elif is_straight and is_flush: return 500000 + (3 if ranks == [14, 3, 2] else ranks[0])
    elif is_straight: return 400000 + (3 if ranks == [14, 3, 2] else ranks[0])
    elif is_flush: return 300000 + ranks[0]*400 + ranks[1]*20 + ranks[2]
    elif is_pair:
        pair_rank = [r for r in set(ranks) if ranks.count(r) == 2][0]
        kicker = [r for r in ranks if r != pair_rank][0]
        return 200000 + pair_rank*400 + kicker
    else: return 100000 + ranks[0]*400 + ranks[1]*20 + ranks[2]

def get_round_hands(mode):
    """52 cards ki deck se do 100% natural random hands nikalega aur power ke hisaab se baantega"""
    deck = [f"{r}{s}" for r in RANKS for s in SUITS]
    
    while True:
        sampled = random.sample(deck, 6)
        hand1, hand2 = sampled[:3], sampled[3:]
        
        score1 = evaluate_hand(hand1)
        score2 = evaluate_hand(hand2)
        
        if score1 != score2: # Draw na ho tabhi aage badho
            break

    # Bada aur chota hand alag karo
    if score1 > score2:
        high_hand, low_hand = hand1, hand2
    else:
        high_hand, low_hand = hand2, hand1
        
    # Jeetne wale ko high_hand de do mode ke hisaab se
    if mode == 'win11':
        return {'1': high_hand, '2': low_hand}
    else: # win22
        return {'1': low_hand, '2': high_hand}

# --- AUTH: Owner + Admin + Auto-Leave Logic ---
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Private chat mein sirf owner use kar sakta hai
    if update.effective_chat.type == 'private': 
        return user_id == OWNER_ID

    # Agar bot group mein hai, toh check karo ki Owner (aap) group mein ho ya nahi
    if update.effective_chat.type in ['group', 'supergroup']:
        try:
            owner = await context.bot.get_chat_member(chat_id, OWNER_ID)
            if owner.status in ['left', 'kicked']:
                await context.bot.send_message(chat_id, "🚫 Mera Owner is group mein nahi hai! Main yeh group chhod raha hoon.")
                await context.bot.leave_chat(chat_id)
                return False
        except Exception:
            # Agar API error de ya owner exist hi na kare group mein
            await context.bot.send_message(chat_id, "🚫 Mera Owner is group mein nahi hai! Main yeh group chhod raha hoon.")
            await context.bot.leave_chat(chat_id)
            return False

    # Owner group mein hai, ab check karo ki command dene wala admin hai ya nahi
    if user_id == OWNER_ID: return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']: return True
    except: 
        pass
        
    return False

# --- COMMANDS ---
async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context) or not context.args: return
    player = context.args[0]
    
    if GAME_STATE['mode'] == 'custom_win11' and player == "1":
        cards = GAME_STATE['custom_cards_1']
    elif GAME_STATE['mode'] == 'custom_win22' and player == "2":
        cards = GAME_STATE['custom_cards_2']
    elif GAME_STATE['mode'] in ['win11', 'win22']:
        if GAME_STATE['prepared_hands'] is None:
            GAME_STATE['prepared_hands'] = get_round_hands(GAME_STATE['mode'])
        
        cards = GAME_STATE['prepared_hands'].get(player, random.sample([f"{r}{s}" for r in RANKS for s in SUITS], 3))
        GAME_STATE['shown_players'].add(player)
        
        if "1" in GAME_STATE['shown_players'] and "2" in GAME_STATE['shown_players']:
            GAME_STATE['prepared_hands'] = None
            GAME_STATE['shown_players'] = set()
    else:
        cards = random.sample([f"{r}{s}" for r in RANKS for s in SUITS], 3)

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
    
    GAME_STATE['prepared_hands'] = None
    GAME_STATE['shown_players'] = set()
    
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
    GAME_STATE.update({'mode': 'random', 'roll_mode': 'normal', 'prepared_hands': None, 'shown_players': set()})
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
        CommandHandler("45", reset_cmd), CommandHandler("sps", lambda u, c: u.message.reply_text(random.choice(['Stone', 'Paper', 'Scissors'])))
    ])
    app.run_polling()

if __name__ == '__main__': main()
