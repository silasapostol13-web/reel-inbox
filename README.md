<h1 align="center">Reel Inbox</h1>

<p align="center">
  <b>Share a Reel from your iPhone with a note. Ask Claude Code about it later.</b><br>
  Claude gets your note, the full transcript, the key frames as images, and any code that was on screen.
</p>

<p align="center">
  <img src="docs/hero.svg" alt="Share from Instagram, add a note, your Mac processes it locally, Claude Code reads it" width="100%">
</p>

<p align="center">
  <img alt="macOS" src="https://img.shields.io/badge/macOS-Apple%20silicon-111?logo=apple">
  <img alt="iOS Shortcut" src="https://img.shields.io/badge/iOS-Shortcuts-111?logo=shortcuts">
  <img alt="MCP" src="https://img.shields.io/badge/Claude%20Code-MCP%20server-d9674a">
  <img alt="Runs locally" src="https://img.shields.io/badge/runs-100%25%20local-2e7d32">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue">
</p>

---

**Quick start** (Mac with Apple silicon, with [Homebrew](https://brew.sh), the Xcode Command Line Tools
(`xcode-select --install`) and [Claude Code](https://code.claude.com/docs/en/setup) already installed;
free, about 10 minutes):

```bash
git clone https://github.com/silasapostol13-web/reel-inbox.git ~/reel-inbox
cd ~/reel-inbox && ./install.sh
```

Then get the **Send to Claude** shortcut onto your iPhone ([step 4](#setup)), share a Reel to it, and
ask Claude Code *"get the reel I just sent"*. Full steps are under [Setup](#setup).

---

A lot of good Claude Code tips, tools and build ideas show up as 40-second Reels. Watching one on
your phone and then trying to explain it to Claude later loses most of it: the repo name that was on
screen for a second, the exact command, what the person actually said.

Reel Inbox closes that gap with three small pieces:

1. **An iPhone Shortcut** in the share sheet. Share a Reel (or TikTok), say or type why you're
   sending it, done. It saves the link and your note to iCloud Drive, so it works with your Mac
   off.
2. **A macOS worker** that downloads each video, transcribes it, picks the frames that matter, and
   reads the on-screen text with Apple's Vision framework. Everything runs on your Mac and costs
   nothing.
3. **An MCP server for Claude Code**, so any session can answer "get the reel I just sent", and Claude
   actually sees the frames.

## What Claude gets

```
~/ReelInbox/2026-11-07-170623-sound-effects-for-the-demo-video/
├── reel.md       ← your note, link, creator, caption, timestamped transcript, on-screen text per frame
├── meta.json     ← the same, structured (status, errors, frame times, opened/done)
├── source.json   ← exactly what the phone sent
└── frames/       ← up to 12 key frames, e.g. 03_0m07s.jpg
```

In Claude Code:

| You say | What happens |
|---|---|
| "get the reel I just sent" | `get_reel` returns the newest one: text plus the frames as images |
| "go through my reels" | `get_reel id:"next"` walks unread reels oldest first, one at a time |
| "what reels do I have?" | `list_reels` shows each one with your note, and how many are unread |
| "the one about sound effects" | `get_reel` matches words from your note, the caption or the creator |
| "mark it done" | `mark_done` hides it from the list (nothing is deleted) |

New sessions are told how many unread reels are waiting, so Claude can mention them without being
asked.

## How it works

```mermaid
flowchart LR
  A["Instagram / TikTok<br/>Share → Send to Claude"] --> B["Note prompt<br/>(type or dictate)"]
  B --> C[("iCloud Drive<br/>Shortcuts/ReelInbox/*.json")]
  C -- "launchd: on change,<br/>at login, every 2 min" --> D["Worker"]
  subgraph Mac["Your Mac (all local)"]
    D --> E["yt-dlp<br/>download"]
    E --> F["whisper.cpp<br/>transcript"]
    E --> G["ffmpeg<br/>candidate frames"]
    G --> H["Apple Vision<br/>similarity + OCR"]
    F --> I[("~/ReelInbox/&lt;id&gt;/")]
    H --> I
  end
  I --> J["MCP server<br/>list_reels · get_reel · mark_done"]
  J --> K["Claude Code"]
```

On an M3 Pro a typical 50-second Reel takes 10–15 seconds from start to finish. A stack sent while the
Mac was asleep is worked through oldest first, one at a time, the next time it's awake.

## Requirements

- A Mac with Apple silicon. Tested on an M3 Pro with macOS 26. Intel Macs are untested.
- [Homebrew](https://brew.sh), Xcode Command Line Tools (`xcode-select --install`), and
  [Claude Code](https://code.claude.com/docs/en/setup)
- An iPhone with the Shortcuts app, signed in to **the same Apple ID** as the Mac, with iCloud Drive on
- About 600 MB of disk, almost all of it the speech model

The installer adds the rest with Homebrew, all free and open source: `yt-dlp`, `ffmpeg`, `whisper.cpp`,
and Python if you don't have Homebrew's already.

## Setup

**1. Have the basics.** Homebrew, the Xcode Command Line Tools, and Claude Code (see Requirements).
To check, paste this into Terminal. If all three answer with a version (and no "command not found"), you're set:

```bash
brew --version && swiftc --version && claude --version
```

**2. Clone the repo** somewhere it can stay. The background job and Claude both point at this folder.
If you move it later, run `./install.sh` again.

```bash
git clone https://github.com/silasapostol13-web/reel-inbox.git ~/reel-inbox
```

**3. Run the installer.** It installs `yt-dlp`, `ffmpeg` and `whisper.cpp` with Homebrew if they're
missing, downloads the speech model (about 575 MB, once), compiles two small Swift helpers, starts the
background job, registers the MCP server for every Claude Code session, and adds a small Claude skill.
It's safe to run again. If it warns that the Shortcuts iCloud folder doesn't exist yet, that's normal
before your first share, as long as iCloud Drive is on.

```bash
cd ~/reel-inbox && ./install.sh
```

**4. Put the Shortcut on your iPhone.** Pick whichever is easier:

- **From the Mac, by AirDrop:** in Finder press **Cmd+Shift+G**, paste `~/reel-inbox/shortcut`, press Return, then right-click
  **Send to Claude.shortcut** → **Share** → **AirDrop** → your iPhone. On the phone, tap
  **Add Shortcut**.
- **On the phone, from GitHub:** open
  [this link](https://github.com/silasapostol13-web/reel-inbox/raw/master/shortcut/Send%20to%20Claude.shortcut)
  in Safari and tap **Download**. Tap the blue download arrow in the address bar (or open the Files
  app → **Downloads**), tap **Send to Claude**, then **Add Shortcut**.

The file is signed by Apple's "anyone can open" signing, so you don't need to change any Shortcuts
setting. It does one thing: asks for your note and saves a small file with the link and the note to
your own iCloud Drive. You can read every step before adding it, or build it yourself from
[`shortcut/build_shortcut.py`](shortcut/build_shortcut.py) (`python3 shortcut/build_shortcut.py`).

**5. Pin it in the share sheet.** Open any Reel in Instagram, tap the paper-plane **Share** button,
then the iOS share icon at the end of the row (labeled **Share to…** or **More**, depending on your
Instagram version). In the sheet that opens, scroll to the bottom, tap **Edit Actions…**, and add
**Send to Claude** to Favorites. TikTok's **Share** → **More** opens the same sheet.

**6. Try it.** Share a Reel, type or dictate a note, tap **Done**. If iOS asks whether Send to
Claude may save a file, tap **Always Allow**. Usually within a minute (it depends on iCloud sync), on
the Mac:

```bash
ls ~/ReelInbox
```

To check that Claude Code can see it, run `claude mcp list`: the `reel-inbox` line should end in
**✔ Connected**. Then open Claude Code anywhere and say *"get the reel I just sent"*.

**Test it without the phone:**

```bash
cd ~/reel-inbox
python3 worker/reel_worker.py --url "https://www.instagram.com/reel/Chunk8-jurw/" --note "test"
```

That link is a 5-second public Reel from Instagram's own account (a cat, no speech, so the transcript
is empty); any public Reel or TikTok link works. The installer's last line prints the same command
with full paths, and either one is fine.
It makes a new folder in `~/ReelInbox` within a few seconds.

> **No share button handy?** Copy the Reel's link and run **Send to Claude** on its own (home screen,
> Action Button, Back Tap). With nothing shared, it uses the link on your clipboard.

## Design decisions

**iCloud Drive is the queue.** No server, no account, no open port, nothing to host. The phone never
needs the Mac: shares wait in iCloud while it's off and get processed when it wakes. The cost is that
timing depends on iCloud sync, which is usually seconds.

**The note comes first.** The Shortcut asks for your note before it does anything else, and always
saves a file. An early version checked for the link first and, on a real share, quietly skipped the
note. Now an odd share still arrives, and the Mac explains what went wrong.

**Transcription is local.** whisper.cpp with `large-v3-turbo` (q5) runs on the GPU through Metal. The
post caption and creator name go in as a prompt, so names and product terms come out spelled right.
No API key, no per-minute cost.

**Frames are picked for what's readable, not just for scene cuts.** Candidates are ffmpeg scene changes
plus a steady sample every ~1.5 s, so slow screen recordings aren't missed. Blank and fade frames are
dropped. The timeline is split into windows, and in each one the frame with the most readable text
wins, so a terminal or a GitHub page beats a talking head. Frames that look alike, measured by
Vision's image feature prints, are merged and the wordier one is kept. The cap is 12.

**OCR is tuned for code.** Apple Vision text recognition runs with language correction off, because
correction "fixes" code into English. Lines that just repeat the speech (burned-in subtitles) and lines
already shown on an earlier frame are dropped from `reel.md`. Claude still gets every frame as an
image, so nothing is really lost.

**The MCP server has no dependencies.** It's about 300 lines of standard-library Python speaking
JSON-RPC over stdio, so there's nothing to pin or update. Frames go back as MCP image content, which
means Claude looks at them instead of guessing from the text. The unread count reaches new sessions
through the server's own instructions, with no hooks or settings changes.

**Nothing fails silently.** A failed reel gets a folder with a plain-English reason ("Instagram
won't show this post without logging in…"). It's retried after 5, 10 and 15 minutes, and if the
Mac is offline right after waking it waits instead of using up retries. After 4 tries it moves to
`failed/` with the error inside.

**Phone files are fetched from iCloud properly.** A file saved on the iPhone first shows up on the Mac
as a placeholder with no data in it, and a background job that just opens it gets stuck. A tiny Swift
helper (`vision/icloudread.swift`) asks iCloud to download it first. This was found the hard way, on
the first real share.

## Cost and privacy

**It's free.** No account, no API key, no subscription. Everything it installs is free and open source,
and transcription runs on your own Mac, so there's no per-minute charge. Claude Code itself runs on your
own Claude plan: asking about a reel uses it like any other message, a bit more than plain text because
Claude looks at up to 12 frame images.

**What stays on your Mac:**

- Video, audio, transcripts, frames and OCR all stay on your Mac. Nothing is sent to any server run by
  this project, because there isn't one.
- The only network traffic is `yt-dlp` fetching the video from Instagram/TikTok, iCloud syncing the
  small note file, and the one-time model download from Hugging Face.
- Your notes live in your own iCloud Drive (**iCloud Drive › Shortcuts › ReelInbox** in Finder; processed
  ones move to its `done/` folder) and in `~/ReelInbox/`.
- Claude Code sees a reel's contents only when you (or a session) call the tool. Because the server is
  registered for every project, each new session is told how many unread reels are waiting, and
  that's all.
- Reel folders are kept until you delete them. Each one holds the frames from someone else's video, so
  treat them as notes for yourself.

**What it puts on your Mac:** the Homebrew tools (`yt-dlp`, `ffmpeg`, `whisper.cpp`, and Python if you
didn't have it), the speech model in `~/Library/Application Support/ReelInbox/` (about 575 MB, plus the
worker log), a background job in `~/Library/LaunchAgents/`, two small helpers in the repo's `bin/`
folder, the MCP server entry in `~/.claude.json` (Claude Code's own settings file), and a skill in `~/.claude/skills/reel-inbox/`.

## Limits and honest caveats

- **Personal use only.** Downloading videos from Instagram or TikTok goes against their terms of
  service. This is a tool for taking notes on content you're already watching, not for re-posting
  anything. Respect creators' work.
- **Downloads can break.** Instagram and TikTok change things often, and `yt-dlp` keeps up, but there
  can be gaps. Keep it current with `brew upgrade yt-dlp`. Public Reels download without a login
  today. Private posts, and anything that needs a login, fail with a clear message. The worker never
  uses your browser cookies.
- **Photo posts and carousels** work too, through the same `yt-dlp` (no extra tool). Every photo slide
  becomes a frame with its text read off it, video slides inside a carousel are transcribed like a
  short video, and the post caption is kept. Up to 20 slides per post.
- **OCR is imperfect** on stylized captions, tiny terminal text and motion blur. That's why the
  frames themselves are always passed along.
- **Mac only**, because the worker uses Apple's Vision framework and launchd. The phone side needs
  iOS Shortcuts.

## Troubleshooting

| Symptom | Where to look |
|---|---|
| `./install.sh` stops at "Homebrew is needed" or "Xcode Command Line Tools" | Install the one it names (the message gives the exact command), then run `./install.sh` again |
| The shortcut won't import on the iPhone | Update iOS, then try the other way in step 4 (AirDrop if the download failed, or the reverse) |
| Nothing shows up | `ls ~/Library/Mobile\ Documents/iCloud~is~workflow~my~workflows/Documents/ReelInbox/`: is the file there? If not, check that iCloud Drive is on, on both the iPhone and the Mac, with the same Apple ID |
| macOS asks whether `python3` may access files in iCloud Drive | Click **Allow**: that's the background job reading what the phone sent |
| A reel failed | `~/ReelInbox/<id>/reel.md` has the reason; the phone's original file moves to `ReelInbox/failed/` in iCloud |
| Worker log | `~/Library/Application Support/ReelInbox/worker.log` |
| Run it by hand | `cd ~/reel-inbox && python3 worker/reel_worker.py --url "<a public Reel link>" --note "test"` |
| Claude doesn't see the tools | In `claude mcp list`, the `reel-inbox` line should end in `✔ Connected`; if not, run `./install.sh` again |

**Uninstall:** `cd ~/reel-inbox && ./uninstall.sh` stops the background job, removes the MCP server, and moves the model
and helpers to the Trash. Your reels, the iCloud queue and the skill are kept unless you add `--all`.
Add `--dry-run` to see what it would do first. It leaves the Homebrew tools (other apps may use them;
`brew uninstall yt-dlp ffmpeg whisper.cpp` if you're sure) and the `reel-inbox` folder itself, which you
can drag to the Trash afterwards. Delete the shortcut on the iPhone by long-pressing it in Shortcuts.

## Repo layout

| Path | What |
|---|---|
| `shortcut/build_shortcut.py` | Builds and signs `shortcut/Send to Claude.shortcut` from code |
| `worker/reel_worker.py` | The worker (standard-library Python). `--url` processes one link by hand |
| `vision/reelvision.swift` | On-device OCR and image similarity with Apple Vision |
| `vision/icloudread.swift` | Reads iCloud placeholders safely through `NSFileCoordinator` |
| `mcp/reel_mcp.py` | The MCP server (stdio, no dependencies) |
| `skill/reel-inbox/SKILL.md` | Teaches Claude what "the reel I sent" means |
| `install.sh` | Safe to re-run: tools, model, helpers, launchd job, MCP registration, skill |
| `uninstall.sh` | Undoes `install.sh`, moving files to the Trash (`--all` includes your reels) |

## Related projects

- **[reel-relay](https://github.com/siemd2/reel-relay)** does something similar as a self-hosted
  server: share by Telegram bot, iOS Shortcut or Instagram DM, transcribe with Groq's hosted Whisper,
  and reach it over a tunnel. Its `get_reel` tool shape was a useful reference. Reel Inbox makes the
  opposite trade-off: no server, no tunnel, no API key, everything on your own Mac.
- **[media-mcp](https://github.com/woosal1337/media-mcp)** is a general MCP server for frames and local
  Whisper transcripts from media files and URLs.
- Built on **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**, **[whisper.cpp](https://github.com/ggml-org/whisper.cpp)**,
  **[FFmpeg](https://ffmpeg.org)**, and Apple's Vision framework.

## License

[MIT](LICENSE)
