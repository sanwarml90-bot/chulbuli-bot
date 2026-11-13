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
- [ ] History: last 20 turns per chat; AI ko last 15 turns + facts milte hain (facts payload me SABSE PEHLE)
- [ ] AI models (v2.2.0): llama-3.1-8b-instruct:free pehle, phir qwen-2.5-7b, gemma-3-4b, cohere/north-mini-code:free LAST (code model chat ke liye nahi)
- [ ] AI persona: real sweet desi girl — "yaar"/"arre", chhote sweet replies, yaadein wapas laati hai, kabhi robotic nahi, kabhi AI/bot nahi kehti
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
- [ ] /warns → warn count (1/3, 2/3); 3 warns = auto-restrict
- [ ] /promote / /demote / /title → admin banao/hatao, custom title
- [ ] Baka-style dot commands: .warn .promote .demote .title .d (replied message delete) — "/" jaisa hi kaam
- [ ] /addsudo / /delsudo / /sudolist (owner only) — sudo users; /auth / /unauth / /authlist
- [ ] /utag / /atag → mass ping (admin only); /reload
- [ ] /nolinks → link filter on/off; blacklist words delete hote hain
- [ ] /rules / /setrules; /note / /get / /notes / /delnote; /report → admins ko tag; /runs; /limits
- [ ] /approve / /unapprove → approved user pe filters nahi lagte (BUG FIX v2.2.0: pehle str/int mismatch se bypass kabhi kaam nahi karta tha)
- [ ] /filter / /filters / /stopfilter → trigger word par auto-reply
- [ ] /antiflood → 3 msgs / 20s se zyada par delete + warning
- [ ] /profanity → gaali wale messages delete; /blacklist_add / /blacklist_remove / /blacklist_clear
- [ ] /whitelist_add / /whitelist_remove / /whitelist_clear → whitelisted domain ka link pass hota hai
- [ ] /noforwards → forwarded messages delete; /antispam → naye members (<10 min) links nahi bhej sakte
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

## 13. Music (v2.2.0 — KustMusic parity)
- [ ] /play <gaana ya link> → YouTube search (yt-dlp), player card: title, duration, requester + Skip/Pause/Resume/Stop buttons
- [ ] /play jab ASSISTANT_SESSION set nahi hai → imaandaar jawab "music assistant abhi connect nahi hai" — fake playing KABHI nahi
- [ ] /queue → abhi baj raha + queue list; /skip → agla gaana; /pause / /resume; /stop (alias /end) → VC chhodta hai; /clear → queue saaf; /ping → pong + assistant status
- [ ] /play DM me → group-only message
- [ ] /play jab UNO chal raha hai → UNO ka /play chalta hai, music chup rehta hai
- [ ] Assistant startup par Railway logs me @CBIOFINDIA (id 8617937893) dikhta hai (get_me se)
- [ ] LIVE voice test — asli group voice chat me, Sanji ke phone se — ABHI BAAKI. Update 2026-11-12 ~21:09 IST: ASSISTANT_SESSION set hai; builder Railpack → Nixpacks + Python 3.9 ho gaya, build log me tgcalls-2.0.0-cp39-manylinux wheel install hua (deployment 932c1a76, ACTIVE) — ab sirf LIVE /play test baaki hai

