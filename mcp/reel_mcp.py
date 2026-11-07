#!/usr/bin/env python3
"""Reel Inbox MCP server (stdio, stdlib only).

Tools:
  list_reels  - newest first, with Silas's note and status
  get_reel    - one reel (newest by default): note, transcript, on-screen text, and the frames as images
  mark_done   - hide a reel from the default list once it has been used

Reads ~/ReelInbox/<id>/{meta.json, reel.md, frames/*.jpg} written by worker/reel_worker.py.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

OUT_ROOT = Path(os.environ.get("REEL_INBOX_OUT", Path.home() / "ReelInbox"))
INBOX = Path(os.environ.get(
    "REEL_INBOX_SRC",
    Path.home() / "Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/ReelInbox"))
SERVER = {"name": "reel-inbox", "version": "1.0.0"}

TOOLS = [
    {
        "name": "list_reels",
        "description": "List Instagram/TikTok reels Silas sent from his phone with 'Send to Claude', newest "
                       "first, with his note about why he sent each one. Done reels are hidden unless "
                       "include_done is true.",
        "inputSchema": {"type": "object", "properties": {
            "limit": {"type": "integer", "description": "How many to list (default 10)."},
            "include_done": {"type": "boolean", "description": "Also list reels marked done."}}},
    },
    {
        "name": "get_reel",
        "description": "Get a reel Silas sent from his phone: his note (why he sent it / which project), the "
                       "full transcript, on-screen text and code (OCR), and the key frames as images. With no "
                       "id it returns the newest one. Use this when Silas says 'the reel I sent', 'the reel I "
                       "just shared', 'check my reel inbox', etc.",
        "inputSchema": {"type": "object", "properties": {
            "id": {"type": "string", "description": "Reel id from list_reels, or any words from its note or "
                                                    "title. Omit for the newest reel."},
            "include_frames": {"type": "boolean", "description": "Return frame images (default true)."},
            "max_frames": {"type": "integer", "description": "Max frame images to return (default 12)."}}},
    },
    {
        "name": "mark_done",
        "description": "Mark a reel as handled so list_reels hides it by default. Nothing is deleted.",
        "inputSchema": {"type": "object", "properties": {
            "id": {"type": "string", "description": "Reel id from list_reels."}}, "required": ["id"]},
    },
]


# ------------------------------------------------------------------ data

def all_reels() -> list[dict]:
    reels = []
    if not OUT_ROOT.exists():
        return reels
    for d in OUT_ROOT.iterdir():
        mp = d / "meta.json"
        if d.is_dir() and mp.exists():
            try:
                m = json.loads(mp.read_text())
            except json.JSONDecodeError:
                continue
            m["_dir"] = d
            reels.append(m)
    reels.sort(key=lambda m: m.get("processed_at") or m["id"], reverse=True)
    return reels


def waiting_line() -> str:
    """Items still in the iCloud inbox: sent from the phone but not processed yet."""
    if not INBOX.exists():
        return ""
    waiting = [p for p in INBOX.iterdir() if p.is_file() and (p.suffix == ".json" or p.name.endswith(".icloud"))]
    if not waiting:
        return ""
    retrying = 0
    for p in waiting:
        try:
            if json.loads(p.read_text()).get("status") == "failed":
                retrying += 1
        except Exception:
            pass
    s = f"Note: {len(waiting)} reel(s) sent from the phone are still waiting to be processed on the Mac"
    if retrying:
        s += f" ({retrying} failed once and will be retried)"
    return s + ". If Silas means one he just sent, it may need another minute; check again shortly."


def find(query: str | None) -> dict | None:
    reels = all_reels()
    if not reels:
        return None
    if not query:
        return reels[0]
    q = query.strip().lower()
    for m in reels:
        if m["id"].lower() == q:
            return m
    for m in reels:
        if m["id"].lower().startswith(q):
            return m
    words = q.split()
    for m in reels:
        hay = " ".join(str(m.get(k) or "") for k in ("id", "note", "title", "caption", "uploader", "url")).lower()
        if all(w in hay for w in words):
            return m
    return None


def summary(m: dict) -> str:
    status = m.get("status")
    s = f"- {m['id']}"
    if m.get("done"):
        s += "  [done]"
    if status != "ok":
        s += f"  [{status.upper()}: {m.get('error') or ''}]"
    s += f"\n  note: {m.get('note') or '(no note)'}"
    s += f"\n  from: {m.get('uploader') or '?'} · {m.get('title') or m.get('url')}"
    s += f"\n  sent: {m.get('sent_at') or m.get('processed_at')} · {len(m.get('frames') or [])} frames"
    return s


# ------------------------------------------------------------------ tools

def list_reels(args: dict) -> list[dict]:
    limit = int(args.get("limit") or 10)
    reels = [m for m in all_reels() if args.get("include_done") or not m.get("done")]
    lines = [summary(m) for m in reels[:limit]]
    head = f"{len(reels)} reel(s)" + ("" if args.get("include_done") else " not marked done")
    text = head + ", newest first:\n" + ("\n".join(lines) if lines else "(none)")
    w = waiting_line()
    return [{"type": "text", "text": text + ("\n\n" + w if w else "")}]


def get_reel(args: dict) -> list[dict]:
    m = find(args.get("id"))
    w = waiting_line()
    if not m:
        msg = "No reel found" + (f" matching '{args.get('id')}'." if args.get("id") else " yet.")
        return [{"type": "text", "text": msg + ("\n\n" + w if w else "")}]
    d: Path = m["_dir"]
    md = (d / "reel.md").read_text() if (d / "reel.md").exists() else json.dumps(m, indent=2, default=str)
    header = f"Reel id: {m['id']}\nFolder: {d}\n"
    if w:
        header += w + "\n"
    out = [{"type": "text", "text": header + "\n" + md}]
    if args.get("include_frames", True) is not False:
        frames = m.get("frames") or []
        cap = int(args.get("max_frames") or 12)
        if len(frames) > cap:
            step = len(frames) / cap
            frames = [frames[int(i * step)] for i in range(cap)]
        for f in frames:
            p = d / f["file"]
            if not p.exists():
                continue
            t = f.get("t", 0)
            out.append({"type": "text", "text": f"Frame {f['file']} at {int(t // 60)}:{int(t % 60):02d}"})
            out.append({"type": "image", "mimeType": "image/jpeg",
                        "data": base64.b64encode(p.read_bytes()).decode()})
    return out


def mark_done(args: dict) -> list[dict]:
    m = find(args.get("id"))
    if not m:
        return [{"type": "text", "text": f"No reel matching '{args.get('id')}'."}]
    mp = m["_dir"] / "meta.json"
    data = json.loads(mp.read_text())
    data["done"] = True
    mp.write_text(json.dumps(data, indent=2))
    return [{"type": "text", "text": f"Marked done: {m['id']}"}]


HANDLERS = {"list_reels": list_reels, "get_reel": get_reel, "mark_done": mark_done}


# ------------------------------------------------------------------ JSON-RPC over stdio

def reply(msg_id, result=None, error=None) -> None:
    msg = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle(req: dict) -> None:
    method, msg_id = req.get("method"), req.get("id")
    if msg_id is None:  # notification (initialized, cancelled, ...)
        return
    params = req.get("params") or {}
    if method == "initialize":
        reply(msg_id, {"protocolVersion": params.get("protocolVersion", "2025-06-18"),
                       "capabilities": {"tools": {}}, "serverInfo": SERVER,
                       "instructions": "Reels Silas shared from his phone. 'The reel I sent' = get_reel "
                                       "with no id. Read his note first: it says why he sent it."})
    elif method == "ping":
        reply(msg_id, {})
    elif method == "tools/list":
        reply(msg_id, {"tools": TOOLS})
    elif method == "tools/call":
        name = params.get("name")
        fn = HANDLERS.get(name)
        if not fn:
            reply(msg_id, error={"code": -32602, "message": f"unknown tool {name}"})
            return
        try:
            reply(msg_id, {"content": fn(params.get("arguments") or {}), "isError": False})
        except Exception as e:  # noqa: BLE001
            reply(msg_id, {"content": [{"type": "text", "text": f"reel-inbox error: {e}"}], "isError": True})
    else:
        reply(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        handle(req)


if __name__ == "__main__":
    main()
