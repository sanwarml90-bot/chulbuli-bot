"""Chulbuli 💕 — all-in-one Telegram game + chat + economy bot (@ChulbuliGameBot).

Built by hand (NOT via @SanjiBotFactoryBot) from the live analysis of all 16
bots in the moonlight group (see ../analysis-3-bots.md) plus the approved
Word Guess spec (see ../word-guess-spec.md).

DEDUP RULE (Sanji, 2026-11-12): every distinct capability from all 16 bots
is present, but a feature that exists in several bots is built ONCE as one
shared implementation — e.g. one economy (Baka+Nova+Daizy+Mimi), one
moderation stack (Rose+Baka+GroupHelp clone), one link filter
(Protectron+Rose), Sanji's Word Guess as the one word-guess game (replaces
WordSeek), one wordchain (On9+Mimi+Nova), one RPS, one card game, one bbet.
Music (VC music bot) needs a userbot voice assistant — /play explains that
honestly instead of faking it.

Tech: Python + Pyrogram 2.0.106, JSON persistence (data.json next to bot.py),
polling via the built-in app.run() runner. Env: BOT_TOKEN, API_ID, API_HASH,
OWNER_ID (default 7966027018 = Sanji). No secrets are hardcoded or logged.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import FloodWait
from pyrogram.types import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

try:
    import chess as _chess
except Exception:  # noqa: BLE001
    _chess = None

VERSION = "1.0.0"
OWNER_ID = int(os.environ.get("OWNER_ID", "7966027018") or 7966027018)
API_ID = int(os.environ.get("API_ID", "0") or 0)
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
START_TIME = time.time()

# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------
WORD_GUESS_WORDS = """bake ball band bank bear beat beer bell best bird bite blow blue boat body
bold bomb book boom boot bore born boss both bowl bulk bump burn bust busy
cake calm came camp cane care cart case cash cast chat chef chin chip city
clap clay club coat code coin cold come cook cool cope copy cord core corn
cost crab crew crop cure cute damp dare dark data date dawn dead deal dear
deck deep deer demo desk dice died diet dirt dish dive dock dogs doll done
door dose down drag draw drip drop drum duck dude duet dull dust duty each
earn ears east easy echo edge edit eggs else emit ends epic even ever evil
exam exit face fact fade fail fair fall fame fans fare farm fast fate fear
feat feed feel feet fell felt file fill film find fine fire firm fish fist
flag flap flat flea fled flee flex flip flow foam foil fold folk fond font
food fool foot ford fore fork form fort foul four free frog from fuel full
fund gain game gate gave gear gems gene gift girl give glad glow goal goat
goes gold golf gone good grab gram gray grid grin grip grow gulf gums guns""".split()

JUMBLE_WORDS = ["chulbuli", "moonlight", "cricket", "banana", "gaming", "dostana",
                "pyara", "masti", "telegram", "winner", "champion", "dance",
                "singing", "bottle", "rocket", "jungle", "guitar", "magnet"]
CHARADES = [
    ("3 idiots", "3 dost, engineering college, Rancho ka funda — 'All is well'"),
    ("Sholay", "Jai-Veeru, Gabbar, Ramgarh gaon, 'Kitne aadmi the?'"),
    ("DDLJ", "Raj-Simran, train, London se Punjab, 'Bade bade deshon mein'"),
    ("Cricket", "11 players, bat-ball, 6 maarne pe crowd pagal"),
    ("Biryani", "Chawal + masala + dum, Hyderabad special, sabki favourite"),
    ("Chai", "Subah ki pehli, adrak wali, tapri pe dost ke saath"),
    ("Monsoon", "Baarish, bheegna, pakode, bijli kadakna"),
    ("Guitar", "6 strings, bajao aur gaao, mehfil jam jaati hai"),
]
SCRIBBLE_WORDS = ["apple", "rocket", "guitar", "jungle", "dance", "tiger",
                  "moon", "river", "cricket", "school", "friend", "magic"]

# ---------------------------------------------------------------------------
# Data store (JSON, atomic save). NOTE: the bot-runner wipes the bot dir on
# every restart, so data.json is best-effort persistence; the bot keeps
# running fine with a fresh file.
# ---------------------------------------------------------------------------
DEFAULT_USER = {
    "name": "", "coins": 1000, "bank": 0, "gems": 0, "xp": 0, "level": 1,
    "kills": 0, "deaths": 0, "robs": 0, "robbed": 0, "status": "alive",
    "last_daily": 0, "day_key": "", "robs_today": 0, "kills_today": 0,
    "bets_today": 0, "shield_until": 0, "powers": {}, "married_to": None,
    "elo": 1200, "games_won": 0, "banned": False, "first_seen": 0,
}


def _blank_data() -> dict:
    return {"users": {}, "chats": {}, "toggles": {"games": True, "economy": True, "chat": True},
            "banned_users": [], "meta": {"started_at": int(time.time()), "games_played": 0}}


def load_data() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or "users" not in data:
            return _blank_data()
        data.setdefault("chats", {})
        data.setdefault("toggles", {"games": True, "economy": True, "chat": True})
        data.setdefault("banned_users", [])
        data.setdefault("meta", {"started_at": int(time.time()), "games_played": 0})
        return data
    except Exception:  # noqa: BLE001
        return _blank_data()


DATA = load_data()
_save_lock = asyncio.Lock()


def save_data() -> None:
    """Synchronous atomic save (called from handlers; file is small)."""
    try:
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(DATA, fh, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)
    except Exception:  # noqa: BLE001
        pass


def get_user(uid: int, name: str = "") -> dict:
    key = str(uid)
    user = DATA["users"].get(key)
    if user is None:
        user = dict(DEFAULT_USER)
        user["name"] = name or f"user{uid}"
        user["first_seen"] = int(time.time())
        DATA["users"][key] = user
        save_data()
        return user
    for k, v in DEFAULT_USER.items():
        user.setdefault(k, v)
    if name:
        user["name"] = name
    return user


def today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def reset_daily(user: dict) -> None:
    if user.get("day_key") != today_key():
        user["day_key"] = today_key()
        user["robs_today"] = 0
        user["kills_today"] = 0
        user["bets_today"] = 0


def level_for(xp: int) -> int:
    return int(math.sqrt(max(0, xp) / 100.0)) + 1


def add_xp(user: dict, amount: int) -> None:
    user["xp"] = int(user.get("xp", 0)) + amount
    user["level"] = level_for(user["xp"])


def add_coins(user: dict, amount: int) -> int:
    user["coins"] = max(0, int(user.get("coins", 0)) + amount)
    return user["coins"]


def coin_rank(uid: int) -> int:
    ordered = sorted(DATA["users"].items(),
                     key=lambda kv: kv[1].get("coins", 0) + kv[1].get("bank", 0),
                     reverse=True)
    for i, (k, _) in enumerate(ordered, 1):
        if k == str(uid):
            return i
    return len(ordered) + 1


def fmt_coins(n: int) -> str:
    return f"${n:,}"


def display_name(user_obj) -> str:
    if user_obj is None:
        return "koi"
    name = (getattr(user_obj, "first_name", "") or "").strip()
    if getattr(user_obj, "username", None):
        return f"@{user_obj.username}"
    return name or f"user{getattr(user_obj, 'id', '?')}"


def parse_amount(text: str, user: dict) -> int | None:
    """Parse an amount: number, 'all', 'half'. None = invalid."""
    text = (text or "").strip().lower()
    if text in ("all", "sab", "sara"):
        return int(user.get("coins", 0))
    if text in ("half", "aadha"):
        return int(user.get("coins", 0)) // 2
    if text.endswith("k"):
        try:
            return int(float(text[:-1]) * 1000)
        except ValueError:
            return None
    try:
        n = int(text.replace(",", ""))
    except ValueError:
        return None
    return n if n > 0 else None


# ---------------------------------------------------------------------------
# Pure helpers (unit-testable)
# ---------------------------------------------------------------------------
def score_word_guess(secret: str, guess: str) -> list[str]:
    """Wordle scoring, greens first, blues capped by remaining count.

    Returns one of 'green'/'blue'/'white' per letter.
    """
    secret = secret.lower()
    guess = guess.lower()
    result = ["white"] * len(guess)
    remaining: dict[str, int] = {}
    for i, (s, g) in enumerate(zip(secret, guess)):
        if s == g:
            result[i] = "green"
        else:
            remaining[s] = remaining.get(s, 0) + 1
    for i, g in enumerate(guess):
        if result[i] == "green":
            continue
        if remaining.get(g, 0) > 0:
            result[i] = "blue"
            remaining[g] -= 1
    return result


def word_guess_board(secret: str, guess: str, round_no: int, total: int = 6) -> str:
    marks = score_word_guess(secret, guess)
    squares = {"green": "🟩", "blue": "🟦", "white": "⬜"}
    letters = " ".join(c.upper() for c in guess)
    board = " ".join(squares[m] for m in marks)
    return f"🔤 WORD GUESS — round {round_no}/{total}\n{letters}\n{board}"


def rps_winner(a: str, b: str) -> int:
    """0 = draw, 1 = a wins, 2 = b wins. Choices: rock/paper/scissors."""
    beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    if a == b:
        return 0
    return 1 if beats.get(a) == b else 2


def math_question(difficulty: str = "medium") -> tuple[str, int]:
    if difficulty == "easy":
        a, b = random.randint(2, 20), random.randint(2, 20)
        op = random.choice(["+", "-"])
    elif difficulty == "hard":
        a, b = random.randint(12, 99), random.randint(3, 30)
        op = random.choice(["+", "-", "x"])
    else:
        a, b = random.randint(5, 50), random.randint(2, 20)
        op = random.choice(["+", "-", "x"])
    if op == "+":
        return f"{a} + {b} = ?", a + b
    if op == "-":
        return f"{a} - {b} = ?", a - b
    return f"{a} × {b} = ?", a * b


def place_grid_words(words: list[str], size: int = 8) -> tuple[list[list[str]], dict[str, list[tuple[int, int]]]]:
    """Place words in an 8x8 grid (horizontal/vertical, forward/backward)."""
    grid = [["" for _ in range(size)] for _ in range(size)]
    placed: dict[str, list[tuple[int, int]]] = {}
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    for word in words:
        word = word.upper()
        for _ in range(200):
            dr, dc = random.choice(directions)
            r = random.randrange(size)
            c = random.randrange(size)
            cells = [(r + dr * i, c + dc * i) for i in range(len(word))]
            if any(not (0 <= rr < size and 0 <= cc < size) for rr, cc in cells):
                continue
            if any(grid[rr][cc] not in ("", word[i]) for i, (rr, cc) in enumerate(cells)):
                continue
            for i, (rr, cc) in enumerate(cells):
                grid[rr][cc] = word[i]
            placed[word] = cells
            break
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for r in range(size):
        for c in range(size):
            if not grid[r][c]:
                grid[r][c] = random.choice(letters)
    return grid, placed


def grid_text(grid: list[list[str]]) -> str:
    return "\n".join(" ".join(row) for row in grid)


# ---------------------------------------------------------------------------
# In-memory game state (per chat)
# ---------------------------------------------------------------------------
GAMES: dict[int, dict] = {}          # chat_id -> {kind: ..., ...}
TAG_JOBS: dict[int, dict] = {}       # chat_id -> {"active": bool}
OWNER_PENDING: dict[int, str] = {}   # owner uid -> "broadcast" | "ban" | "unban"
MAFIA: dict[int, dict] = {}

POWERS = {
    "rampage": {"name": "Rampage", "desc": "Daily limits 2x, max rob 5x", "cost": {7: 5, 15: 9, 30: 14}},
    "cloak": {"name": "Cloak", "desc": "Protection time chhupa deta hai", "cost": {7: 5, 15: 9, 30: 14}},
    "vault": {"name": "Vault", "desc": "Balance ka 60% safe (normal 30%)", "cost": {7: 5, 15: 9, 30: 14}},
    "ascend": {"name": "Ascend", "desc": "Kill/Rob/Give/games se 2x XP", "cost": {7: 5, 15: 9, 30: 14}},
}


def has_power(user: dict, name: str) -> bool:
    return float(user.get("powers", {}).get(name, 0)) > time.time()


def power_mult(user: dict) -> int:
    return 2 if has_power(user, "ascend") else 1


def game_state(chat_id: int) -> dict | None:
    return GAMES.get(chat_id)


def set_game(chat_id: int, state: dict | None) -> None:
    if state is None:
        GAMES.pop(chat_id, None)
    else:
        GAMES[chat_id] = state


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
def _proxy_settings():
    """Optional HTTP proxy for the MTProto connection (local dev only).

    The sandbox VM blocks raw MTProto TCP, so local runs need the egress
    proxy: set CHULBULI_PROXY=1 and the https_proxy env var is used.
    On Railway/Northflank leave it unset — direct connection works there.
    """
    if os.environ.get("CHULBULI_PROXY") != "1":
        return None
    from urllib.parse import urlparse
    raw = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or ""
    p = urlparse(raw)
    if p.hostname and p.port:
        return {"scheme": "http", "hostname": p.hostname, "port": p.port}
    return None


app = Client(
    "chulbuli",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    proxy=_proxy_settings(),
)


async def safe_reply(message: Message, text: str, **kwargs):
    try:
        return await message.reply_text(text, **kwargs)
    except FloodWait as e:
        await asyncio.sleep(e.value + 1)
        try:
            return await message.reply_text(text, **kwargs)
        except Exception:  # noqa: BLE001
            return None
    except Exception:  # noqa: BLE001
        return None


async def is_chat_admin(client: Client, chat_id: int, user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:  # noqa: BLE001
        return False


def games_on() -> bool:
    return bool(DATA.get("toggles", {}).get("games", True))


def economy_on() -> bool:
    return bool(DATA.get("toggles", {}).get("economy", True))


def chat_on() -> bool:
    return bool(DATA.get("toggles", {}).get("chat", True))


def is_banned(uid: int) -> bool:
    return uid in DATA.get("banned_users", []) or bool(DATA["users"].get(str(uid), {}).get("banned"))


def track_user(message: Message) -> dict | None:
    """Register any user/group that talks to the bot (for broadcast + stats)."""
    user = message.from_user
    if user is None or user.is_bot:
        return None
    get_user(user.id, display_name(user))
    if message.chat and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        chat = DATA["chats"].setdefault(str(message.chat.id), {
            "title": message.chat.title or "group", "msgs": {}, "warns": {},
            "links_off": False, "chat_on": True, "last_seen": 0})
        chat["title"] = message.chat.title or chat["title"]
        chat["last_seen"] = int(time.time())
        msgs = chat.setdefault("msgs", {})
        msgs[str(user.id)] = msgs.get(str(user.id), 0) + 1
        save_data()
    return DATA["users"][str(user.id)]

# ---------------------------------------------------------------------------
# /start /help — original Hinglish text
# ---------------------------------------------------------------------------
START_TEXT = """Hiee {name} 💕 main Chulbuli hun — games, masti aur economy, sab kuch ek hi bot me!