## 14. Gap audit v2.2.0 (16 moonlight bots — kya missing tha, kya bana, kya nahi ban sakta)
Per-bot detail — source: analysis-3-bots.md (live GHOST test 2026-11-12).
- **Baka @im_bakabot** — economy/powers/games/group-mgmt pehle se tha. v2.2.0 me bana: dot mod commands (.warn .promote .demote .title .d), /warns. Nahi bana: kill/rob ke baad CAPTCHA/human-verify (interactive verify flow — baad me), gems "Premium only" (payment-gated).
- **Nova @ItzNovaBot** — 17 games, romance, economy pehle se tha. v2.2.0 me bana: /addsudo /delsudo /sudolist, /auth /unauth /authlist, /revealgrid /checkgrid, /leaderboard buttons (eco/chess/subway/grid). Nahi bana: /groupbot on/off per-group activation (Chulbuli me global owner-panel toggles hain, per-group nahi), LUDO (rules observe nahi hue), /ws4 /ws6 (WordSeek-style direct guess — standing rule, nahi banega), /subwaycoins (paise kharch karta hai).
- **Daizy @GENZ_GAME_BOT** — cricket/RPS/Math/BBet pehle se tha. v2.2.0 me bana: /leaderboard buttons. Nahi bana: group me add karne par free-coins bonus (50k/1L/3L — feasible, baad me), inline RPS (inline mode chahiye — baad me).
- **Rose @MissRose_bot** — v2.2.0 me bana: /warn /warns, /approve /unapprove, /filter /filters /stopfilter, /note /get /notes /delnote, /rules /setrules, /report, /runs, /id, /info, /limits, /antiflood, link lock (/nolinks). Nahi bana: CAPTCHA (verify flow), Federations (cross-group infra — bada kaam), Connections (DM se group manage), Import/Export, AntiRaid, Log Channels, Languages, Topics, Clean Commands/Service — sab feasible hain, is build me nahi.
- **Protectron @ProtectronBot** — v2.2.0 me bana: /antispam (naye members ke links), /nolinks, /noforwards, /antiflood (3 msgs/20s), /profanity, /blacklist (+_add/_remove/_clear), /whitelist (+_add/_remove/_clear). NAHI BAN SAKTA: Advanced antispam neural network (ML model — available nahi), /imagefilter porn images (ML image classification — available nahi). Nahi bana (feasible, baad me): /noevents /nobots /nocontacts /nolocations /nohashtags /nocommands (message-type locks).
- **moonlight protection @itssmoonlight_bot** — COPY NAHI KIYA (group ka apna bot hai — standing rule). /staff Chulbuli me pehle se hai.
- **Abuse Restrictions @Abuserestrictionbot** — blacklist + profanity filter se cover (abuse words delete, restrict-on-ban-word = /warn flow).
- **WordSeek @WordSeekBot** — Chulbuli ka Word Guess (Sanji-approved spec: 🟩🟦⬜, 6 guesses, +500, har guess par NAYA board message) hi word-guess game hai. Seedha guess (bina reply) NAHI bana — standing rule (previous attempt refused — do NOT retry).
- **Word Grid @WordGridRobot** — /wordgrid, /hint, /balance, /end, /new pehle se tha. v2.2.0 me bana: /gridtop, /revealgrid, /checkgrid.
- **On9 Word Chain @on9wordchainbot** — v2.2.0 me bana: 8 modes (/startclassic /starthard /startchaos /startcfl /startrfl /startbl /startrl /startelim /startmelim), /flee, /runinfo, /wcstats. Nahi bana: /groupstats /globalstats (cross-group data — baad me), /addvp /remvp, wordchain /extend, /exists (dictionary check — baad me).
- **True Mafia @TrueMafiaBot** — /mafia game + /profile pehle se tha; v2.2.0 me /profile me money/gems/protection dikhta hai. Nahi bana: poora 16-role roster 1:1 map (subset implemented), gender choice prompt (irreversible — skip).
- **Mimi @im_mimibot** — v2.2.0 me bana: /acc alias, /alive, /vault, /shop, /inv, /guide, /free (+500, 6h cooldown), gift codes (/gencode owner /redeem /delcode /cinfo), +actions (+hug/+kiss/+pat/+slap/+bite/+punch/+murder), /ship /st. Nahi bana: /pro /tokens /exc /boost /binfo /equip /bh /seticon /reveal /locker /present /rh (token/premium economy — detail observe nahi hua).
- **User Tagger @UserTagger1Bot** — /utag /atag /cancel /reload pehle se tha.
- **ChatFight @ChatFightBot** — /mystats pehle se tha; v2.2.0 me aaj ka count + group rank dikhta hai. Nahi bana: global rank-entry announcements (cross-group counting — baad me).
- **VC music @vcmusiclubot (KUST MUSIC)** — v2.2.0 me bana: /play /queue /skip /pause /resume /stop (/end) /clear /ping + player card buttons (YouTube via yt-dlp; assistant @CBIOFINDIA via ASSISTANT_SESSION env). NAHI BAN SAKTA abhi: voice backend — pytgcalls 2.1.0 ka native dep `tgcalls` ke Linux wheels sirf Python ≤3.9 ke liye hain; Railway Python 3.12 par voice inactive rehta hai (module honestly degrade karta hai, fake playback nahi). Nahi bana: /mute /unmute /tmute /kick /ban in VC, /playlist (baad me), Spotify/SoundCloud/Apple/Resso sources (sirf YouTube), 24×7 mode, /clone (skip).
- **Vctts @Vcttsrobot** — COPY NAHI KIYA (Sanji ka apna bot hai — standing rule).

