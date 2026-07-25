"""
Flappy Race – combined server (port 5000)
  GET /*   → serves game/build/web/ static files
  GET /ws  → N-player WebSocket relay + waiting room
"""
import asyncio, json, os
from aiohttp import web

WEB_DIR = os.path.join(os.path.dirname(__file__), "game", "build", "web")
PORT    = 5000

# ── Global room ──────────────────────────────────────────
clients      = {}   # player_id -> WebSocketResponse
player_names = {}   # player_id -> str
player_skins = {}   # player_id -> int
game_state   = "waiting"   # "waiting" | "playing"
_next_id     = 0

async def broadcast(msg, exclude=None):
    text = json.dumps(msg)
    for pid, ws in list(clients.items()):
        if pid == exclude or ws.closed:
            continue
        try:
            await ws.send_str(text)
        except Exception:
            pass

async def ws_handler(request):
    global game_state, _next_id
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)

    pid = _next_id; _next_id += 1
    clients[pid]      = ws
    player_names[pid] = f"Player {pid + 1}"
    player_skins[pid] = 0

    print(f"[+] #{pid} connected  ({len(clients)} online)")

    # Welcome the new player with current room state
    await ws.send_str(json.dumps({
        "type":       "welcome",
        "id":         pid,
        "game_state": game_state,
        "players": {
            str(k): {"name": player_names[k], "skin": player_skins.get(k, 0)}
            for k in player_names
        },
    }))

    # Tell everyone else about the new arrival
    await broadcast({"type": "join", "id": pid,
                     "name": player_names[pid], "skin": 0}, exclude=pid)

    try:
        async for msg in ws:
            if msg.type != web.WSMsgType.TEXT:
                continue
            try:
                d = json.loads(msg.data)
                t = d.get("type")

                if t == "start":
                    if game_state == "waiting":
                        game_state = "playing"
                        await broadcast({"type": "start"})

                elif t == "state":
                    await broadcast({
                        "type":  "state",
                        "id":    pid,
                        "y":     d.get("y"),
                        "score": d.get("score", 0),
                        "alive": d.get("alive", True),
                        "skin":  player_skins.get(pid, 0),
                    }, exclude=pid)

                elif t == "name":
                    player_names[pid] = str(d.get("name", player_names[pid]))[:20]
                    player_skins[pid] = int(d.get("skin", 0))
                    await broadcast({"type":  "name", "id": pid,
                                     "name":  player_names[pid],
                                     "skin":  player_skins[pid]})

                elif t == "reset":
                    game_state = "waiting"
                    await broadcast({"type": "reset"})

            except Exception as e:
                print(f"  msg error: {e}")

    except Exception:
        pass
    finally:
        del clients[pid]
        player_names.pop(pid, None)
        player_skins.pop(pid, None)
        if not clients:
            game_state = "waiting"
        print(f"[-] #{pid} left  ({len(clients)} online)")
        await broadcast({"type": "leave", "id": pid})

    return ws

# ── Static file handler ──────────────────────────────────
async def static_handler(request):
    path = request.match_info.get("path", "") or "index.html"
    fp   = os.path.join(WEB_DIR, path)
    if os.path.isdir(fp):
        fp = os.path.join(fp, "index.html")
    if not os.path.exists(fp):
        raise web.HTTPNotFound()
    return web.FileResponse(fp)

app = web.Application()
app.router.add_get("/ws",         ws_handler)
app.router.add_get("/",           static_handler)
app.router.add_get("/{path:.*}",  static_handler)

if __name__ == "__main__":
    print(f"Flappy Race  →  http://0.0.0.0:{PORT}")
    print(f"WebSocket    →  ws://0.0.0.0:{PORT}/ws")
    web.run_app(app, host="0.0.0.0", port=PORT)
