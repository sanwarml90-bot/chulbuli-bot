# Chulbuli — Test Checklist (test.md)

Har chhoti se badi detail ka test list. Automated suite: `test_chulbuli.py`
(run: `~/workspace/bot-copy-3in1/venv/bin/python test_chulbuli.py` — 3 baar, 0 fail hona chahiye).
Live test sirf Sanji ke phone se (browser se Telegram send nahi hota).

## 1. Chat persona — Daizy style (sabse important)
- [ ] Sirf naam lene par ("chulbuli", "hii chulbuli") → chhota greeting ("hiee 💕" / "hlooo 😄"), AI call NAHI hota
- [ ] Greeting me yaad wala naam aata hai ("hiee Arjun 💕")
- [ ] Baaki baat-cheet lowercase casual Hinglish, ONE line, sweet — jaise Daizy ("im good thanks just chillin")
- [ ] "tum AI ho / bot ho / real ho?" → hansi-mazaak me taal deti hai, kabhi AI/bot confirm NAHI karti
- [ ] "kaise ho?" → "im good thanks, just chillin 😄" jaisa chhota jawab
- [ ] "i love you / pyaar" → sweet jawab, "awww" style
- [ ] Gussa/bakwas par → calm jawab, ladti nahi
- [ ] Kahin bhi user ko dikhne wale text me "AI" / "artificial" / "OpenRouter" / "model" word NAHI hai
- [ ] DM me bhi wahi style; group me sirf tag / "chulbuli" likhne / reply par jawab deti hai

## 2. Memory (strong)
- [ ] "mera naam X hai" → naam yaad; agle greeting me naam aata hai
- [ ] "mujhe cricket pasand hai" → fact yaad; /yaad me dikhta hai
- [ ] "mujhe X pasand nahi" → purani pasand replace hoti hai (ek hi opinion)
- [ ] "main X se hun" → city yaad; "mera birthday X hai" → birthday yaad
- [ ] "yaad rakhna ..." → explicit yaad
- [ ] Galat naam nahi banta ("main doctor hun" / "main thik hun" → naam NAHI)
- [ ] /yaad → apni yaadein dikhti hain (DM + group dono me)
- [ ] /bhool → facts + naam delete, coins/economy SAFE rehte hain
- [ ] History: last 20 turns per chat; AI ko last 10 turns + facts milte hain
- [ ] Facts 30 se zyada nahi; purane facts pehle delete hote hain

## 3. Economy
- [ ] /bal → balance, rank, status (alive/dead), kills, level
- [ ] /daily → roz ke coins + XP (ek din me ek baar)
- [ ] /give → reply karke coins dena
- [ ] /deposit / /withdraw → bank jama/nikasi, limit check
- [ ] /toprich → top 10 ameer; /leaderboard → game + economy leaders
- [ ] /rank → XP rank; /pfp → profile; /gems → gems store; /convert → gems → coins

## 4. Actions & Powers
- [ ] /rob / /kill / /protect / /shield / /revive (reply karke)
- [ ] /topkill / /toprob → top lists
- [ ] /powers → saari powers; /pinfo → details; /act → gems se activate; /mypowers; /extend
- [ ] Rampage / Cloak / Vault / Ascend — har ek ka asar sahi (limits, protection, XP)

## 5. Games — Phase 1
- [ ] /wordguess → board (🟩🟦⬜), reply karke guess, 6 guesses, jeetne par +500 coins, 3 min timeout
- [ ] /wordgrid → 8x8 grid, words, points, /hint, /balance
- [ ] /wordchain → join, 10s/turn, galat/repeat = out
- [ ] /rps → challenge, best of 3; /cricket → hand cricket; /math → 15 rounds; /bbet → 50/50; /card; /number → 100–500 guess

## 6. Games — Phase 2 (16 games)
- [ ] /uno → lobby, join, 7 cards, Skip/Reverse/+2/Wild/+4, winner pot/+5000
- [ ] /chess → legal moves, checkmate/stalemate, /elo, /chesstop
- [ ] /mines → 5x5, 3 mines, multiplier, /cashout
- [ ] /tap → 30s race, sabse zyada taps jeette hain
- [ ] /crash → multiplier, /cashout crash se pehle
- [ ] /jumble → scrambled word, pehla sahi +300; /charades → clue se guess +300
- [ ] /bingo → 5x5, auto-draw 12s, pehli line jeetti hai
- [ ] /xoxo → tic-tac-toe, pot winner ko
- [ ] /mafia → 5–12 players, roles, night kill/save/check, day vote, win check
- [ ] /hack → 4-digit code, feedback, 3 min; /bomb → pass the bomb, fuse 20–60s
- [ ] /roulette → red/black/green/number, 2x/36x; /bluff → claim/call, khali haath jeetta hai
- [ ] /subway → solo runner, obstacles, +10/obstacle; /scribble → 3 rounds, drawer + guesser points
- [ ] /end → koi bhi game khatam (bet refund ke saath)

## 7. Romance
- [ ] /propose (reply) → /marry accept → /ship compatibility → /divorce

## 8. Moderation (admins only)
- [ ] /warn / /unwarn / /mute / /unmute / /ban / /unban / /kick / /pin / /unpin / /purge
- [ ] /utag / /atag → mass ping (admin only); /reload
- [ ] /nolinks → link filter on/off; blacklist words delete hote hain
- [ ] /info / /id → user/group info; /staff → staff list

## 9. Owner Panel (/owner — sirf Sanji, ID 7966027018)
- [ ] Stats → total users, total groups; Groups → group list
- [ ] Toggles → Games / Economy / Chat / Baatein (AI) on-off, turant asar
- [ ] Broadcast → sab DMs + sab groups me announcement, delivery count
- [ ] Users ban/unban by ID; Status + Restart kaam karte hain

## 10. Buttons (commands ke saath-saath)
- [ ] /start + /help → menu keyboard (Games, Paise, Word Guess, Romance, Balance, Top, Help)
- [ ] Har submenu → sahi text + Back/Menu button
- [ ] Balance/Top button → /bal / /toprich jaisa hi text
- [ ] Game lobbies me "🙋 Join karo" button → join hota hai, player list update, button rehta hai
- [ ] Saare commands ab bhi kaam karte hain (buttons sirf extra hain)

## 11. Edge cases
- [ ] Banned user → koi command kaam nahi karti
- [ ] Games off → "Games abhi off hain"; Economy off → paise wale commands mana karte hain; Chat off → baat-cheet band
- [ ] Galat command / galat amount → seedha error, crash nahi
- [ ] Word Guess timeout (3 min) → word reveal, round khatam
- [ ] Data save: restart ke baad coins/facts/history same rehte hain

## 12. Deployment
- [ ] VERSION bump; commit + push; `git ls-remote` HEAD = naya commit; pushed file = local file
- [ ] Railway chulbuli-bot → nayi deployment ACTIVE, Online, "[chulbuli] starting vX" log, koi ERROR nahi
- [ ] Live /start Sanji ke phone se (browser se test nahi hota)

## Pending / Known gaps
- Word Guess: seedha guess (bina reply) — WordSeek style — ABHI NAHI bana (ek attempt refuse hua; Sanji dobara bole to phir try)
- Music /play → placeholder hai (voice ke liye userbot assistant chahiye, fake nahi kiya)
- Live test hamesha Sanji ke phone se (browser ka Telegram send kaam nahi karta)