## 15. Chat realism (v2.3.0 — Sanji ki shikayat, 2026-11-12 21:15 IST)
Sanji: "har bar emojis send karti hai esse ai lagti hai or bat karte karte fir se hi hello send karti hai... typing dikhe... reaction bhi de... reply kar ke bat kare... har 5 mint me group ke last msg pade... daizy ki trah math question... har bar ese bat na kare jese bat start hui hai"
- [ ] Emojis: zyada tar chat replies me KOI emoji nahi — sirf kabhi-kabhi ek. Har message me emoji = AI jaisa lagta hai, ab nahi
- [ ] Beech me "hiee"/"hello" dobara nahi — jis se baat chal rahi hai us se continue kare; 30 min ke gap ke baad hi dobara greet kare; naya user ab bhi greet hota hai
- [ ] Reply length: aam taur par 1-2 lines, kabhi 3-4 lines bhi (topic ke hisaab se)
- [ ] Typing indicator: chat reply se pehle upar "typing..." dikhe, 1-3 sec ka natural pause (reply jitna lamba, utna zyada) — DM aur group dono me; commands/games turant rehte hain
- [ ] Reply-to quote: chat reply usi ke message ko quote karke aaye
- [ ] Reaction: jawaab dete hue us message par kabhi-kabhi emoji reaction (❤️ 😄 😂 👍 🔥 🥰) — har bar nahi; reaction fail ho to reply phir bhi jaye
- [ ] Proactive (har 5 min): active group (10 min me message aaya ho) me ek person ko reply karke baat shuru kare — group ki history ke hisaab se; 30 min me bot bol chuka ho to chup rahe; chat off ho to kuch nahi; DM me kabhi nahi; apne ya dusre bot ke message par nahi
- [ ] Math poster (har 30-60 min, ek active group me): Daizy-style math question — level (easy/medium/hard) + reward (easy +100, medium +250, hard +500 coins); pehla sahi jawab jeete; 5 min me koi jawab na de to chup-chaap khatam (koi spam nahi); game chal raha ho to post nahi
- [ ] Memory/continuity: pehle ki baat yaad rakh ke bole — wahi sawaal dobara nahi, dobara introduce nahi; naam yaad rahe to naam se bole (bina greet kiye, jab baat chal rahi ho)
- [ ] LIVE test Sanji ke phone se: group me "chulbuli" bolo → typing dikhe → quote reply aaye → reaction dikhe; beech me dobara "hiee" na aaye; 5 min baad group me khud baat shuru kare; math question aaye aur sahi jawab par coins mile

## 16. Live bug fixes (v2.3.1 — Sanji ki live report, 2026-11-12 ~21:28 IST)
Sanji: "naam lene par bhi reply nahi aa raha hai... /promote try kiya to permission error... /play wala kam nahi kar raha hai, koi response nahi"
- [ ] /play: YouTube bot-check ("Sign in to confirm you're not a bot") ab bot ko chup nahi karata — resolve_track DownloadError ko MusicError("youtube_blocked") me badalta hai, /play hamesha imaandari se jawab deta hai ("youtube ne block kar diya, thodi der me try karo"); koi bhi aur error bhi reply deta hai, kabhi silence nahi. (YouTube ka bot-check khud fix NAHI hua — sirf silence fix hua.)
- [ ] /promote: Pyrogram 2.0.106 me `promote_chat_member` sirf `ChatPrivileges` object leta hai — purana boolean-kwargs call HAR BAAR TypeError deta tha, isliye /promote kabhi kaam hi nahi karta tha (permission ki baat hi nahi thi). Ab: bot ke apne rights mirror karke promote karta hai; bot ke paas "Add New Admins" na ho to wahi specific right naam se batata hai; asli error logs me print hota hai
- [ ] /demote: all-False ChatPrivileges se demote (dhyaan: ChatPrivileges() default can_manage_chat=True hota hai — sab fields explicit False)
- [ ] /title: `set_chat_admin_custom_title` naam ka method Pyrogram me hai hi nahi — sahi naam `set_administrator_title` use hota hai
- [ ] Name-call: chat_reply_ai kabhi raise nahi karta, kabhi blank reply nahi deta (AI fail ho ya blank de to rule-based line); group + DM handler dono me safety net; naam lete hi Railway logs me "[chulbuli] name-call in <chat> from <user>" line aati hai — isse pata chalta hai message bot tak pahuncha ya nahi (privacy mode = line hi nahi aayegi)
- [ ] LIVE test Sanji ke phone se: test group me (bot ko ADMIN banao, "Add New Admins" ke saath) — "chulbuli" bolo → reply aaye; /promote (reply karke) → admin bane; /play <gaana> → ya to baje ya youtube-block wali imaandari wali baat aaye (silence nahi)

