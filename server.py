"""
Combined server on port 5000:
  GET /*   → serves game/build/web/ static files
  GET /ws  → WebSocket — pairs two players and relays their state
"""
import asyncio
import os
from aiohttp import web

WEB_DIR = os.path.join(os.path.dirname(__file__), "game", "build", "web")
PORT    = 5000

# ── matchmaking ─────────────────────────────────────────
waiting_ws = None   # one WebSocket waiting for a partner

async def ws_handler(request):
    global waiting_ws
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    if waiting_ws is None or waiting_ws.closed:
        # First player — hold until a partner arrives
        waiting_ws = ws
        print("Player 1 connected, waiting for Player 2…")
        try:
            # Just keep the connection alive; relay task will handle traffic
            async for _ in ws:
                pass
        finally:
            if waiting_ws is ws:
                waiting_ws = None
        return ws

    # Second player — pair up and relay
    partner   = waiting_ws
    waiting_ws = None
    print("Player 2 connected — match started!")

    async def forward(src, dst):
        try:
            async for msg in src:
                if not dst.closed:
                    await dst.send_str(msg.data)
        except Exception:
            pass
        finally:
            await dst.close()

    await asyncio.gather(
        forward(ws,      partner),
        forward(partner, ws),
    )
    return ws

# ── static file handler ─────────────────────────────────
async def static_handler(request):
    path = request.match_info.get("path", "index.html") or "index.html"
    file_path = os.path.join(WEB_DIR, path)
    if os.path.isdir(file_path):
        file_path = os.path.join(file_path, "index.html")
    if not os.path.exists(file_path):
        raise web.HTTPNotFound()
    return web.FileResponse(file_path)

app = web.Application()
app.router.add_get("/ws",       ws_handler)
app.router.add_get("/",         static_handler)
app.router.add_get("/{path:.*}", static_handler)

if __name__ == "__main__":
    print(f"Serving Flappy Race at http://0.0.0.0:{PORT}")
    print(f"WebSocket endpoint: ws://... /ws  (use wss:// for deployed link)")
    web.run_app(app, host="0.0.0.0", port=PORT)
