Import asyncio
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
def home(): 
    return "Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_server)
    t.daemon = True 
    t.start()

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


Is code me add krdo aur saath me baaki ka code as it is hi rehna chahiye smjhe aap