## 17. AI models + YouTube /play (v2.3.2 — live log evidence, 2026-11-12 ~21:44 IST)
Live Railway logs 21:44:31 IST: bot ne AI_MODELS ke chaaron models try kiye, sab fail — llama-3.1-8b-instruct:free → 404, qwen-2.5-7b-instruct:free → 404, gemma-3-4b-it:free → 404, cohere/north-mini-code:free → 429. Live OpenRouter free list (~21:53 IST) se verify: teeno 404 wale models free list me ab hain hi nahi.
- [ ] AI_MODELS: sirf us waqt free-listed models — chhote/fast non-reasoning chat models pehle (liquid/lfm-3-1.7b, thinkingmachines/inkling-2-small, recursive/flint-v1.0, nemotron-3.5-lightning), phir baaki, cohere + gemma-4 models aakhir me, openrouter/free sabse aakhir (auto-route fallback); max_tokens 800 waise hi; koi model live-test NAHI hua (key yahan nahi hai) — live deploy ke logs batayenge kaunsa chalta hai; sab fail ho to rule-based fallback (kabhi silence nahi)
- [ ] /play YouTube: resolve_track ab `extractor_args: {"youtube": {"player_client": ["android", "ios", "web"]}}` bhejta hai (mobile clients bot-check bypass karte hain — installed yt-dlp 2026.10.26 se verify); pehli koshish YouTube block ho to ek retry `["tv", "web"]` clients se; "The page needs to be reloaded." (live logs 21:39:51/21:40:01/21:40:31) ab youtube_blocked me aata hai, \"song not found\" me nahi — /play hamesha imaandari se jawab deta hai
- [ ] YouTube cookies NAHI daale (Sanji ka account chahiye — available nahi); /play fix hone ka daava NAHI — workaround se chances badhte hain, live /play test hi prove karega
- [ ] LIVE test Sanji ke phone se: test group me (bot ADMIN) — \"chulbuli\" bolo → reply aaye (v2.3.1 safety net + logs me name-call line); /play <gaana> → ya to baje ya youtube-block wali imaandari wali baat aaye; chat me AI jawab aaye (rule-based fallback nahi, asli AI) — logs me kaunsa model chala ye dikhega

## 18. Voice-stack diagnostics (v2.3.3 — Sanji ki live /play report, 2026-11-12 ~22:04 IST)
Sanji: "/play pe 'Warriyo - Mortals (ft. Laura Brehm) mil gaya! par voice assistant abhi connect nahi hai'". Matlab YouTube search ab kaam karta hai (v2.3.2 workaround), par voice stack nahi chal raha — aur logs me reason chhupa tha: pytgcalls import fail hota to `except` chup-chaap None kar deta tha, ASSISTANT_SESSION khaali hota to `_music_ensure_assistant` bina bole False deta tha.
- [ ] Import blocks ab asli exception print karte hain: yt-dlp / pytgcalls / imageio-ffmpeg fail ho to Railway logs me "[chulbuli] music: <name> import failed: <exception>" aata hai (koi secret kabhi print nahi hota)
- [ ] Startup diagnostic (ek baar, "[chulbuli] starting" ke turant baad): "[chulbuli] python: <version> (<platform>)" + "[chulbuli] voice: pytgcalls=<True/False> session=<set/MISSING> yt_dlp=<True/False> ffmpeg=<yes/no>" — session ki value kabhi print nahi hoti, sirf set hai ya MISSING
- [ ] /play jab voice stack na ho to logs me reason likhta hai: "[chulbuli] /play voice unavailable: pytgcalls missing" ya "ASSISTANT_SESSION missing" — user ko wahi chhota imaandari wala reply milta hai, badla nahi
- [ ] `_music_ensure_assistant`: har failure path ab asli exception print karta hai — session missing, pytgcalls missing, client start fail, get_me fail, PyTgCalls init fail, stream-end hook fail; koi `except: pass` nahi bacha is function me
- [ ] Diagnostics-only release — voice/play logic, AI models, aur koi feature change NAHI hua
- [ ] LIVE check (deploy ke baad Railway logs me): startup pe python version line + voice line dhoondho — isse pata chalega pytgcalls install hua ya nahi, session set hai ya MISSING; phir /play karo to "/play voice unavailable: <reason>" line exact cause batayegi
- Word Guess: seedha guess (bina reply) — WordSeek style — NAHI banega (previous attempt refused — do NOT retry, rephrase, ya route around)
- Music: module bana hua hai, ASSISTANT_SESSION set hai, builder Nixpacks + Python 3.9 ho gaya aur tgcalls-2.0.0-cp39 wheel install hua (2026-11-12, deployment 932c1a76) — ab sirf LIVE /play test baaki hai Sanji ke phone se; PYTHONUNBUFFERED=1 fix parent kar raha hai
- Name-call ka sabse likely live cause (code se bahar): test group me bot ADMIN nahi hai → Telegram privacy mode me plain "chulbuli" bot tak pahuncht hi nahi (commands /promote, /play phir bhi pahunchte hain — isliye /promote ne reply diya par naam pe kuch nahi aaya). Fix: group me bot ko admin banao (full rights + "Add New Admins"). Agar admin banane ke baad bhi naam pe reply na aaye to Railway logs me "[chulbuli] name-call" line dhoondho — line na ho = message aaya hi nahi; line ho = handler me kuch aur hai.
- Live test hamesha Sanji ke phone se (browser ka Telegram send kaam nahi karta)

