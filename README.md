# Chulbuli 💕 — all-in-one Telegram bot (@ChulbuliGameBot)

Hand-built (NOT via @SanjiBotFactoryBot) from the live analysis of all 16 bots
in the moonlight group (`../analysis-3-bots.md`) + the approved Word Guess
spec (`../word-guess-spec.md`).

## Dedup rule (Sanji)

Every distinct capability from all 16 bots is present, but a feature that
exists in several bots is built ONCE as one shared implementation:

| Merged module | Source bots |
|---|---|
| Shared economy (coins/bank/gems/XP) | Baka, Nova, Daizy, Mimi |
| Actions (rob/kill/protect/revive) | Baka, Nova, Mimi |
| Powers (Rampage/Cloak/Vault/Ascend) | Baka |
| Word Guess (Sanji's spec) | WordSeek → replaced by Sanji's spec |
| Word Grid | WordGridRobot |
| Wordchain | On9, Mimi, Nova |
| RPS | Daizy, Nova |
| Cricket | Daizy |
| Math Rush | Daizy |
| BBet/Bet | Daizy, Nova |
| Card | Baka, Nova |
| Number guess | Daizy |
| Romance (propose/marry/ship) | Nova, Mimi |
| Chat persona (Hinglish) | Nova, Daizy, Mimi, Baka |
| Moderation (warn/mute/ban/kick/pin/purge/staff) | Rose, Baka, GroupHelp clone |
| Link filter + blacklist | Protectron, Rose, Abuse Restrictions |
| Tagger (/utag /atag) | UserTagger |
| Message counter (/toprank) | ChatFight |
| Owner panel (/owner) | new — Sanji's requirement |
| Music (/play) | VC music — honest placeholder: voice-chat music needs a userbot assistant, not faked |

NOT copied: moonlight protection (group's own GroupHelp clone) and
@Vcttsrobot (Sanji's own TTS bot).

## Run

```bash
pip install -r requirements.txt
BOT_TOKEN=... API_ID=... API_HASH=... python bot.py
```

Env vars: `BOT_TOKEN`, `API_ID`, `API_HASH`, `OWNER_ID` (default 7966027018).
Persistence: `data.json` next to `bot.py` (best-effort — the bot-runner wipes
the bot dir on every restart, so data is not guaranteed across restarts).

## Phase 1 (this version)

Economy, actions, powers, Word Guess (spec-exact), Word Grid, Wordchain,
RPS, Cricket, Math Rush, BBet, Card, Number guess, romance, moderation,
link filter + blacklist, tagger, counter, chat persona, owner panel
(stats / users / groups / toggles / broadcast / status+restart).

## Phase 2 (planned)

UNO, Chess, Mines, Tap, Crash, Jumble, Charades, Bingo, Xoxo, Mafia lobby,
Hack, Bomb, Roulette, Bluff, Subway, Scribble. `/help` already says they are
coming — do not list them as working before they exist.