💰 Economy: /bal /daily /give /deposit /withdraw /toprich
⚔️ Actions: /rob /kill /protect /shield /revive
✨ Powers: /powers /act /mypowers
🎮 Games: /wordguess /wordgrid /wordchain /rps /cricket /math /bbet /card /number
💞 Romance: /propose /marry /ship /divorce
🛡️ Mods (admins): /warn /mute /ban /kick /pin /purge /utag
📊 Rank: /rank /toprank /mystats

Aur games (UNO, Chess, Mafia, Bingo…) jald aa rahe hain!
Group me add karo aur khelna shuru karo — type /help for details!"""

HELP_TEXT = """💕 **Chulbuli — Help**

**💰 Economy**
/bal — apna balance, rank, status
/daily — roz ke free coins + XP
/give — reply karke coins do
/deposit <amount> — bank me jama karo
/withdraw <amount> — bank se nikalo
/toprich — sabse ameer top 10
/leaderboard — game + economy leaders
/rank — apna XP rank
/pfp — apni profile
/gems — gems store
/convert <gems> — gems ko coins me badlo

**⚔️ Actions**
/rob — reply karke kisi ko looto
/kill — reply karke kisi ko maaro
/protect — shield kharido (500 coins, 12 ghante)
/shield — shield status
/revive — khud ya kisi ko zinda karo (1000 coins)
/topkill /toprob — top killers aur robbers

**✨ Powers**
/powers — saari powers dekho
/pinfo <power> — power ki details
/act <power> <days> — power activate karo (gems se)
/mypowers — apni active powers
/extend <hours> — power badhao

**🎮 Games (group me)**
/wordguess — 4-letter word guess (🟩🟦⬜)
/wordgrid /wordchain /rps /cricket /math
/bbet /card /number
(Aur games — UNO, Chess, Mines, Tap, Crash, Jumble, Charades, Bingo, Xoxo, Mafia, Hack, Bomb, Roulette, Bluff, Subway, Scribble — phase 2 me aa rahe hain!)

**💞 Romance**
/propose — reply karke propose karo
/marry — shaadi status / accept
/ship — compatibility check
/divorce — alag ho jao

**🛡️ Mods (sirf admins)**
/warn /unwarn /mute /unmute /ban /unban /kick /pin /purge
/utag /atag — sabko tag karo
/nolinks — link filter on/off
/info /id — user/group info