## 19. Voice layer rewritten on the REAL pytgcalls 2.1.0 API (v2.3.4 — v2.3.3 logs, 2026-11-12 ~22:14 IST)
ROOT CAUSE (proven, not guessed): v2.3.3 startup log — `[chulbuli] music: pytgcalls import failed: ImportError("cannot import name 'PyTgCalls' from 'pytgcalls'")` + `voice: pytgcalls=False session=set yt_dlp=True ffmpeg=yes`, python 3.9.18. The real pytgcalls-2.1.0 wheel (PyPI se download karke padha) me `PyTgCalls` class hai hi nahi — aur 2.1.0 hi PyPI pe latest hai (koi 3.x release nahi). Matlab v2.2.0 ka music code ek aise API pe likha tha jo kabhi release hi nahi hua; import fail hota tha, isiliye /play hamesha "voice assistant connect nahi hai" bolta tha.
- [ ] Voice layer ab asli 2.1.0 API pe hai (wheel source se verify): `GroupCallFactory(assistant_client)` ek baar banta hai (`_ASSISTANT["factory"]`); har chat ka apna `GroupCallFile` hota hai — `factory.get_file_group_call(input_filename=<local file>, play_on_repeat=False)` → `await gc.start(chat_id)` join karta hai; skip = `gc.input_filename = next_path` (connected ho to playout khud restart hota hai); pause/resume = sync `pause_playout()` / `resume_playout()`; stop = `gc.stop_playout()` + `await gc.stop()`; auto-advance = `@gc.on_playout_ended` handler (async, `(gc, filename)` args)
- [ ] GroupCallFile sirf LOCAL FILE bajata hai, URL nahi — isiliye /play pehle yt-dlp se audio download karta hai (`_music_download_sync` → temp file `chulbuli-music/` me; wahi mobile player clients + tv/web retry, mp3 extract jab ffmpeg ho; `asyncio.to_thread` me chalta hai taaki event loop block na ho). Download fail ho (YouTube bot-check samet) to imaandari wala reply aata hai, "baj raha hai" kabhi fake nahi hota. Temp file track badalne / rukne / khatam hone pe delete hoti hai
- [ ] Purani API ka ek bhi naam code me nahi bacha — `PyTgCalls`, `AudioPiped`, `join_group_call`, `leave_group_call`, `change_stream`, `pause_stream`, `resume_stream`, `on_stream_end` sab hataye gaye (test bhi assert karta hai); `music_voice_available()` / `voice_unavailable_reason()` ("GroupCallFactory missing") / startup diagnostic ab factory ko check karte hain; session value ab bhi kabhi print nahi hoti
- [ ] Test harness ab ASLI 2.1.0 API ko mirror karta hai (v2.3.1 wala lesson: purana harness real library se zyada permissive tha, isiliye 401 tests ne dead import kabhi pakda nahi) — fake factory + fake GroupCallFile (property setter restart record karta hai, `on_playout_ended` decorator, sync pause/resume); purane naam call karne pe AttributeError aata hai. Tests: download-then-play flow, skip via input_filename setter, pause/resume, stop cleanup (temp file deleted), playout-end auto-advance, empty queue pe leave, fresh call after leave, download failure pe honest reply (kabhi "playing" fake nahi), voice reason me GroupCallFactory ka naam
- [ ] Tests: 424/424 PASS, 3 consecutive runs (baseline 401; +23 naye). requirements.txt ka pin wahi hai (`pytgcalls==2.1.0; python_version < "3.10"` — 2.1.0 PyPI pe latest hai); sirf comment update hua
- [ ] LIVE test Sanji ke phone se (ABHI TAK NAHI HUA — ye rewrite live-verify NAHI hai): test group me jahan VOICE CHAT chal raha ho, /play <gaana> karo — gaana download hoke VC me ACTUALLY bajna chahiye (assistant @CBIOFINDIA VC join karega). Agar group me koi VC nahi hai to bot imaandari se bolega "group me koi voice chat nahi hai — pehle VC start karo". /skip, /pause, /resume, /stop bhi test karo; do gaane queue karo to pehla khatam hote hi dusra khud bajna chahiye

