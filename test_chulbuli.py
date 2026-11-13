"""Chulbuli test suite — pure functions + simulated handler end-to-end tests.
Run: ../venv/bin/python /tmp/test_chulbuli.py
No network, no real Telegram calls. Token never used here.
"""
import asyncio
import contextlib
from datetime import datetime, timezone
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.expanduser("~/workspace/bot-copy-3in1/chulbuli-bot"))
os.chdir(os.path.expanduser("~/workspace/bot-copy-3in1/chulbuli-bot"))

from pyrogram.errors import BotMethodInvalid, FloodWait

import bot as B

PASS = []
FAIL = []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" — {extra}" if extra and not cond else ""))


# ---------- pure functions ----------
check("wg fear", B.score_word_guess("fire", "fear") == ["green", "blue", "white", "blue"],
      str(B.score_word_guess("fire", "fear")))
check("wg dup letters", B.score_word_guess("ball", "lala") == ["blue", "green", "green", "white"],
      str(B.score_word_guess("ball", "lala")))
check("wg all green", B.score_word_guess("fire", "fire") == ["green"] * 4)
check("wg all white", B.score_word_guess("fire", "junk") == ["white"] * 4)
board = B.word_guess_board("fire", "fear", 1)
check("wg board", "🟩 🟦 ⬜ 🟦" in board and "F E A R" in board and "round 1/6" in board, board)
check("rps rock>scissors", B.rps_winner("rock", "scissors") == 1)
check("rps paper>rock", B.rps_winner("paper", "rock") == 1)
check("rps draw", B.rps_winner("rock", "rock") == 0)
check("rps lose", B.rps_winner("rock", "paper") == 2)
for _ in range(20):
    q, a = B.math_question("easy")
    assert eval(q.replace("×", "*").replace(" = ?", "")) == a, q
check("math 20 ok", True)
grid, placed = B.place_grid_words(["ship", "candy", "fire"])
check("grid 8x8", len(grid) == 8 and all(len(r) == 8 for r in grid))
check("grid placed>=2", len(placed) >= 2, str(list(placed)))
u = {"coins": 5000}
check("amount num", B.parse_amount("100", u) == 100)
check("amount all", B.parse_amount("all", u) == 5000)
check("amount half", B.parse_amount("half", u) == 2500)
check("amount k", B.parse_amount("2k", u) == 2000)
check("amount bad", B.parse_amount("abc", u) is None)
check("level", B.level_for(0) == 1 and B.level_for(100) == 2 and B.level_for(400) == 3)
check("wg wordlist", len(B.WORD_GUESS_WORDS) == 210 and "fire" in B.WORD_GUESS_WORDS
      and all(len(w) == 4 for w in B.WORD_GUESS_WORDS))


# ---------- Phase 2 pure-function checks ----------
check("uno deck 108", len(B.uno_new_deck()) == 108)
check("uno can play color", B.uno_can_play(("r", "5"), ("g", "5"), "g"))
check("uno can play value", B.uno_can_play(("r", "5"), ("g", "9"), "g") is False)
check("uno can play same value", B.uno_can_play(("r", "5"), ("g", "5"), "b"))
check("uno wild", B.uno_can_play(("W", "W"), ("g", "5"), "g"))
check("uno parse r5", B.uno_parse_card("r5") == (("r", "5"), None))
check("uno parse skip", B.uno_parse_card("g skip") == (("g", "S"), None))
check("uno parse wild", B.uno_parse_card("wild red") == (("W", "W"), "r"))
check("uno parse +4", B.uno_parse_card("+4 blue") == (("W", "+4"), "b"))
check("uno parse bad", B.uno_parse_card("xyz") == (None, None))
check("elo update", B.elo_update(1200, 1200) == (1216, 1184))
check("elo update upset", B.elo_update(1000, 1400)[0] > 1016)
check("mines mult 0", B.mines_mult(0) == 1.0)
check("mines mult 10", B.mines_mult(10) == 6.0)
check("crash point range", all(1.0 <= B.crash_point() <= 5.0 for _ in range(50)))
check("roulette color 0", B.roulette_color(0) == "green")
check("roulette color 1", B.roulette_color(1) == "red")
check("roulette color 2", B.roulette_color(2) == "black")
check("roulette color 36", B.roulette_color(36) == "red")
check("hack score partial", B.hack_score("1234", "1243") == (2, 2))
check("hack score exact", B.hack_score("1234", "1234") == (4, 0))
check("hack score none", B.hack_score("1234", "5678") == (0, 0))
check("xoxo win row", B.xoxo_winner(["X", "X", "X", "", "", "", "", "", ""]) == "X")
check("xoxo win col", B.xoxo_winner(["O", "", "", "O", "", "", "O", "", ""]) == "O")
check("xoxo draw", B.xoxo_winner(["X", "O", "X", "X", "O", "O", "O", "X", "X"]) == "draw")
check("xoxo none", B.xoxo_winner(["X", "", "", "", "", "", "", "", ""]) is None)
_bboard = B.bingo_board()
check("bingo board 25", len(_bboard) == 25 and _bboard[12] == 0 and len(set(x for x in _bboard if x)) == 24)
check("bingo lines 1", B.bingo_lines([1, 2, 3, 4, 5] + list(range(6, 26)), {1, 2, 3, 4, 5}) == 1)
check("bingo lines 0", B.bingo_lines([1, 2, 3, 4, 5] + list(range(6, 26)), {1, 2}) == 0)
check("jumble scramble", (lambda w: (lambda s: s != w and sorted(s) == sorted(w))(B.jumble_scramble(w)))("banana"))
check("charades normalize", B.charades_normalize("3 Idiots!") == "3 idiots")
check("bluff deck 52", len(B.bluff_deck()) == 52 and len(set(B.bluff_deck())) == 52)
check("bluff rank", B.bluff_rank_of("10S") == "10" and B.bluff_rank_of("AH") == "A")
check("subway obstacle", B.subway_obstacle()[1] in ("jump", "slide", "dodge"))
check("mafia roles 5", sorted(B.mafia_assign_roles([1, 2, 3, 4, 5]).values()) == ["detective", "doctor", "mafia", "townie", "townie"])
check("mafia roles 8", sorted(B.mafia_assign_roles([1, 2, 3, 4, 5, 6, 7, 8]).values()).count("mafia") == 2)
check("ai models list", len(B.AI_MODELS) >= 1 and B.AI_MODELS[0].endswith(":free"))
_b = B._chess.Board()
_b.push_uci("f2f3"); _b.push_uci("e7e5"); _b.push_uci("g2g4"); _b.push_uci("d8h4")
check("chess fools mate", B._chess is not None and _b.is_checkmate())


# ---------- fake Telegram objects ----------
class FakeUser:
    def __init__(self, uid, name="Tester", username=None):
        self.id = uid
        self.first_name = name
        self.username = username
        self.is_bot = False


class FakeChat:
    def __init__(self, cid, ctype, title="Test Group"):
        self.id = cid
        self.type = ctype
        self.title = title


class FakeDialog:
    """Minimal dialog for the peer-cache walk (only .chat.id is read)."""
    def __init__(self, chat_id):
        self.chat = FakeChat(chat_id, "supergroup")


class FakeMessage:
    _id = 1000
    outbox = []  # (chat_id, text) of everything the bot "sent"
    outbox_full = []  # (chat_id, text, kwargs) — same sends, with reply_markup etc.
    edits = []  # (chat_id, text, kwargs) of every edit_text call

    def __init__(self, text, uid=111, name="Tester", chat_id=-100123, ctype="group",
                 reply_to=None, username=None):
        FakeMessage._id += 1
        self.id = FakeMessage._id
        self.text = text
        self.from_user = FakeUser(uid, name, username)
        from pyrogram.enums import ChatType
        self.chat = FakeChat(chat_id, ChatType.GROUP if ctype == "group" else ChatType.PRIVATE,
                             "Test Group" if ctype == "group" else "")
        self.reply_to_message = reply_to
        self.entities = None
        self.date = datetime.now(timezone.utc)
        parts = text.split()
        self.command = [p.lstrip("/").split("@")[0] for p in parts] if parts and parts[0].startswith("/") else []

    async def reply_text(self, text, **kwargs):
        FakeMessage.outbox.append((self.chat.id, text))
        FakeMessage.outbox_full.append((self.chat.id, text, kwargs))
        m = FakeMessage.__new__(FakeMessage)
        FakeMessage._id += 1
        m.id = FakeMessage._id
        m.text = text
        m.from_user = FakeUser(999, "Chulbuli")
        m.from_user.is_bot = True
        m.chat = self.chat
        m.reply_to_message = None
        m.entities = None
        m.command = []
        return m

    async def edit_text(self, text, **kwargs):
        FakeMessage.edits.append((self.chat.id, text, kwargs))
        self.text = text
        return self

    async def delete(self):
        return True


class FakeCallbackQuery:
    """Stand-in for a Pyrogram CallbackQuery (menu / join buttons)."""

    def __init__(self, data, uid=111, name="Tester", message=None):
        self.data = data
        self.from_user = FakeUser(uid, name)
        self.message = message
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))


class FakeChatMember:
    def __init__(self, user, status="administrator", privileges=None):
        self.user = user
        self.status = status
        self.privileges = privileges


class FakeApp:
    """Stand-in for the module-global Pyrogram client (DM sends in games)."""
    calls = []
    me = FakeUser(8405203833, "Chulbuli")
    # The bot's own admin rights in the test group (real ChatPrivileges object,
    # like get_chat_member returns for an admin). Tests may narrow it.
    bot_privileges = B.ChatPrivileges(
        can_manage_chat=True, can_delete_messages=True, can_manage_video_chats=True,
        can_restrict_members=True, can_promote_members=True, can_change_info=True,
        can_post_messages=True, can_edit_messages=True, can_invite_users=True,
        can_pin_messages=True)

    async def get_me(self):
        return FakeApp.me

    async def send_message(self, chat_id, text, **kwargs):
        FakeMessage.outbox.append((chat_id, text))
        FakeMessage.outbox_full.append((chat_id, text, kwargs))
        m = FakeMessage.__new__(FakeMessage)
        FakeMessage._id += 1
        m.id = FakeMessage._id
        m.text = text
        return m

    async def send_chat_action(self, chat_id, action):
        FakeApp.calls.append(("chat_action", chat_id, str(action)))
        return True

    async def send_reaction(self, chat_id, message_id, emoji=""):
        FakeApp.calls.append(("reaction", chat_id, message_id, emoji))
        return True

    async def edit_message_text(self, chat_id, message_id, text, **kwargs):
        FakeMessage.edits.append((chat_id, text, kwargs))
        return None

    async def get_chat_members(self, chat_id, filter=None):
        yield FakeChatMember(FakeUser(7966027018, "Sanji"), "owner")
        yield FakeChatMember(FakeUser(222, "Admin2"), "administrator")

    async def get_chat_member(self, chat_id, user_id):
        return FakeChatMember(FakeUser(user_id, "Tester"), "administrator",
                              privileges=FakeApp.bot_privileges)

    async def promote_chat_member(self, chat_id, user_id, privileges=None, **kwargs):
        # Mirror real Pyrogram 2.0.106: only a ChatPrivileges object is accepted.
        # The old bot code passed boolean kwargs and raised TypeError on every
        # call — the permissive fake hid that, so the fake must be strict now.
        if kwargs:
            raise TypeError(f"promote_chat_member() got unexpected keyword arguments {sorted(kwargs)}")
        FakeApp.calls.append(("promote", chat_id, user_id, privileges))
        return True

    async def set_administrator_title(self, chat_id, user_id, title):
        FakeApp.calls.append(("title", chat_id, user_id, title))
        return True

    async def restrict_chat_member(self, chat_id, user_id, permissions=None, **kwargs):
        FakeApp.calls.append(("restrict", chat_id, user_id))
        return True

    async def ban_chat_member(self, chat_id, user_id, **kwargs):
        FakeApp.calls.append(("ban", chat_id, user_id))
        return True

    async def unban_chat_member(self, chat_id, user_id, **kwargs):
        FakeApp.calls.append(("unban", chat_id, user_id))
        return True

    async def pin_chat_message(self, chat_id, message_id, **kwargs):
        FakeApp.calls.append(("pin", chat_id, message_id))
        return True

    async def unpin_chat_message(self, chat_id, **kwargs):
        FakeApp.calls.append(("unpin", chat_id))
        return True

    async def delete_messages(self, chat_id, message_ids, **kwargs):
        FakeApp.calls.append(("delete_messages", chat_id, list(message_ids)))
        return True

    async def export_chat_invite_link(self, chat_id):
        return "https://t.me/+fakeinvite"

    get_chat_calls = []
    get_chat_fail = {}  # chat_id -> exception instance to raise
    invoke_calls = []
    dialogs_called = False

    async def invoke(self, query, *args, **kwargs):
        FakeApp.invoke_calls.append(query)
        return None

    async def get_chat(self, chat_id):
        FakeApp.get_chat_calls.append(chat_id)
        if chat_id in FakeApp.get_chat_fail:
            raise FakeApp.get_chat_fail[chat_id]

        class _C:
            username = None
            invite_link = None
        return _C()

    # Dialogs the bot is in (incl. moonlight's large-id supergroup, whose
    # numeric channel id exceeds 2**31-1 — the "Peer id invalid" case).
    # NOTE: only the ASSISTANT (a user client) may walk these — the real
    # Telegram API rejects messages.GetDialogs for BOTS with 400
    # BOT_METHOD_INVALID, so the bot peer-cache path must never call it.
    dialogs = [-1003866876068, -100502, 111]

    async def get_dialogs(self, limit=0):
        # Mirror real Telegram: bots CANNOT call messages.GetDialogs.
        # If the bot population ever calls this, the test fails loudly.
        FakeApp.dialogs_called = True
        raise BotMethodInvalid("The method can't be used by bots")


class DummyClient:
    pass