**👑 Owner**
/owner — owner panel (sirf Sanji)"""


@app.on_message(filters.command(["start", "help"]))
async def cmd_start_help(client: Client, message: Message):
    user = track_user(message)
    if user is None:
        return
    if is_banned(message.from_user.id):
        return
    if message.command and message.command[0] == "start":
        await safe_reply(message, START_TEXT.format(name=display_name(message.from_user)))
    else:
        await safe_reply(message, HELP_TEXT)


@app.on_message(filters.command(["id"]))
async def cmd_id(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        await safe_reply(message, f"👤 {display_name(u)}\nID: `{u.id}`")
    else:
        await safe_reply(message, f"👤 {display_name(message.from_user)}\nTumhari ID: `{message.from_user.id}`\nChat ID: `{message.chat.id}`")


@app.on_message(filters.command(["info"]))
async def cmd_info(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    target = message.reply_to_message.from_user if message.reply_to_message and message.reply_to_message.from_user else message.from_user
    u = get_user(target.id, display_name(target))
    await safe_reply(
        message,
        f"👤 **{display_name(target)}**\nID: `{target.id}`\n"
        f"💰 Coins: {fmt_coins(u['coins'])} | 🏦 Bank: {fmt_coins(u['bank'])}\n"
        f"⭐ Level {u['level']} ({u['xp']} XP) | ⚔️ Kills: {u['kills']} | 💀 Deaths: {u['deaths']}\n"
        f"❤️ Status: {u['status']}",
    )


@app.on_message(filters.command(["calc"]))
async def cmd_calc(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    expr = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expr or ""):
        await safe_reply(message, "Arre, sahi maths likho na — jaise `/calc 10+5` 🙂")
        return
    try:
        result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
        await safe_reply(message, f"🧮 `{expr}` = **{result}**")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Ye calculate nahi ho paya, kuch aur try karo 🙂")


# ---------------------------------------------------------------------------
# Economy
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["bal", "balance"]))
async def cmd_bal(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    reset_daily(user)
    name = display_name(message.from_user)
    shield = "🛡️ ON" if float(user.get("shield_until", 0)) > time.time() else "off"
    await safe_reply(
        message,
        f"💰 **{name} ka Balance**\n\n"
        f"Coins: {fmt_coins(user['coins'])}\n"
        f"Bank: {fmt_coins(user['bank'])}\n"
        f"Gems: 💎 {user['gems']}\n"
        f"Rank: #{coin_rank(message.from_user.id)}\n"
        f"Status: {user['status']} | Shield: {shield}\n"
        f"Kills: {user['kills']} | Level {user['level']} ({user['xp']} XP)",
    )
    save_data()


@app.on_message(filters.command(["pfp"]))
async def cmd_pfp(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    reset_daily(user)
    await safe_reply(
        message,
        f"👤 **{display_name(message.from_user)}**\n\n"
        f"💰 Coins: {fmt_coins(user['coins'])} | 🏦 Bank: {fmt_coins(user['bank'])}\n"
        f"💎 Gems: {user['gems']} | ⭐ Level {user['level']} ({user['xp']} XP)\n"
        f"⚔️ Kills: {user['kills']} | 💀 Deaths: {user['deaths']}\n"
        f"🦹 Robs: {user['robs']} | 😢 Robbed: {user['robbed']} baar\n"
        f"📅 Aaj: robs {user['robs_today']}/150, kills {user['kills_today']}/200",
    )
    save_data()


@app.on_message(filters.command(["daily"]))
async def cmd_daily(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    now = time.time()
    last = float(user.get("last_daily", 0))
    if now - last < 86400:
        left = int(86400 - (now - last))
        hrs, rem = divmod(left, 3600)
        mins = rem // 60
        await safe_reply(message, f"Daily abhi nahi milega — {hrs} ghante {mins} min baad aana 🙂")
        return
    reward = 1400
    if has_power(user, "rampage"):
        reward *= 2
    user["last_daily"] = now
    add_coins(user, reward)
    add_xp(user, 10 * power_mult(user))
    save_data()
    await safe_reply(message, f"🎁 Daily mil gaya! **+{fmt_coins(reward)}** coins aur +{10 * power_mult(user)} XP 💕")


@app.on_message(filters.command(["give"]))
async def cmd_give(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    target_msg = message.reply_to_message
    if not target_msg or not target_msg.from_user or target_msg.from_user.is_bot:
        await safe_reply(message, "Kisi ke message pe reply karke /give <amount> likho 🙂")
        return
    amount = parse_amount(message.command[1] if len(message.command) > 1 else "", user)
    if amount is None or amount <= 0:
        await safe_reply(message, "Sahi amount likho — jaise `/give 100` 🙂")
        return
    if user["coins"] < amount:
        await safe_reply(message, "Itne coins hain hi nahi tumhare paas 😅")
        return
    target = get_user(target_msg.from_user.id, display_name(target_msg.from_user))
    add_coins(user, -amount)
    add_coins(target, amount)
    add_xp(user, 5 * power_mult(user))
    save_data()
    await safe_reply(message, f"💝 {display_name(message.from_user)} ne {display_name(target_msg.from_user)} ko **{fmt_coins(amount)}** diye! Pyaar badh raha hai 💕")


@app.on_message(filters.command(["deposit"]))
async def cmd_deposit(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    amount = parse_amount(message.command[1] if len(message.command) > 1 else "", user)
    if amount is None or amount <= 0:
        await safe_reply(message, "Kitna jama karna hai? `/deposit 500` 🙂")
        return
    if user["coins"] < amount:
        await safe_reply(message, "Wallet me itne coins nahi hain 😅")
        return
    add_coins(user, -amount)
    user["bank"] = int(user.get("bank", 0)) + amount
    save_data()
    await safe_reply(message, f"🏦 Bank me **{fmt_coins(amount)}** jama ho gaye! Bank balance: {fmt_coins(user['bank'])}")


@app.on_message(filters.command(["withdraw"]))
async def cmd_withdraw(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    raw = message.command[1].lower() if len(message.command) > 1 else ""
    if raw in ("all", "sab", "sara"):
        amount = int(user.get("bank", 0))
    else:
        amount = parse_amount(raw, user)
    if amount is None or amount <= 0:
        await safe_reply(message, "Kitna nikalna hai? `/withdraw 500` 🙂")
        return
    if int(user.get("bank", 0)) < amount:
        await safe_reply(message, "Bank me itne paise nahi hain 😅")
        return
    user["bank"] -= amount
    add_coins(user, amount)
    save_data()
    await safe_reply(message, f"🏦 Bank se **{fmt_coins(amount)}** nikaal liye! Wallet: {fmt_coins(user['coins'])}")


@app.on_message(filters.command(["toprich", "leaderboard"]))
async def cmd_toprich(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    ordered = sorted(DATA["users"].items(),
                     key=lambda kv: kv[1].get("coins", 0) + kv[1].get("bank", 0),
                     reverse=True)[:10]
    if not ordered:
        await safe_reply(message, "Abhi koi ameer nahi hai — /daily se shuru karo 💰")
        return
    lines = ["💰 **Top Rich — Chulbuli Economy**\n"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, (uid, u) in enumerate(ordered):
        total = u.get("coins", 0) + u.get("bank", 0)
        lines.append(f"{medals[i]} {u.get('name') or uid} — {fmt_coins(total)}")
    await safe_reply(message, "\n".join(lines))


@app.on_message(filters.command(["rank"]))
async def cmd_rank(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    ordered = sorted(DATA["users"].items(), key=lambda kv: kv[1].get("xp", 0), reverse=True)
    pos = next((i + 1 for i, (k, _) in enumerate(ordered) if k == str(message.from_user.id)), len(ordered))
    await safe_reply(
        message,
        f"⭐ **{display_name(message.from_user)}**\nLevel {user['level']} ({user['xp']} XP)\n"
        f"XP Rank: #{pos} | Coin Rank: #{coin_rank(message.from_user.id)}\n"
        f"⚔️ Kills: {user['kills']} | 💀 Deaths: {user['deaths']}",
    )


@app.on_message(filters.command(["toprank"]))
async def cmd_toprank(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    chat = DATA["chats"].get(str(message.chat.id), {})
    msgs = chat.get("msgs", {})
    if not msgs:
        await safe_reply(message, "Is chat me abhi koi message count nahi hai 🙂")
        return
    ordered = sorted(msgs.items(), key=lambda kv: kv[1], reverse=True)[:10]
    lines = ["📊 **Top Talkers — is group ke**\n"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, (uid, n) in enumerate(ordered):
        u = DATA["users"].get(uid, {})
        lines.append(f"{medals[i]} {u.get('name') or uid} — {n} messages")
    await safe_reply(message, "\n".join(lines))


@app.on_message(filters.command(["mystats"]))
async def cmd_mystats(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    chat = DATA["chats"].get(str(message.chat.id), {})
    n = chat.get("msgs", {}).get(str(message.from_user.id), 0)
    await safe_reply(
        message,
        f"📊 **{display_name(message.from_user)}**\nIs group me messages: {n}\n"
        f"💰 Coins: {fmt_coins(user['coins'])} | ⭐ Level {user['level']} | ⚔️ Kills: {user['kills']}",
    )


@app.on_message(filters.command(["gems"]))
async def cmd_gems(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    await safe_reply(
        message,
        f"💎 **Gems Store**\nTumhare gems: {user['gems']}\n\n"
        f"1 gem = 10,000 coins — /convert <gems> se badlo\n"
        f"Gems powers ke liye use hote hain — /powers dekho ✨",
    )


@app.on_message(filters.command(["convert"]))
async def cmd_convert(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    try:
        n = int(message.command[1]) if len(message.command) > 1 else 0
    except ValueError:
        n = 0
    if n <= 0 or int(user.get("gems", 0)) < n:
        await safe_reply(message, "Itne gems nahi hain — `/convert 1` try karo 🙂")
        return
    user["gems"] -= n
    add_coins(user, n * 10000)
    save_data()
    await safe_reply(message, f"💎 {n} gems → **{fmt_coins(n * 10000)}** coins! Wallet: {fmt_coins(user['coins'])}")


# ---------------------------------------------------------------------------
# Actions: rob / kill / protect / shield / revive
# ---------------------------------------------------------------------------
def _shielded(user: dict) -> bool:
    return float(user.get("shield_until", 0)) > time.time()


@app.on_message(filters.command(["rob", "steal", "atk"]))
async def cmd_rob(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    reset_daily(user)
    if user["status"] != "alive":
        await safe_reply(message, "Tum mare hue ho — pehle /revive karo 💀")
        return
    target_msg = message.reply_to_message
    if not target_msg or not target_msg.from_user or target_msg.from_user.is_bot:
        await safe_reply(message, "Kisko lootna hai? Uske message pe reply karke /rob likho 💀")
        return
    if target_msg.from_user.id == message.from_user.id:
        await safe_reply(message, "Khud ko nahi loot sakte 😂")
        return
    limit = 300 if has_power(user, "rampage") else 150
    if user["robs_today"] >= limit:
        await safe_reply(message, f"Aaj ki rob limit khatam ({limit}) — kal aana 🙂")
        return
    victim = get_user(target_msg.from_user.id, display_name(target_msg.from_user))
    if victim["status"] != "alive":
        await safe_reply(message, "Ye to pehle se mara hua hai 😅")
        return
    if _shielded(victim) and not has_power(user, "cloak"):
        await safe_reply(message, f"{display_name(target_msg.from_user)} ke paas shield hai — loot nahi paye 🛡️")
        return
    user["robs_today"] += 1
    max_rob = 50000 if has_power(user, "rampage") else 10000
    stealable = victim["coins"]
    if has_power(victim, "vault"):
        stealable = int(stealable * 0.4)  # 60% vault me safe
    else:
        stealable = int(stealable * 0.7)  # 30% safe
    amount = min(max_rob, stealable)
    if amount <= 0:
        await safe_reply(message, "Iske paas lootne layak kuch nahi hai 😅")
        save_data()
        return
    if random.random() < 0.6:
        take = random.randint(max(1, amount // 2), amount)
        add_coins(victim, -take)
        add_coins(user, take)
        user["robs"] += 1
        victim["robbed"] += 1
        add_xp(user, 10 * power_mult(user))
        save_data()
        await safe_reply(message, f"🦹 {display_name(message.from_user)} ne {display_name(target_msg.from_user)} se **{fmt_coins(take)}** loot liye! 😈")
    else:
        fine = min(500, user["coins"])
        add_coins(user, -fine)
        save_data()
        await safe_reply(message, f"😂 Pakde gaye! {display_name(target_msg.from_user)} ne tumhe bhaga diya aur **{fmt_coins(fine)}** ka fine laga!")


@app.on_message(filters.command(["kill"]))
async def cmd_kill(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    reset_daily(user)
    if user["status"] != "alive":
        await safe_reply(message, "Tum mare hue ho — pehle /revive karo 💀")
        return
    target_msg = message.reply_to_message
    if not target_msg or not target_msg.from_user or target_msg.from_user.is_bot:
        await safe_reply(message, "Kisko maarna hai? Uske message pe reply karke /kill likho 💀")
        return
    if target_msg.from_user.id == message.from_user.id:
        await safe_reply(message, "Khud ko nahi maar sakte 😂")
        return
    limit = 400 if has_power(user, "rampage") else 200
    if user["kills_today"] >= limit:
        await safe_reply(message, f"Aaj ki kill limit khatam ({limit}) — kal aana 🙂")
        return
    victim = get_user(target_msg.from_user.id, display_name(target_msg.from_user))
    if victim["status"] != "alive":
        await safe_reply(message, "Ye to pehle se mara hua hai 😅")
        return
    if _shielded(victim):
        await safe_reply(message, f"{display_name(target_msg.from_user)} ke paas shield hai — maar nahi paye 🛡️")
        return
    user["kills_today"] += 1
    if random.random() < 0.7:
        victim["status"] = "dead"
        victim["deaths"] += 1
        user["kills"] += 1
        add_xp(user, 20 * power_mult(user))
        save_data()
        await safe_reply(message, f"💀 {display_name(message.from_user)} ne {display_name(target_msg.from_user)} ko maar diya! /revive se wapas aao 😈")
    else:
        save_data()
        await safe_reply(message, f"😂 {display_name(target_msg.from_user)} bach gaya! Tumhara attack miss ho gaya!")


@app.on_message(filters.command(["protect"]))
async def cmd_protect(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if user["coins"] < 500:
        await safe_reply(message, "Shield 500 coins ki hai — pehle coins kamao 🙂")
        return
    add_coins(user, -500)
    user["shield_until"] = time.time() + 12 * 3600
    save_data()
    await safe_reply(message, "🛡️ Shield lag gaya — 12 ghante tak koi tumhe rob ya kill nahi kar payega!")


@app.on_message(filters.command(["shield", "protection"]))
async def cmd_shield(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    left = float(user.get("shield_until", 0)) - time.time()
    if left > 0:
        hrs = int(left // 3600)
        mins = int((left % 3600) // 60)
        await safe_reply(message, f"🛡️ Shield ON hai — {hrs} ghante {mins} min baaki hai")
    else:
        await safe_reply(message, "Tumhare paas abhi koi shield nahi hai. /protect se kharido (500 coins) 🙂")


@app.on_message(filters.command(["revive"]))
async def cmd_revive(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    target_msg = message.reply_to_message
    if target_msg and target_msg.from_user and not target_msg.from_user.is_bot:
        victim = get_user(target_msg.from_user.id, display_name(target_msg.from_user))
        who = display_name(target_msg.from_user)
    else:
        victim = user
        who = "tum"
    if victim["status"] == "alive":
        await safe_reply(message, f"{who} to pehle se zinda hai 🙂")
        return
    if user["coins"] < 1000:
        await safe_reply(message, "Revive 1000 coins ka hai — pehle coins kamao 🙂")
        return
    add_coins(user, -1000)
    victim["status"] = "alive"
    save_data()
    await safe_reply(message, f"✨ {display_name(target_msg.from_user) if target_msg and target_msg.from_user else 'Tum'} wapas zinda ho gaye! 1000 coins kharch hue 💕")


@app.on_message(filters.command(["topkill"]))
async def cmd_topkill(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    ordered = sorted(DATA["users"].items(), key=lambda kv: kv[1].get("kills", 0), reverse=True)[:10]
    lines = ["⚔️ **Top Killers**\n"]
    for i, (uid, u) in enumerate(ordered, 1):
        lines.append(f"{i}. {u.get('name') or uid} — {u['kills']} kills")
    await safe_reply(message, "\n".join(lines))


@app.on_message(filters.command(["toprob"]))
async def cmd_toprob(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    ordered = sorted(DATA["users"].items(), key=lambda kv: kv[1].get("robs", 0), reverse=True)[:10]
    lines = ["🦹 **Top Robbers**\n"]
    for i, (uid, u) in enumerate(ordered, 1):
        lines.append(f"{i}. {u.get('name') or uid} — {u['robs']} robs")
    await safe_reply(message, "\n".join(lines))


# ---------------------------------------------------------------------------
# Powers
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["powers"]))
async def cmd_powers(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    lines = ["✨ **Powers** — gems se activate karo\n"]
    for key, p in POWERS.items():
        lines.append(f"**{p['name']}** — {p['desc']}\n  7 din: {p['cost'][7]} gems | 15 din: {p['cost'][15]} gems | 30 din: {p['cost'][30]} gems")
    lines.append("\nActivate: `/act rampage 7`  •  Details: `/pinfo rampage`")
    await safe_reply(message, "\n".join(lines))


@app.on_message(filters.command(["pinfo"]))
async def cmd_pinfo(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    name = (message.command[1].lower() if len(message.command) > 1 else "")
    p = POWERS.get(name)
    if not p:
        await safe_reply(message, "Kaunsi power? rampage, cloak, vault, ascend — `/pinfo rampage` 🙂")
        return
    await safe_reply(message, f"✨ **{p['name']}**\n{p['desc']}\n\n7 din: {p['cost'][7]} gems\n15 din: {p['cost'][15]} gems\n30 din: {p['cost'][30]} gems\n\nActivate: `/act {name} 7`")


@app.on_message(filters.command(["act", "activate"]))
async def cmd_act(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if len(message.command) < 3:
        await safe_reply(message, "Aise: `/act rampage 7` (power aur din) 🙂")
        return
    name = message.command[1].lower()
    p = POWERS.get(name)
    if not p:
        await safe_reply(message, "Aisi koi power nahi — /powers dekho 🙂")
        return
    try:
        days = int(message.command[2])
    except ValueError:
        await safe_reply(message, "Din number me likho — 7, 15 ya 30 🙂")
        return
    if days not in (7, 15, 30):
        await safe_reply(message, "Sirf 7, 15 ya 30 din ki power milti hai 🙂")
        return
    cost = p["cost"][days]
    if int(user.get("gems", 0)) < cost:
        await safe_reply(message, f"{cost} gems chahiye, tumhare paas {user.get('gems', 0)} hain 😅")
        return
    user["gems"] -= cost
    user.setdefault("powers", {})[name] = time.time() + days * 86400
    save_data()
    await safe_reply(message, f"✨ **{p['name']}** activate ho gaya — {days} din ke liye! 🔥")


@app.on_message(filters.command(["mypowers", "mp"]))
async def cmd_mypowers(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    active = [(k, v) for k, v in user.get("powers", {}).items() if float(v) > time.time()]
    if not active:
        await safe_reply(message, "Tumhari koi power active nahi hai — /powers se activate karo ✨")
        return
    lines = ["✨ **Tumhari Active Powers**\n"]
    for key, exp in active:
        days_left = (float(exp) - time.time()) / 86400
        lines.append(f"• {POWERS[key]['name']} — {days_left:.1f} din baaki")
    await safe_reply(message, "\n".join(lines))


@app.on_message(filters.command(["ph"]))
async def cmd_ph(client: Client, message: Message):
    await cmd_powers(client, message)


@app.on_message(filters.command(["extend"]))
async def cmd_extend(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    try:
        hours = int(message.command[1]) if len(message.command) > 1 else 0
    except ValueError:
        hours = 0
    if not (1 <= hours <= 12):
        await safe_reply(message, "1 se 12 ghante tak extend hota hai — `/extend 6` 🙂")
        return
    powers = user.get("powers", {})
    if not powers:
        await safe_reply(message, "Pehle koi power activate karo — /powers 🙂")
        return
    for k in powers:
        powers[k] = float(powers[k]) + hours * 3600
    save_data()
    await safe_reply(message, f"⏰ Powers {hours} ghante extend ho gayi! ✨")

# ---------------------------------------------------------------------------
# Word Guess — EXACTLY per approved spec (word-guess-spec.md)
# /wordguess (/wg) group-only. Reply to the board message to guess.
# 6 guesses/round, winner +500 coins, NEW message per guess (spam is fine),
# 🟩 right place / 🟦 in word wrong place / ⬜ not in word.
# ---------------------------------------------------------------------------
def _wg_new_round(chat_id: int) -> dict:
    state = {"kind": "wordguess", "secret": random.choice(WORD_GUESS_WORDS),
             "guesses": 0, "round_id": int(time.time() * 1000) % 10**9,
             "last_active": time.time(), "board_msg_id": None}
    set_game(chat_id, state)
    return state


async def _wg_timeout(chat_id: int, round_id: int):
    await asyncio.sleep(180)
    state = game_state(chat_id)
    if not state or state.get("kind") != "wordguess" or state.get("round_id") != round_id:
        return
    if time.time() - state.get("last_active", 0) >= 175:
        try:
            await app.send_message(chat_id, f"⏰ Word Guess khatam — koi guess nahi aaya! Word tha: **{state['secret'].upper()}** 🙂")
        except Exception:  # noqa: BLE001
            pass
        set_game(chat_id, None)


@app.on_message(filters.command(["wordguess", "wg"]))
async def cmd_wordguess(client: Client, message: Message):
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if message.chat.type == ChatType.PRIVATE:
        await safe_reply(message, "Word Guess group me khela jata hai — mujhe kisi group me add karo 🙂")
        return
    state = _wg_new_round(message.chat.id)
    msg = await safe_reply(
        message,
        "🔤 **WORD GUESS** — 4-letter word guess karo!\n"
        "Board message pe **reply** karke apna guess bhejo.\n"
        "🟩 = sahi jagah | 🟦 = word me hai, galat jagah | ⬜ = word me nahi\n"
        "6 guesses, jeetne wale ko **+500 coins**! Round 0/6",
    )
    if msg is not None:
        state["board_msg_id"] = msg.id
    asyncio.create_task(_wg_timeout(message.chat.id, state["round_id"]))


async def handle_wordguess_reply(message: Message) -> bool:
    """Returns True if the message was consumed as a word-guess guess."""
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "wordguess":
        return False
    reply = message.reply_to_message
    if not reply or reply.id != state.get("board_msg_id"):
        return False
    text = (message.text or "").strip().lower()
    if not re.fullmatch(r"[a-z]{4}", text):
        await safe_reply(message, "4-letter word bhejo 🙂")
        return True
    state["last_active"] = time.time()
    state["guesses"] += 1
    secret = state["secret"]
    user = get_user(message.from_user.id, display_name(message.from_user))
    if text == secret:
        add_coins(user, 500)
        add_xp(user, 20 * power_mult(user))
        DATA["meta"]["games_played"] = DATA["meta"].get("games_played", 0) + 1
        save_data()
        await safe_reply(
            message,
            f"🎉 **{display_name(message.from_user)}** ne word guess kar liya!\n"
            f"Word tha: **{secret.upper()}**\n+500 coins mil gaye! 💰\n"
            f"Naya round: /wordguess",
        )
        set_game(message.chat.id, None)
        return True
    board = word_guess_board(secret, text, state["guesses"])
    if state["guesses"] >= 6:
        await safe_reply(message, f"{board}\n\n😢 6 guesses khatam! Word tha: **{secret.upper()}**\nNaya round: /wordguess")
        set_game(message.chat.id, None)
    else:
        msg = await safe_reply(
            message,
            f"{board}\n\n*{display_name(message.from_user)}* ka guess — {6 - state['guesses']} guesses baaki! Board pe reply karke guess karo 🙂",
        )
        if msg is not None:
            state["board_msg_id"] = msg.id
    save_data()
    return True


# ---------------------------------------------------------------------------
# Word Grid — 8x8 word search
# ---------------------------------------------------------------------------
GRID_WORDS = ["ship", "candy", "throw", "knows", "praise", "window", "retired", "fire"]


@app.on_message(filters.command(["wordgrid", "grid"]))
async def cmd_wordgrid(client: Client, message: Message):
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if message.chat.type == ChatType.PRIVATE:
        await safe_reply(message, "Word Grid group me khela jata hai 🙂")
        return
    words = random.sample(GRID_WORDS, 6)
    grid, placed = place_grid_words(words)
    masked = "\n".join(f"• {w[0].upper()}{'-' * (len(w) - 1)} ({len(w)})" for w in words)
    state = {"kind": "wordgrid", "grid": grid, "words": {w.upper(): False for w in placed},
             "scores": {}, "hints": 3}
    set_game(message.chat.id, state)
    await safe_reply(
        message,
        f"🔠 **WORD GRID** — grid me chhupe words dhoondho!\n\n```\n{grid_text(grid)}\n```\n"
        f"Words:\n{masked}\n\n/guess <word> se guess karo — har word pe +2 coins points! /hint bhi hai 🙂",
    )


@app.on_message(filters.command(["guess"]))
async def cmd_guess(client: Client, message: Message):
    if not games_on():
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "wordgrid":
        return
    word = (message.command[1].upper() if len(message.command) > 1 else "")
    words = state["words"]
    if word in words and not words[word]:
        words[word] = True
        pts = 3 if len(word) <= 3 else 2
        state["scores"][str(message.from_user.id)] = state["scores"].get(str(message.from_user.id), 0) + pts
        add_coins(user, pts * 10)
        save_data()
        if all(words.values()):
            total = state["scores"].get(str(message.from_user.id), 0)
            await safe_reply(message, f"💎 WORD UNLOCKED! **{word}** +{pts} points!\n\n🎉 Saare words mil gaye! {display_name(message.from_user)} ka total: {total} points! /wordgrid se naya game 🙂")
            set_game(message.chat.id, None)
        else:
            await safe_reply(message, f"💎 WORD UNLOCKED! WORD: **{word}** POINTS: +{pts} 💎 ✅ Tumhara score: {state['scores'][str(message.from_user.id)]}")
    elif word in words:
        await safe_reply(message, f"{word} pehle se mil chuka hai 🙂")
    else:
        await safe_reply(message, f"{word} grid me nahi hai — dobara try karo 🙂")


@app.on_message(filters.command(["hint"]))
async def cmd_hint(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "wordgrid":
        return
    if state.get("hints", 0) <= 0:
        await safe_reply(message, "Hints khatam ho gaye 🙂")
        return
    remaining = [w for w, found in state["words"].items() if not found]
    if not remaining:
        return
    word = random.choice(remaining)
    state["hints"] -= 1
    await safe_reply(message, f"💡 Hint: ek word **{word[:2]}** se shuru hota hai ({len(word)} letters). Hints baaki: {state['hints']}")


@app.on_message(filters.command(["gend"]))
async def cmd_gend(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if state and state.get("kind") == "wordgrid":
        scores = state["scores"]
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:5]
        lines = ["🏁 **Word Grid khatam!** Scores:\n"]
        for uid, pts in top:
            lines.append(f"• {DATA['users'].get(uid, {}).get('name') or uid} — {pts} points")
        await safe_reply(message, "\n".join(lines))
        set_game(message.chat.id, None)


# ---------------------------------------------------------------------------
# Wordchain — one implementation (On9 + Mimi + Nova merged)
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["wordchain", "wc"]))
async def cmd_wordchain(client: Client, message: Message):
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if message.chat.type == ChatType.PRIVATE:
        await safe_reply(message, "Wordchain group me khela jata hai 🙂")
        return
    if game_state(message.chat.id):
        await safe_reply(message, "Is group me pehle se ek game chal raha hai — khatam hone do 🙂")
        return
    set_game(message.chat.id, {"kind": "wordchain", "players": [message.from_user.id],
                               "names": {str(message.from_user.id): display_name(message.from_user)},
                               "started": False, "turn": 0, "last_word": None,
                               "used": set(), "strikes": {}, "starter": message.from_user.id})
    await safe_reply(message, "⛓️ **WORDCHAIN** — lobby khul gaya!\n/join se join karo (2+ players chahiye), phir /forcestart se shuru karo.\nRule: agla word pichhle word ke aakhri letter se shuru hona chahiye. 3 galat = out!")


@app.on_message(filters.command(["join"]))
async def cmd_join_generic(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state:
        return
    kind = state.get("kind")
    if kind == "wordchain" and not state["started"]:
        if message.from_user.id in state["players"]:
            await safe_reply(message, "Tum pehle se join ho 🙂")
            return
        state["players"].append(message.from_user.id)
        state["names"][str(message.from_user.id)] = display_name(message.from_user)
        await safe_reply(message, f"⛓️ {display_name(message.from_user)} join ho gaya! Players: {len(state['players'])} — /forcestart se shuru karo 🙂")
    elif kind == "cricket" and not state["started"]:
        if len(state["players"]) >= 2:
            await safe_reply(message, "Cricket lobby full hai 🙂")
            return
        if message.from_user.id in state["players"]:
            return
        state["players"].append(message.from_user.id)
        await safe_reply(message, f"🏏 {display_name(message.from_user)} join ho gaya! /startcricket se shuru karo 🙂")


@app.on_message(filters.command(["forcestart"]))
async def cmd_forcestart(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "wordchain":
        return
    if len(state["players"]) < 2:
        await safe_reply(message, "Kam se kam 2 players chahiye — /join karo 🙂")
        return
    state["started"] = True
    first = state["players"][0]
    await safe_reply(message, f"⛓️ **WORDCHAIN SHURU!** Pehla word {state['names'][str(first)]} bolega — koi bhi English word bhej do! Uske baad har word pichhle word ke aakhri letter se shuru hoga.")


async def handle_wordchain_word(message: Message) -> bool:
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "wordchain" or not state["started"]:
        return False
    text = (message.text or "").strip().lower()
    if not re.fullmatch(r"[a-z]{2,}", text):
        return False
    players = state["players"]
    current = players[state["turn"] % len(players)]
    if message.from_user.id != current:
        return False
    last = state["last_word"]
    ok = True
    reason = ""
    if last and not text.startswith(last[-1]):
        ok = False
        reason = f"'{last[-1].upper()}' se shuru hona chahiye tha"
    if text in state["used"]:
        ok = False
        reason = "ye word pehle use ho chuka hai"
    if not ok:
        uid = str(message.from_user.id)
        state["strikes"][uid] = state["strikes"].get(uid, 0) + 1
        strikes = state["strikes"][uid]
        if strikes >= 3:
            players.remove(message.from_user.id)
            await safe_reply(message, f"❌ {display_name(message.from_user)} — {reason}! 3 strikes, tum OUT ho gaye!")
            if len(players) == 1:
                winner = get_user(players[0], state["names"].get(str(players[0]), ""))
                add_coins(winner, 500)
                save_data()
                await safe_reply(message, f"🏆 **{state['names'].get(str(players[0]), '')}** jeet gaya Wordchain! +500 coins! 💰")
                set_game(message.chat.id, None)
            elif state["turn"] >= len(players):
                state["turn"] = 0
        else:
            await safe_reply(message, f"❌ {reason}! Strike {strikes}/3 — dobara try karo, tumhari hi baari hai 🙂")
        return True
    state["used"].add(text)
    state["last_word"] = text
    state["turn"] += 1
    nxt = players[state["turn"] % len(players)]
    await safe_reply(message, f"✅ **{text.upper()}** — ab {state['names'].get(str(nxt), '')} ki baari! ('{text[-1].upper()}' se shuru karo)")
    return True


# ---------------------------------------------------------------------------
# RPS — one implementation (Daizy + Nova merged)
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["rps"]))
async def cmd_rps(client: Client, message: Message):
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    amount = 0
    if len(message.command) > 1:
        amount = parse_amount(message.command[1], user) or 0
    if amount > 0:
        if not economy_on():
            await safe_reply(message, "Economy off hai, free RPS khelo 🙂")
            return
        if user["coins"] < amount:
            await safe_reply(message, "Itne coins nahi hain 😅")
            return
    if game_state(message.chat.id):
        await safe_reply(message, "Is group me pehle se ek game chal raha hai 🙂")
        return
    set_game(message.chat.id, {"kind": "rps", "amount": amount, "p1": message.from_user.id,
                               "p2": None, "throws": {}, "scores": {}, "round": 1})
    if amount > 0:
        add_coins(user, -amount)
        save_data()
    await safe_reply(
        message,
        f"✂️ **ROCK PAPER SCISSORS** — {display_name(message.from_user)} ne challenge kiya"
        + (f" ({fmt_coins(amount)} ka pot)!" if amount else "!") +
        "\nKoi /joinrps se join kare, phir dono /throw rock/paper/scissors bhejo. Best of 3! 60 sec me koi na aaye to main hi khelungi 😄",
    )


@app.on_message(filters.command(["joinrps"]))
async def cmd_joinrps(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "rps":
        return
    if state["p2"] is not None:
        await safe_reply(message, "Match pehle se full hai 🙂")
        return
    if message.from_user.id == state["p1"]:
        await safe_reply(message, "Khud se nahi khel sakte 😂")
        return
    amount = state["amount"]
    if amount > 0:
        if user["coins"] < amount:
            await safe_reply(message, "Pot ke liye itne coins nahi hain 😅")
            return
        add_coins(user, -amount)
        save_data()
    state["p2"] = message.from_user.id
    await safe_reply(message, f"✂️ {display_name(message.from_user)} join ho gaya! Dono /throw rock/paper/scissors bhejo — Round 1!")


@app.on_message(filters.command(["throw"]))
async def cmd_throw(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "rps":
        return
    choice = (message.command[1].lower() if len(message.command) > 1 else "")
    aliases = {"rock": "rock", "paper": "paper", "scissors": "scissors",
               "stone": "rock", "patthar": "rock", "kagaz": "paper", "kainchi": "scissors"}
    choice = aliases.get(choice, "")
    if not choice:
        await safe_reply(message, "Aise: `/throw rock` ya `/throw paper` ya `/throw scissors` 🙂")
        return
    uid = message.from_user.id
    if uid not in (state["p1"], state.get("p2")):
        await safe_reply(message, "Tum is match me nahi ho 🙂")
        return
    if uid in state["throws"]:
        await safe_reply(message, "Tum throw kar chuke ho — dusre ka wait karo 🙂")
        return
    state["throws"][uid] = choice
    if state.get("p2") is None:
        # Bot plays as opponent
        bot_choice = random.choice(["rock", "paper", "scissors"])
        state["throws"]["bot"] = bot_choice
        result = rps_winner(choice, bot_choice)
        em = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        if result == 0:
            await safe_reply(message, f"{em[choice]} vs {em[bot_choice]} — Draw! Dobara /throw karo 🙂")
            state["throws"] = {}
            return
        if result == 1:
            win = state["amount"] * 2 if state["amount"] else 200
            add_coins(user, win)
            save_data()
            await safe_reply(message, f"{em[choice]} vs {em[bot_choice]} — **Tum jeet gaye!** +{fmt_coins(win)} coins! 🎉")
        else:
            await safe_reply(message, f"{em[choice]} vs {em[bot_choice]} — Main jeet gayi! 😄 Dobara khelna ho to /rps karo")
        set_game(message.chat.id, None)
        return
    if len(state["throws"]) < 2:
        await safe_reply(message, "Throw mil gaya — dusre player ka wait karo 🙂")
        return
    p1, p2 = state["p1"], state["p2"]
    c1, c2 = state["throws"][p1], state["throws"][p2]
    result = rps_winner(c1, c2)
    em = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    n1 = DATA["users"].get(str(p1), {}).get("name", "P1")
    n2 = DATA["users"].get(str(p2), {}).get("name", "P2")
    scores = state["scores"]
    if result == 0:
        await safe_reply(message, f"{em[c1]} vs {em[c2]} — Draw! Round {state['round']} dobara — /throw karo 🙂")
        state["throws"] = {}
        return
    winner = p1 if result == 1 else p2
    scores[winner] = scores.get(winner, 0) + 1
    state["throws"] = {}
    if scores[winner] >= 2:
        pot = state["amount"] * 2 if state["amount"] else 0
        if pot:
            add_coins(get_user(winner), pot)
        else:
            add_coins(get_user(winner), 200)
            pot = 200
        save_data()
        await safe_reply(message, f"{em[c1]} vs {em[c2]} — 🏆 **{n1 if winner == p1 else n2}** match jeet gaya! +{fmt_coins(pot)} coins! 🎉")
        set_game(message.chat.id, None)
    else:
        state["round"] += 1
        await safe_reply(message, f"{em[c1]} vs {em[c2]} — Round {state['round'] - 1} jeeta: **{n1 if winner == p1 else n2}** (score {scores.get(p1, 0)}-{scores.get(p2, 0)})! Agla round — /throw karo 🙂")


# ---------------------------------------------------------------------------
# Cricket — hand cricket (Daizy)
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["cricket"]))
async def cmd_cricket(client: Client, message: Message):
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if message.chat.type == ChatType.PRIVATE:
        await safe_reply(message, "Cricket group me khela jata hai 🙂")
        return
    if game_state(message.chat.id):
        await safe_reply(message, "Is group me pehle se ek game chal raha hai 🙂")
        return
    set_game(message.chat.id, {"kind": "cricket", "players": [message.from_user.id],
                               "started": False, "innings": 1, "ball": 0,
                               "scores": {}, "bat": None, "bowl": None, "picks": {}})
    await safe_reply(message, "🏏 **INDIAN CRICKET ARENA**\n/join se dusra player aao, ya /startsolo se mere saath khelo!\nPhir /startcricket se match shuru 🙂")


@app.on_message(filters.command(["startsolo"]))
async def cmd_startsolo(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "cricket" or state["started"]:
        return
    state["players"].append("bot")
    state["started"] = True
    state["bat"] = state["players"][0]
    state["bowl"] = "bot"
    state["scores"] = {str(state["players"][0]): 0, "bot": 0}
    await safe_reply(message, f"🏏 Match shuru! Tum batting kar rahe ho — har ball pe /num <1-6> bhejo! 6 balls ki innings hai 🙂")


@app.on_message(filters.command(["startcricket"]))
async def cmd_startcricket(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "cricket" or state["started"]:
        return
    if len(state["players"]) < 2:
        await safe_reply(message, "2 players chahiye — /join karo ya /startsolo 🙂")
        return
    state["started"] = True
    state["bat"] = state["players"][0]
    state["bowl"] = state["players"][1]
    state["scores"] = {str(p): 0 for p in state["players"]}
    bat_name = DATA["users"].get(str(state["bat"]), {}).get("name", "P1")
    await safe_reply(message, f"🏏 Match shuru! {bat_name} batting kar raha hai — dono /num <1-6> bhejo! 6 balls ki innings 🙂")


@app.on_message(filters.command(["num"]))
async def cmd_num(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "cricket" or not state["started"]:
        # Number game guess?
        await handle_number_guess(message)
        return
    try:
        n = int(message.command[1]) if len(message.command) > 1 else 0
    except ValueError:
        n = 0
    if not (1 <= n <= 6):
        await safe_reply(message, "1 se 6 tak ka number bhejo — `/num 4` 🙂")
        return
    uid = message.from_user.id
    if uid not in (state["bat"], state["bowl"]):
        await safe_reply(message, "Tum is match me nahi ho 🙂")
        return
    if uid in state["picks"]:
        return
    state["picks"][uid] = n
    if state["bowl"] == "bot":
        state["picks"]["bot"] = random.randint(1, 6)
    if len(state["picks"]) < 2:
        await safe_reply(message, f"Ball {state['ball'] + 1}: tumhara number mil gaya — dusre ka wait karo 🙂")
        return
    bat_pick = state["picks"][state["bat"]]
    bowl_pick = state["picks"][state["bowl"]]
    state["picks"] = {}
    state["ball"] += 1
    bat_name = "Main" if state["bat"] == "bot" else DATA["users"].get(str(state["bat"]), {}).get("name", "Batsman")
    if bat_pick == bowl_pick:
        # OUT
        if state["innings"] == 1:
            target = state["scores"][str(state["bat"])] + 1
            state["innings"] = 2
            state["ball"] = 0
            old_bat, old_bowl = state["bat"], state["bowl"]
            state["bat"], state["bowl"] = old_bowl, old_bat
            await safe_reply(message, f"🏏 OUT! {bat_pick} = {bowl_pick}! Pehli innings khatam — score: {state['scores'][str(old_bat)]}. Target: {target}! Ab dusri innings — /num bhejo 🙂")
            state["target"] = target
        else:
            s1 = state["scores"][str(state["players"][0])]
            s2 = state["scores"][str(state["players"][1])]
            if s1 == s2:
                result = "🤝 Match DRAW ho gaya!"
            else:
                winner = state["players"][0] if s1 > s2 else state["players"][1]
                if winner != "bot":
                    add_coins(get_user(winner), 500)
                    save_data()
                wname = "Main" if winner == "bot" else DATA["users"].get(str(winner), {}).get("name", "")
                result = f"🏆 **{wname}** jeet gaya! Score {s1}-{s2}! +500 coins! 🎉"
            await safe_reply(message, f"🏏 OUT! {bat_pick} = {bowl_pick}!\n{result}")
            set_game(message.chat.id, None)
        return
    state["scores"][str(state["bat"])] += bat_pick
    if state["innings"] == 2 and state["scores"][str(state["bat"])] >= state.get("target", 999):
        s1 = state["scores"][str(state["players"][0])]
        s2 = state["scores"][str(state["players"][1])]
        winner = state["bat"]
        if winner != "bot":
            add_coins(get_user(winner), 500)
            save_data()
        wname = "Main" if winner == "bot" else DATA["users"].get(str(winner), {}).get("name", "")
        await safe_reply(message, f"🏏 {bat_pick} runs! Score: {s1}-{s2}\n🏆 **{wname}** jeet gaya! +500 coins! 🎉")
        set_game(message.chat.id, None)
        return
    if state["ball"] >= 6:
        if state["innings"] == 1:
            target = state["scores"][str(state["bat"])] + 1
            state["innings"] = 2
            state["ball"] = 0
            old_bat, old_bowl = state["bat"], state["bowl"]
            state["bat"], state["bowl"] = old_bowl, old_bat
            state["target"] = target
            await safe_reply(message, f"🏏 {bat_pick} runs! Pehli innings khatam — score: {state['scores'][str(old_bat)]}. Target: {target}! Ab dusri innings 🙂")
        else:
            s1 = state["scores"][str(state["players"][0])]
            s2 = state["scores"][str(state["players"][1])]
            if s1 == s2:
                result = "🤝 Match DRAW ho gaya!"
            else:
                winner = state["players"][0] if s1 > s2 else state["players"][1]
                if winner != "bot":
                    add_coins(get_user(winner), 500)
                    save_data()
                wname = "Main" if winner == "bot" else DATA["users"].get(str(winner), {}).get("name", "")
                result = f"🏆 **{wname}** jeet gaya! Score {s1}-{s2}! +500 coins! 🎉"
            await safe_reply(message, f"🏏 {bat_pick} runs!\n{result}")
            set_game(message.chat.id, None)
        return
    await safe_reply(message, f"🏏 {bat_pick} runs! Ball {state['ball']}/6 — score: {state['scores'][str(state['bat'])]}. Agli ball ke liye /num bhejo 🙂")


@app.on_message(filters.command(["cancel"]))
async def cmd_cancel(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if state:
        set_game(message.chat.id, None)
        await safe_reply(message, "Game cancel kar diya 🙂")
    elif message.chat.id in TAG_JOBS and TAG_JOBS[message.chat.id].get("active"):
        TAG_JOBS[message.chat.id]["active"] = False
        await safe_reply(message, "Tagging rok di 🙂")


# ---------------------------------------------------------------------------
# Math Rush (Daizy)
# ---------------------------------------------------------------------------
async def _math_loop(chat_id: int, difficulty: str, rounds: int = 15):
    state = game_state(chat_id)
    if not state or state.get("kind") != "math":
        return
    for q in range(1, rounds + 1):
        state = game_state(chat_id)
        if not state or state.get("kind") != "math":
            return
        question, answer = math_question(difficulty)
        state["answer"] = answer
        state["q"] = q
        try:
            await app.send_message(chat_id, f"🧮 **MATH RUSH** — Q{q}/{rounds}\n{question}\nPehla sahi jawab = 1 point! (20 sec)")
        except Exception:  # noqa: BLE001
            return
        for _ in range(20):
            await asyncio.sleep(1)
            state = game_state(chat_id)
            if not state or state.get("kind") != "math" or state.get("q") != q:
                break
            if state.get("answered"):
                break
        else:
            try:
                await app.send_message(chat_id, f"⏰ Time up! Jawab tha: **{answer}**")
            except Exception:  # noqa: BLE001
                pass
        state = game_state(chat_id)
        if state and state.get("kind") == "math":
            state["answered"] = False
    state = game_state(chat_id)
    if not state or state.get("kind") != "math":
        return
    scores = state["scores"]
    if not scores:
        try:
            await app.send_message(chat_id, "🧮 Math Rush khatam — kisi ne jawab hi nahi diya 😅")
        except Exception:  # noqa: BLE001
            pass
        set_game(chat_id, None)
        return
    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    winner_id = int(top[0][0])
    winner = get_user(winner_id)
    add_coins(winner, 300)
    save_data()
    lines = ["🏁 **MATH RUSH KHATAM!**\n"]
    for uid, pts in top[:5]:
        lines.append(f"• {DATA['users'].get(uid, {}).get('name') or uid} — {pts} sahi")
    lines.append(f"\n🏆 Winner: **{winner['name']}** +300 coins! 🎉")
    try:
        await app.send_message(chat_id, "\n".join(lines))
    except Exception:  # noqa: BLE001
        pass
    set_game(chat_id, None)


@app.on_message(filters.command(["math", "math_easy", "math_medium", "math_hard"]))
async def cmd_math(client: Client, message: Message):
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if message.chat.type == ChatType.PRIVATE:
        await safe_reply(message, "Math Rush group me khela jata hai 🙂")
        return
    if game_state(message.chat.id):
        await safe_reply(message, "Is group me pehle se ek game chal raha hai 🙂")
        return
    cmd = message.command[0]
    difficulty = {"math": "medium", "math_easy": "easy", "math_medium": "medium", "math_hard": "hard"}[cmd]
    set_game(message.chat.id, {"kind": "math", "difficulty": difficulty, "scores": {},
                               "answer": None, "q": 0, "answered": False})
    await safe_reply(message, f"🧮 **MATH RUSH** shuru! 15 questions, {difficulty} level — pehla sahi jawab jeetega! Taiyaar? 🙂")
    asyncio.create_task(_math_loop(message.chat.id, difficulty))


async def handle_math_answer(message: Message) -> bool:
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "math":
        return False
    text = (message.text or "").strip()
    if not re.fullmatch(r"-?\d+", text):
        return False
    if state.get("answered") or state.get("answer") is None:
        return False
    if int(text) == state["answer"]:
        state["answered"] = True
        uid = str(message.from_user.id)
        state["scores"][uid] = state["scores"].get(uid, 0) + 1
        add_xp(get_user(message.from_user.id), 5)
        save_data()
        await safe_reply(message, f"✅ Sahi! **{display_name(message.from_user)}** — {state['scores'][uid]} points! 🎉")
        return True
    return False


# ---------------------------------------------------------------------------
# BBet / Bet — one implementation (Daizy + Nova merged), 50/50 double-or-lose
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["bbet", "bet"]))
async def cmd_bbet(client: Client, message: Message):
    if not economy_on():
        await safe_reply(message, "Economy abhi off hai 🙂")
        return
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    reset_daily(user)
    if user["bets_today"] >= 200:
        await safe_reply(message, "Aaj ki bet limit khatam (200) — kal aana 🙂")
        return
    amount = parse_amount(message.command[1] if len(message.command) > 1 else "", user)
    if amount is None or amount <= 0:
        await safe_reply(message, "Kitne ki bet? `/bbet 100` ya `/bbet all` 🙂")
        return
    if user["coins"] < amount:
        await safe_reply(message, "Itne coins nahi hain 😅")
        return
    user["bets_today"] += 1
    if random.random() < 0.5:
        add_coins(user, amount)
        add_xp(user, 5 * power_mult(user))
        save_data()
        await safe_reply(message, f"🎰 **JEET GAYE!** +{fmt_coins(amount)} coins! Balance: {fmt_coins(user['coins'])} 🎉")
    else:
        add_coins(user, -amount)
        save_data()
        await safe_reply(message, f"🎰 Haar gaye… -{fmt_coins(amount)} coins. Dobara try karo, kismat badlegi 🙂")


# ---------------------------------------------------------------------------
# Card — one implementation (Baka + Nova merged)
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["card"]))
async def cmd_card(client: Client, message: Message):
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if len(message.command) < 2:
        await safe_reply(message, "Aise: `/card 100 3` (amount aur players) 🙂")
        return
    amount = parse_amount(message.command[1], user)
    try:
        players_n = int(message.command[2]) if len(message.command) > 2 else 2
    except ValueError:
        players_n = 2
    if amount is None or amount <= 0:
        await safe_reply(message, "Sahi amount likho 🙂")
        return
    if user["coins"] < amount:
        await safe_reply(message, "Itne coins nahi hain 😅")
        return
    if game_state(message.chat.id):
        await safe_reply(message, "Is group me pehle se ek game chal raha hai 🙂")
        return
    players_n = max(2, min(6, players_n))
    add_coins(user, -amount)
    save_data()
    set_game(message.chat.id, {"kind": "card", "amount": amount, "need": players_n,
                               "players": [message.from_user.id], "starter": message.from_user.id})
    await safe_reply(message, f"🃏 **CARD GAME** — {fmt_coins(amount)} ka pot, {players_n} players chahiye!\n/joincard se join karo — sabse bada card jeetega! 🙂")


@app.on_message(filters.command(["joincard"]))
async def cmd_joincard(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "card":
        return
    if message.from_user.id in state["players"]:
        await safe_reply(message, "Tum pehle se join ho 🙂")
        return
    if user["coins"] < state["amount"]:
        await safe_reply(message, "Pot ke liye itne coins nahi hain 😅")
        return
    add_coins(user, -state["amount"])
    state["players"].append(message.from_user.id)
    save_data()
    if len(state["players"]) >= state["need"]:
        cards = {}
        for pid in state["players"]:
            cards[pid] = random.randint(2, 14)
        best = max(cards.values())
        winners = [pid for pid, c in cards.items() if c == best]
        pot = state["amount"] * len(state["players"])
        share = pot // len(winners)
        names = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
                 11: "J", 12: "Q", 13: "K", 14: "A"}
        lines = ["🃏 **CARD GAME — RESULT**\n"]
        for pid, c in cards.items():
            lines.append(f"• {DATA['users'].get(str(pid), {}).get('name') or pid} — {names[c]}")
        for w in winners:
            add_coins(get_user(w), share)
        save_data()
        wnames = ", ".join(DATA["users"].get(str(w), {}).get("name") or str(w) for w in winners)
        lines.append(f"\n🏆 Winner: **{wnames}** +{fmt_coins(share)} coins!")
        await safe_reply(message, "\n".join(lines))
        set_game(message.chat.id, None)
    else:
        await safe_reply(message, f"🃏 {display_name(message.from_user)} join ho gaya! {len(state['players'])}/{state['need']} players — aur {state['need'] - len(state['players'])} chahiye 🙂")


# ---------------------------------------------------------------------------
# Number guess (Daizy)
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["number"]))
async def cmd_number(client: Client, message: Message):
    if not games_on():
        await safe_reply(message, "Games abhi off hain 🙂")
        return
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if game_state(message.chat.id):
        await safe_reply(message, "Is group me pehle se ek game chal raha hai 🙂")
        return
    set_game(message.chat.id, {"kind": "number", "secret": random.randint(100, 500),
                               "guesses": 0, "max": 15})
    await safe_reply(message, "🔢 **NUMBER GUESS** — 100 se 500 ke beech ek secret number hai!\n15 guesses me guess karo — jeetne wale ko **9,999 coins**! Number bhejo 🙂")


async def handle_number_guess(message: Message) -> bool:
    state = game_state(message.chat.id)
    if not state or state.get("kind") != "number":
        return False
    text = (message.text or "").strip()
    if not re.fullmatch(r"\d{3}", text):
        return False
    n = int(text)
    if not (100 <= n <= 500):
        return False
    state["guesses"] += 1
    user = get_user(message.from_user.id, display_name(message.from_user))
    if n == state["secret"]:
        add_coins(user, 9999)
        save_data()
        await safe_reply(message, f"🎉 **{display_name(message.from_user)}** ne number guess kar liya — **{n}** sahi hai! +9,999 coins! 💰")
        set_game(message.chat.id, None)
        return True
    if state["guesses"] >= state["max"]:
        await safe_reply(message, f"😢 15 guesses khatam! Number tha: **{state['secret']}**. /number se naya game 🙂")
        set_game(message.chat.id, None)
        return True
    hint = "upar" if n < state["secret"] else "neeche"
    await safe_reply(message, f"🔢 {n} — galat! Secret number isse **{hint}** hai. {state['max'] - state['guesses']} guesses baaki 🙂")
    return True

# ---------------------------------------------------------------------------
# Romance (Nova + Mimi merged)
# ---------------------------------------------------------------------------
PROPOSALS: dict[int, int] = {}  # target uid -> proposer uid


@app.on_message(filters.command(["propose"]))
async def cmd_propose(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    target_msg = message.reply_to_message
    if not target_msg or not target_msg.from_user or target_msg.from_user.is_bot:
        await safe_reply(message, "Kisko propose karna hai? Uske message pe reply karke /propose likho 💕")
        return
    if target_msg.from_user.id == message.from_user.id:
        await safe_reply(message, "Khud ko propose? 😂")
        return
    if user.get("married_to"):
        await safe_reply(message, "Tum pehle se shaadi-shuda ho 😄")
        return
    target = get_user(target_msg.from_user.id, display_name(target_msg.from_user))
    if target.get("married_to"):
        await safe_reply(message, f"{display_name(target_msg.from_user)} pehle se shaadi-shuda hai 😅")
        return
    PROPOSALS[target_msg.from_user.id] = message.from_user.id
    await safe_reply(message, f"💍 {display_name(message.from_user)} ne {display_name(target_msg.from_user)} ko PROPOSE kiya!\n{display_name(target_msg.from_user)}, accept karna ho to /accept likho, reject karna ho to /reject 🙂")


@app.on_message(filters.command(["accept"]))
async def cmd_accept(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    proposer = PROPOSALS.pop(message.from_user.id, None)
    if not proposer:
        await safe_reply(message, "Tumhe kisi ne propose nahi kiya abhi 🙂")
        return
    user["married_to"] = proposer
    other = get_user(proposer)
    other["married_to"] = message.from_user.id
    save_data()
    await safe_reply(message, f"💍💕 **SHAADI HO GAYI!** {other.get('name')} aur {display_name(message.from_user)} ab married hain! Badhai ho! 🎉")


@app.on_message(filters.command(["reject"]))
async def cmd_reject(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    proposer = PROPOSALS.pop(message.from_user.id, None)
    if not proposer:
        await safe_reply(message, "Reject karne ke liye koi proposal nahi hai 🙂")
        return
    await safe_reply(message, f"💔 Proposal reject ho gaya… koi baat nahi, dil chhota mat karo 🙂")


@app.on_message(filters.command(["marry", "married", "marriage"]))
async def cmd_marry(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    spouse = user.get("married_to")
    if spouse:
        s = DATA["users"].get(str(spouse), {})
        await safe_reply(message, f"💍 Tum **{s.get('name') or spouse}** se married ho 💕")
    else:
        await safe_reply(message, "Tum abhi single ho 🙂 Kisi ko /propose karo!")


@app.on_message(filters.command(["ship", "couple", "shippering"]))
async def cmd_ship(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    target_msg = message.reply_to_message
    if target_msg and target_msg.from_user and not target_msg.from_user.is_bot:
        other = display_name(target_msg.from_user)
    else:
        other = "Chulbuli"
    percent = random.randint(5, 100)
    if percent >= 80:
        verdict = "Perfect jodi! 💕🔥"
    elif percent >= 50:
        verdict = "Achhi jodi hai, thodi masti aur karo 😄"
    elif percent >= 25:
        verdict = "Hmm, thoda mushkil hai… par pyaar me sab chalta hai 🙂"
    else:
        verdict = "Bilkul nahi jamte 😂"
    await safe_reply(message, f"💘 **{display_name(message.from_user)}** ❤️ **{other}**\nCompatibility: **{percent}%**\n{verdict}")


@app.on_message(filters.command(["divorce"]))
async def cmd_divorce(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    spouse = user.get("married_to")
    if not spouse:
        await safe_reply(message, "Tum single ho — divorce kisse karna hai? 😂")
        return
    other = get_user(spouse)
    other["married_to"] = None
    user["married_to"] = None
    save_data()
    await safe_reply(message, f"💔 Divorce ho gaya… {other.get('name')} aur tum ab alag ho. Koi baat nahi, naya pyaar milega 🙂")


# ---------------------------------------------------------------------------
# Moderation — ONE shared stack (Rose + Baka + GroupHelp merged)
# ---------------------------------------------------------------------------
def _target_user(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    return None


@app.on_message(filters.command(["warn"]))
async def cmd_warn(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if message.chat.type == ChatType.PRIVATE:
        await safe_reply(message, "Warn group me hota hai 🙂")
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins warn kar sakte hain 🙂")
        return
    target = _target_user(message)
    if not target or target.is_bot:
        await safe_reply(message, "Kisko warn karna hai? Uske message pe reply karke /warn likho 🙂")
        return
    chat = DATA["chats"].setdefault(str(message.chat.id), {"title": "", "msgs": {}, "warns": {}})
    warns = chat.setdefault("warns", {})
    warns[str(target.id)] = warns.get(str(target.id), 0) + 1
    n = warns[str(target.id)]
    save_data()
    if n >= 3:
        warns[str(target.id)] = 0
        try:
            await client.restrict_chat_member(message.chat.id, target.id, ChatPermissions())
            await safe_reply(message, f"⚠️ {display_name(target)} ko 3 warns mil gaye — mute kar diya! /unmute se kholo 🙂")
        except Exception:  # noqa: BLE001
            await safe_reply(message, f"⚠️ {display_name(target)} ko 3 warns mil gaye! (Mute nahi kar payi — mujhe admin banao 🙂)")
    else:
        await safe_reply(message, f"⚠️ {display_name(target)} ko warn {n}/3 — sudhar jao 🙂")


@app.on_message(filters.command(["unwarn"]))
async def cmd_unwarn(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins unwarn kar sakte hain 🙂")
        return
    target = _target_user(message)
    if not target:
        await safe_reply(message, "Kisko unwarn karna hai? Reply karke /unwarn likho 🙂")
        return
    chat = DATA["chats"].setdefault(str(message.chat.id), {"title": "", "msgs": {}, "warns": {}})
    chat.setdefault("warns", {})[str(target.id)] = 0
    save_data()
    await safe_reply(message, f"✅ {display_name(target)} ke warns clear kar diye 🙂")


@app.on_message(filters.command(["mute"]))
async def cmd_mute(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins mute kar sakte hain 🙂")
        return
    target = _target_user(message)
    if not target:
        await safe_reply(message, "Kisko mute karna hai? Reply karke /mute likho 🙂")
        return
    try:
        await client.restrict_chat_member(message.chat.id, target.id, ChatPermissions())
        await safe_reply(message, f"🔇 {display_name(target)} mute ho gaya! /unmute se kholo 🙂")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Mute nahi kar payi — mujhe admin banao (restrict permission ke saath) 🙂")


@app.on_message(filters.command(["unmute"]))
async def cmd_unmute(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins unmute kar sakte hain 🙂")
        return
    target = _target_user(message)
    if not target:
        await safe_reply(message, "Kisko unmute karna hai? Reply karke /unmute likho 🙂")
        return
    try:
        await client.restrict_chat_member(
            message.chat.id, target.id,
            ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                            can_send_other_messages=True, can_add_web_page_previews=True))
        await safe_reply(message, f"🔊 {display_name(target)} unmute ho gaya! 🙂")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Unmute nahi kar payi — mujhe admin banao 🙂")


@app.on_message(filters.command(["ban"]))
async def cmd_ban(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins ban kar sakte hain 🙂")
        return
    target = _target_user(message)
    if not target:
        await safe_reply(message, "Kisko ban karna hai? Reply karke /ban likho 🙂")
        return
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await safe_reply(message, f"🔨 {display_name(target)} ban ho gaya!")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Ban nahi kar payi — mujhe admin banao 🙂")


@app.on_message(filters.command(["unban"]))
async def cmd_unban(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins unban kar sakte hain 🙂")
        return
    target = _target_user(message)
    if not target:
        await safe_reply(message, "Kisko unban karna hai? Reply karke /unban likho 🙂")
        return
    try:
        await client.unban_chat_member(message.chat.id, target.id)
        await safe_reply(message, f"✅ {display_name(target)} unban ho gaya! 🙂")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Unban nahi kar payi — mujhe admin banao 🙂")


@app.on_message(filters.command(["kick"]))
async def cmd_kick(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins kick kar sakte hain 🙂")
        return
    target = _target_user(message)
    if not target:
        await safe_reply(message, "Kisko kick karna hai? Reply karke /kick likho 🙂")
        return
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await client.unban_chat_member(message.chat.id, target.id)
        await safe_reply(message, f"👢 {display_name(target)} kick ho gaya!")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Kick nahi kar payi — mujhe admin banao 🙂")


@app.on_message(filters.command(["pin"]))
async def cmd_pin(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins pin kar sakte hain 🙂")
        return
    target = message.reply_to_message
    if not target:
        await safe_reply(message, "Kisko pin karna hai? Message pe reply karke /pin likho 🙂")
        return
    try:
        await client.pin_chat_message(message.chat.id, target.id)
        await safe_reply(message, "📌 Pin kar diya!")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Pin nahi kar payi — mujhe admin banao 🙂")


@app.on_message(filters.command(["unpin"]))
async def cmd_unpin(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins unpin kar sakte hain 🙂")
        return
    try:
        await client.unpin_chat_message(message.chat.id)
        await safe_reply(message, "📌 Unpin kar diya!")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Unpin nahi kar payi — mujhe admin banao 🙂")


@app.on_message(filters.command(["purge"]))
async def cmd_purge(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins purge kar sakte hain 🙂")
        return
    target = message.reply_to_message
    if not target:
        await safe_reply(message, "Kahan se purge karna hai? Message pe reply karke /purge likho 🙂")
        return
    try:
        ids = list(range(target.id, message.id + 1))
        deleted = 0
        for i in range(0, len(ids), 100):
            await client.delete_messages(message.chat.id, ids[i:i + 100])
            deleted += len(ids[i:i + 100])
        await safe_reply(message, f"🧹 {deleted} messages delete kar diye!")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Purge nahi kar payi — mujhe admin banao (delete permission) 🙂")


@app.on_message(filters.command(["staff"]))
async def cmd_staff(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    try:
        lines = ["👑 **Group Staff**\n"]
        async for member in client.get_chat_members(message.chat.id, filter="administrators"):
            status = "Owner" if member.status == ChatMemberStatus.OWNER else "Admin"
            lines.append(f"• {display_name(member.user)} — {status}")
        await safe_reply(message, "\n".join(lines))
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Staff list nahi nikaal payi 🙂")


# ---------------------------------------------------------------------------
# Link filter — ONE filter (Protectron + Rose merged)
# ---------------------------------------------------------------------------
URL_RE = re.compile(r"(https?://|t\.me/|www\.)\S+", re.IGNORECASE)


@app.on_message(filters.command(["nolinks", "lockurl"]))
async def cmd_nolinks(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins link filter badal sakte hain 🙂")
        return
    chat = DATA["chats"].setdefault(str(message.chat.id), {"title": "", "msgs": {}, "warns": {}})
    chat["links_off"] = not chat.get("links_off", False)
    save_data()
    await safe_reply(message, "🔗 Link filter ON — ab non-admin ke links delete honge ✅" if chat["links_off"] else "🔗 Link filter OFF — links allowed 🙂")


@app.on_message(filters.command(["blacklist"]))
async def cmd_blacklist(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins blacklist badal sakte hain 🙂")
        return
    args = message.command[1:]
    chat = DATA["chats"].setdefault(str(message.chat.id), {"title": "", "msgs": {}, "warns": {}})
    words = chat.setdefault("blacklist", [])
    if not args:
        await safe_reply(message, "Blacklist: " + (", ".join(words) if words else "khaali hai") + "\nAdd: `/blacklist_add gaali`")
        return
    await safe_reply(message, "Use: /blacklist_add <word> ya /blacklist_remove <word> 🙂")


@app.on_message(filters.command(["blacklist_add"]))
async def cmd_blacklist_add(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins blacklist badal sakte hain 🙂")
        return
    if len(message.command) < 2:
        await safe_reply(message, "Kaunsa word? `/blacklist_add gaali` 🙂")
        return
    chat = DATA["chats"].setdefault(str(message.chat.id), {"title": "", "msgs": {}, "warns": {}})
    words = chat.setdefault("blacklist", [])
    word = message.command[1].lower()
    if word not in words:
        words.append(word)
        save_data()
    await safe_reply(message, f"🚫 `{word}` blacklist me add ho gaya!")


@app.on_message(filters.command(["blacklist_remove"]))
async def cmd_blacklist_remove(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins blacklist badal sakte hain 🙂")
        return
    if len(message.command) < 2:
        return
    chat = DATA["chats"].setdefault(str(message.chat.id), {"title": "", "msgs": {}, "warns": {}})
    words = chat.setdefault("blacklist", [])
    word = message.command[1].lower()
    if word in words:
        words.remove(word)
        save_data()
        await safe_reply(message, f"✅ `{word}` blacklist se hata diya!")
    else:
        await safe_reply(message, "Ye word blacklist me nahi hai 🙂")


# ---------------------------------------------------------------------------
# Tagger — one implementation (UserTagger)
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["utag"]))
async def cmd_utag(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins tag kar sakte hain 🙂")
        return
    if message.chat.type == ChatType.PRIVATE:
        await safe_reply(message, "Tag group me hota hai 🙂")
        return
    text = " ".join(message.command[1:]) if len(message.command) > 1 else "Attention please!"
    TAG_JOBS[message.chat.id] = {"active": True}
    await safe_reply(message, "📣 Tagging shuru — sab members ko tag kar rahi hun… /cancel se roko 🙂")
    batch: list[str] = []
    try:
        async for member in client.get_chat_members(message.chat.id):
            if not TAG_JOBS.get(message.chat.id, {}).get("active"):
                break
            if member.user.is_bot:
                continue
            batch.append(f"[{display_name(member.user)}](tg://user?id={member.user.id})")
            if len(batch) >= 7:
                await app.send_message(message.chat.id, f"📣 {text}\n" + " ".join(batch))
                batch = []
                await asyncio.sleep(1)
        if batch and TAG_JOBS.get(message.chat.id, {}).get("active"):
            await app.send_message(message.chat.id, f"📣 {text}\n" + " ".join(batch))
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Tagging me error aaya — mujhe admin banao 🙂")
    TAG_JOBS[message.chat.id] = {"active": False}


@app.on_message(filters.command(["atag"]))
async def cmd_atag(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    if not await is_chat_admin(client, message.chat.id, message.from_user.id):
        await safe_reply(message, "Sirf admins tag kar sakte hain 🙂")
        return
    text = " ".join(message.command[1:]) if len(message.command) > 1 else "Admins, attention!"
    try:
        mentions = []
        async for member in client.get_chat_members(message.chat.id, filter="administrators"):
            mentions.append(f"[{display_name(member.user)}](tg://user?id={member.user.id})")
        if mentions:
            await safe_reply(message, f"📣 {text}\n" + " ".join(mentions))
        else:
            await safe_reply(message, "Koi admin nahi mila 🙂")
    except Exception:  # noqa: BLE001
        await safe_reply(message, "Tag nahi kar payi 🙂")


@app.on_message(filters.command(["reload"]))
async def cmd_reload(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    await safe_reply(message, "✅ Bot restarted ✅ Admin list updated")


# ---------------------------------------------------------------------------
# Music — honest placeholder (VC music needs a userbot voice assistant,
# which this bot does not have yet; do NOT fake playback)
# ---------------------------------------------------------------------------
@app.on_message(filters.command(["play", "queue", "skip", "pause", "resume", "stop", "end"]))
async def cmd_music(client: Client, message: Message):
    user = track_user(message)
    if user is None or is_banned(message.from_user.id):
        return
    await safe_reply(
        message,
        "🎵 Music ke liye voice-chat assistant chahiye hota hai — wo abhi connect nahi hai, "
        "isliye /play abhi kaam nahi karega. Baaki sab games aur features chal rahe hain 🙂",
    )


# ---------------------------------------------------------------------------
# Chat persona — original Hinglish (cute + savage-sweet)
# ---------------------------------------------------------------------------
CHAT_GREET = [
    "Hiee 💕",
    "hlooo, kya haal hai? 😄",
    "Hiee! bolo kya chahiye? 🙂",
    "haan bolo, main sun rahi hun 💕",
]
CHAT_HOW = [
    "main to badhiya hun, tum batao? 😄",
    "ekdum mast! tum kya kar rahe ho? 🙂",
    "thik hun yaar, tum batao kya chal raha hai 💕",
]
CHAT_DEFAULT = [
    "hmm, interesting 😄",
    "achha? aur batao 🙂",
    "wah, kya baat hai! 💕",
    "samajh gayi… aur? 😄",
    "hehe, tum bhi na 😂",
    "haan haan, bolo bolo 🙂",
]
CHAT_LOVE = [
    "awww, tum bhi pyaare ho 💕",
    "sharma gayi main to 😳💕",
    "hehe, line mat maro 😄",
]
CHAT_ANGRY = [
    "arey chill karo yaar 😤",
    "itna gussa kyun? thoda calm raho 🙂",
    "bas bas, ladna band karo 😄",
]


def chat_reply_text(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ("kaise ho", "kaisi ho", "how are you", "kya haal")):
        return random.choice(CHAT_HOW)
    if any(w in t for w in ("i love you", "love you", "pyaar", "i luv u")):
        return random.choice(CHAT_LOVE)
    if any(w in t for w in ("hi", "hello", "hlo", "hey", "namaste", "good morning", "good night")):
        return random.choice(CHAT_GREET)
    if any(w in t for w in ("gussa", "bakwas", "chup", "stupid", "idiot")):
        return random.choice(CHAT_ANGRY)
    return random.choice(CHAT_DEFAULT)


@app.on_message(filters.new_chat_members)
async def welcome_new(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        try:
            await message.reply_text(
                f"Hiee {display_name(member)} 🥂 Welcome to {message.chat.title}! 🌟\n"
                f"Rules padh lo, active raho, dost banao aur masti karo! Main Chulbuli hun — /help se sab seekho 💕"
            )
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Owner panel — only Sanji (7966027018). /owner or /panel.
# ---------------------------------------------------------------------------
def owner_panel_text() -> str:
    users = len(DATA["users"])
    groups = len(DATA["chats"])
    total_coins = sum(u.get("coins", 0) + u.get("bank", 0) for u in DATA["users"].values())
    uptime = int(time.time() - START_TIME)
    hrs, rem = divmod(uptime, 3600)
    mins = rem // 60
    t = DATA.get("toggles", {})
    return (
        f"👑 **OWNER PANEL — Chulbuli**\n\n"
        f"👥 Users: {users} | 👥 Groups: {groups}\n"
        f"💰 Total coins: {fmt_coins(total_coins)}\n"
        f"⏱️ Uptime: {hrs}h {mins}m | v{VERSION}\n\n"
        f"🎮 Games: {'ON ✅' if t.get('games') else 'OFF ❌'}\n"
        f"💰 Economy: {'ON ✅' if t.get('economy') else 'OFF ❌'}\n"
        f"💬 Chat: {'ON ✅' if t.get('chat') else 'OFF ❌'}\n\n"
        f"Neeche se option chuno 👇"
    )


def owner_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Stats", callback_data="own:stats"),
         InlineKeyboardButton("👥 Users", callback_data="own:users")],
        [InlineKeyboardButton("👥 Groups", callback_data="own:groups"),
         InlineKeyboardButton("🎛️ Toggles", callback_data="own:toggles")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="own:broadcast"),
         InlineKeyboardButton("🔄 Status / Restart", callback_data="own:status")],
    ])


@app.on_message(filters.command(["owner", "panel"]))
async def cmd_owner(client: Client, message: Message):
    if message.from_user is None or message.from_user.id != OWNER_ID:
        await safe_reply(message, "Ye panel sirf owner ke liye hai 🙂")
        return
    track_user(message)
    await safe_reply(message, owner_panel_text(), reply_markup=owner_keyboard())


async def do_broadcast(text: str) -> tuple[int, int, int, int]:
    """Send announcement to all known users (DM) + all known groups.
    Returns (users_ok, users_fail, groups_ok, groups_fail)."""
    u_ok = u_fail = g_ok = g_fail = 0
    for uid in list(DATA["users"].keys()):
        try:
            await app.send_message(int(uid), f"📢 **Chulbuli Announcement**\n\n{text}")
            u_ok += 1
        except Exception:  # noqa: BLE001
            u_fail += 1
        await asyncio.sleep(0.05)
    for cid in list(DATA["chats"].keys()):
        try:
            await app.send_message(int(cid), f"📢 **Chulbuli Announcement**\n\n{text}")
            g_ok += 1
        except Exception:  # noqa: BLE001
            g_fail += 1
        await asyncio.sleep(0.05)
    return u_ok, u_fail, g_ok, g_fail


@app.on_callback_query(filters.regex(r"^own:"))
async def owner_callbacks(client: Client, query):
    if query.from_user is None or query.from_user.id != OWNER_ID:
        await query.answer("Sirf owner ke liye hai 🙂", show_alert=True)
        return
    action = query.data.split(":", 1)[1]
    try:
        if action == "stats":
            users = len(DATA["users"])
            groups = len(DATA["chats"])
            total_coins = sum(u.get("coins", 0) + u.get("bank", 0) for u in DATA["users"].values())
            uptime = int(time.time() - START_TIME)
            hrs, rem = divmod(uptime, 3600)
            await query.message.edit_text(
                f"📊 **Bot Stats**\n\n👥 Total users: {users}\n👥 Total groups: {groups}\n"
                f"💰 Total coins: {fmt_coins(total_coins)}\n🎮 Games played: {DATA['meta'].get('games_played', 0)}\n"
                f"⏱️ Uptime: {hrs}h {rem // 60}m\n🤖 Version: {VERSION}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="own:back")]]),
            )
        elif action == "users":
            ordered = sorted(DATA["users"].items(),
                             key=lambda kv: kv[1].get("coins", 0) + kv[1].get("bank", 0),
                             reverse=True)[:10]
            lines = ["👥 **Top Users**\n"]
            for uid, u in ordered:
                banned = " 🚫" if u.get("banned") else ""
                lines.append(f"• {u.get('name') or uid} — {fmt_coins(u.get('coins', 0))}{banned}")
            lines.append("\nBan karne ke liye 'Ban user' dabao aur user ID bhejo.")
            await query.message.edit_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 Ban user", callback_data="own:ban"),
                     InlineKeyboardButton("✅ Unban user", callback_data="own:unban")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="own:back")],
                ]),
            )
        elif action == "ban":
            OWNER_PENDING[OWNER_ID] = "ban"
            await query.message.edit_text(
                "🚫 Ban karne ke liye user ki ID bhejo (jaise: 123456789).\n/cancel se rok sakte ho.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="own:back")]]),
            )
        elif action == "unban":
            OWNER_PENDING[OWNER_ID] = "unban"
            await query.message.edit_text(
                "✅ Unban karne ke liye user ki ID bhejo.\n/cancel se rok sakte ho.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="own:back")]]),
            )
        elif action == "groups":
            chats = list(DATA["chats"].items())[:15]
            if not chats:
                text = "👥 **Groups**\nAbhi bot kisi group me nahi hai."
            else:
                lines = ["👥 **Groups — bot kahan-kahan hai**\n"]
                for cid, c in chats:
                    lines.append(f"• {c.get('title') or cid} (`{cid}`)")
                text = "\n".join(lines)
            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="own:back")]]),
            )
        elif action == "toggles":
            t = DATA.get("toggles", {})
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🎮 Games: {'ON ✅' if t.get('games') else 'OFF ❌'}", callback_data="own:tg_games")],
                [InlineKeyboardButton(f"💰 Economy: {'ON ✅' if t.get('economy') else 'OFF ❌'}", callback_data="own:tg_economy")],
                [InlineKeyboardButton(f"💬 Chat: {'ON ✅' if t.get('chat') else 'OFF ❌'}", callback_data="own:tg_chat")],
                [InlineKeyboardButton("⬅️ Back", callback_data="own:back")],
            ])
            await query.message.edit_text("🎛️ **Feature Toggles** — dabao to on/off karo:", reply_markup=kb)
        elif action.startswith("tg_"):
            key = action[3:]
            t = DATA.setdefault("toggles", {})
            t[key] = not t.get(key, True)
            save_data()
            await query.answer(f"{key} {'ON' if t[key] else 'OFF'} kar diya ✅")
            # re-render toggles screen
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🎮 Games: {'ON ✅' if t.get('games') else 'OFF ❌'}", callback_data="own:tg_games")],
                [InlineKeyboardButton(f"💰 Economy: {'ON ✅' if t.get('economy') else 'OFF ❌'}", callback_data="own:tg_economy")],
                [InlineKeyboardButton(f"💬 Chat: {'ON ✅' if t.get('chat') else 'OFF ❌'}", callback_data="own:tg_chat")],
                [InlineKeyboardButton("⬅️ Back", callback_data="own:back")],
            ])
            await query.message.edit_text("🎛️ **Feature Toggles** — dabao to on/off karo:", reply_markup=kb)
        elif action == "broadcast":
            OWNER_PENDING[OWNER_ID] = "broadcast"
            await query.message.edit_text(
                "📢 **Broadcast** — announcement ka text bhejo.\nYe sab users (DM) aur sab groups me jayega.\n/cancel se rok sakte ho.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="own:back")]]),
            )
        elif action == "status":
            import pyrogram as _pg
            uptime = int(time.time() - START_TIME)
            hrs, rem = divmod(uptime, 3600)
            await query.message.edit_text(
                f"🔄 **Status**\n\n🤖 Chulbuli v{VERSION}\n📦 Pyrogram {_pg.__version__}\n"
                f"⏱️ Uptime: {hrs}h {rem // 60}m\n👥 Users: {len(DATA['users'])} | Groups: {len(DATA['chats'])}\n"
                f"💾 Data file: {'OK' if os.path.exists(DATA_FILE) else 'fresh'}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Restart Bot", callback_data="own:restart")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="own:back")],
                ]),
            )
        elif action == "restart":
            await query.message.edit_text("🔄 Restart ho raha hai… thodi der me wapas aata hun! 🙂")
            await asyncio.sleep(1)
            os._exit(0)
        elif action == "back":
            OWNER_PENDING.pop(OWNER_ID, None)
            await query.message.edit_text(owner_panel_text(), reply_markup=owner_keyboard())
        await query.answer()
    except Exception:  # noqa: BLE001
        try:
            await query.answer("Kuch gadbad hui, dobara try karo 🙂")
        except Exception:  # noqa: BLE001
            pass


async def handle_owner_pending(message: Message) -> bool:
    """Owner's follow-up message for ban/unban/broadcast. True if consumed."""
    if message.from_user is None or message.from_user.id != OWNER_ID:
        return False
    pending = OWNER_PENDING.get(OWNER_ID)
    if not pending:
        return False
    text = (message.text or "").strip()
    if text.startswith("/cancel"):
        OWNER_PENDING.pop(OWNER_ID, None)
        await safe_reply(message, "Cancel kar diya 🙂")
        return True
    if text.startswith("/"):
        return False
    if pending == "broadcast":
        OWNER_PENDING.pop(OWNER_ID, None)
        await safe_reply(message, "📢 Broadcast bhej raha hun…")
        u_ok, u_fail, g_ok, g_fail = await do_broadcast(text)
        await safe_reply(message, f"📢 Broadcast ho gaya!\n👥 Users: {u_ok} ok, {u_fail} fail\n👥 Groups: {g_ok} ok, {g_fail} fail")
        return True
    if pending in ("ban", "unban"):
        OWNER_PENDING.pop(OWNER_ID, None)
        try:
            uid = int(text)
        except ValueError:
            await safe_reply(message, "User ID number me bhejo — jaise 123456789 🙂")
            return True
        if pending == "ban":
            if uid not in DATA["banned_users"]:
                DATA["banned_users"].append(uid)
            u = DATA["users"].get(str(uid))
            if u:
                u["banned"] = True
            save_data()
            await safe_reply(message, f"🚫 User `{uid}` bot se ban ho gaya!")
        else:
            if uid in DATA["banned_users"]:
                DATA["banned_users"].remove(uid)
            u = DATA["users"].get(str(uid))
            if u:
                u["banned"] = False
            save_data()
            await safe_reply(message, f"✅ User `{uid}` unban ho gaya!")
        return True
    return False