## 20. ffprobe missing -> skip mp3 extract, keep native audio (v2.3.5 — Sanji ki live /play report, 2026-11-13 ~08:32 IST)
Sanji: "/play pe 'download failed: ERROR: Postprocessing: ffprobe and ffmpeg not found. Please install or provide the path using ffmpeg-location'". Matlab gaana mil gaya, download bhi shuru hua, par mp3 banate waqt fail ho gaya.
ROOT CAUSE (verify kiya hua, guess nahi): `_music_download_sync` me `if music_ffmpeg_setup():` hote hi FFmpegExtractAudio postprocessor lag jata tha. `music_ffmpeg_setup()` imageio-ffmpeg ka `ffmpeg` binary dhoondh ke truthy deta hai — par imageio-ffmpeg ki folder me SIRF `ffmpeg` binary hai, `ffprobe` hai hi nahi (venv me check karke confirm kiya). yt-dlp ka FFmpegExtractAudio postprocessor ko ffmpeg AUR ffprobe DONO chahiye — isiliye Railway pe (system ffmpeg/ffprobe nahi, sirf imageio-ffmpeg binary) postprocessor fail hota tha aur poora download fail ho jata tha, jabki audio file khud download ho chuki thi. Startup diagnostic `ffmpeg=yes` sirf ffmpeg binary ka matlab tha, ffprobe ka nahi — isiliye ye dikhai nahi diya.
- [ ] Fix: postprocessor tabhi lagta hai jab `shutil.which("ffmpeg")` AUR `shutil.which("ffprobe")` dono milein (music_ffmpeg_setup() ke baad check hota hai). ffprobe na mile to postprocessor skip hota hai aur yt-dlp ka native container (webm/m4a) rehta hai — tgcalls apni bundled ffmpeg libraries se webm/m4a khud decode karta hai, conversion ki zaroorat nahi. Skip hone pe log me aata hai: "[chulbuli] music: ffprobe missing — keeping native audio, no mp3 extract"
- [ ] Download ka path no-postprocessor case me bhi sahi milta hai — `requested_downloads` / stem-scan fallback pehle se tha, ab native extension (.m4a/.webm) wali file return hoti hai; GroupCallFile ko extension se farak nahi padta, file path chahiye
- [ ] apt/nixpacks se ffmpeg/ffprobe install NAHI kiya, requirements.txt change NAHI hua — fix ye hai ki ffprobe maanga hi na jaye, system package add karna nahi. YouTube search/download workaround (mobile player clients + tv/web retry) waisa hi hai
- [ ] Test harness ab asli yt-dlp behaviour mirror karta hai: fake YDL postprocessor on + ffprobe missing ho to wahi asli error raise karta hai ("ERROR: Postprocessing: ffprobe and ffmpeg not found..."). Naye checks: ffprobe missing → download succeed, native ext file, skip log aata hai; dono present → postprocessor on, mp3 return; fake postprocessor bina ffprobe ke fail karta hai
- [ ] Tests: 429/429 PASS, 3 consecutive runs (baseline 424; +5 naye)
- [ ] LIVE test Sanji ke phone se (ABHI TAK NAHI HUA — ye fix live-verify NAHI hai): test group me jahan VOICE CHAT chal raha ho, /play <gaana> karo — gaana download hoke VC me ACTUALLY bajna chahiye. Logs me "[chulbuli] music: ffprobe missing — keeping native audio, no mp3 extract" line dikhegi (Railway pe yehi path chalega, mp3 extract skip hoga)

## 21. Peer-cache population — "Peer id invalid" crash fix (v2.3.6 — live v2.3.4 logs, 2026-11-13 08:33:59 + 08:35:30 IST)
Live logs me do baar "Task exception was never retrieved" — `KeyError: 'ID not found: -1003962580050'` aur `-1003866876068` (moonlight) → `ValueError('Peer id invalid')`, `Client.handle_updates()` me. Matlab bot un chats me deaf ho jata hai.
ROOT CAUSE (installed Pyrogram 2.0.106 source se verify kiya, guess nahi): `utils.get_peer_type` channel id > 2**31-1 ko reject karta hai (`MIN_CHANNEL_ID = -1002147483647` — moonlight -1003866876068 isse bada hai). `resolve_peer` wahan tabhi pahunchta hai jab peer session cache me NAHI hai; cache me ho to `get_peer_by_id` se mil jata hai aur ye code kabhi chalta hi nahi. Railway pe har deploy ke saath session file nayi banti hai (filesystem ephemeral) — isiliye har deploy ke baad cache khaali hota hai, aur pehla min-update (`is_min` path → `GetChannelDifference` → `resolve_peer`) crash karta hai. `handle_updates` har update batch ke liye naya task banta hai (session.py:255) — ek crash se poora loop nahi marta, par us chat ka har min-update waise hi marta hai, to bot wahan deaf rehta hai jab tak peer cache na ho.
- [ ] Fix: startup pe peer cache bharo — `_populate_peer_cache(client, label)`: `client.get_dialogs()` ko walk karta hai; `Client.invoke()` har result ke users/chats pe `fetch_peers` chalata hai, to saare dialogs ke peers cache ho jate hain. Bot client ke liye `_schedule_peer_cache_population()` (pehle update pe ek baar, wahi pattern jo `_music_schedule_startup` ka hai — `app.run()` ka koi startup hook nahi hai); assistant client ke liye `_music_ensure_assistant` ke successful start ke baad task banta hai. Dono me log aata hai: "[chulbuli] peer cache (bot|assistant): N dialogs cached". Koi bhi failure swallow hoti hai (log + partial count) — startup kabhi block nahi hota
- [ ] Dusri layer: NAHI hai, aur jaan-bujh ke nahi banayi — Dispatcher sirf handlers ke exceptions guard karta hai (`dispatcher.py`); `handle_updates` ki failure ka Pyrogram me koi supported hook nahi hai, aur `Client.handle_updates` ko monkey-patch karna internals chhedna hota. Population hi fix hai
- [ ] Runtime case (bot chalte hue naye group me add ho): `_music_assistant_join_chat` pehle se `app.get_chat(chat_id)` se resolve karta hai (API call, cache par bharosa nahi). Naya: agar `get_chat` peer error se fail ho to ek baar `_populate_peer_cache(app, "bot")` chala ke retry karta hai — sirf peer errors ("Peer id invalid" / "ID not found" / KeyError / ValueError) pe, baaki errors fail-fast. Baaki jagah (broadcast, proactive loop, math poster) pehle se per-recipient try/except me hain; handler se chalne wale sends safe hain kyunki non-min update ka peer `handle_updates` ke shuru me hi `fetch_peers` se cache ho chuka hota hai
- [ ] Tests: 434/434 PASS, 3 consecutive runs (baseline 429; +5 naye): population counts dialogs (FakeApp ke dialogs me moonlight ka bada id bhi hai), failure mid-walk swallow + partial count, scheduler ek hi baar chalta hai, assistant ki population alag se, join-retry populate ke baad succeed karta hai
- [ ] LIVE test (ABHI TAK NAHI HUA — ye robustness fix live-prove NAHI hai): bot moonlight aur baaki groups me kuch der chale bina "Peer id invalid" task exception ke — logs me "[chulbuli] peer cache (bot): N dialogs cached" aur "[chulbuli] peer cache (assistant): N dialogs cached" lines dikhni chahiye