async def main():
    client = DummyClient()
    B.app = FakeApp()  # DM sends (UNO hands, mafia roles, ...) go to the outbox
    # Hermetic run: fresh data, and keep saves out of the repo's data.json
    B.DATA = B._blank_data()
    B.DATA_FILE = "/tmp/test_chulbuli_data.json"
    if os.path.exists(B.DATA_FILE):
        os.remove(B.DATA_FILE)
    FakeMessage.outbox.clear()

    # /start in DM
    m = FakeMessage("/start", uid=111, chat_id=111, ctype="private")
    await B.cmd_start_help(client, m)
    check("/start replies", any("Chulbuli" in t for _, t in FakeMessage.outbox))

    # /bal — new user starts with 1000 coins
    FakeMessage.outbox.clear()
    m = FakeMessage("/bal", uid=111, chat_id=111, ctype="private")
    await B.cmd_bal(client, m)
    check("/bal 1000", any("$1,000" in t for _, t in FakeMessage.outbox),
          str(FakeMessage.outbox[-1][1] if FakeMessage.outbox else ""))

    # /daily — first claim +1400, second claim cooldown
    FakeMessage.outbox.clear()
    m = FakeMessage("/daily", uid=111, chat_id=111, ctype="private")
    await B.cmd_daily(client, m)
    check("/daily +1400", any("1,400" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_daily(client, m)
    check("/daily cooldown", any("baad aana" in t for _, t in FakeMessage.outbox))

    # /deposit + /withdraw
    FakeMessage.outbox.clear()
    await B.cmd_deposit(client, FakeMessage("/deposit 500", uid=111, chat_id=111, ctype="private"))
    check("/deposit", any("500" in t and "Bank" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_withdraw(client, FakeMessage("/withdraw 200", uid=111, chat_id=111, ctype="private"))
    check("/withdraw", any("200" in t for _, t in FakeMessage.outbox))

    # /give via reply
    FakeMessage.outbox.clear()
    target_msg = FakeMessage("hello", uid=222, name="Friend", chat_id=-100123)
    give = FakeMessage("/give 100", uid=111, chat_id=-100123, reply_to=target_msg)
    await B.cmd_give(client, give)
    check("/give", any("100" in t for _, t in FakeMessage.outbox))
    check("/give balances", B.DATA["users"]["111"]["coins"] == 1000 + 1400 - 500 + 200 - 100
          and B.DATA["users"]["222"]["coins"] == 1000 + 100,
          f"111={B.DATA['users']['111']['coins']} 222={B.DATA['users']['222']['coins']}")

    # /owner from non-owner is refused
    FakeMessage.outbox.clear()
    await B.cmd_owner(client, FakeMessage("/owner", uid=111, chat_id=111, ctype="private"))
    check("/owner refused", any("sirf owner" in t for _, t in FakeMessage.outbox))

    # Word Guess end-to-end in group
    FakeMessage.outbox.clear()
    start = FakeMessage("/wordguess", uid=111, chat_id=-100123)
    await B.cmd_wordguess(client, start)
    check("/wordguess starts", any("WORD GUESS" in t for _, t in FakeMessage.outbox))
    state = B.game_state(-100123)
    check("wg state secret 4-letter", state and len(state["secret"]) == 4)
    board_id = state["board_msg_id"]
    # wrong guess (reply to board)
    board_msg = FakeMessage("board", uid=999, chat_id=-100123)
    board_msg.id = board_id
    board_msg.from_user.is_bot = True
    FakeMessage.outbox.clear()
    wrong = "zzzz" if state["secret"] != "zzzz" else "qqqq"
    guess = FakeMessage(wrong, uid=111, chat_id=-100123, reply_to=board_msg)
    consumed = await B.handle_wordguess_reply(guess)
    check("wg wrong guess consumed", consumed)
    check("wg new board message (spam ok)", any("round 1/6" in t for _, t in FakeMessage.outbox),
          str([t[:60] for _, t in FakeMessage.outbox]))
    # correct guess (reply to the NEW board message)
    state = B.game_state(-100123)
    board_msg2 = FakeMessage("board2", uid=999, chat_id=-100123)
    board_msg2.id = state["board_msg_id"]
    board_msg2.from_user.is_bot = True
    before = B.DATA["users"]["111"]["coins"]
    FakeMessage.outbox.clear()
    guess2 = FakeMessage(state["secret"], uid=111, chat_id=-100123, reply_to=board_msg2)
    consumed = await B.handle_wordguess_reply(guess2)
    check("wg win consumed", consumed)
    check("wg win +500", B.DATA["users"]["111"]["coins"] == before + 500,
          f"before={before} after={B.DATA['users']['111']['coins']}")
    check("wg win message", any("guess kar liya" in t for _, t in FakeMessage.outbox))
    check("wg round cleared", B.game_state(-100123) is None)

    # /rob via reply (force success path by seeding random? just check it replies sanely)
    FakeMessage.outbox.clear()
    victim_msg = FakeMessage("hi", uid=222, name="Friend", chat_id=-100123)
    await B.cmd_rob(client, FakeMessage("/rob", uid=111, chat_id=-100123, reply_to=victim_msg))
    check("/rob replies", len(FakeMessage.outbox) == 1)

    # /protect + /shield
    FakeMessage.outbox.clear()
    await B.cmd_protect(client, FakeMessage("/protect", uid=111, chat_id=111, ctype="private"))
    check("/protect", any("Shield lag gaya" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_shield(client, FakeMessage("/shield", uid=111, chat_id=111, ctype="private"))
    check("/shield on", any("Shield ON" in t for _, t in FakeMessage.outbox))

    # chat persona in group (mentions chulbuli)
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("chulbuli kaisi ho?", uid=111, chat_id=-100123))
    check("chat persona", len(FakeMessage.outbox) == 1)

    # banned user ignored
    B.DATA["banned_users"].append(999)
    FakeMessage.outbox.clear()
    await B.cmd_bal(client, FakeMessage("/bal", uid=999, chat_id=111, ctype="private"))
    check("banned ignored", len(FakeMessage.outbox) == 0)
    B.DATA["banned_users"].remove(999)

    # ================= Phase 2 simulated end-to-end tests =================
    _orig_sleep = asyncio.sleep

    async def _fast_sleep(d):
        return None

    # /start + /help list every Phase 2 game as live
    _games = ("/uno", "/chess", "/mines", "/tap", "/crash", "/jumble", "/charades",
              "/bingo", "/xoxo", "/mafia", "/hack", "/bomb", "/roulette", "/bluff",
              "/subway", "/scribble")
    check("/start lists phase2", all(x in B.START_TEXT for x in _games))
    check("/help lists phase2", all(x in B.HELP_TEXT for x in _games))
    check("/help no coming soon", "phase 2 me aa rahe hain" not in B.HELP_TEXT)
    FakeMessage.outbox.clear()
    await B.cmd_start_help(client, FakeMessage("/help", uid=111, chat_id=111, ctype="private"))
    check("/help handler", any("/uno" in t and "/mafia" in t for _, t in FakeMessage.outbox))

    # ---- UNO: lobby -> join -> forcestart -> play -> draw -> pass -> win ----
    B.get_user(111)["coins"] = 5000
    B.get_user(222)["coins"] = 5000
    await B.cmd_uno(client, FakeMessage("/uno", uid=111, name="Uno1", chat_id=-100201))
    await B.cmd_join_generic(client, FakeMessage("/join", uid=222, name="Uno2", chat_id=-100201))
    FakeMessage.outbox.clear()
    await B.cmd_forcestart(client, FakeMessage("/forcestart", uid=111, name="Uno1", chat_id=-100201))
    st = B.game_state(-100201)
    check("uno started", st is not None and st.get("started") and len(st["hands"][111]) == 7 and len(st["hands"][222]) == 7)
    playable = next((c for c in st["hands"][111] if B.uno_can_play(c, st["top"], st["color"])), None)
    if playable is None:
        # unlucky random deal: force a playable card into the hand so the test is deterministic
        st["hands"][111][0] = (st["color"], "5")
        playable = st["hands"][111][0]
    check("uno playable exists", playable is not None)
    if playable[0] == "W":
        _arg = "wild red" if playable[1] == "W" else "+4 red"
    else:
        _arg = f"{playable[0]}{playable[1]}"
    FakeMessage.outbox.clear()
    await B.cmd_uno_play(client, FakeMessage(f"/play {_arg}", uid=111, name="Uno1", chat_id=-100201))
    check("uno play reduces hand", len(st["hands"][111]) == 6)
    _cur = st["players"][st["turn"] % len(st["players"])]
    _hand_before = len(st["hands"][_cur])
    await B.cmd_uno_draw(client, FakeMessage("/draw", uid=_cur, name="UnoX", chat_id=-100201))
    check("uno draw", len(st["hands"][_cur]) == _hand_before + 1 and st.get("drew"))
    await B.cmd_pass(client, FakeMessage("/pass", uid=_cur, name="UnoX", chat_id=-100201))
    check("uno pass clears drew", st.get("drew") is False)
    # win path: one playable card left
    st["hands"][111] = [("r", "3")]
    st["top"] = ("r", "7"); st["color"] = "r"; st["turn"] = 0; st["discard"] = []
    _before = B.get_user(111)["coins"]
    FakeMessage.outbox.clear()
    await B.cmd_uno_play(client, FakeMessage("/play r3", uid=111, name="Uno1", chat_id=-100201))
    check("uno win", B.game_state(-100201) is None and any("UNO jeet liya" in t for _, t in FakeMessage.outbox))
    check("uno win coins", B.get_user(111)["coins"] == _before + 5000)

    # ---- Chess: fool's mate, illegal move, elo ----
    await B.cmd_chess(client, FakeMessage("/chess", uid=111, name="Chess1", chat_id=-100202))
    await B.cmd_join_generic(client, FakeMessage("/join", uid=222, name="Chess2", chat_id=-100202))
    st = B.game_state(-100202)
    check("chess started", st is not None and st.get("started"))
    await B.cmd_chess_move(client, FakeMessage("/move f2f3", uid=111, name="Chess1", chat_id=-100202))
    await B.cmd_chess_move(client, FakeMessage("/move e7e5", uid=222, name="Chess2", chat_id=-100202))
    FakeMessage.outbox.clear()
    await B.cmd_chess_move(client, FakeMessage("/move e2e5", uid=111, name="Chess1", chat_id=-100202))
    check("chess illegal", any("legal nahi" in t for _, t in FakeMessage.outbox))
    await B.cmd_chess_move(client, FakeMessage("/move g2g4", uid=111, name="Chess1", chat_id=-100202))
    FakeMessage.outbox.clear()
    await B.cmd_chess_move(client, FakeMessage("/move d8h4", uid=222, name="Chess2", chat_id=-100202))
    check("chess checkmate", B.game_state(-100202) is None and any("CHECKMATE" in t for _, t in FakeMessage.outbox))
    check("chess elo changed", B.get_user(222)["elo"] > 1200 and B.get_user(111)["elo"] < 1200)
    FakeMessage.outbox.clear()
    await B.cmd_elo(client, FakeMessage("/elo", uid=111, name="Chess1", chat_id=111, ctype="private"))
    check("/elo", any("Elo" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_chesstop(client, FakeMessage("/chesstop", uid=111, name="Chess1", chat_id=111, ctype="private"))
    check("/chesstop", any("Chess" in t for _, t in FakeMessage.outbox))

    # ---- Mines: safe pick + cashout, and boom ----
    B.get_user(111)["coins"] = 5000
    await B.cmd_mines(client, FakeMessage("/mines 100", uid=111, name="Miner", chat_id=-100203))
    st = B.game_state(-100203)
    check("mines lobby", st is not None and st["kind"] == "mines" and len(st["mines"]) == 3)
    _safe = next(i for i in range(25) if i not in st["mines"])
    _before = B.get_user(111)["coins"]
    await B.cmd_mines_pick(client, FakeMessage(f"/pick {_safe // 5 + 1} {_safe % 5 + 1}", uid=111, name="Miner", chat_id=-100203))
    check("mines safe pick", _safe in B.game_state(-100203)["revealed"])
    FakeMessage.outbox.clear()
    await B.cmd_cashout(client, FakeMessage("/cashout", uid=111, name="Miner", chat_id=-100203))
    check("mines cashout", B.game_state(-100203) is None and B.get_user(111)["coins"] == _before + 123 and any("Cashout" in t for _, t in FakeMessage.outbox))
    B.get_user(111)["coins"] = 5000
    await B.cmd_mines(client, FakeMessage("/mines 100", uid=111, name="Miner", chat_id=-100204))
    st = B.game_state(-100204)
    _mine = next(iter(st["mines"]))
    FakeMessage.outbox.clear()
    await B.cmd_mines_pick(client, FakeMessage(f"/pick {_mine // 5 + 1} {_mine % 5 + 1}", uid=111, name="Miner", chat_id=-100204))
    check("mines boom", B.game_state(-100204) is None and any("BOOM" in t for _, t in FakeMessage.outbox))

    # ---- Tap: lobby + race end (sleep injected to feed taps) ----
    B.get_user(111)["coins"] = 5000
    B.get_user(222)["coins"] = 5000
    await B.cmd_tap(client, FakeMessage("/tap 100", uid=111, name="Tap1", chat_id=-100205))
    await B.cmd_join_generic(client, FakeMessage("/jointap", uid=222, name="Tap2", chat_id=-100205))
    st = B.game_state(-100205)
    check("tap lobby", st is not None and st["players"] == [111, 222])
    _post_bet = B.get_user(111)["coins"]
    FakeMessage.outbox.clear()

    async def _inject_taps(d):
        s = B.game_state(-100205)
        if s is not None and s.get("started"):
            s["taps"] = {"111": 5, "222": 3}

    asyncio.sleep = _inject_taps
    try:
        await B._tap_start(-100205)
    finally:
        asyncio.sleep = _orig_sleep
    check("tap winner", B.game_state(-100205) is None and any("jeet gaya" in t for _, t in FakeMessage.outbox)
          and B.get_user(111)["coins"] == _post_bet + 200)

    # ---- Crash: lobby + crash end (fast sleep), and cashout unit test ----
    B.get_user(111)["coins"] = 5000
    B.get_user(222)["coins"] = 5000
    await B.cmd_crash(client, FakeMessage("/crash 100", uid=111, name="Crash1", chat_id=-100206))
    await B.cmd_join_generic(client, FakeMessage("/joincrash", uid=222, name="Crash2", chat_id=-100206))
    st = B.game_state(-100206)
    check("crash lobby", st is not None and len(st["players"]) == 2)
    FakeMessage.outbox.clear()
    asyncio.sleep = _fast_sleep
    try:
        await B._crash_start(-100206)
    finally:
        asyncio.sleep = _orig_sleep
    check("crash ends", B.game_state(-100206) is None and any("CRASH" in t for _, t in FakeMessage.outbox))
    B.get_user(111)["coins"] = 5000
    await B.cmd_crash(client, FakeMessage("/crash 100", uid=111, name="Crash1", chat_id=-100216))
    st = B.game_state(-100216)
    st["started"] = True; st["mult"] = 2.5; st["players"] = [111]
    FakeMessage.outbox.clear()
    await B.cmd_cashout(client, FakeMessage("/cashout", uid=111, name="Crash1", chat_id=-100216))
    check("crash cashout", B.get_user(111)["coins"] == 4900 + 250 and any("cashout" in t for _, t in FakeMessage.outbox))

    # ---- Jumble + Charades: wrong guess ignored, right guess wins ----
    await B.cmd_jumble(client, FakeMessage("/jumble", uid=111, name="Jum", chat_id=-100217))
    st = B.game_state(-100217)
    check("jumble start", st is not None and "word" in st and st.get("started"))
    check("jumble wrong ignored", await B.handle_jumble_guess(FakeMessage("zzzqqq", uid=222, name="G2", chat_id=-100217)) is False)
    _before = B.get_user(222)["coins"]
    check("jumble win", await B.handle_jumble_guess(FakeMessage(st["word"], uid=222, name="G2", chat_id=-100217)) is True
          and B.game_state(-100217) is None and B.get_user(222)["coins"] == _before + 300)
    await B.cmd_charades(client, FakeMessage("/charades", uid=111, name="Cha", chat_id=-100218))
    st = B.game_state(-100218)
    check("charades start", st is not None and "answer" in st and st.get("started"))
    check("charades wrong ignored", await B.handle_charades_guess(FakeMessage("zzzqqq", uid=222, name="G2", chat_id=-100218)) is False)
    check("charades win", await B.handle_charades_guess(FakeMessage(st["answer"], uid=222, name="G2", chat_id=-100218)) is True
          and B.game_state(-100218) is None)

    # ---- Bingo: lobby + full draw loop (fast sleep) ----
    B.get_user(111)["coins"] = 5000
    B.get_user(222)["coins"] = 5000
    await B.cmd_bingo(client, FakeMessage("/bingo 100", uid=111, name="Bingo1", chat_id=-100207))
    await B.cmd_join_generic(client, FakeMessage("/joinbingo", uid=222, name="Bingo2", chat_id=-100207))
    st = B.game_state(-100207)
    check("bingo lobby", st is not None and st["players"] == [111, 222])
    FakeMessage.outbox.clear()
    asyncio.sleep = _fast_sleep
    try:
        await B._bingo_start(-100207)
    finally:
        asyncio.sleep = _orig_sleep
    check("bingo ends", B.game_state(-100207) is None and any("BINGO" in t for _, t in FakeMessage.outbox))

    # ---- Xoxo: wrong turn, occupied cell, full win line ----
    B.get_user(111)["coins"] = 5000
    B.get_user(222)["coins"] = 5000
    await B.cmd_xoxo(client, FakeMessage("/xoxo 100", uid=111, name="X1", chat_id=-100208))
    await B.cmd_join_generic(client, FakeMessage("/joinxoxo", uid=222, name="X2", chat_id=-100208))
    st = B.game_state(-100208)
    check("xoxo start", st is not None and st.get("started") and st["board"] == [""] * 9)
    FakeMessage.outbox.clear()
    await B.cmd_xoxo_place(client, FakeMessage("/place 5", uid=222, name="X2", chat_id=-100208))
    check("xoxo wrong turn", any("baari nahi" in t for _, t in FakeMessage.outbox))
    await B.cmd_xoxo_place(client, FakeMessage("/place 1", uid=111, name="X1", chat_id=-100208))
    FakeMessage.outbox.clear()
    await B.cmd_xoxo_place(client, FakeMessage("/place 1", uid=222, name="X2", chat_id=-100208))
    check("xoxo occupied", any("bhari hai" in t for _, t in FakeMessage.outbox))
    await B.cmd_xoxo_place(client, FakeMessage("/place 5", uid=222, name="X2", chat_id=-100208))
    await B.cmd_xoxo_place(client, FakeMessage("/place 2", uid=111, name="X1", chat_id=-100208))
    await B.cmd_xoxo_place(client, FakeMessage("/place 6", uid=222, name="X2", chat_id=-100208))
    FakeMessage.outbox.clear()
    await B.cmd_xoxo_place(client, FakeMessage("/place 3", uid=111, name="X1", chat_id=-100208))
    check("xoxo win", B.game_state(-100208) is None and any("jeet gaya" in t for _, t in FakeMessage.outbox))

    # ---- Mafia: lobby -> roles -> night kill -> day vote -> town wins ----
    await B.cmd_mafia(client, FakeMessage("/mafia", uid=111, name="Asha", chat_id=-100209))
    for _uid, _name in [(222, "Bina"), (333, "Chetan"), (444, "Deepak"), (555, "Esha")]:
        await B.cmd_join_generic(client, FakeMessage("/join", uid=_uid, name=_name, chat_id=-100209))
    FakeMessage.outbox.clear()
    await B.cmd_forcestart(client, FakeMessage("/forcestart", uid=111, name="Asha", chat_id=-100209))
    mst = B.MAFIA.get(-100209)
    check("mafia started", mst is not None and mst.get("started") and len(mst["players"]) == 5)
    _roles = list(mst["roles"].values())
    check("mafia roles dealt", _roles.count("mafia") == 1 and _roles.count("detective") == 1 and _roles.count("doctor") == 1)
    _mafia_uid = next(u for u, r in mst["roles"].items() if r == "mafia")
    _doctor_uid = next(u for u, r in mst["roles"].items() if r == "doctor")
    _det_uid = next(u for u, r in mst["roles"].items() if r == "detective")
    _townies = [u for u, r in mst["roles"].items() if r == "townie"]
    _target_uid = _townies[0]
    _target_name = mst["names"][str(_target_uid)]
    FakeMessage.outbox.clear()
    await B.cmd_mafiakill(client, FakeMessage(f"/mafiakill {_target_name}", uid=_mafia_uid, name=mst["names"][str(_mafia_uid)], chat_id=_mafia_uid, ctype="private"))
    check("mafia kill set", mst["night"].get("kill") == _target_uid)
    _other_townie = _townies[1]
    await B.cmd_mafia_save(client, FakeMessage(f"/save {mst['names'][str(_other_townie)]}", uid=_doctor_uid, name=mst["names"][str(_doctor_uid)], chat_id=_doctor_uid, ctype="private"))
    check("mafia save set", mst["night"].get("save") == _other_townie)
    FakeMessage.outbox.clear()
    await B.cmd_mafia_check(client, FakeMessage(f"/check {mst['names'][str(_mafia_uid)]}", uid=_det_uid, name=mst["names"][str(_det_uid)], chat_id=_det_uid, ctype="private"))
    check("mafia check reply", any("MAFIA" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B._mafia_resolve_night(-100209)
    check("mafia night kill", _target_uid not in mst["alive"] and mst["phase"] == "day")
    _mafia_name = mst["names"][str(_mafia_uid)]
    for _u in list(mst["alive"]):
        if _u != _mafia_uid:
            await B.cmd_mafia_vote(client, FakeMessage(f"/vote {_mafia_name}", uid=_u, name=mst["names"][str(_u)], chat_id=-100209))
    asyncio.sleep = _fast_sleep
    try:
        await B._mafia_day_timer(-100209, 1)
    finally:
        asyncio.sleep = _orig_sleep
    check("mafia town wins", -100209 not in B.MAFIA and any("TOWN JEET" in t for _, t in FakeMessage.outbox))

    # ---- Hack: wrong guess, then the real code ----
    B.get_user(111)["coins"] = 5000
    await B.cmd_hack(client, FakeMessage("/hack 100", uid=111, name="Hacker", chat_id=-100210))
    st = B.game_state(-100210)
    check("hack start", st is not None and len(st["code"]) == 4)
    FakeMessage.outbox.clear()
    await B.cmd_hackguess(client, FakeMessage("/hackguess 0000", uid=111, name="Hacker", chat_id=-100210))
    check("hack wrong guess", any("sahi jagah" in t for _, t in FakeMessage.outbox))
    _before = B.get_user(111)["coins"]
    await B.cmd_hackguess(client, FakeMessage(f"/hackguess {st['code']}", uid=111, name="Hacker", chat_id=-100210))
    check("hack win", B.game_state(-100210) is None and B.get_user(111)["coins"] == _before + 100)

    # ---- Bomb: lobby -> pass -> fuse explodes ----
    B.get_user(111)["coins"] = 5000
    B.get_user(222)["coins"] = 5000
    await B.cmd_bomb(client, FakeMessage("/bomb", uid=111, name="Bomber1", chat_id=-100211))
    await B.cmd_join_generic(client, FakeMessage("/join", uid=222, name="Bomber2", chat_id=-100211))
    await B.cmd_forcestart(client, FakeMessage("/forcestart", uid=111, name="Bomber1", chat_id=-100211))
    st = B.game_state(-100211)
    check("bomb start", st is not None and st.get("started") and st.get("holder") in (111, 222))
    _holder = st["holder"]
    _other = 222 if _holder == 111 else 111
    _other_msg = FakeMessage("hi", uid=_other, name="Bomber2" if _other == 222 else "Bomber1", chat_id=-100211)
    FakeMessage.outbox.clear()
    await B.cmd_pass(client, FakeMessage("/pass", uid=_holder, name="Bomber1" if _holder == 111 else "Bomber2", chat_id=-100211, reply_to=_other_msg))
    check("bomb pass", B.game_state(-100211)["holder"] == _other)
    _gid = st.get("gid")
    await B._bomb_fuse(-100211, _gid, 0)
    check("bomb explodes", B.game_state(-100211) is None and any("BOOM" in t for _, t in FakeMessage.outbox))

    # ---- Roulette: reply + coins move by exactly the bet ----
    B.get_user(111)["coins"] = 5000
    _before = B.get_user(111)["coins"]
    FakeMessage.outbox.clear()
    await B.cmd_roulette(client, FakeMessage("/roulette 100 red", uid=111, name="Rou", chat_id=111, ctype="private"))
    check("roulette replies", any("Roulette" in t for _, t in FakeMessage.outbox))
    check("roulette coins", B.get_user(111)["coins"] in (_before - 100, _before + 100))

    # ---- Bluff: claim -> call -> win path ----
    B.get_user(111)["coins"] = 5000
    B.get_user(222)["coins"] = 5000
    await B.cmd_bluff(client, FakeMessage("/bluff 100", uid=111, name="Bluff1", chat_id=-100212))
    await B.cmd_join_generic(client, FakeMessage("/join", uid=222, name="Bluff2", chat_id=-100212))
    await B.cmd_forcestart(client, FakeMessage("/forcestart", uid=111, name="Bluff1", chat_id=-100212))
    st = B.game_state(-100212)
    check("bluff start", st is not None and st.get("started") and len(st["hands"][111]) == 26)
    FakeMessage.outbox.clear()
    await B.cmd_bluff_claim(client, FakeMessage("/claim A 2", uid=111, name="Bluff1", chat_id=-100212))
    check("bluff claim", len(st["hands"][111]) == 24 and len(st["pile"]) == 2)
    FakeMessage.outbox.clear()
    await B.cmd_bluff_call(client, FakeMessage("/call", uid=222, name="Bluff2", chat_id=-100212))
    check("bluff call resolves", len(st["pile"]) == 0 and any("SACH" in t or "BLUFF PAKDA" in t for _, t in FakeMessage.outbox))
    st["hands"][111] = ["AH"]
    st["turn"] = 0
    st["last_claim"] = None
    st["pile"] = []
    FakeMessage.outbox.clear()
    await B.cmd_bluff_claim(client, FakeMessage("/claim A 1", uid=111, name="Bluff1", chat_id=-100212))
    check("bluff win", B.game_state(-100212) is None and any("Bluff jeet gaya" in t for _, t in FakeMessage.outbox))

    # ---- Subway: right move scores, wrong move ends the run ----
    B.get_user(111)["coins"] = 5000
    await B.cmd_subway(client, FakeMessage("/subway", uid=111, name="Sub", chat_id=-100213))
    st = B.game_state(-100213)
    check("subway start", st is not None and st.get("kind") == "subway")
    st["action"] = "jump"
    FakeMessage.outbox.clear()
    await B.cmd_subway_action(client, FakeMessage("/jump", uid=111, name="Sub", chat_id=-100213))
    check("subway correct", B.game_state(-100213)["score"] == 1)
    st = B.game_state(-100213)
    st["action"] = "slide"
    st["answered"] = False
    FakeMessage.outbox.clear()
    await B.cmd_subway_action(client, FakeMessage("/jump", uid=111, name="Sub", chat_id=-100213))
    check("subway wrong ends", B.game_state(-100213) is None and any("SUBWAY KHATAM" in t for _, t in FakeMessage.outbox))

    # ---- Scribble: guess the word, guesser +200, drawer +100 ----
    await B.cmd_scribble(client, FakeMessage("/scribble", uid=111, name="Scrib1", chat_id=-100214))
    await B.cmd_join_generic(client, FakeMessage("/join", uid=222, name="Scrib2", chat_id=-100214))
    await B.cmd_forcestart(client, FakeMessage("/forcestart", uid=111, name="Scrib1", chat_id=-100214))
    st = B.game_state(-100214)
    check("scribble start", st is not None and st.get("started") and st.get("round_started") and st.get("word"))
    _bg = B.get_user(222)["coins"]
    _bd = B.get_user(111)["coins"]
    check("scribble guess", await B.handle_scribble_guess(FakeMessage(st["word"], uid=222, name="Scrib2", chat_id=-100214)) is True
          and B.get_user(222)["coins"] == _bg + 200 and B.get_user(111)["coins"] == _bd + 100)

    # ---- /end clears an active game, does nothing with no game ----
    await B.cmd_wordguess(client, FakeMessage("/wordguess", uid=111, name="End1", chat_id=-100215))
    check("end setup", B.game_state(-100215) is not None)
    FakeMessage.outbox.clear()
    await B.cmd_end_game(client, FakeMessage("/end", uid=111, name="End1", chat_id=-100215))
    check("/end clears", B.game_state(-100215) is None and any("Game khatam" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_end_game(client, FakeMessage("/end", uid=111, name="End1", chat_id=-100215))
    check("/end no game", len(FakeMessage.outbox) == 0)

    # ---- AI chat: no key -> None, fallback rule-based; toggle off -> None;
    #      mocked API success; first model fails -> second model answers ----
    os.environ.pop("OPENROUTER_API_KEY", None)
    check("ai no key", await B.ai_chat_reply("hello ji", "Tester") is None)
    _rb = await B.chat_reply_ai("hello ji")
    check("ai fallback rule-based", isinstance(_rb, str) and len(_rb) > 0)

    class _FakeResp:
        def __init__(self, payload):
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(self._payload).encode()

    _real_urlopen = urllib.request.urlopen
    B.DATA["toggles"]["ai"] = False
    os.environ["OPENROUTER_API_KEY"] = "dummy-test-key"
    check("ai toggle off", await B.ai_chat_reply("hello ji", "Tester") is None)
    B.DATA["toggles"]["ai"] = True

    def _fake_urlopen_ok(req, timeout=20):
        return _FakeResp({"choices": [{"message": {"content": "arey hello ji, kaise ho? 😄"}}]})

    urllib.request.urlopen = _fake_urlopen_ok
    try:
        _got = await B.ai_chat_reply("hi chulbuli", "Tester")
    finally:
        urllib.request.urlopen = _real_urlopen
    check("ai mocked success", _got == "arey hello ji, kaise ho? 😄", str(_got))

    def _fake_urlopen_fail_first(req, timeout=20):
        # fail the FIRST model in the chain (whatever it currently is),
        # the second one must answer
        if B.AI_MODELS[0].encode() in (req.data or b""):
            raise urllib.error.URLError("boom")
        return _FakeResp({"choices": [{"message": {"content": "fallback reply"}}]})

    urllib.request.urlopen = _fake_urlopen_fail_first
    try:
        _got2 = await B.ai_chat_reply("hi", "Tester")
    finally:
        urllib.request.urlopen = _real_urlopen
        os.environ.pop("OPENROUTER_API_KEY", None)
    check("ai fallback model", _got2 == "fallback reply", str(_got2))

    # ---- safe_reply logs failures instead of swallowing them ----
    class _BadMsg(FakeMessage):
        async def reply_text(self, text, **kwargs):
            raise RuntimeError("boom")

    _buf = io.StringIO()
    with contextlib.redirect_stdout(_buf):
        _res = await B.safe_reply(_BadMsg("hi", uid=111, chat_id=111, ctype="private"), "hello")
    check("safe_reply logs", _res is None and "safe_reply failed" in _buf.getvalue(), _buf.getvalue())

    # ================= v2.1.0: no user-visible "AI", real-girl prompt ============
    import re as _re
    _ai_word = _re.compile(r"\bAI\b", _re.IGNORECASE)
    _visible = [B.START_TEXT, B.HELP_TEXT, B.MENU_GAMES_TEXT, B.MENU_ECONOMY_TEXT,
                B.MENU_WORDGUESS_TEXT, B.MENU_ROMANCE_TEXT, B.owner_panel_text(),
                B.balance_text(B.get_user(111), 111, "Tester"), B.toprich_text()]
    for _lst in (B.CHAT_GREET, B.CHAT_HOW, B.CHAT_DEFAULT, B.CHAT_LOVE, B.CHAT_ANGRY, B.CHAT_REAL):
        _visible += list(_lst)
    for _i in range(30):
        _visible.append(B.chat_reply_text("hello ji", "Tester"))
        _visible.append(B.chat_reply_text("kaise ho", "Tester"))
        _visible.append(B.chat_reply_text("tum AI ho?", "Tester"))
        _visible.append(B.chat_reply_text("are you a bot?", "Tester"))
    check("no AI word user-visible", not any(_ai_word.search(s) for s in _visible),
          str([s for s in _visible if _ai_word.search(s)][:2]))
    check("no artificial/openrouter user-visible",
          not any(w in s.lower() for s in _visible for w in ("artificial", "openrouter")), "")
    check("no robot emoji user-visible", not any("🤖" in s for s in _visible), "")
    check("owner panel says Baatein", "💬 Baatein:" in B.owner_panel_text()
          and "AI" not in B.owner_panel_text(), B.owner_panel_text())
    check("ai system never-ai rule", "NOT an AI" in B.AI_SYSTEM and "NEVER" in B.AI_SYSTEM
          and "unless asked" not in B.AI_SYSTEM, "")
    check("ai system memory instruction", "remember" in B.AI_SYSTEM.lower()
          and "facts" in B.AI_SYSTEM.lower(), "")
    check("ai system deflects identity", "Chulbuli hun" in B.AI_SYSTEM, "")
    check("rule-based deflects identity",
          B.chat_reply_text("tum AI ho?", "Tester") in B.CHAT_REAL
          and B.chat_reply_text("are you a bot?", "Tester") in B.CHAT_REAL, "")

    # ================= v2.1.0: strong memory ================================
    _mem_uid = 777001
    B.DATA["memory"].pop(str(_mem_uid), None)
    B.extract_facts(_mem_uid, "mera naam Arjun hai")
    check("memory name", B.memory_name(_mem_uid) == "Arjun", B.memory_name(_mem_uid))
    B.extract_facts(_mem_uid, "mujhe cricket pasand hai")
    B.extract_facts(_mem_uid, "main Delhi se hun")
    _facts = B.memory_facts(_mem_uid)
    check("memory facts", "cricket pasand hai" in _facts and "Delhi se hai" in _facts, str(_facts))
    B.extract_facts(_mem_uid, "mujhe cricket pasand hai")  # duplicate
    check("memory dedupe", B.memory_facts(_mem_uid).count("cricket pasand hai") == 1)
    B.extract_facts(_mem_uid, "mujhe cricket pasand nahi")  # opinion change replaces
    check("memory opinion replace", "cricket pasand nahi" in B.memory_facts(_mem_uid)
          and "cricket pasand hai" not in B.memory_facts(_mem_uid), str(B.memory_facts(_mem_uid)))
    B.extract_facts(_mem_uid, "yaad rakhna main doctor hun")
    check("memory explicit remember", any("doctor" in f for f in B.memory_facts(_mem_uid)),
          str(B.memory_facts(_mem_uid)))
    check("memory no false name", B.memory_name(_mem_uid) == "Arjun", B.memory_name(_mem_uid))
    # /yaad shows name + facts
    FakeMessage.outbox.clear()
    await B.cmd_yaad(client, FakeMessage("/yaad", uid=_mem_uid, name="Arjun", chat_id=_mem_uid, ctype="private"))
    check("yaad shows memory", any("Arjun" in t and "cricket pasand nahi" in t for _, t in FakeMessage.outbox),
          str(FakeMessage.outbox[-1:]))
    # history caps at 20
    B.DATA["history"].pop(str(-100777), None)
    for _i in range(15):
        B.record_exchange(-100777, _mem_uid, "Arjun", f"msg {_i}", f"reply {_i}")
    check("history caps 20", len(B.DATA["history"][str(-100777)]) == 20,
          str(len(B.DATA["history"][str(-100777)])))
    # AI payload carries facts + recent history
    _captured = {}
    _real_post = B._ai_post

    def _capture_post(model, messages):
        _captured["messages"] = messages
        return "haan Arjun, yaad hai mujhe 😄"

    B._ai_post = _capture_post
    B.DATA["toggles"]["ai"] = True
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    try:
        _r = await B.ai_chat_reply("aur batao", "Arjun", chat_id=-100777, user_id=_mem_uid)
    finally:
        B._ai_post = _real_post
        os.environ.pop("OPENROUTER_API_KEY", None)
    _sys = _captured["messages"][0]["content"]
    check("ai payload has facts", "cricket pasand nahi" in _sys and "Naam: Arjun" in _sys, _sys[:300])
    _mid = _captured["messages"][1:-1]
    check("ai payload has history", len(_mid) == 15
          and all(m["role"] in ("user", "assistant") for m in _mid), str(len(_mid)))
    check("ai payload memory first", _captured["messages"][0]["content"].startswith("TUMHE IS USER"),
          _captured["messages"][0]["content"][:80])
    check("ai payload current msg", _captured["messages"][-1]["content"] == "Arjun: aur batao",
          _captured["messages"][-1]["content"])
    check("ai payload reply", _r == "haan Arjun, yaad hai mujhe 😄", str(_r))
    # ---- Name call (Baka/Mimi style): bare "chulbuli" gets a short greeting, NO AI call ----
    check("name call plain", B.is_name_call("chulbuli"))
    check("name call caps", B.is_name_call("Chulbuli"))
    check("name call hi", B.is_name_call("hii chulbuli"))
    check("name call hlo", B.is_name_call("chulbuli hlo"))
    check("name call emoji", B.is_name_call("chulbuli 💕"))
    check("name call oye", B.is_name_call("oye chulbuli"))
    check("not name call question", not B.is_name_call("chulbuli kaise ho?"))
    check("not name call joke", not B.is_name_call("chulbuli joke sunao"))
    check("not name call doing", not B.is_name_call("chulbuli tum kya kar rahi ho"))
    check("not name call no name", not B.is_name_call("hello"))
    check("not name call sentence", not B.is_name_call("mujhe chulbuli pasand hai"))
    _nc_calls = []
    _real_post2 = B._ai_post

    def _record_post(model, messages):
        _nc_calls.append(model)
        return "YEH AI KA LAMBA JAWAB HAI"

    B._ai_post = _record_post
    B.DATA["toggles"]["ai"] = True
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    B.DATA["history"].pop(str(889001), None)
    B.DATA["memory"].pop(str(889001), None)
    try:
        _greet_r = await B.chat_reply_ai("chulbuli", "Tester", chat_id=889001, user_id=889001)
        _q_calls_before = len(_nc_calls)
        _q_r = await B.chat_reply_ai("chulbuli, tumhe cricket pasand hai?", "Tester", chat_id=889001, user_id=889001)
    finally:
        B._ai_post = _real_post2
        os.environ.pop("OPENROUTER_API_KEY", None)
    check("name call no AI call", _q_calls_before == 0, str(_nc_calls))
    check("name call short greeting", _greet_r in B.CHAT_GREET or _greet_r.startswith("hiee Tester") or "Tester" in _greet_r, str(_greet_r))
    check("name call recorded", len(B.DATA["history"].get(str(889001), [])) >= 2)
    check("real question calls AI", len(_nc_calls) == 1 and _q_r == "YEH AI KA LAMBA JAWAB HAI", str(_q_r))
    # name call uses the remembered name
    B.DATA["memory"].pop(str(889002), None)
    B.DATA["history"].pop(str(889002), None)
    B.extract_facts(889002, "mera naam Arjun hai")
    _greet_named = await B.chat_reply_ai("chulbuli", "", chat_id=889002, user_id=889002)
    check("name call remembered name", "Arjun" in _greet_named, str(_greet_named))
    # ---- Daizy style: lowercase, short one-liners, sweet ----
    _all_chat = B.CHAT_GREET + B.CHAT_HOW + B.CHAT_DEFAULT + B.CHAT_LOVE + B.CHAT_ANGRY
    check("daizy all lowercase", all(not s or not s[0].isalpha() or s[0].islower() for s in _all_chat),
          str([s for s in _all_chat if s and s[0].isalpha() and not s[0].islower()]))
    check("daizy all short", all(len(s) <= 60 for s in _all_chat),
          str([s for s in _all_chat if len(s) > 60]))
    check("daizy system lowercase", "lowercase" in B.AI_SYSTEM.lower(), "")
    check("daizy system daizy", "daizy" in B.AI_SYSTEM.lower(), "")
    check("daizy system one line", "one-line" in B.AI_SYSTEM.lower() or "one line" in B.AI_SYSTEM.lower(), "")
    _g = B._greet("")
    check("daizy greet lowercase", _g.startswith(("hiee", "hlooo", "haan")), _g)
    check("daizy start lowercase", B.START_TEXT.startswith("hiee"), B.START_TEXT[:20])
    check("daizy no AI in chat lists", not any("AI" in s for s in _all_chat), "")
    # chat_reply_ai records the exchange + greets by remembered name (no key -> fallback)
    B.DATA["history"].pop(str(888001), None)
    B.DATA["memory"].pop(str(888001), None)
    os.environ.pop("OPENROUTER_API_KEY", None)
    await B.chat_reply_ai("mera naam Simran hai", "Simran", chat_id=888001, user_id=888001)
    check("chat records name", B.memory_name(888001) == "Simran", B.memory_name(888001))
    _r2 = await B.chat_reply_ai("hii", "Simran", chat_id=888001, user_id=888001)
    check("chat greeting uses name", "Simran" in _r2, _r2)
    check("chat history recorded", len(B.DATA["history"][str(888001)]) == 4,
          str(len(B.DATA["history"][str(888001)])))
    # /bhool clears facts but keeps coins
    _coins_before = B.get_user(_mem_uid)["coins"]
    FakeMessage.outbox.clear()
    await B.cmd_bhool(client, FakeMessage("/bhool", uid=_mem_uid, name="Arjun", chat_id=_mem_uid, ctype="private"))
    check("bhool clears facts", B.memory_facts(_mem_uid) == [] and B.memory_name(_mem_uid) == "")
    check("bhool keeps coins", B.get_user(_mem_uid)["coins"] == _coins_before)
    FakeMessage.outbox.clear()
    await B.cmd_yaad(client, FakeMessage("/yaad", uid=_mem_uid, name="Arjun", chat_id=_mem_uid, ctype="private"))
    check("yaad empty after bhool", any("kuch khaas yaad nahi" in t for _, t in FakeMessage.outbox))

    # ================= v2.1.0: inline buttons ===============================
    def _cbs_of(markup):
        return [b.callback_data for row in (markup.inline_keyboard if markup else []) for b in row]

    FakeMessage.outbox.clear(); FakeMessage.outbox_full.clear(); FakeMessage.edits.clear()
    await B.cmd_start_help(client, FakeMessage("/start", uid=111, name="Tester", chat_id=111, ctype="private"))
    _kb = FakeMessage.outbox_full[-1][2].get("reply_markup")
    check("start has menu keyboard", _kb is not None, "")
    check("start menu buttons", "menu:games" in _cbs_of(_kb) and "menu:balance" in _cbs_of(_kb)
          and "menu:help" in _cbs_of(_kb) and "menu:wordguess" in _cbs_of(_kb), str(_cbs_of(_kb)))
    _cb_msg = FakeMessage(B.START_TEXT.format(name="Tester"), uid=999, name="Chulbuli", chat_id=111, ctype="private")
    FakeMessage.edits.clear()
    await B.menu_callbacks(client, FakeCallbackQuery("menu:games", uid=111, name="Tester", message=_cb_msg))
    check("menu games shows games", any("/uno" in t and "/mafia" in t for _, t, _ in FakeMessage.edits),
          str([t[:60] for _, t, _ in FakeMessage.edits]))
    check("menu games back button", "menu:home" in _cbs_of(FakeMessage.edits[-1][2].get("reply_markup")))
    FakeMessage.edits.clear(); FakeMessage.outbox.clear()
    await B.menu_callbacks(client, FakeCallbackQuery("menu:balance", uid=111, name="Tester", message=_cb_msg))
    await B.cmd_bal(client, FakeMessage("/bal", uid=111, name="Tester", chat_id=111, ctype="private"))
    check("menu balance same as bal", FakeMessage.edits[-1][1] == FakeMessage.outbox[-1][1],
          f"{FakeMessage.edits[-1][1][:60]!r} vs {FakeMessage.outbox[-1][1][:60]!r}")
    check("menu balance back button", "menu:home" in _cbs_of(FakeMessage.edits[-1][2].get("reply_markup")))
    FakeMessage.edits.clear(); FakeMessage.outbox.clear()
    await B.menu_callbacks(client, FakeCallbackQuery("menu:top", uid=111, name="Tester", message=_cb_msg))
    await B.cmd_toprich(client, FakeMessage("/toprich", uid=111, name="Tester", chat_id=111, ctype="private"))
    check("menu top same as toprich", FakeMessage.edits[-1][1] == FakeMessage.outbox[-1][1])
    FakeMessage.edits.clear()
    await B.menu_callbacks(client, FakeCallbackQuery("menu:help", uid=111, name="Tester", message=_cb_msg))
    check("menu help shows help", any("Economy" in t for _, t, _ in FakeMessage.edits))
    # UNO lobby has a Join button; button join works and keeps the button
    FakeMessage.outbox.clear(); FakeMessage.outbox_full.clear(); FakeMessage.edits.clear()
    B.get_user(111)["coins"] = 5000
    B.get_user(222)["coins"] = 5000
    await B.cmd_uno(client, FakeMessage("/uno", uid=111, name="Uno1", chat_id=-100201))
    _lobby_kb = FakeMessage.outbox_full[-1][2].get("reply_markup")
    check("uno lobby has join button", _lobby_kb is not None and "join:game" in _cbs_of(_lobby_kb),
          str(_cbs_of(_lobby_kb)))
    _lobby_msg = FakeMessage(FakeMessage.outbox[-1][1], uid=999, name="Chulbuli", chat_id=-100201)
    _jq = FakeCallbackQuery("join:game", uid=222, name="Uno2", message=_lobby_msg)
    await B.join_callbacks(client, _jq)
    check("button join adds player", 222 in B.game_state(-100201)["players"])
    check("button join keeps button", any("join:game" in _cbs_of(kw.get("reply_markup"))
                                          for _, _, kw in FakeMessage.edits), str(FakeMessage.edits))
    check("button join lists players", any("Players:" in t and "Uno2" in t for _, t, _ in FakeMessage.edits),
          str([t for _, t, _ in FakeMessage.edits]))
    check("button join answered", any(a[0] and "Join ho gaya" in a[0] for a in _jq.answers), str(_jq.answers))
    # /join command still works (same logic)
    FakeMessage.outbox.clear()
    _jr = await B.do_join(-100201, 333, "Uno3")
    check("do_join returns text", isinstance(_jr, str) and "join ho gaya" in _jr, str(_jr))
    check("do_join adds player", 333 in B.game_state(-100201)["players"])
    await B.cmd_end_game(client, FakeMessage("/end", uid=111, name="Uno1", chat_id=-100201))

    # ================= v2.2.0: AI model order + memory, music, gap features ====
    # ---- AI: chat model first, code model last; persona + memory ----
    # v2.3.2: old llama/qwen/gemma-3 models 404'd on live logs (2026-11-12) —
    # the list is now drawn only from the live OpenRouter free list.
    check("ai first is chat model", B.AI_MODELS[0] == "liquid/lfm-3-1.7b:free",
          str(B.AI_MODELS))
    check("ai no dead models", not any(m in B.AI_MODELS for m in (
        "meta-llama/llama-3.1-8b-instruct:free",
        "qwen/qwen-2.5-7b-instruct:free",
        "google/gemma-3-4b-it:free")), str(B.AI_MODELS))
    _live_free = {
        "baidu/ernie-5.5-flash-preview:free",
        "thinkingmachines/inkling-2-small:free",
        "liquid/lfm-3-1.7b:free", "recursive/flint-v1.0:free",
        "nvidia/nemotron-3.5-super-vl:free",
        "dots-studio/dots-3-note-preview:free",
        "liquid/lfm-2.5-2.6b:free",
        "nvidia/nemotron-3.5-lightning:free",
        "cohere/north-mini-code:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-4-31b-it:free",
        "openrouter/free",
    }
    check("ai models from live free list", all(m in _live_free for m in B.AI_MODELS),
          str(B.AI_MODELS))
    check("ai code model late", "cohere/north-mini-code:free" in B.AI_MODELS[-4:],
          str(B.AI_MODELS))
    check("ai openrouter fallback last", B.AI_MODELS[-1] == "openrouter/free",
          str(B.AI_MODELS))
    check("ai all models free", all(m.endswith(":free") or m == "openrouter/free"
                                     for m in B.AI_MODELS))
    # fallback chain intact: with no key, ai_chat_reply returns None (the
    # rule-based persona answers instead — never silence, never an error)
    _saved_key = os.environ.pop("OPENROUTER_API_KEY", None)
    try:
        _no_key = await B.ai_chat_reply("hello", "Tester")
        check("ai no key returns none", _no_key is None, str(_no_key))
    finally:
        if _saved_key is not None:
            os.environ["OPENROUTER_API_KEY"] = _saved_key
    check("ai system girl persona", "sweet desi girl" in B.AI_SYSTEM
          and "yaar" in B.AI_SYSTEM and "arre" in B.AI_SYSTEM, "")
    check("ai system memory use", "MEMORY" in B.AI_SYSTEM and "remember" in B.AI_SYSTEM.lower()
          and "facts" in B.AI_SYSTEM.lower(), "")
    check("ai system never robotic", "robotic" in B.AI_SYSTEM.lower()
          and "never lecture" in B.AI_SYSTEM.lower(), "")
    # rule-based fallback still greets by the remembered name
    B.extract_facts(889777, "mera naam Arjun hai")
    _fb_greet = await B.chat_reply_ai("hii", "Tester", chat_id=889777, user_id=889777)
    check("ai fallback greets by name", "Arjun" in _fb_greet, str(_fb_greet))

    # ---- Music: pure queue logic ----
    B.MUSIC.clear()
    _t1 = {"title": "Gaana One", "url": "https://x/1", "audio": "https://a/1", "duration": 200, "by": "A", "by_id": 1}
    _t2 = {"title": "Gaana Two", "url": "https://x/2", "audio": "https://a/2", "duration": 61, "by": "B", "by_id": 2}
    check("music queue add pos", B.music_queue_add(-100500, _t1) == 1
          and B.music_queue_add(-100500, _t2) == 2)
    check("music queue next", B.music_queue_next(-100500)["title"] == "Gaana One")
    check("music queue text", "Gaana Two" in B.music_queue_text(-100500))
    check("music fmt duration", B.fmt_duration(200) == "3:20" and B.fmt_duration(3661) == "1:01:01")
    B.MUSIC.clear()
    _st = B.music_state(-100500)
    _st["current"] = _t1
    check("music player text", "Gaana One" in B.music_player_text(-100500)
          and "baj raha hai" in B.music_player_text(-100500))
    check("music player buttons", "mus:skip" in _cbs_of(B.music_player_markup())
          and "mus:pause" in _cbs_of(B.music_player_markup())
          and "mus:stop" in _cbs_of(B.music_player_markup()))
    # resolve_track raises MusicError when yt-dlp is missing
    _saved_ytdlp = B._yt_dlp
    B._yt_dlp = None
    try:
        B.resolve_track("koi gaana")
        check("music resolve no ytdlp raises", False)
    except B.MusicError:
        check("music resolve no ytdlp raises", True)
    finally:
        B._yt_dlp = _saved_ytdlp

    # ---- Music: /play with no assistant -> honest message, nothing faked ----
    class _FakeYDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, src, download=False):
            if download:
                # mirror real yt-dlp: the FFmpegExtractAudio postprocessor
                # needs BOTH ffmpeg and ffprobe; with the postprocessor on
                # but ffprobe missing, real yt-dlp fails the whole download
                # with "ffprobe and ffmpeg not found" (v2.3.5 root cause —
                # Railway has the imageio-ffmpeg binary only, no ffprobe).
                if self.opts.get("postprocessors") and shutil.which("ffprobe") is None:
                    raise Exception("ERROR: Postprocessing: ffprobe and ffmpeg not found. "
                                    "Please install or provide the path using ffmpeg-location")
                # simulate a real download: write a dummy audio file where
                # outtmpl points — mp3 when the ffmpeg postprocessor is on
                # (as _music_download_sync requests), else the native ext
                ext = "mp3" if self.opts.get("postprocessors") else "m4a"
                path = self.opts["outtmpl"].replace("%(ext)s", ext)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as _f:
                    _f.write(b"fake-audio")
                return {"title": "Test Gaana", "webpage_url": "https://youtube.com/watch?v=test",
                        "url": "https://audio.example/test.m4a", "duration": 200,
                        "requested_downloads": [{"filepath": path}]}
            return {"title": "Test Gaana", "webpage_url": "https://youtube.com/watch?v=test",
                    "url": "https://audio.example/test.m4a", "duration": 200}

    class _FakeYtDlp:
        YoutubeDL = _FakeYDL

    _real_ytdlp = B._yt_dlp
    _real_factory = B._GroupCallFactory
    _real_mkc = B._music_make_client
    _real_session = B.ASSISTANT_SESSION
    B._yt_dlp = _FakeYtDlp
    B.MUSIC.clear()
    FakeMessage.outbox.clear()
    B.ASSISTANT_SESSION = ""
    B._GroupCallFactory = None
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100501))
    check("music play no assistant honest", any("assistant" in t and "connect nahi" in t for _, t in FakeMessage.outbox),
          str([t for _, t in FakeMessage.outbox]))
    check("music play no assistant no fake", B.music_state(-100501).get("current") is None
          and B.music_state(-100501).get("playing") is False)
    # /play in DM -> group-only
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=111, ctype="private"))
    check("music play dm group only", any("group" in t for _, t in FakeMessage.outbox))
    # /ping works
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/ping", uid=111, name="Tester", chat_id=-100501))
    check("music ping", any("pong!" in t for _, t in FakeMessage.outbox))
    # /queue empty, /skip nothing, /stop nothing
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/queue", uid=111, name="Tester", chat_id=-100501))
    check("music queue empty", any("khaali" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/skip", uid=111, name="Tester", chat_id=-100501))
    check("music skip nothing", any("baj nahi raha" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/stop", uid=111, name="Tester", chat_id=-100501))
    check("music stop nothing", any("chal nahi raha" in t for _, t in FakeMessage.outbox))

    # ---- Music: mocked assistant -> queue + player card + controls ----
    # Fakes mirror the REAL pytgcalls 2.1.0 API (verified from the wheel):
    # GroupCallFactory(client) -> get_file_group_call(input_filename,
    # play_on_repeat) -> GroupCallFile with async start(chat_id)/stop(),
    # sync pause_playout()/resume_playout()/stop_playout(), an
    # input_filename property whose setter restarts playout when connected,
    # and an on_playout_ended decorator for async (gc, filename) handlers.
    # There is deliberately NO join_group_call / change_stream /
    # pause_stream / resume_stream / on_stream_end here — calling one raises
    # AttributeError, exactly like the real library would (the v2.2.0–v2.3.3
    # harness faked those names, which is why 401 tests never caught the
    # dead import).
    class _FakeGroupCallFile:
        def __init__(self, input_filename="", output_filename=None, play_on_repeat=False):
            self._input_filename = input_filename or ""
            self.play_on_repeat = play_on_repeat
            self.is_connected = False
            self.started = []
            self.stopped = 0
            self.restarts = []
            self.paused = False
            self._end_handlers = []

        @property
        def input_filename(self):
            return self._input_filename

        @input_filename.setter
        def input_filename(self, value):
            self._input_filename = value or ""
            if self.is_connected:
                self.restarts.append(value)

        async def start(self, chat_id):
            self.started.append(chat_id)
            self.is_connected = True

        async def stop(self):
            self.stopped += 1
            self.is_connected = False

        def pause_playout(self):
            self.paused = True

        def resume_playout(self):
            self.paused = False

        def stop_playout(self):
            self.input_filename = ""

        def on_playout_ended(self, fn):
            self._end_handlers.append(fn)
            return fn

    class _FakeGroupCallFactory:
        def __init__(self, user_client):
            self.user_client = user_client
            self.created = []

        def get_file_group_call(self, input_filename=None, output_filename=None,
                                play_on_repeat=True):
            gc = _FakeGroupCallFile(input_filename=input_filename,
                                    play_on_repeat=play_on_repeat)
            self.created.append(gc)
            return gc

    class _FakeAssistantClient:
        async def start(self):
            return True

        async def get_me(self):
            class _Me:
                username = "CBIOFINDIA"
                id = 8617937893
            return _Me()

        async def join_chat(self, link):
            return True

    B._GroupCallFactory = _FakeGroupCallFactory
    B._music_make_client = lambda: _FakeAssistantClient()
    B.ASSISTANT_SESSION = "fake-session-for-test"
    B._ASSISTANT.update({"client": None, "factory": None, "started": False, "me": None, "init_started": True})
    B.MUSIC.clear()
    FakeMessage.outbox.clear()
    FakeApp.calls.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100502))
    check("music mocked play card", any("Test Gaana" in t for _, t in FakeMessage.outbox),
          str([t for _, t in FakeMessage.outbox]))
    check("music mocked playing", B.music_state(-100502).get("playing") is True
          and B.music_state(-100502)["current"]["title"] == "Test Gaana")
    _gc502 = B.music_state(-100502)["gc"]
    _file502 = B.music_state(-100502)["file"]
    check("music mocked joined call", _gc502 is not None and len(_gc502.started) == 1
          and len(B._ASSISTANT["factory"].created) == 1)
    check("music mocked downloaded file", _file502 is not None and os.path.isfile(_file502),
          str(_file502))
    check("music assistant identity logged", B._ASSISTANT.get("me") is not None
          and B._ASSISTANT["me"].username == "CBIOFINDIA"
          and B._ASSISTANT["me"].id == 8617937893)
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100502))
    check("music mocked queue second", any("queue me add" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/queue", uid=111, name="Tester", chat_id=-100502))
    check("music mocked queue shows", any("Test Gaana" in t for _, t in FakeMessage.outbox))
    await B.cmd_music(client, FakeMessage("/pause", uid=111, name="Tester", chat_id=-100502))
    check("music mocked pause", B.music_state(-100502).get("paused") is True
          and _gc502.paused is True)
    await B.cmd_music(client, FakeMessage("/resume", uid=111, name="Tester", chat_id=-100502))
    check("music mocked resume", B.music_state(-100502).get("paused") is False
          and _gc502.paused is False)
    FakeMessage.edits.clear()
    await B.cmd_music(client, FakeMessage("/skip", uid=111, name="Tester", chat_id=-100502))
    check("music mocked skip plays next", B.music_state(-100502)["current"]["title"] == "Test Gaana"
          and len(_gc502.restarts) == 1)
    check("music mocked skip deletes old file", not os.path.exists(_file502))
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/clear", uid=111, name="Tester", chat_id=-100502))
    check("music mocked clear", B.music_state(-100502)["queue"] == []
          and any("clear" in t for _, t in FakeMessage.outbox))
    _file_before_stop = B.music_state(-100502)["file"]
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/stop", uid=111, name="Tester", chat_id=-100502))
    check("music mocked stop", B.music_state(-100502).get("playing") is False
          and _gc502.stopped >= 1)
    check("music mocked stop deletes file", _file_before_stop is not None
          and not os.path.exists(_file_before_stop)
          and B.music_state(-100502)["file"] is None)
    # music buttons: pause/resume via callback
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100503))
    _pq = FakeCallbackQuery("mus:pause", uid=111, name="Tester",
                            message=FakeMessage("x", uid=111, chat_id=-100503))
    await B.music_callbacks(client, _pq)
    check("music button pause", B.music_state(-100503).get("paused") is True)
    _rq = FakeCallbackQuery("mus:resume", uid=111, name="Tester",
                            message=FakeMessage("x", uid=111, chat_id=-100503))
    await B.music_callbacks(client, _rq)
    check("music button resume", B.music_state(-100503).get("paused") is False)
    # /play stays silent while a UNO game is running (UNO owns /play then)
    B.set_game(-100504, {"kind": "uno", "players": [111], "started": True})
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100504))
    check("music play defers to uno", len(FakeMessage.outbox) == 0)
    B.set_game(-100504, None)
    # restore real music deps
    B._yt_dlp = _real_ytdlp
    B._GroupCallFactory = _real_factory
    B._music_make_client = _real_mkc
    B.ASSISTANT_SESSION = _real_session
    B._ASSISTANT.update({"client": None, "factory": None, "started": False, "me": None, "init_started": False})
    B.MUSIC.clear()

    # ---- v2.3.3: voice-stack diagnostics (logs must show WHY /play fails) ----
    # Live report (2026-11-12 ~22:04 IST): /play found the song but said the
    # voice assistant is not connected — and the logs said nothing about why.
    # voice_unavailable_reason: which piece is missing, never the session value
    _real_factory = B._GroupCallFactory
    _real_session = B.ASSISTANT_SESSION
    B._GroupCallFactory = None
    B.ASSISTANT_SESSION = ""
    check("voice reason factory missing", B.voice_unavailable_reason() == "GroupCallFactory missing",
          B.voice_unavailable_reason())

    class _FakeFactory2:
        def __init__(self, user_client):
            self.user_client = user_client

    B._GroupCallFactory = _FakeFactory2
    check("voice reason session missing", B.voice_unavailable_reason() == "ASSISTANT_SESSION missing",
          B.voice_unavailable_reason())
    B.ASSISTANT_SESSION = "fake-session-for-test"
    check("voice reason ok", B.voice_unavailable_reason() == "voice ok" and B.music_voice_available() is True)
    # startup diagnostics: format + session value redacted
    _saved_path = os.environ.get("PATH", "")
    _buf = io.StringIO()
    with contextlib.redirect_stdout(_buf):
        B.print_startup_diagnostics()
    _diag = _buf.getvalue()
    os.environ["PATH"] = _saved_path
    check("startup diagnostics python", f"[chulbuli] python: {sys.version.split()[0]}" in _diag, _diag)
    check("startup diagnostics voice line",
          "[chulbuli] voice: pytgcalls=True session=set yt_dlp=True ffmpeg=" in _diag, _diag)
    B.ASSISTANT_SESSION = "SECRET-SESSION-VALUE-123"
    _buf2 = io.StringIO()
    with contextlib.redirect_stdout(_buf2):
        B.print_startup_diagnostics()
    _diag2 = _buf2.getvalue()
    os.environ["PATH"] = _saved_path
    check("startup diagnostics redacts session", "SECRET-SESSION-VALUE-123" not in _diag2
          and "session=set" in _diag2, _diag2)
    B.ASSISTANT_SESSION = ""
    # /play with no voice stack logs the exact reason (reply stays honest)
    B._GroupCallFactory = None
    B._yt_dlp = _FakeYtDlp
    FakeMessage.outbox.clear()
    _buf3 = io.StringIO()
    with contextlib.redirect_stdout(_buf3):
        await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100505))
    check("play voice unavailable logged", "/play voice unavailable: GroupCallFactory missing" in _buf3.getvalue(),
          _buf3.getvalue())
    check("play voice unavailable honest reply", any("connect nahi" in t for _, t in FakeMessage.outbox),
          str([t for _, t in FakeMessage.outbox]))
    B._yt_dlp = _real_ytdlp
    # _music_ensure_assistant: every failure path prints the real reason
    B._ASSISTANT.update({"client": None, "factory": None, "started": False, "me": None, "init_started": True})
    _buf4 = io.StringIO()
    with contextlib.redirect_stdout(_buf4):
        _r = await B._music_ensure_assistant()
    check("ensure assistant no session logs", _r is False and "ASSISTANT_SESSION missing" in _buf4.getvalue(),
          _buf4.getvalue())
    B.ASSISTANT_SESSION = "fake-session-for-test"
    _buf5 = io.StringIO()
    with contextlib.redirect_stdout(_buf5):
        _r = await B._music_ensure_assistant()
    check("ensure assistant no pytgcalls logs", _r is False and "pytgcalls not installed" in _buf5.getvalue(),
          _buf5.getvalue())

    class _BoomClient:
        async def start(self):
            raise RuntimeError("boom-start")

        async def get_me(self):
            raise RuntimeError("should not reach get_me")

    _real_mkc = B._music_make_client
    B._GroupCallFactory = _FakeFactory2
    B._music_make_client = lambda: _BoomClient()
    _buf6 = io.StringIO()
    with contextlib.redirect_stdout(_buf6):
        _r = await B._music_ensure_assistant()
    os.environ["PATH"] = _saved_path
    check("ensure assistant start failure logs", _r is False and "boom-start" in _buf6.getvalue(),
          _buf6.getvalue())
    B._music_make_client = _real_mkc
    # import-failure prints: real import blocks, shadowed modules, subprocess
    _shadow = tempfile.mkdtemp(prefix="chulbuli-import-shadow-")
    for _mod, _marker in (("yt_dlp", "boom-yt"), ("pytgcalls", "boom-calls"),
                          ("imageio_ffmpeg", "boom-ff")):
        with open(os.path.join(_shadow, _mod + ".py"), "w") as _f:
            _f.write(f"raise ImportError('{_marker}')\n")
    _env = dict(os.environ)
    _env["PYTHONPATH"] = _shadow + os.pathsep + _env.get("PYTHONPATH", "")
    _botdir = os.path.expanduser("~/workspace/bot-copy-3in1/chulbuli-bot")
    _res = subprocess.run([sys.executable, "-c", "import bot"], cwd=_botdir, env=_env,
                          capture_output=True, text=True, timeout=120)
    _imp_out = _res.stdout
    check("import failure print yt-dlp", "yt-dlp import failed" in _imp_out and "boom-yt" in _imp_out,
          _imp_out[:500])
    check("import failure print pytgcalls", "pytgcalls import failed" in _imp_out and "boom-calls" in _imp_out,
          _imp_out[:500])
    check("import failure print ffmpeg", "imageio-ffmpeg import failed" in _imp_out and "boom-ff" in _imp_out,
          _imp_out[:500])
    # restore music state
    B._GroupCallFactory = _real_factory
    B.ASSISTANT_SESSION = _real_session
    B._ASSISTANT.update({"client": None, "factory": None, "started": False, "me": None, "init_started": False})
    B.MUSIC.clear()

    # ---- v2.3.4: voice layer on the REAL pytgcalls 2.1.0 API ----
    # Root cause (v2.3.3 logs, 2026-11-12 ~22:14 IST): the import failed with
    # "cannot import name 'PyTgCalls'" — the 2.1.0 wheel has no such class,
    # and 2.1.0 is the latest pytgcalls on PyPI. The voice layer now uses
    # GroupCallFactory -> GroupCallFile (local file, input_filename switch,
    # on_playout_ended auto-advance) instead of the never-shipped 3.x API.
    _src = open(os.path.join(os.path.dirname(B.__file__), "bot.py")).read()
    _old_api = ["PyTgCalls", "AudioPiped", "join_group_call", "leave_group_call",
                "change_stream", "pause_stream", "resume_stream", "on_stream_end"]
    check("old voice api absent from bot.py",
          all(name not in _src for name in _old_api),
          str([n for n in _old_api if n in _src]))
    check("new voice api present in bot.py",
          "GroupCallFactory" in _src and "get_file_group_call" in _src
          and "on_playout_ended" in _src and "input_filename" in _src)
    # download: sync function writes a real file; blocked download -> honest error
    B._yt_dlp = _FakeYtDlp
    _dl_track = {"title": "Test Gaana", "url": "https://youtube.com/watch?v=test",
                 "audio": "https://audio.example/test.m4a", "duration": 200}
    _dl_path = B._music_download_sync(_dl_track)
    check("download sync writes file", os.path.isfile(_dl_path), str(_dl_path))
    B._music_delete_file(_dl_path)
    check("download delete removes file", not os.path.exists(_dl_path))

    class _FakeYtDlpBlockedDl:
        class YoutubeDL:
            def __init__(self, opts):
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def extract_info(self, src, download=False):
                if download:
                    raise Exception("ERROR: [youtube] x: Sign in to confirm you're not a bot")
                return {"title": "Test Gaana", "webpage_url": "https://youtube.com/watch?v=test",
                        "url": "https://audio.example/test.m4a", "duration": 200}

    _real_ytdlp2 = B._yt_dlp
    B._yt_dlp = _FakeYtDlpBlockedDl
    try:
        B._music_download_sync(_dl_track)
        check("download sync youtube blocked", False)
    except B.MusicError as _e:
        check("download sync youtube blocked", str(_e) == "youtube_blocked", str(_e))
    B._yt_dlp = _real_ytdlp2
    # ---- v2.3.5: ffprobe missing -> no mp3 extract, native file kept ----
    # (Sanji's live /play report, 2026-11-13: "download failed: ERROR:
    # Postprocessing: ffprobe and ffmpeg not found". Root cause: the old
    # code added FFmpegExtractAudio whenever ffmpeg was findable, but the
    # postprocessor needs BOTH ffmpeg and ffprobe — imageio-ffmpeg ships
    # ffmpeg only, so on Railway the whole download failed even though
    # the audio itself downloaded fine. Now the postprocessor is added
    # only when both binaries are findable; else the native container is
    # kept, which tgcalls decodes itself.)
    _real_which = shutil.which

    def _which_no_ffprobe(name):
        if name == "ffprobe":
            return None
        return _real_which(name)

    def _which_both(name):
        if name in ("ffmpeg", "ffprobe"):
            return f"/usr/bin/{name}"
        return _real_which(name)

    _buf235 = io.StringIO()
    shutil.which = _which_no_ffprobe
    try:
        with contextlib.redirect_stdout(_buf235):
            _dl_path235 = B._music_download_sync(_dl_track)
    finally:
        shutil.which = _real_which
    check("v235 ffprobe missing download succeeds", os.path.isfile(_dl_path235), str(_dl_path235))
    check("v235 ffprobe missing native ext", _dl_path235.endswith((".m4a", ".webm", ".opus")),
          str(_dl_path235))
    check("v235 ffprobe missing skip logged", "ffprobe missing" in _buf235.getvalue(),
          _buf235.getvalue())
    B._music_delete_file(_dl_path235)
    shutil.which = _which_both
    try:
        _dl_path235b = B._music_download_sync(_dl_track)
    finally:
        shutil.which = _real_which
    check("v235 both present mp3", _dl_path235b.endswith(".mp3"), str(_dl_path235b))
    B._music_delete_file(_dl_path235b)
    # the fake mirrors real yt-dlp: postprocessor on + ffprobe missing fails
    _forced235 = _FakeYDL({"outtmpl": os.path.join(B._MUSIC_TMPDIR, "forced235.%(ext)s"),
                           "postprocessors": [{"key": "FFmpegExtractAudio"}]})
    shutil.which = _which_no_ffprobe
    try:
        _forced235.extract_info("https://youtube.com/watch?v=test", download=True)
        check("v235 fake postprocessor fails without ffprobe", False)
    except Exception as _e235:
        check("v235 fake postprocessor fails without ffprobe",
              "ffprobe and ffmpeg not found" in str(_e235), str(_e235))
    finally:
        shutil.which = _real_which
    # full mocked flow on the 2.1.0 API: play -> skip -> playout-end advance -> stop
    B._GroupCallFactory = _FakeGroupCallFactory
    B._music_make_client = lambda: _FakeAssistantClient()
    B.ASSISTANT_SESSION = "fake-session-for-test"
    B._ASSISTANT.update({"client": None, "factory": None, "started": False, "me": None, "init_started": True})
    B.MUSIC.clear()
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100506))
    _gc506 = B.music_state(-100506)["gc"]
    _f506 = B.music_state(-100506)["file"]
    check("v234 play downloads then joins", B.music_state(-100506).get("playing") is True
          and _gc506 is not None and _gc506.started == [-100506]
          and _f506 is not None and os.path.isfile(_f506), str(_f506))
    check("v234 play uses file group call", _gc506.play_on_repeat is False
          and _gc506.input_filename == _f506)
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100506))
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100506))
    check("v234 two queued", len(B.music_state(-100506)["queue"]) == 2)
    # playout-end hook fires -> auto-advance to the next queued track
    _end_handlers = list(_gc506._end_handlers)
    check("v234 playout-end hook registered", len(_end_handlers) == 1)
    _old_file = B.music_state(-100506)["file"]
    await _end_handlers[0](_gc506, _old_file)
    check("v234 playout-end advances", B.music_state(-100506).get("playing") is True
          and len(_gc506.restarts) == 1
          and B.music_state(-100506)["file"] != _old_file
          and len(B.music_state(-100506)["queue"]) == 1)
    check("v234 advance deletes old file", not os.path.exists(_old_file))
    # skip -> switches to the last queued track via the input_filename setter
    await B.cmd_music(client, FakeMessage("/skip", uid=111, name="Tester", chat_id=-100506))
    check("v234 skip switches file", len(_gc506.restarts) == 2
          and len(B.music_state(-100506)["queue"]) == 0)
    # playout-end with an empty queue -> leaves the call, nothing playing
    await _end_handlers[0](_gc506, B.music_state(-100506)["file"])
    check("v234 playout-end empty queue leaves", B.music_state(-100506).get("playing") is False
          and B.music_state(-100506).get("current") is None
          and _gc506.stopped >= 1)
    # play again after leaving -> a FRESH group call is created
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100506))
    _gc506b = B.music_state(-100506)["gc"]
    check("v234 fresh call after leave", _gc506b is not None and _gc506b is not _gc506
          and _gc506b.started == [-100506])
    # stop -> leaves + deletes the temp file + clears state
    _f506b = B.music_state(-100506)["file"]
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/stop", uid=111, name="Tester", chat_id=-100506))
    check("v234 stop cleans up", B.music_state(-100506).get("playing") is False
          and _gc506b.stopped >= 1 and B.music_state(-100506)["file"] is None
          and not os.path.exists(_f506b))
    # download failure mid-play -> honest reply, never a fake "playing" state
    B._yt_dlp = _FakeYtDlpBlockedDl
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100507))
    check("v234 download blocked honest", any("block" in t for _, t in FakeMessage.outbox),
          str([t for _, t in FakeMessage.outbox]))
    check("v234 download blocked no fake", B.music_state(-100507).get("current") is None
          and B.music_state(-100507).get("playing") is False)
    # pause/resume go through the per-chat group call (sync playout calls)
    B._yt_dlp = _FakeYtDlp
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100508))
    _gc508 = B.music_state(-100508)["gc"]
    await B.cmd_music(client, FakeMessage("/pause", uid=111, name="Tester", chat_id=-100508))
    check("v234 pause via gc", B.music_state(-100508).get("paused") is True and _gc508.paused is True)
    await B.cmd_music(client, FakeMessage("/resume", uid=111, name="Tester", chat_id=-100508))
    check("v234 resume via gc", B.music_state(-100508).get("paused") is False and _gc508.paused is False)
    # voice-unavailable reason names the real class
    B._GroupCallFactory = None
    check("v234 voice reason names factory",
          B.voice_unavailable_reason() == "GroupCallFactory missing")
    # restore music state
    B._yt_dlp = _real_ytdlp
    B._GroupCallFactory = _real_factory
    B._music_make_client = _real_mkc
    B.ASSISTANT_SESSION = _real_session
    B._ASSISTANT.update({"client": None, "factory": None, "started": False, "me": None, "init_started": False})
    B.MUSIC.clear()

    # ---- Gap features: moderation (Baka/Rose/Protectron) ----
    _owner = B.OWNER_ID
    _fake_app = FakeApp()
    _bad = FakeMessage("bad msg", uid=222, name="BadGuy", chat_id=-100600)
    FakeMessage.outbox.clear()
    await B.cmd_warn(client, FakeMessage("/warn", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("gap warn 1/3", any("warn 1/3" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_warns(client, FakeMessage("/warns", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("gap warns list", any("warns: 1/3" in t for _, t in FakeMessage.outbox))
    FakeApp.calls.clear()
    FakeMessage.outbox.clear()
    await B.cmd_promote(_fake_app, FakeMessage("/promote", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("gap promote", any("admin ban gaya" in t for _, t in FakeMessage.outbox)
          and any(c[0] == "promote" for c in FakeApp.calls))
    FakeMessage.outbox.clear()
    await B.cmd_title(_fake_app, FakeMessage("/title Star Admin", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("gap title", any("Star Admin" in t for _, t in FakeMessage.outbox)
          and any(c[0] == "title" for c in FakeApp.calls))
    # dot-prefix: .warn via the group text handler
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage(".warn", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("gap dot warn", any("warn 2/3" in t for _, t in FakeMessage.outbox))
    # sudo / auth
    FakeMessage.outbox.clear()
    await B.cmd_addsudo(client, FakeMessage("/addsudo 555", uid=_owner, name="Sanji", chat_id=-100600))
    check("gap addsudo", 555 in B.DATA.get("sudos", [])
          and any("sudo ban gaya" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_sudolist(client, FakeMessage("/sudolist", uid=_owner, name="Sanji", chat_id=-100600))
    check("gap sudolist", any("555" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_delsudo(client, FakeMessage("/delsudo 555", uid=_owner, name="Sanji", chat_id=-100600))
    check("gap delsudo", 555 not in B.DATA.get("sudos", []))
    FakeMessage.outbox.clear()
    await B.cmd_auth(client, FakeMessage("/auth", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("gap auth", 222 in B._chat_data(-100600).get("auth", []))
    B.track_user(_bad)
    FakeMessage.outbox.clear()
    await B.cmd_authlist(client, FakeMessage("/authlist", uid=_owner, name="Sanji", chat_id=-100600))
    check("gap authlist", any("BadGuy" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_unauth(client, FakeMessage("/unauth", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("gap unauth", 222 not in B._chat_data(-100600).get("auth", []))
    # rules + notes
    FakeMessage.outbox.clear()
    await B.cmd_setrules(client, FakeMessage("/setrules 1. gaali mat do", uid=_owner, name="Sanji", chat_id=-100600))
    await B.cmd_rules(client, FakeMessage("/rules", uid=111, name="Tester", chat_id=-100600))
    check("gap rules", any("gaali mat do" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_note(client, FakeMessage("/note welcome hiee welcome!", uid=_owner, name="Sanji", chat_id=-100600))
    await B.cmd_getnote(client, FakeMessage("/get welcome", uid=111, name="Tester", chat_id=-100600))
    check("gap note get", any("hiee welcome!" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_notes(client, FakeMessage("/notes", uid=111, name="Tester", chat_id=-100600))
    check("gap notes list", any("welcome" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_delnote(client, FakeMessage("/delnote welcome", uid=_owner, name="Sanji", chat_id=-100600))
    check("gap delnote", "welcome" not in B._chat_data(-100600).get("notes", {}))
    # report / runs / limits
    FakeMessage.outbox.clear()
    await B.cmd_report(_fake_app, FakeMessage("/report spam hai", uid=111, name="Tester", chat_id=-100600, reply_to=_bad))
    check("gap report", any("Report" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_runs(client, FakeMessage("/runs", uid=111, name="Tester", chat_id=-100600))
    check("gap runs", any(t in B.RUN_LINES for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_limits(client, FakeMessage("/limits", uid=111, name="Tester", chat_id=-100600))
    check("gap limits", any("Kills aaj" in t for _, t in FakeMessage.outbox))
    # filters: set + trigger + approve bypass + stopfilter
    FakeMessage.outbox.clear()
    await B.cmd_filter(client, FakeMessage("/filter hiee hiee, kya haal hai!", uid=_owner, name="Sanji", chat_id=-100600))
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("hiee doston", uid=111, name="Tester", chat_id=-100600))
    check("gap filter triggers", any("kya haal hai" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_approve(client, FakeMessage("/approve", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("hiee doston", uid=222, name="BadGuy", chat_id=-100600))
    check("gap approved bypasses filter", len(FakeMessage.outbox) == 0)
    FakeMessage.outbox.clear()
    await B.cmd_unapprove(client, FakeMessage("/unapprove", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("gap unapprove", 222 not in B._chat_data(-100600).get("approved", []))
    FakeMessage.outbox.clear()
    await B.cmd_stopfilter(client, FakeMessage("/stopfilter hiee", uid=_owner, name="Sanji", chat_id=-100600))
    check("gap stopfilter", "hiee" not in B._chat_data(-100600).get("filters", {}))
    # antiflood: 4 fast messages -> warning
    FakeMessage.outbox.clear()
    await B.cmd_antiflood(client, FakeMessage("/antiflood", uid=_owner, name="Sanji", chat_id=-100601))
    check("gap antiflood on", any("Antiflood" in t and "ON" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    for _i in range(4):
        await B.group_text_handler(client, FakeMessage("spam spam", uid=111, name="Tester", chat_id=-100601))
    check("gap antiflood warns", any("flood" in t for _, t in FakeMessage.outbox))
    await B.cmd_antiflood(client, FakeMessage("/antiflood", uid=_owner, name="Sanji", chat_id=-100601))
    # profanity: gaali message with 'chulbuli' gets deleted (no chat reply)
    FakeMessage.outbox.clear()
    await B.cmd_profanity(client, FakeMessage("/profanity", uid=_owner, name="Sanji", chat_id=-100602))
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("chulbuli tu madarchod hai", uid=111, name="Tester", chat_id=-100602))
    check("gap profanity deletes", len(FakeMessage.outbox) == 0)
    await B.cmd_profanity(client, FakeMessage("/profanity", uid=_owner, name="Sanji", chat_id=-100602))
    # blacklist clear
    FakeMessage.outbox.clear()
    await B.cmd_blacklist_add(client, FakeMessage("/blacklist_add badword", uid=_owner, name="Sanji", chat_id=-100603))
    check("gap blacklist add", "badword" in B._chat_data(-100603).get("blacklist", []))
    await B.cmd_blacklist_clear(client, FakeMessage("/blacklist_clear", uid=_owner, name="Sanji", chat_id=-100603))
    check("gap blacklist clear", B._chat_data(-100603).get("blacklist", []) == [])
    # whitelist: whitelisted link passes the link filter, others don't
    await B.cmd_nolinks(client, FakeMessage("/nolinks", uid=_owner, name="Sanji", chat_id=-100604))
    await B.cmd_whitelist_add(client, FakeMessage("/whitelist_add example.com", uid=_owner, name="Sanji", chat_id=-100604))
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("chulbuli https://example.com/song", uid=111, name="Tester", chat_id=-100604))
    check("gap whitelist passes", len(FakeMessage.outbox) > 0)
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("chulbuli https://badsite.com/x", uid=111, name="Tester", chat_id=-100604))
    check("gap link filter blocks", len(FakeMessage.outbox) == 0)
    await B.cmd_nolinks(client, FakeMessage("/nolinks", uid=_owner, name="Sanji", chat_id=-100604))
    # noforwards + antispam
    FakeMessage.outbox.clear()
    await B.cmd_noforwards(client, FakeMessage("/noforwards", uid=_owner, name="Sanji", chat_id=-100605))
    _fwd = FakeMessage("chulbuli dekho", uid=111, name="Tester", chat_id=-100605)
    _fwd.forward_from = object()
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, _fwd)
    check("gap noforwards deletes", len(FakeMessage.outbox) == 0)
    await B.cmd_noforwards(client, FakeMessage("/noforwards", uid=_owner, name="Sanji", chat_id=-100605))
    await B.cmd_antispam(client, FakeMessage("/antispam", uid=_owner, name="Sanji", chat_id=-100606))
    B._chat_data(-100606).setdefault("joined_at", {})["111"] = int(time.time())
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("chulbuli https://x.com/y", uid=111, name="Tester", chat_id=-100606))
    check("gap antispam new member link", len(FakeMessage.outbox) == 0)
    await B.cmd_antispam(client, FakeMessage("/antispam", uid=_owner, name="Sanji", chat_id=-100606))

    # ---- Gap features: wordchain modes, wordgrid, mafia, mimi ----
    FakeMessage.outbox.clear()
    await B.cmd_wc_modes(client, FakeMessage("/startclassic", uid=111, name="Tester", chat_id=-100610))
    check("gap wc classic lobby", any("WORDCHAIN (classic)" in t for _, t in FakeMessage.outbox)
          and B.game_state(-100610).get("mode") == "classic")
    B.set_game(-100610, None)
    FakeMessage.outbox.clear()
    await B.cmd_wc_modes(client, FakeMessage("/starthard", uid=111, name="Tester", chat_id=-100610))
    check("gap wc hard mode", B.game_state(-100610).get("min_len") == 4)
    B.set_game(-100610, None)
    FakeMessage.outbox.clear()
    await B.cmd_wc_modes(client, FakeMessage("/startelim", uid=111, name="Tester", chat_id=-100610))
    check("gap wc elim mode", B.game_state(-100610).get("strikes_max") == 1)
    B.set_game(-100610, None)
    FakeMessage.outbox.clear()
    await B.cmd_wc_modes(client, FakeMessage("/startchaos", uid=111, name="Tester", chat_id=-100610))
    check("gap wc chaos letter", B.game_state(-100610).get("chaos_letter") in "abcdefghijklmnopqrstuvwxyz")
    B.set_game(-100610, None)
    # hard mode: 3-letter word is a strike (min 4)
    B.set_game(-100611, {"kind": "wordchain", "players": [111, 222], "names": {"111": "Tester", "222": "Two"},
                            "started": True, "turn": 0, "last_word": None, "used": set(),
                            "strikes": {}, "starter": 111, "mode": "hard", "min_len": 4, "strikes_max": 3})
    FakeMessage.outbox.clear()
    await B.handle_wordchain_word(FakeMessage("abc", uid=111, name="Tester", chat_id=-100611))
    check("gap wc hard short word strike", any("kam se kam 4" in t for _, t in FakeMessage.outbox))
    # elim mode: one wrong word = OUT, other player wins + wc_wins
    B.set_game(-100612, {"kind": "wordchain", "players": [111, 222], "names": {"111": "Tester", "222": "Two"},
                            "started": True, "turn": 0, "last_word": "apple", "used": {"apple"},
                            "strikes": {}, "starter": 111, "mode": "elim", "min_len": 2, "strikes_max": 1})
    FakeMessage.outbox.clear()
    await B.handle_wordchain_word(FakeMessage("banana", uid=111, name="Tester", chat_id=-100612))
    check("gap wc elim one strike out", any("OUT" in t for _, t in FakeMessage.outbox)
          and B.game_state(-100612) is None)
    check("gap wc wins counted", B.get_user(222).get("wc_wins", 0) >= 1)
    FakeMessage.outbox.clear()
    await B.cmd_wcstats(client, FakeMessage("/wcstats", uid=222, name="Two", chat_id=-100612))
    check("gap wcstats", any("wins: 1" in t or "wins: " in t for _, t in FakeMessage.outbox))
    # flee + runinfo
    await B.cmd_wc_modes(client, FakeMessage("/startclassic", uid=111, name="Tester", chat_id=-100613))
    await B.do_join(-100613, 222, "Two")
    FakeMessage.outbox.clear()
    await B.cmd_flee(client, FakeMessage("/flee", uid=222, name="Two", chat_id=-100613))
    check("gap flee lobby", any("nikal gaya" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_runinfo(client, FakeMessage("/runinfo", uid=111, name="Tester", chat_id=-100613))
    check("gap runinfo", any("Wordchain run info" in t for _, t in FakeMessage.outbox))
    B.set_game(-100613, None)
    # wordgrid: /new alias + /gridtop
    FakeMessage.outbox.clear()
    await B.cmd_wordgrid(client, FakeMessage("/new", uid=111, name="Tester", chat_id=-100614))
    check("gap new is wordgrid", B.game_state(-100614) is not None
          and B.game_state(-100614).get("kind") == "wordgrid")
    B.set_game(-100614, None)
    B.get_user(111)["grid_points"] = 15
    B.get_user(222)["grid_points"] = 7
    FakeMessage.outbox.clear()
    await B.cmd_gridtop(client, FakeMessage("/gridtop", uid=111, name="Tester", chat_id=-100614))
    check("gap gridtop", any("Word Grid Top" in t and "15" in t for _, t in FakeMessage.outbox))
    # /revealgrid + /checkgrid need an active grid
    await B.cmd_wordgrid(client, FakeMessage("/wordgrid", uid=111, name="Tester", chat_id=-100615))
    FakeMessage.outbox.clear()
    await B.cmd_revealgrid(client, FakeMessage("/revealgrid", uid=_owner, name="Sanji", chat_id=-100615))
    check("gap revealgrid", any("Grid reveal" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_checkgrid(client, FakeMessage("/checkgrid", uid=_owner, name="Sanji", chat_id=-100615))
    check("gap checkgrid", any("status" in t for _, t in FakeMessage.outbox))
    B.set_game(-100615, None)
    # mafia /profile
    FakeMessage.outbox.clear()
    await B.cmd_profile(client, FakeMessage("/profile", uid=111, name="Tester", chat_id=-100616))
    check("gap profile", any("Profile" in t and "Coins" in t for _, t in FakeMessage.outbox))
    # mimi: alive/vault/shop/inv/guide/free
    FakeMessage.outbox.clear()
    await B.cmd_alive(client, FakeMessage("/alive", uid=111, name="Tester", chat_id=-100617))
    check("gap alive", any("alive" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_vault(client, FakeMessage("/vault", uid=111, name="Tester", chat_id=-100617))
    check("gap vault", any("Vault" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_shop(client, FakeMessage("/shop", uid=111, name="Tester", chat_id=-100617))
    check("gap shop", any("Shop" in t and "Rampage" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_inv(client, FakeMessage("/inv", uid=111, name="Tester", chat_id=-100617))
    check("gap inv", any("Inventory" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_guide(client, FakeMessage("/guide", uid=111, name="Tester", chat_id=-100617))
    check("gap guide", any("Guide" in t for _, t in FakeMessage.outbox))
    # gift codes: gencode -> redeem -> redeem again -> cinfo -> delcode
    FakeMessage.outbox.clear()
    await B.cmd_gencode(client, FakeMessage("/gencode 5000", uid=_owner, name="Sanji", chat_id=-100618))
    _code = None
    for _, t in FakeMessage.outbox:
        import re as _re
        _m = _re.search(r"CHUL-[A-Z0-9]{6}", t)
        if _m:
            _code = _m.group(0)
    check("gap gencode", _code is not None, str(FakeMessage.outbox))
    _before = B.get_user(222)["coins"]
    FakeMessage.outbox.clear()
    await B.cmd_redeem(client, FakeMessage(f"/redeem {_code}", uid=222, name="Two", chat_id=-100618))
    check("gap redeem", B.get_user(222)["coins"] == _before + 5000
          and any("coins mile" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_redeem(client, FakeMessage(f"/redeem {_code}", uid=222, name="Two", chat_id=-100618))
    check("gap redeem once", any("pehle hi redeem" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_cinfo(client, FakeMessage(f"/cinfo {_code}", uid=_owner, name="Sanji", chat_id=-100618))
    check("gap cinfo", any("uses: 1/1" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_delcode(client, FakeMessage(f"/delcode {_code}", uid=_owner, name="Sanji", chat_id=-100618))
    check("gap delcode", _code not in B.DATA.get("gift_codes", {}))
    # /free + cooldown
    B.get_user(333)["last_free"] = 0
    FakeMessage.outbox.clear()
    await B.cmd_free(client, FakeMessage("/free", uid=333, name="Free", chat_id=-100619))
    check("gap free", any("+500 free coins" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_free(client, FakeMessage("/free", uid=333, name="Free", chat_id=-100619))
    check("gap free cooldown", any("cooldown" in t for _, t in FakeMessage.outbox))
    # +hug via group text handler (reply-based)
    _target_msg = FakeMessage("hello", uid=222, name="Two", chat_id=-100620)
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("+hug", uid=111, name="Tester", chat_id=-100620, reply_to=_target_msg))
    check("gap plus hug", any("hug kiya" in t for _, t in FakeMessage.outbox))
    # aliases: /acc, /wordly, /lb
    FakeMessage.outbox.clear()
    await B.cmd_bal(client, FakeMessage("/acc", uid=111, name="Tester", chat_id=111, ctype="private"))
    check("gap acc alias", any("$" in t for _, t in FakeMessage.outbox))
    FakeMessage.outbox.clear()
    await B.cmd_jumble(client, FakeMessage("/wordly", uid=111, name="Tester", chat_id=-100621))
    check("gap wordly alias", B.game_state(-100621) is not None
          and B.game_state(-100621).get("kind") == "jumble")
    B.set_game(-100621, None)
    # leaderboard buttons
    FakeMessage.outbox.clear()
    FakeMessage.outbox_full.clear()
    await B.cmd_toprich(client, FakeMessage("/leaderboard", uid=111, name="Tester", chat_id=-100622))
    _lb_kb = FakeMessage.outbox_full[-1][2].get("reply_markup")
    check("gap leaderboard buttons", _lb_kb is not None and "lb:chess" in _cbs_of(_lb_kb),
          str(_cbs_of(_lb_kb)))
    FakeMessage.edits.clear()
    _lbq = FakeCallbackQuery("lb:chess", uid=111, name="Tester",
                             message=FakeMessage("x", uid=111, chat_id=-100622))
    await B.leaderboard_callbacks(client, _lbq)
    check("gap leaderboard chess top", any("Chess Top" in t for _, t, _ in FakeMessage.edits))
    # /mystats shows today count + group rank
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("hello ji", uid=111, name="Tester", chat_id=-100623))
    await B.group_text_handler(client, FakeMessage("aur batao", uid=111, name="Tester", chat_id=-100623))
    FakeMessage.outbox.clear()
    await B.cmd_mystats(client, FakeMessage("/mystats", uid=111, name="Tester", chat_id=-100623))
    # ================= v2.3.0: chat realism ================================
    # (Sanji: emojis har bar nahi, beech me "hello" dobara nahi, typing
    # dikhe, quote karke reply, reaction de, har 5 min group me baat
    # shuru kare, daizy-style math question, kabhi aisa na lage jaise
    # baat abhi shuru hui hai)
    import re as _re2
    import pyrogram as _pyro
    from pyrogram.enums import ChatAction as _ChatAction
    check("reaction api exists", hasattr(_pyro.Client, "send_reaction")
          and hasattr(_pyro.types.Message, "react"))
    check("typing action enum", hasattr(_pyro.enums.ChatAction, "TYPING"))

    # ---- fewer emojis: most chat lines carry NO emoji at all ----
    _EMOJI_RE = _re2.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")

    def _emoji_count(s):
        return len(_EMOJI_RE.findall(s))

    _all_chat_v23 = (B.CHAT_GREET + B.CHAT_HOW + B.CHAT_DEFAULT + B.CHAT_LOVE
                     + B.CHAT_ANGRY + B.CHAT_REAL + B.CHAT_CONTINUE)
    _clean = sum(1 for s in _all_chat_v23 if _emoji_count(s) == 0)
    check("fewer emojis most lines clean", _clean >= len(_all_chat_v23) * 0.7,
          f"{_clean}/{len(_all_chat_v23)} clean")
    check("fewer emojis max one per line", all(_emoji_count(s) <= 1 for s in _all_chat_v23),
          str([s for s in _all_chat_v23 if _emoji_count(s) > 1]))
    check("ai system rare emojis", "rare" in B.AI_SYSTEM.lower()
          and "every message" in B.AI_SYSTEM.lower())
    check("ai system no re-greet", "never greet them again" in B.AI_SYSTEM.lower())
    check("ai system length variety", "3-4 lines" in B.AI_SYSTEM)
    check("chat default longer lines", any(len(s) > 40 for s in B.CHAT_DEFAULT))
    check("continue lines never greet",
          all(not s.startswith(("hiee", "hlooo", "hello", "hii")) for s in B.CHAT_CONTINUE)
          and all(len(s) <= 60 for s in B.CHAT_CONTINUE))

    # ---- no re-greeting mid-conversation ----
    os.environ.pop("OPENROUTER_API_KEY", None)
    B.DATA["toggles"]["ai"] = True
    _nc_uid = 889301
    B.DATA["history"].pop(str(_nc_uid), None)
    B.DATA["memory"].pop(str(_nc_uid), None)
    _first = await B.chat_reply_ai("chulbuli", "Tester", chat_id=_nc_uid, user_id=_nc_uid)
    check("fresh name call greets", _first in B.CHAT_GREET or _first.startswith("hiee Tester")
          or "Tester" in _first, str(_first))
    _second = await B.chat_reply_ai("hii", "Tester", chat_id=_nc_uid, user_id=_nc_uid)
    check("mid-convo no re-greet", _second not in B.CHAT_GREET
          and not _second.startswith(("hiee", "hlooo", "hello", "hii")), str(_second))
    check("mid-convo keeps name", "Tester" in _second, str(_second))
    _third = await B.chat_reply_ai("chulbuli", "Tester", chat_id=_nc_uid, user_id=_nc_uid)
    check("mid-convo name call continues", _third not in B.CHAT_GREET
          and not _third.startswith("hiee"), str(_third))
    B.DATA["memory"][str(_nc_uid)]["last_seen"] = int(time.time()) - 31 * 60
    _after_gap = await B.chat_reply_ai("hii", "Tester", chat_id=_nc_uid, user_id=_nc_uid)
    check("greet again after long gap", _after_gap in B.CHAT_GREET or _after_gap.startswith("hiee")
          or "Tester" in _after_gap, str(_after_gap))
    _newbie = await B.chat_reply_ai("chulbuli", "Newbie", chat_id=_nc_uid, user_id=889302)
    check("new user still greeted", _newbie in B.CHAT_GREET or _newbie.startswith("hiee Newbie")
          or "Newbie" in _newbie, str(_newbie))
    check("ongoing needs history+recent msgs",
          B._conversation_ongoing(None, 111) is False
          and B._conversation_ongoing(_nc_uid, None) is False
          and B._conversation_ongoing(_nc_uid, 889303) is False)

    # ---- typing indicator + reply-to quote + reaction (chat replies only) ----
    class _RecClient:
        """Records chat actions + reactions the bot sends."""

        def __init__(self):
            self.actions = []    # (chat_id, action)
            self.reactions = []  # (chat_id, message_id, emoji)

        async def send_chat_action(self, chat_id, action):
            self.actions.append((chat_id, action))
            return True

        async def send_reaction(self, chat_id, message_id, emoji=""):
            self.reactions.append((chat_id, message_id, emoji))
            return True

        async def get_chat_member(self, chat_id, user_id):
            return FakeChatMember(FakeUser(user_id, "Tester"), "member")

    _sleeps = []
    _real_sleep2 = asyncio.sleep

    async def _rec_sleep(d):
        _sleeps.append(d)
        return None

    asyncio.sleep = _rec_sleep
    try:
        _rc = _RecClient()
        FakeMessage.outbox.clear()
        FakeMessage.outbox_full.clear()
        _m = FakeMessage("chulbuli kaisi ho?", uid=111, name="Tester", chat_id=-100700)
        await B.group_text_handler(_rc, _m)
        check("typing shown before chat reply", len(_rc.actions) >= 1
              and _rc.actions[0][0] == -100700 and _rc.actions[0][1] == _ChatAction.TYPING,
              str(_rc.actions))
        check("typing delay 1-3s", len(_sleeps) >= 1 and all(1.0 <= s <= 3.0 for s in _sleeps),
              str(_sleeps))
        check("chat reply quotes user", len(FakeMessage.outbox_full) == 1
              and FakeMessage.outbox_full[0][2].get("reply_to_message_id") == _m.id,
              str(FakeMessage.outbox_full))
        check("typing delay scales with length", B.typing_delay("x") == 1.0
              and B.typing_delay("x" * 200) == 3.0 and 1.0 < B.typing_delay("x" * 50) < 3.0)
        # reaction: force it on, then force it off
        _real_random = B.random.random
        B.random.random = lambda: 0.0
        _rc2 = _RecClient()
        _m2 = FakeMessage("chulbuli suno na", uid=111, name="Tester", chat_id=-100700)
        await B.group_text_handler(_rc2, _m2)
        check("reaction sent on chat reply", len(_rc2.reactions) == 1
              and _rc2.reactions[0][1] == _m2.id and _rc2.reactions[0][2] in B.REACT_EMOJIS,
              str(_rc2.reactions))
        B.random.random = lambda: 0.99
        _rc3 = _RecClient()
        await B.group_text_handler(_rc3, FakeMessage("chulbuli aur batao", uid=111, name="Tester", chat_id=-100700))
        check("reaction sparing not always", len(_rc3.reactions) == 0)
        B.random.random = _real_random
        # reaction failure must not break the reply

        class _FailReact(_RecClient):
            async def send_reaction(self, chat_id, message_id, emoji=""):
                raise RuntimeError("boom")

        _rc4 = _FailReact()
        FakeMessage.outbox.clear()
        await B.group_text_handler(_rc4, FakeMessage("chulbuli kya kar rahi ho", uid=111, name="Tester", chat_id=-100700))
        check("reaction failure reply still sent", len(FakeMessage.outbox) == 1)
        # DM chat reply also types + quotes
        _rc_dm = _RecClient()
        FakeMessage.outbox.clear()
        FakeMessage.outbox_full.clear()
        _dm = FakeMessage("hello ji", uid=111, name="Tester", chat_id=111, ctype="private")
        await B.private_text_handler(_rc_dm, _dm)
        check("dm chat reply types + quotes", len(_rc_dm.actions) >= 1
              and len(FakeMessage.outbox_full) == 1
              and FakeMessage.outbox_full[0][2].get("reply_to_message_id") == _dm.id,
              str(FakeMessage.outbox_full))
        # commands stay instant: no typing action
        _rc5 = _RecClient()
        await B.cmd_bal(_rc5, FakeMessage("/bal", uid=111, name="Tester", chat_id=111, ctype="private"))
        check("commands stay instant", len(_rc5.actions) == 0)
    finally:
        asyncio.sleep = _real_sleep2

    # ---- proactive group engagement: selection logic ----
    _now = int(time.time())
    B.DATA.setdefault("recent", {})
    B.DATA["recent"].pop(str(-100710), None)
    B.DATA["chats"].pop(str(-100710), None)
    B.record_recent(-100710, 111, "Tester", "aaj cricket khelte hain kya?", 5001)
    _tgt = B._pick_proactive_target(-100710, _now)
    check("proactive picks recent human msg", _tgt is not None and _tgt.get("u") == 111
          and _tgt.get("m") == 5001, str(_tgt))
    B.DATA["recent"][str(-100710)][-1]["ts"] = _now - 601
    check("proactive skips idle group", B._pick_proactive_target(-100710, _now) is None)
    B.DATA["recent"][str(-100710)][-1]["ts"] = _now - 60
    B._chat_data(-100710)["last_bot_spoke"] = _now - 100
    check("proactive skips after bot spoke", B._pick_proactive_target(-100710, _now) is None)
    B._chat_data(-100710)["last_bot_spoke"] = _now - 2000
    B.DATA["toggles"]["chat"] = False
    check("proactive respects chat off", B._pick_proactive_target(-100710, _now) is None)
    B.DATA["toggles"]["chat"] = True
    B.record_recent(-100710, 222, "Friend", "42", 5002)
    _tgt2 = B._pick_proactive_target(-100710, _now)
    check("proactive skips bare numbers", _tgt2 is not None
          and _tgt2.get("t") == "aaj cricket khelte hain kya?", str(_tgt2))
    check("recent capped at 20", (lambda: [B.record_recent(-100710, 111, "T", f"msg{i}", 6000 + i)
                                           for i in range(25)] and len(B.DATA["recent"][str(-100710)]) == 20)())

    # ---- proactive tick: sends once in an active group, skips idle/DM ----
    # Hermetic: earlier handler tests left other active groups in recent —
    # clear them so only the groups below exist for this tick.
    FakeApp.calls.clear()
    FakeMessage.outbox.clear()
    FakeMessage.outbox_full.clear()
    B.DATA["recent"] = {}
    B.DATA["recent"][str(-100710)] = [
        {"u": 111, "n": "Tester", "t": "aaj cricket khelte hain kya?", "ts": _now - 30, "m": 5001, "bot": False},
    ]
    B._chat_data(-100710)["last_bot_spoke"] = 0
    B.DATA["recent"][str(-100711)] = [
        {"u": 111, "n": "Tester", "t": "purani baat", "ts": _now - 3600, "m": 6001, "bot": False},
    ]
    B.DATA["recent"][str(111)] = [
        {"u": 111, "n": "Tester", "t": "dm me baat", "ts": _now - 30, "m": 7001, "bot": False},
    ]
    asyncio.sleep = _rec_sleep
    try:
        _sent = await B._proactive_tick(_now)
    finally:
        asyncio.sleep = _real_sleep2
    check("proactive tick sends once", _sent == 1, str(_sent))
    check("proactive reply quotes target",
          any(kw.get("reply_to_message_id") == 5001 for _, _, kw in FakeMessage.outbox_full),
          str(FakeMessage.outbox_full))
    check("proactive skips idle + DM",
          all(cid != -100711 and cid != 111 for cid, _, _ in FakeMessage.outbox_full))
    check("proactive tick shows typing",
          any(c[0] == "chat_action" and c[1] == -100710 for c in FakeApp.calls), str(FakeApp.calls))
    check("proactive marks bot spoke", B._chat_data(-100710).get("last_bot_spoke", 0) > 0)

    # ---- periodic math questions (Daizy-style) ----
    check("math rewards", B.MATH_SINGLE_REWARDS == {"easy": 100, "medium": 250, "hard": 500})
    _mg = -100720
    B.DATA["recent"] = {}
    B.DATA["recent"][str(_mg)] = [
        {"u": 111, "n": "Tester", "t": "bore ho raha hun yaar", "ts": _now - 30, "m": 8001, "bot": False},
    ]
    B._chat_data(_mg)["last_math_post"] = 0
    B._chat_data(_mg)["last_bot_spoke"] = 0
    B._MATH_SINGLE.pop(_mg, None)
    check("math group picked when active", B._pick_math_group(_now) == _mg)
    B.set_game(_mg, {"kind": "uno", "players": [111]})
    check("math group skipped during game", B._pick_math_group(_now) is None)
    B.set_game(_mg, None)
    B._chat_data(_mg)["last_math_post"] = _now - 100
    check("math group skipped if posted recently", B._pick_math_group(_now) is None)
    B._chat_data(_mg)["last_math_post"] = 0
    FakeMessage.outbox.clear()
    asyncio.sleep = _rec_sleep
    try:
        _posted = await B._math_poster_tick(_now)
    finally:
        asyncio.sleep = _real_sleep2
    check("math poster posts", _posted is True
          and any("math question" in t for _, t in FakeMessage.outbox),
          str([t for _, t in FakeMessage.outbox]))
    _ms = B._MATH_SINGLE.get(_mg)
    check("math single state set", _ms is not None and _ms.get("answer") is not None
          and _ms.get("reward") == B.MATH_SINGLE_REWARDS[_ms["difficulty"]], str(_ms))
    _q_text = [t for _, t in FakeMessage.outbox if "math question" in t][0]
    _q_line = [ln for ln in _q_text.split("\n") if "= ?" in ln][0]
    check("math posted question matches answer",
          eval(_q_line.replace("×", "*").replace(" = ?", "")) == _ms["answer"], _q_line)
    check("math posted shows level + reward", _ms["difficulty"] in _q_text
          and f"+{_ms['reward']} coins" in _q_text, _q_text)
    _coins_before = B.get_user(222)["coins"]
    FakeMessage.outbox.clear()
    await B.handle_math_answer(FakeMessage(str(_ms["answer"]), uid=222, name="Friend", chat_id=_mg))
    check("math single correct wins coins", B.get_user(222)["coins"] == _coins_before + _ms["reward"]
          and _mg not in B._MATH_SINGLE and any("sahi jawab" in t for _, t in FakeMessage.outbox),
          str(B.get_user(222)["coins"]))
    B._MATH_SINGLE[_mg] = {"answer": 42, "reward": 250, "difficulty": "medium",
                           "gid": "test-gid", "expires": _now + 300}
    _coins_before2 = B.get_user(222)["coins"]
    FakeMessage.outbox.clear()
    await B.handle_math_answer(FakeMessage("41", uid=222, name="Friend", chat_id=_mg))
    check("math single wrong answer no coins", B.get_user(222)["coins"] == _coins_before2
          and _mg in B._MATH_SINGLE)
    await B.handle_math_answer(FakeMessage("hello", uid=222, name="Friend", chat_id=_mg))
    check("math single non-number ignored", _mg in B._MATH_SINGLE)
    await B._math_single_timeout(_mg, "test-gid", 0)
    check("math single expires quietly", _mg not in B._MATH_SINGLE)
    B._MATH_SINGLE[_mg] = {"answer": 7, "reward": 100, "difficulty": "easy",
                           "gid": "new-gid", "expires": _now + 300}
    await B._math_single_timeout(_mg, "old-gid", 0)
    check("math single stale timeout keeps new", _mg in B._MATH_SINGLE)
    B._MATH_SINGLE.pop(_mg, None)

    # ---- v2.3.1: /play never goes silent on a YouTube bot-check (live bug) ----
    class _BlockedYDL:
        def __init__(self, opts):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, src, download=False):
            raise Exception("ERROR: [youtube] nYxC9j1BnRw: Sign in to confirm you're not a bot")

    class _FakeYtDlpBlocked:
        YoutubeDL = _BlockedYDL

    _saved_ydl = B._yt_dlp
    B._yt_dlp = _FakeYtDlpBlocked
    try:
        B.resolve_track("test gaana")
        check("play youtube_blocked classified", False, "resolve_track did not raise")
    except B.MusicError as _e:
        check("play youtube_blocked classified", str(_e) == "youtube_blocked", str(_e))
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100501))
    check("play blocked replies honestly", any("youtube" in t and "block" in t for _, t in FakeMessage.outbox),
          str([t for _, t in FakeMessage.outbox]))

    class _FailYDL(_BlockedYDL):
        def extract_info(self, src, download=False):
            raise Exception("some random yt-dlp failure")

    B._yt_dlp = type("Y", (), {"YoutubeDL": _FailYDL})
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100501))
    check("play generic failure replies", len(FakeMessage.outbox) > 0,
          str([t for _, t in FakeMessage.outbox]))
    B._yt_dlp = _saved_ydl

    # ---- v2.3.2: YouTube anti-bot clients + retry, reload classified ----
    # "The page needs to be reloaded." (live logs 21:39:51/21:40:01/21:40:31)
    # is a YouTube block too, not "song not found".
    check("play blocked marker live errors",
          B._is_youtube_blocked("ERROR: [youtube] nYxC9j1BnRw: Sign in to confirm you're not a bot")
          and B._is_youtube_blocked("ERROR: [youtube] abc123: The page needs to be reloaded.")
          and B._is_youtube_blocked("Sign in to confirm you're not a bot")
          and not B._is_youtube_blocked("some random yt-dlp failure"))

    class _ReloadYDL:
        def __init__(self, opts):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, src, download=False):
            raise Exception("ERROR: [youtube] abc123: The page needs to be reloaded.")

    _saved_ydl = B._yt_dlp
    B._yt_dlp = type("Y", (), {"YoutubeDL": _ReloadYDL})
    try:
        B.resolve_track("test gaana")
        check("play reload classified blocked", False, "resolve_track did not raise")
    except B.MusicError as _e:
        check("play reload classified blocked", str(_e) == "youtube_blocked", str(_e))
    FakeMessage.outbox.clear()
    await B.cmd_music(client, FakeMessage("/play test gaana", uid=111, name="Tester", chat_id=-100501))
    check("play reload replies honestly", any("youtube" in t and "block" in t for _, t in FakeMessage.outbox),
          str([t for _, t in FakeMessage.outbox]))

    # first attempt uses the mobile player clients; a YouTube block retries
    # once with the tv/web clients; a generic failure does NOT retry.
    class _RetryYDL:
        calls = []

        def __init__(self, opts):
            self.opts = opts
            type(self).calls.append(opts)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, src, download=False):
            if len(type(self).calls) == 1:
                raise Exception("ERROR: [youtube] x: Sign in to confirm you're not a bot")
            return {"title": "Retry Gaana", "webpage_url": "https://youtube.com/watch?v=retry",
                    "url": "https://audio.example/retry.m4a", "duration": 180}

    _RetryYDL.calls.clear()
    B._yt_dlp = type("Y", (), {"YoutubeDL": _RetryYDL})
    _retry_track = B.resolve_track("retry gaana")
    check("play retry succeeds", _retry_track["title"] == "Retry Gaana", str(_retry_track))
    check("play retry two attempts", len(_RetryYDL.calls) == 2, str(len(_RetryYDL.calls)))
    check("play first attempt mobile clients",
          _RetryYDL.calls[0].get("extractor_args", {}).get("youtube", {}).get("player_client")
          == ["android", "ios", "web"], str(_RetryYDL.calls[0].get("extractor_args")))
    check("play retry alternate clients",
          _RetryYDL.calls[1].get("extractor_args", {}).get("youtube", {}).get("player_client")
          == ["tv", "web"], str(_RetryYDL.calls[1].get("extractor_args")))

    class _GenericYDL:
        calls = []

        def __init__(self, opts):
            self.opts = opts
            type(self).calls.append(opts)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, src, download=False):
            raise Exception("some random yt-dlp failure")

    _GenericYDL.calls.clear()
    B._yt_dlp = type("Y", (), {"YoutubeDL": _GenericYDL})
    try:
        B.resolve_track("test gaana")
        check("play generic failure raises", False, "resolve_track did not raise")
    except B.MusicError as _e:
        check("play generic failure raises", str(_e).startswith("search failed"), str(_e))
    check("play generic failure no retry", len(_GenericYDL.calls) == 1,
          str(len(_GenericYDL.calls)))
    B._yt_dlp = _saved_ydl

    # ---- v2.3.1: /promote uses ChatPrivileges (real Pyrogram API) ----
    _fake_app2 = FakeApp()
    FakeApp.calls.clear()
    FakeMessage.outbox.clear()
    await B.cmd_promote(_fake_app2, FakeMessage("/promote", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    _promo = [c for c in FakeApp.calls if c[0] == "promote"]
    check("promote uses ChatPrivileges", len(_promo) == 1 and _promo[0][3] is not None
          and _promo[0][3].can_promote_members is False
          and _promo[0][3].can_delete_messages is True, str(_promo))
    check("promote success reply", any("admin ban gaya" in t for _, t in FakeMessage.outbox))
    # bot without can_promote_members -> specific message, no promote call
    FakeApp.bot_privileges = B.ChatPrivileges(can_manage_chat=True, can_delete_messages=True,
                                              can_promote_members=False)
    FakeApp.calls.clear()
    FakeMessage.outbox.clear()
    await B.cmd_promote(_fake_app2, FakeMessage("/promote", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("promote no right names it", any("Add New Admins" in t for _, t in FakeMessage.outbox)
          and not any(c[0] == "promote" for c in FakeApp.calls),
          str([t for _, t in FakeMessage.outbox]))
    FakeApp.bot_privileges = B.ChatPrivileges(
        can_manage_chat=True, can_delete_messages=True, can_manage_video_chats=True,
        can_restrict_members=True, can_promote_members=True, can_change_info=True,
        can_post_messages=True, can_edit_messages=True, can_invite_users=True,
        can_pin_messages=True)
    # demote -> all-False privileges
    FakeApp.calls.clear()
    FakeMessage.outbox.clear()
    await B.cmd_demote(_fake_app2, FakeMessage("/demote", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    _dem = [c for c in FakeApp.calls if c[0] == "promote"]
    check("demote all false privileges", len(_dem) == 1 and _dem[0][3] is not None and not any([
        _dem[0][3].can_manage_chat, _dem[0][3].can_delete_messages,
        _dem[0][3].can_restrict_members, _dem[0][3].can_promote_members,
        _dem[0][3].can_change_info, _dem[0][3].can_invite_users,
        _dem[0][3].can_pin_messages, _dem[0][3].can_manage_video_chats]), str(_dem))
    # title -> set_administrator_title (real Pyrogram name)
    FakeApp.calls.clear()
    FakeMessage.outbox.clear()
    await B.cmd_title(_fake_app2, FakeMessage("/title Star Admin", uid=_owner, name="Sanji", chat_id=-100600, reply_to=_bad))
    check("title uses set_administrator_title", any(c[0] == "title" and c[3] == "Star Admin" for c in FakeApp.calls)
          and any("Star Admin" in t for _, t in FakeMessage.outbox), str(FakeApp.calls))

    # ---- v2.3.1: bare name-call in a group ALWAYS gets a reply ----
    FakeMessage.outbox.clear()
    await B.group_text_handler(client, FakeMessage("chulbuli", uid=111, name="Tester", chat_id=-100700))
    check("name call group replies", len(FakeMessage.outbox) > 0
          and any(t.strip() for _, t in FakeMessage.outbox),
          str([t for _, t in FakeMessage.outbox]))
    # chat_reply_ai never raises / never returns blank even if memory breaks
    _orig_extract = B.extract_facts
    B.extract_facts = lambda uid, text: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        _r = await B.chat_reply_ai("chulbuli", "Tester", chat_id=-100701, user_id=111)
        check("chat reply ai never raises", isinstance(_r, str) and _r.strip() != "", repr(_r))
    finally:
        B.extract_facts = _orig_extract
    # whitespace AI reply falls back to a real line
    _orig_ai = B.ai_chat_reply

    async def _blank_ai(*a, **k):
        return "   "

    B.ai_chat_reply = _blank_ai
    try:
        _r2 = await B.chat_reply_ai("kya haal hai", "Tester", chat_id=-100702, user_id=111)
        check("chat reply ai blank falls back", isinstance(_r2, str) and _r2.strip() != "", repr(_r2))
    finally:
        B.ai_chat_reply = _orig_ai

    # ---- v2.3.6: peer-cache population ("Peer id invalid" crash) ----
    # Live logs (v2.3.4, 2026-11-13 08:33:59 + 08:35:30 IST): handle_updates
    # died twice with KeyError 'ID not found: -1003962580050' / '-1003866876068'
    # (moonlight) -> ValueError('Peer id invalid'). Root cause, verified in
    # the installed Pyrogram 2.0.106 source: utils.get_peer_type rejects
    # channel ids > 2**31-1, and resolve_peer only reaches that code when
    # the peer is NOT in the session cache (a fresh session file after a
    # deploy starts empty). Walking get_dialogs() caches every peer, because
    # Client.invoke() runs fetch_peers on every result's users/chats.
    # handle_updates is a fresh task per update batch (session.py:255), so
    # one crash does not kill the loop globally — but every min-update from
    # the uncached chat dies the same way, so the bot goes deaf there until
    # the peer is cached. There is no supported hook for handle_updates
    # failures (the Dispatcher only guards handlers), so the population
    # is the fix — no monkey-patching.
    _real_factory6 = B._GroupCallFactory
    _real_mkc6 = B._music_make_client
    _real_session6 = B.ASSISTANT_SESSION
    # (v2.3.8) the BOT path no longer walks dialogs at all — it walks the
    # known chat ids from DATA/MUSIC (see the v2.3.8 section below). The
    # dialogs walk stays for USER clients (the assistant) only.
    # failure mid-walk is swallowed, partial count returned (dialogs path)
    class _BoomDialogsClient:
        async def get_dialogs(self, limit=0):
            yield FakeDialog(-100502)
            raise RuntimeError("boom-dialogs")

    _buf_pc2 = io.StringIO()
    with contextlib.redirect_stdout(_buf_pc2):
        _n2 = await B._populate_peer_cache(_BoomDialogsClient(), "assistant")
    check("peer cache failure swallowed", _n2 == 1 and "boom-dialogs" in _buf_pc2.getvalue(),
          _buf_pc2.getvalue())
    # scheduler fires once only (first-update pattern, like _music_schedule_startup)
    B._PEER_CACHE_STARTED = False
    _buf_pc3 = io.StringIO()
    with contextlib.redirect_stdout(_buf_pc3):
        B._schedule_peer_cache_population()
        B._schedule_peer_cache_population()
        await asyncio.sleep(0.05)
    check("peer cache scheduler once only",
          B._PEER_CACHE_STARTED is True
          and _buf_pc3.getvalue().count("chats cached") == 1,
          _buf_pc3.getvalue())
    # assistant client gets its own population after a successful start

    class _FakeAssistantClient2:
        def __init__(self):
            self.dialogs_walked = False
            self.joined = []

        async def start(self):
            return True

        async def get_me(self):
            class _Me:
                username = "CBIOFINDIA"
                id = 8617937893
            return _Me()

        async def get_dialogs(self, limit=0):
            self.dialogs_walked = True
            yield FakeDialog(-100502)
            yield FakeDialog(222)

        async def join_chat(self, link):
            self.joined.append(link)
            return True

    _asst2 = _FakeAssistantClient2()
    B._GroupCallFactory = _FakeGroupCallFactory
    B._music_make_client = lambda: _asst2
    B.ASSISTANT_SESSION = "fake-session-for-test"
    B._ASSISTANT.update({"client": None, "factory": None, "started": False, "me": None, "init_started": True})
    _buf_pc4 = io.StringIO()
    with contextlib.redirect_stdout(_buf_pc4):
        _ok = await B._music_ensure_assistant()
        await asyncio.sleep(0.05)
    check("peer cache covers assistant", _ok is True and _asst2.dialogs_walked is True
          and "peer cache (assistant): 2 dialogs cached" in _buf_pc4.getvalue(),
          _buf_pc4.getvalue())
    # assistant join: get_chat fails on an uncached peer -> populate -> retry
    _real_get_chat = B.app.get_chat
    _join_calls = {"n": 0}
    _pop_calls = []

    async def _flaky_get_chat(chat_id):
        _join_calls["n"] += 1
        if _join_calls["n"] == 1:
            raise ValueError("Peer id invalid: -1003866876068")

        class _C:
            username = "testgroup"
            invite_link = None
        return _C()

    _real_populate = B._populate_peer_cache

    async def _rec_populate(client, label, **kwargs):
        _pop_calls.append(label)
        return 0

    B.app.get_chat = _flaky_get_chat
    B._populate_peer_cache = _rec_populate
    try:
        await B._music_assistant_join_chat(-1003866876068)
        check("assistant join retries after populate", _pop_calls == ["bot"]
              and _asst2.joined == ["testgroup"], str((_pop_calls, _asst2.joined)))
    finally:
        B.app.get_chat = _real_get_chat
        B._populate_peer_cache = _real_populate
    # ---- v2.3.8: bot peer cache must NOT use get_dialogs ----
    # Live v2.3.6 logs (2026-11-13 08:53:54 IST): the bot population died
    # with BotMethodInvalid — Telegram rejects messages.GetDialogs for
    # bots ("peer cache (bot): stopped after 0 dialogs"). Only the
    # assistant (a user client) can walk dialogs (54 cached live). The bot
    # now walks its KNOWN chat ids instead: get_chat per id, with a raw
    # channels.GetChannels fallback for supergroups whose numeric id
    # exceeds 2**31-1 — get_chat's resolve_peer raises ValueError("Peer id
    # invalid") for those when uncached (verified in the installed
    # Pyrogram 2.0.106 source: get_peer_type rejects ids below
    # MIN_CHANNEL_ID -1002147483647; get_chat resolves the peer first).
    # Save/restore DATA + MUSIC so the fixture is hermetic.
    _saved_chats8 = dict(B.DATA.get("chats", {}))
    _saved_hist8 = dict(B.DATA.get("history", {}))
    _saved_recent8 = dict(B.DATA.get("recent", {}))
    _saved_music8 = dict(B.MUSIC)
    _saved_gcc8 = list(FakeApp.get_chat_calls)
    _saved_inv8 = list(FakeApp.invoke_calls)
    _saved_gcf8 = dict(FakeApp.get_chat_fail)
    try:
        B.DATA["chats"] = {"-1003866876068": {"title": "moonlight"},
                           "-100502": {"title": "small group"},
                           "-100999": {"title": "dead group"}}
        B.DATA["history"] = {"222": []}
        B.DATA["recent"] = {}
        B.MUSIC.clear()
        B.MUSIC[-100777] = {"queue": [], "current": None}
        FakeApp.get_chat_calls.clear()
        FakeApp.invoke_calls.clear()
        FakeApp.dialogs_called = False
        # get_chat simulates the real resolve_peer failure for the
        # uncached large id, and a dead id that fails everywhere.
        # (Class attributes — the methods read FakeApp.*, not the instance.)
        FakeApp.get_chat_fail = {
            -1003866876068: ValueError("Peer id invalid: -1003866876068"),
            -100999: RuntimeError("boom-chat"),
        }
        _buf8 = io.StringIO()
        with contextlib.redirect_stdout(_buf8):
            _n8 = await B._populate_peer_cache(B.app, "bot", use_dialogs=False)
        _out8 = _buf8.getvalue()
        # moonlight + small group + history DM + music group = 4 cached;
        # the dead id is skipped, not fatal.
        check("v238 bot never calls get_dialogs",
              FakeApp.dialogs_called is False, str(FakeApp.dialogs_called))
        check("v238 bot get_chat per known id",
              sorted(FakeApp.get_chat_calls) == [-1003866876068, -100999, -100777, -100502, 222],
              str(FakeApp.get_chat_calls))
        check("v238 bot large id falls back to GetChannels",
              len(FakeApp.invoke_calls) == 1
              and isinstance(FakeApp.invoke_calls[0], B.raw.functions.channels.GetChannels)
              and FakeApp.invoke_calls[0].id[0].channel_id == 3866876068
              and FakeApp.invoke_calls[0].id[0].access_hash == 0,
              str(FakeApp.invoke_calls))
        check("v238 bot bad id skipped",
              _n8 == 4 and "peer cache (bot): 4 chats cached, 1 failed" in _out8, _out8)
        check("v238 bot known ids cover history+music",
              -100777 in FakeApp.get_chat_calls and 222 in FakeApp.get_chat_calls,
              str(FakeApp.get_chat_calls))
        # FloodWait stops the walk early instead of hammering every id.
        FakeApp.get_chat_calls.clear()
        FakeApp.invoke_calls.clear()
        FakeApp.get_chat_fail = {-1003866876068: FloodWait(5)}
        _buf8b = io.StringIO()
        with contextlib.redirect_stdout(_buf8b):
            _n8b = await B._populate_peer_cache(B.app, "bot", use_dialogs=False)
        check("v238 floodwait stops walk",
              _n8b == 0 and FakeApp.get_chat_calls == [-1003866876068]
              and "flood-wait 5s, stopping after 0 chats" in _buf8b.getvalue(),
              _buf8b.getvalue())
    finally:
        B.DATA["chats"] = _saved_chats8
        B.DATA["history"] = _saved_hist8
        B.DATA["recent"] = _saved_recent8
        B.MUSIC.clear()
        B.MUSIC.update(_saved_music8)
        FakeApp.get_chat_calls.clear()
        FakeApp.get_chat_calls.extend(_saved_gcc8)
        FakeApp.invoke_calls.clear()
        FakeApp.invoke_calls.extend(_saved_inv8)
        FakeApp.get_chat_fail = _saved_gcf8
        FakeApp.dialogs_called = False
    # ---- v2.3.7: USER_ALREADY_PARTICIPANT is a success, not a failure ----
    # Live /play report 2026-11-13 08:55 IST: the assistant was ALREADY a
    # member, Telegram returned 400 USER_ALREADY_PARTICIPANT, and the old
    # code turned that into MusicError("assistant group me join nahi kar
    # paya"). Being already a participant IS the goal — the join is a
    # no-op and the play retry must surface the true gc.start result.
    class _FakeAsstJoin:
        def __init__(self, behaviour):
            self.behaviour = behaviour  # "already" | "string" | "other" | "ok"
            self.joined = []

        async def join_chat(self, link):
            self.joined.append(link)
            if self.behaviour == "already":
                raise B.UserAlreadyParticipant(
                    "The user is already a participant of this chat")
            if self.behaviour == "string":
                raise Exception("[400 USER_ALREADY_PARTICIPANT] - The user is "
                                "already a participant of this chat")
            if self.behaviour == "other":
                raise Exception("FLOOD_WAIT_10")
            return True

    async def _chat_with_username(chat_id):
        class _C:
            username = "testgroup"
            invite_link = None
        return _C()

    async def _chat_with_link(chat_id):
        class _C:
            username = None
            invite_link = "https://t.me/+testinvite"
        return _C()

    _real_get_chat2 = B.app.get_chat
    try:
        # username path: join raises the real class -> returns normally
        _asst_already = _FakeAsstJoin("already")
        B._ASSISTANT.update({"client": _asst_already, "factory": None,
                             "started": True, "me": None, "init_started": True})
        B.app.get_chat = _chat_with_username
        try:
            await B._music_assistant_join_chat(-100503)
            check("v237 join already participant by username",
                  _asst_already.joined == ["testgroup"])
        except B.MusicError as _e:
            check("v237 join already participant by username", False, str(_e))
        # invite-link path: same class, no username on the chat
        _asst_already2 = _FakeAsstJoin("already")
        B._ASSISTANT.update({"client": _asst_already2})
        B.app.get_chat = _chat_with_link
        try:
            await B._music_assistant_join_chat(-100503)
            check("v237 join already participant by link",
                  _asst_already2.joined == ["https://t.me/+testinvite"])
        except B.MusicError as _e:
            check("v237 join already participant by link", False, str(_e))
        # string fallback: the error surfaces as plain text, still a success
        _asst_str = _FakeAsstJoin("string")
        B._ASSISTANT.update({"client": _asst_str})
        B.app.get_chat = _chat_with_username
        try:
            await B._music_assistant_join_chat(-100503)
            check("v237 join already participant string fallback",
                  _asst_str.joined == ["testgroup"])
        except B.MusicError as _e:
            check("v237 join already participant string fallback", False, str(_e))
        # a DIFFERENT join error still fails honestly
        _asst_other = _FakeAsstJoin("other")
        B._ASSISTANT.update({"client": _asst_other})
        try:
            await B._music_assistant_join_chat(-100503)
            check("v237 join other error still fails", False, "no MusicError raised")
        except B.MusicError as _e:
            check("v237 join other error still fails",
                  "join nahi kar paya" in str(_e), str(_e))
    finally:
        B.app.get_chat = _real_get_chat2
    # gc.start's original exception is logged before the join attempt
    class _FlakyGroupCallFile(_FakeGroupCallFile):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.start_calls = 0

        async def start(self, chat_id):
            self.start_calls += 1
            if self.start_calls == 1:
                raise RuntimeError("boom-start-first")
            self.started.append(chat_id)
            self.is_connected = True

    class _FlakyGroupCallFactory(_FakeGroupCallFactory):
        def get_file_group_call(self, input_filename=None, output_filename=None,
                                play_on_repeat=True):
            gc = _FlakyGroupCallFile(input_filename=input_filename,
                                     play_on_repeat=play_on_repeat)
            self.created.append(gc)
            return gc

    _flaky_factory = _FlakyGroupCallFactory(_FakeAsstJoin("ok"))
    _real_ytdlp2 = B._yt_dlp
    B._yt_dlp = _FakeYtDlp
    B._GroupCallFactory = _FlakyGroupCallFactory
    B._ASSISTANT.update({"client": _FakeAsstJoin("ok"),
                         "factory": _flaky_factory, "started": True,
                         "me": None, "init_started": True})
    B.MUSIC.clear()
    _buf237 = io.StringIO()
    _track237 = {"title": "Test Gaana", "url": "https://youtube.com/watch?v=test",
                 "audio": "https://audio.example/test.m4a", "duration": 200,
                 "by": "", "by_id": 0}
    _stream_exc = None
    try:
        with contextlib.redirect_stdout(_buf237):
            await B._music_stream_track(-100503, _track237)
    except Exception as _e:  # noqa: BLE001
        _stream_exc = _e
    _gc503 = B.music_state(-100503).get("gc")
    check("v237 gc.start failure logged before join",
          "gc.start failed, trying assistant join" in _buf237.getvalue()
          and "boom-start-first" in _buf237.getvalue(),
          _buf237.getvalue() + f" exc={_stream_exc!r}")
    check("v237 gc.start retried after join",
          _stream_exc is None and _gc503 is not None and _gc503.start_calls == 2
          and B.music_state(-100503).get("in_call") is True,
          f"exc={_stream_exc!r}")
    B._yt_dlp = _real_ytdlp2
    try:
        await B._music_leave(-100503)
    except Exception:
        pass
    B.MUSIC.clear()
    # restore music state
    B._GroupCallFactory = _real_factory6
    B._music_make_client = _real_mkc6
    B.ASSISTANT_SESSION = _real_session6
    B._ASSISTANT.update({"client": None, "factory": None, "started": False, "me": None, "init_started": False})
    B.MUSIC.clear()

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILED:", FAIL)
        sys.exit(1)


asyncio.run(main())