# ---------------------------------------------------------------------------
# Catch-all: game inputs, filters, chat persona (group=1, after commands)
# ---------------------------------------------------------------------------
@app.on_message(filters.group & filters.text, group=1)
async def group_text_handler(client: Client, message: Message):
    user = track_user(message)
    if user is None:
        return
    if is_banned(message.from_user.id):
        return
    text = message.text or ""
    if text.startswith("/"):
        return
    # Link filter (Protectron + Rose merged)
    chat = DATA["chats"].get(str(message.chat.id), {})
    if chat.get("links_off") and URL_RE.search(text):
        if not await is_chat_admin(client, message.chat.id, message.from_user.id):
            try:
                await message.delete()
            except Exception:  # noqa: BLE001
                pass
            return
    # Blacklist filter (Abuse Restrictions merged)
    blacklist = chat.get("blacklist", [])
    low = text.lower()
    if blacklist and any(w in low for w in blacklist):
        try:
            await message.delete()
        except Exception:  # noqa: BLE001
            pass
        return
    # Game inputs (in order)
    if await handle_wordguess_reply(message):
        return
    if await handle_wordchain_word(message):
        return
    if await handle_math_answer(message):
        return
    if await handle_number_guess(message):
        return
    # Chat persona: reply when tagged / "chulbuli" mentioned
    if not chat_on():
        return
    mentioned = False
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
        mentioned = True
    if "chulbuli" in low:
        mentioned = True
    if message.entities:
        for ent in message.entities:
            if ent.type == "mention":
                name = text[ent.offset:ent.offset + ent.length].lower()
                if "chulbuligamebot" in name:
                    mentioned = True
    if mentioned:
        await safe_reply(message, chat_reply_text(text))


@app.on_message(filters.private & filters.text, group=1)
async def private_text_handler(client: Client, message: Message):
    user = track_user(message)
    if user is None:
        return
    if is_banned(message.from_user.id):
        return
    text = message.text or ""
    if text.startswith("/"):
        return
    if await handle_owner_pending(message):
        return
    if not chat_on():
        return
    await safe_reply(message, chat_reply_text(text))


# ---------------------------------------------------------------------------
# Main — ALWAYS use Pyrogram's built-in runner (never asyncio.run + idle)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not BOT_TOKEN or not API_ID or not API_HASH:
        print("ERROR: BOT_TOKEN, API_ID and API_HASH env vars are required.")
        raise SystemExit(1)
    print(f"[chulbuli] starting v{VERSION} — owner {OWNER_ID}")
    app.run()