## 22. USER_ALREADY_PARTICIPANT is success, not failure (v2.3.7 — Sanji ki live /play report, 2026-11-13 ~08:55 IST)
Sanji: "/play pe 'assistant group me join nahi kar paya: Telegram says: [400 USER_ALREADY_PARTICIPANT] - The user is already a participant of this chat (caused by "messages.ImportChatInvite")'".
ROOT CAUSE (verify kiya hua, guess nahi): `_music_assistant_join_chat` me `user_client.join_chat(username)` / `join_chat(link)` ek bare `except Exception` ke andar tha jo kuch bhi fail hone pe `MusicError("assistant group me join nahi kar paya: ...")` raise karta tha. Assistant (@CBIOFINDIA) group ka member PEHLE SE tha, to Telegram sahi tareeke se 400 USER_ALREADY_PARTICIPANT return karta hai — par code "pehle se member hai" ko bhi failure maan raha tha. Pehle se member hona SUCCESS hai: assistant group me hai aur VC join kar sakta hai. Installed Pyrogram 2.0.106 me `pyrogram.errors.UserAlreadyParticipant` class maujood hai (`pyrogram.errors.exceptions.bad_request_400`) — uska string form bilkul wahi hai jo Sanji ki report me tha. Ek aur baat: join tabhi try hota hai jab `gc.start(chat_id)` pehle fail ho chuka ho (`_music_stream_track` me), aur wo ORIGINAL gc.start exception ab tak swallow ho jati thi — join error usko mask kar deta tha.
- [ ] Fix: `_music_assistant_join_chat` me `UserAlreadyParticipant` catch karke normal return hota hai (dono join paths — username aur invite link — pe). Belt-and-braces fallback: exception ke text me "USER_ALREADY_PARTICIPANT" ho to bhi success maana jata hai (agar kisi Pyrogram version me ye alag tareeke se surface ho). Koi AUR join error pehle jaise hi `MusicError("assistant group me join nahi kar paya: ...")` raise karta hai
- [ ] `_music_stream_track` me ab original `gc.start(chat_id)` exception print hoti hai (`[chulbuli] music gc.start failed, trying assistant join: <exc>`) join try karne se PEHLE — taaki logs me asli pehli failure dikhe, sirf join error nahi. Retry flow waisa hi hai; agar retry pe bhi gc.start fail ho to `_music_start_error_text` se imaandari wala reply aata hai (e.g. GroupCallNotFound → "group me koi voice chat nahi hai — pehle VC start karo")
- [ ] Tests: 440/440 PASS, 3 consecutive runs (baseline 434; +6 naye): join_chat se UserAlreadyParticipant (username path aur invite-link path dono) → no MusicError, function normal return; string fallback (plain Exception me "USER_ALREADY_PARTICIPANT") → bhi success; alag join error (FLOOD_WAIT_10) → ab bhi MusicError "join nahi kar paya"; gc.start ki pehli failure join se pehle log hoti hai aur retry pe start succeed karta hai (flaky fake GroupCallFile: pehli start raise, dusri succeed)
- [ ] LIVE test Sanji ke phone se (ABHI TAK NAHI HUA — ye fix live-verify NAHI hai): test group me jahan VOICE CHAT chal raha ho, /play <gaana> karo — assistant pehle se group me hai to join no-op hoga aur gaana ACTUALLY bajna chahiye. Agar retry pe bhi gc.start fail ho to uska asli error ab logs/reply me dikhega

