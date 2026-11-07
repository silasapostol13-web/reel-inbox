# Reel Inbox

Personal tool. Share an Instagram Reel (or TikTok) from the iPhone with a note, and any Claude Code
session can later "get the reel I just sent": the note, a full transcript, the key frames as images,
and the on-screen text/code. Free and local: no server, no account, no API keys.

```
iPhone share sheet ─► "Send to Claude" Shortcut ─► iCloud Drive/Shortcuts/ReelInbox/reel-<time>.json
                                                              │  (queues while the Mac is off)
Mac launchd agent (com.silas.reelinbox) ◄─────────────────────┘
  yt-dlp download ─► whisper.cpp transcript ─► ffmpeg candidate frames ─► Vision similarity + OCR
  ─► ~/ReelInbox/<id>/ reel.md · meta.json · source.json · frames/*.jpg
Claude Code ─► reel-inbox MCP server (user scope): list_reels · get_reel · mark_done
```

## Pieces

| Path | What |
|---|---|
| `shortcut/build_shortcut.py` | Builds + signs `shortcut/Send to Claude.shortcut` |
| `worker/reel_worker.py` | The Mac worker (stdlib Python). `--url URL --note "..."` processes one link by hand |
| `vision/reelvision.swift` | On-device OCR + image similarity (Apple Vision) → `bin/reelvision` |
| `mcp/reel_mcp.py` | Stdio MCP server (stdlib Python, no SDK) |
| `install.sh` | Re-runnable installer: model, Swift helper, launchd agent, MCP registration |
| `~/.claude/skills/reel-inbox/SKILL.md` | Tells Claude "the reel I sent" means `get_reel` (lives outside the repo) |

## How frames are picked

Candidates = ffmpeg scene changes + one frame every ~1.5s. Blank/fade frames are dropped. The timeline
is split into windows (~one per 3s, up to 10) and the frame with the most readable text wins each
window; the last slots go to the wordiest frames anywhere. Frames that look alike (Vision feature-print
distance < 0.6) are merged, keeping the wordier one. Max 12.

OCR lines that just repeat the spoken words (burned-in subtitles) and lines already shown on an
earlier frame are left out of `reel.md`. Claude still gets the images, so nothing is lost.

## Mac off / asleep

The phone never needs the Mac: the Shortcut saves into iCloud Drive (even offline) and the files
queue there. The agent runs at login (`RunAtLoad`), whenever the folder changes (`WatchPaths`), and
every 2 minutes (`StartInterval`), so after a wake it sweeps the whole backlog: oldest first by send
time, one reel at a time (no parallel load). iCloud placeholders (`.x.json.icloud`) are pulled down
with `brctl download`. If the Mac is offline right after waking, it waits for the next sweep without
using up retries.

Claude side: `get_reel` marks a reel opened; `list_reels` shows `[NEW]` and a count; `get_reel`
with id `next` walks the stack oldest-first; each new session is told "N new reels" at start
(through the MCP server's instructions, no hook needed).

## Ways to send

- From Instagram/TikTok: Share (paper plane) → Share to… → Send to Claude → note → Done.
- Copied link: run Send to Claude with nothing shared (Action Button, Back Tap, home-screen icon,
  widget) and it uses the clipboard. No link → it says so and stops.

## Failures

Nothing fails silently. A failed item stays in the iCloud inbox and is retried after 5, then 10
minutes (5 min × attempt); after 4 tries it moves to `ReelInbox/failed/` with the error inside. Every failure also gets
a `~/ReelInbox/<id>/` folder with status `failed` and a plain-English reason, so `list_reels` shows it.
If Instagram starts demanding a login for public reels, the error says so. Do not add browser
cookies without asking Silas.

Logs: `~/Library/Application Support/ReelInbox/worker.log`.

## Install / update

```bash
brew install yt-dlp ffmpeg whisper-cpp
./install.sh
```

Keep yt-dlp current (`brew upgrade yt-dlp`). Instagram changes often and an old yt-dlp is the most
likely reason downloads start failing.