## 23. Bot peer cache must NOT use get_dialogs (v2.3.8 — live v2.3.6 logs, 2026-11-13 08:53:54 IST)
Live v2.3.6 logs: `[chulbuli] peer cache (bot): stopped after 0 dialogs: BotMethodInvalid('Telegram says: [400 BOT_METHOD_INVALID] - The method can't be used by bots (caused by "messages.GetDialogs")')`. Matlab v2.3.6 ka fix BOT ke liye kabhi chala hi nahi — 0 dialogs cache hue. Sirf assistant (user client) kaam karta hai (`peer cache (assistant): 54 dialogs cached` 08:53:56 IST). Bot isliye moonlight me ABHI BHI deaf hai — agla min-update wahan se aate hi wahi "Peer id invalid" crash dobara hoga. v2.3.6 ke window (08:48–09:01 IST) me koi "Peer id invalid" dobara nahi aaya, par wo timing/luck hai, proof nahi — BotMethodInvalid line hi proof hai ki bot cache kaam nahi karta.
ROOT CAUSE (installed Pyrogram 2.0.106 source se verify kiya): `messages.GetDialogs` sirf user accounts ke liye hai — bots ke liye Telegram 400 BOT_METHOD_INVALID deta hai. Aur dusri taraf, `get_chat` bhi uncached bade supergroup id ko resolve nahi kar sakta: `get_chat` pehle `resolve_peer` call karta hai, aur `resolve_peer` → `utils.get_peer_type` uncached id pe `ValueError("Peer id invalid")` raise karta hai (moonlight -1003866876068, `MIN_CHANNEL_ID = -1002147483647` se bada) — koi API call hone se pehle. To bot ke liye get_chat sirf tab kaam karta hai jab peer pehle se cache ho ya id chhota ho.
- [ ] Fix: population ab client type se split hai — `_populate_peer_cache(client, label, use_dialogs=True)`. Assistant (user client) `get_dialogs()` walk karta rehta hai (kaam karta hai). Bot (`use_dialogs=False`) apne KNOWN chat ids walk karta hai (`_known_chat_ids()`: DATA["chats"] + DATA["history"] + DATA["recent"] ke str keys + MUSIC keys — sab `track_user`/`_chat_data`/`record_exchange` se pehle se record hote hain jab bhi bot kisi group ko serve karta hai; user ids jaan-bujh ke nahi liye — users ke liye resolve_peer khud heal karta hai aur users table bahut badi ho sakti hai). Har id pe `_cache_bot_peer(client, chat_id)`: pehle `get_chat` try karta hai; agar peer error se fail ho aur id -100... supergroup/channel ho to raw `channels.GetChannels` call karta hai — `InputChannel(channel_id, access_hash=0)` se (participant ke liye server id se resolve karta hai; yehi call Pyrogram ke `resolve_peer` fallback me bhi hai) — aur `Client.invoke` returned chat ko `fetch_peers` se cache karta hai. Ek kharab id baaki ko nahi rokti (per-chat try/except); FloodWait aaye to walk wahi ruk jata hai
- [ ] `_music_assistant_join_chat` ka get_chat-retry path waisa hi hai, bas ab `_populate_peer_cache(app, "bot", use_dialogs=False)` call karta hai. Music/download logic, AI models, baaki features — kuch nahi badla
- [ ] Tests: 445/445 PASS, 3 consecutive runs (baseline 440; +6 naye, −1 purana v2.3.6 "population counts dialogs" check hata diya — bot ab dialogs walk karta hi nahi): bot kabhi get_dialogs call nahi karta (FakeApp.get_dialogs ab BotMethodInvalid raise karta hai — agar code path use kare to test turant fail hota); bot har known id pe get_chat call karta hai (chats + history + MUSIC ka union); bada id (moonlight) GetChannels fallback se cache hota hai (channel_id=3866876068, access_hash=0, ek hi invoke call); kharab id skip hoti hai bina baaki roke ("4 chats cached, 1 failed"); FloodWait aaye to walk wahi ruk jata hai (baad wale ids try hi nahi hote); assistant ab bhi get_dialogs use karta hai (purana test waisa hi)
- [ ] LIVE test (ABHI TAK NAHI HUA — ye fix live-prove NAHI hai): v2.3.8 ke logs me `[chulbuli] peer cache (bot): N chats cached` dikhna chahiye jahan N > 0 ho (BotMethodInvalid wali line NAHI aani chahiye), aur uske baad moonlight/groups me bina "Peer id invalid" task exception ke chalna chahiye
