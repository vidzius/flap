# main.py
# Flappy Bird Multiplayer Race
# pip install pygame numpy websockets

import asyncio
import pygame
import random
import json
import math
import os
import sys
import time

# ── detect if running in browser ──
WEB = sys.platform == "emscripten"

# ── window ──
W, H = 480, 640
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Flappy Race")
clock  = pygame.time.Clock()
FPS    = 60

# ── fonts ──
def font(size, bold=False):
    return pygame.font.SysFont("arial", size, bold=bold)
F_SM  = font(16)
F_MD  = font(22, bold=True)
F_LG  = font(34, bold=True)
F_XL  = font(52, bold=True)

# ── colours ──
C_SKY    = (110, 190, 255)
C_SKY2   = (180, 225, 255)
C_GROUND = (220, 185, 105)
C_GRDARK = (180, 145,  70)
C_PIPE   = ( 80, 200,  90)
C_PIPED  = ( 50, 155,  60)
C_PIPER  = (220, 255, 180)
C_BG     = ( 18,  24,  45)
C_PANEL  = ( 28,  36,  65)
C_ACCENT = (255, 210,  30)
C_WHITE  = (255, 255, 255)
C_BLACK  = (  0,   0,   0)
C_RED    = (255,  70,  70)
C_GREEN  = ( 70, 220, 100)
C_COIN   = (255, 200,  20)
C_DIM    = (150, 165, 195)
C_P1     = (255, 220,  40)   # player 1 yellow
C_P2     = (100, 180, 255)   # player 2 blue

GROUND_H = 80
PIPE_GAP = 175
PIPE_W   = 68
GRAVITY  = 0.44
FLAP_STR = -9.2

# ── save data (disabled on web) ──
DATA_FILE = "flappy_race_save.json"

def load_save():
    if WEB:
        return {"high_score": 0, "wins": 0, "games": 0}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"high_score": 0, "wins": 0, "games": 0}

def write_save(d):
    if WEB:
        return
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(d, f, indent=2)
    except Exception:
        pass

save = load_save()

RACE_PIPE_OPTIONS   = [10, 25, 50]
race_pipe_total    = 10
selected_race_pipes = 10
skin_options       = ["yellow", "blue", "pink"]
skin_colors        = {
    "yellow": C_P1,
    "blue": C_P2,
    "pink": (255, 120, 180),
}
selected_skin      = "yellow"
wait_skin_index    = 0
finish_times       = {}
race_results_open  = False

# ─────────────────────────────────────────────
#  DRAWING HELPERS
# ─────────────────────────────────────────────
def draw_text(surf, txt, x, y, f=F_MD, col=C_WHITE, shadow=True):
    if shadow:
        s = f.render(txt, True, C_BLACK)
        surf.blit(s, (x+2, y+2))
    surf.blit(f.render(txt, True, col), (x, y))

def draw_center(surf, txt, cx, cy, f=F_MD, col=C_WHITE, shadow=True):
    t = f.render(txt, True, col)
    x = cx - t.get_width()  // 2
    y = cy - t.get_height() // 2
    if shadow:
        s = f.render(txt, True, C_BLACK)
        surf.blit(s, (x+2, y+2))
    surf.blit(t, (x, y))

def draw_rect(surf, col, rect, radius=8, border=0, bcol=None):
    pygame.draw.rect(surf, col, rect, border_radius=radius)
    if border and bcol:
        pygame.draw.rect(surf, bcol, rect, border, border_radius=radius)

def draw_gradient(surf, rect, c1, c2, vertical=True):
    r = pygame.Rect(rect)
    for i in range(r.height if vertical else r.width):
        t  = i / max(r.height-1 if vertical else r.width-1, 1)
        cr = int(c1[0]+(c2[0]-c1[0])*t)
        cg = int(c1[1]+(c2[1]-c1[1])*t)
        cb = int(c1[2]+(c2[2]-c1[2])*t)
        if vertical:
            pygame.draw.line(surf,(cr,cg,cb),(r.x,r.y+i),(r.x+r.w,r.y+i))
        else:
            pygame.draw.line(surf,(cr,cg,cb),(r.x+i,r.y),(r.x+i,r.y+r.h))

# ─────────────────────────────────────────────
#  BUTTON
# ─────────────────────────────────────────────
class Btn:
    def __init__(self, rect, txt, col=C_PANEL, txt_col=C_WHITE):
        self.rect    = pygame.Rect(rect)
        self.txt     = txt
        self.col     = col
        self.txt_col = txt_col

    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        hov    = self.rect.collidepoint(mx, my)
        c      = tuple(min(255, v+30) for v in self.col) if hov else self.col
        draw_rect(surf, c, self.rect, radius=10,
                  border=2, bcol=C_ACCENT)
        draw_center(surf, self.txt,
                    self.rect.centerx, self.rect.centery,
                    F_MD, self.txt_col)

    def clicked(self, events):
        for ev in events:
            if (ev.type == pygame.MOUSEBUTTONDOWN
                    and ev.button == 1
                    and self.rect.collidepoint(ev.pos)):
                return True
        return False

# ─────────────────────────────────────────────
#  MINION BIRD DRAWING
# ─────────────────────────────────────────────
def draw_bird(surf, x, y, r, col, rot=0):
    cx, cy = int(x), int(y)
    # body
    pygame.draw.circle(surf, col,          (cx,cy), r)
    pygame.draw.circle(surf, C_BLACK,      (cx,cy), r, 2)
    # overalls
    ob = pygame.Rect(cx-r, cy+int(r*0.2), 2*r, int(r*0.9))
    pygame.draw.ellipse(surf, (30,85,175), ob)
    # goggle strap
    pygame.draw.rect(surf, (20,20,20),
                     (cx-r-1, cy-int(r*0.26), 2*r+2, max(3,r//5)))
    # goggles
    gr = int(r*0.42)
    for ex, ey in ((cx-int(r*0.32), cy-int(r*0.12)),
                   (cx+int(r*0.32), cy-int(r*0.12))):
        pygame.draw.circle(surf, (110,110,110), (ex,ey), gr+3)
        pygame.draw.circle(surf, (185,185,185), (ex,ey), gr)
        pygame.draw.circle(surf, C_WHITE,       (ex,ey), int(gr*0.60))
        pygame.draw.circle(surf, (75,42,12),    (ex,ey), int(gr*0.28))
        pygame.draw.circle(surf, C_BLACK,       (ex,ey), int(gr*0.13))
        pygame.draw.circle(surf, C_WHITE,
                           (ex-int(gr*0.13), ey-int(gr*0.13)),
                           max(1,int(gr*0.08)))
    # smile
    pygame.draw.arc(surf, (110,45,15),
                    (cx-int(r*0.38), cy+int(r*0.16),
                     int(r*0.76), int(r*0.46)),
                    math.radians(15), math.radians(165), 2)
    # arms
    pygame.draw.line(surf, col,
                     (cx-r+3, cy+int(r*0.05)),
                     (cx-r-14, cy+int(r*0.05)), 5)
    pygame.draw.line(surf, col,
                     (cx+r-3, cy+int(r*0.05)),
                     (cx+r+14, cy+int(r*0.05)), 5)

# ─────────────────────────────────────────────
#  PIPE
# ─────────────────────────────────────────────
class Pipe:
    def __init__(self, x, seed):
        self.x      = float(x)
        random.seed(seed)
        self.gap_y  = random.randint(160, H-GROUND_H-160)
        self.passed = False

    def update(self, spd):
        self.x -= spd

    def top_rect(self):
        return pygame.Rect(int(self.x), 0,
                           PIPE_W, self.gap_y - PIPE_GAP//2)

    def bot_rect(self):
        by = self.gap_y + PIPE_GAP//2
        return pygame.Rect(int(self.x), by,
                           PIPE_W, H-GROUND_H-by)

    def draw(self, surf):
        for rect in (self.top_rect(), self.bot_rect()):
            if rect.height <= 0:
                continue
            draw_gradient(surf, rect, C_PIPE, C_PIPED)
            rim_h = 16
            if rect.y == 0:
                rim = pygame.Rect(rect.x-4, rect.bottom-rim_h,
                                  rect.w+8, rim_h)
            else:
                rim = pygame.Rect(rect.x-4, rect.y,
                                  rect.w+8, rim_h)
            draw_rect(surf, C_PIPER, rim, radius=4)
            pygame.draw.rect(surf, C_PIPED, rim, 2, border_radius=4)

    def collides(self, bx, by, br):
        r = pygame.Rect(int(bx)-br+3, int(by)-br+3,
                        (br-3)*2, (br-3)*2)
        return r.colliderect(self.top_rect()) or \
               r.colliderect(self.bot_rect())

# ─────────────────────────────────────────────
#  PARTICLE
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, col):
        a       = random.uniform(0, math.tau)
        s       = random.uniform(1, 4)
        self.x  = float(x)
        self.y  = float(y)
        self.vx = math.cos(a)*s
        self.vy = math.sin(a)*s
        self.col= col
        self.life = random.randint(20, 40)
        self.max  = self.life
        self.r    = random.randint(3, 6)

    def update(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 0.18
        self.life -= 1

    def draw(self, surf):
        t = self.life / self.max
        r = max(1, int(self.r * t))
        s = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.col, int(255*t)), (r,r), r)
        surf.blit(s, (int(self.x)-r, int(self.y)-r))

# ─────────────────────────────────────────────
#  CLOUD
# ─────────────────────────────────────────────
clouds = [{"x": random.randint(0,W),
           "y": random.randint(30, H//2-60),
           "w": random.randint(70,160),
           "h": random.randint(28,55),
           "s": random.uniform(0.25,0.6)}
          for _ in range(6)]

def update_clouds():
    for c in clouds:
        c["x"] -= c["s"]
        if c["x"] + c["w"] < 0:
            c["x"] = W + 10
            c["y"] = random.randint(30, H//2-60)

def draw_clouds(surf):
    for c in clouds:
        cx,cy,cw,ch = int(c["x"]),int(c["y"]),c["w"],c["h"]
        pygame.draw.ellipse(surf, C_WHITE, (cx,cy,cw,ch))
        pygame.draw.ellipse(surf, C_WHITE,
                            (cx+cw//4, cy-ch//3, cw//2, ch))

# ─────────────────────────────────────────────
#  GAME SCENE  (shared logic for both players)
# ─────────────────────────────────────────────
class Scene:
    def __init__(self, seed=42):
        self.seed      = seed
        self.pipes     = []
        self.frame     = 0
        self.pipe_seed = seed
        self.speed     = 3.0
        self.particles = []
        self.ground_x  = 0.0

    def spawn_pipe(self):
        self.pipe_seed += 1
        self.pipes.append(Pipe(W+10, self.pipe_seed))

    def update(self):
        self.frame += 1
        if self.frame % 95 == 0:
            self.spawn_pipe()
        for p in self.pipes:
            p.update(self.speed)
        self.pipes = [p for p in self.pipes
                      if p.x + PIPE_W > -20]
        self.ground_x = (self.ground_x - self.speed) % 48
        for pt in self.particles:
            pt.update()
        self.particles = [pt for pt in self.particles
                          if pt.life > 0]

    def emit(self, x, y, col, n=8):
        for _ in range(n):
            self.particles.append(Particle(x, y, col))

    def draw_bg(self, surf):
        draw_gradient(surf, (0,0,W,H-GROUND_H), C_SKY, C_SKY2)
        draw_clouds(surf)
        for p in self.pipes:
            p.draw(surf)
        # ground
        pygame.draw.rect(surf, C_GROUND,
                         (0, H-GROUND_H, W, GROUND_H))
        pygame.draw.rect(surf, C_GRDARK,
                         (0, H-GROUND_H, W, 8))
        # ground stripes
        gx = int(self.ground_x)
        while gx < W:
            pygame.draw.line(surf, C_GRDARK,
                             (gx, H-GROUND_H+10),
                             (gx+22, H-GROUND_H+10), 2)
            gx += 48
        for pt in self.particles:
            pt.draw(surf)

# ─────────────────────────────────────────────
#  PLAYER STATE
# ─────────────────────────────────────────────
class Player:
    def __init__(self, col, name="You"):
        self.base_col = col
        self.name     = name
        self.skin     = "yellow"
        self.set_skin(self.skin)
        self.reset()

    def reset(self):
        self.x           = 90
        self.y           = float(H//2)
        self.vel         = 0.0
        self.score       = 0
        self.alive       = True
        self.finished    = False
        self.finish_time = None
        self.hit_timer   = 0
        self.radius      = 22

    def set_skin(self, skin):
        self.skin = skin
        self.col  = skin_colors.get(skin, self.base_col)

    def flap(self):
        if self.alive and not self.finished:
            self.vel = FLAP_STR

    def finish(self, scene):
        self.finished = True
        self.finish_time = round(time.time() - scene.start_time, 2)
        finish_times[self.name] = self.finish_time
        add_popup(f"{self.name} finished {self.finish_time:.2f}s!", C_COIN)
        if self is p1:
            global race_results_open
            race_results_open = True

    def update(self, scene, multiplayer=False):
        if not self.alive or self.finished:
            return
        if self.hit_timer > 0:
            self.hit_timer -= 1

        self.vel += GRAVITY
        self.y   += self.vel

        for p in scene.pipes:
            if not p.passed and p.x + PIPE_W < self.x:
                p.passed = True
                self.score += 1
                scene.emit(self.x, self.y, C_ACCENT, n=10)
                if self.score >= race_pipe_total:
                    self.finish(scene)

        if self.y - self.radius <= 0 or self.y + self.radius >= H - GROUND_H:
            if multiplayer:
                if self.hit_timer <= 0:
                    self.hit_timer = 60
                    self.x = max(50, self.x - int(self.radius * 1.5))
                    scene.emit(self.x, self.y, self.col, n=14)
                    add_popup(f"{self.name} hit a pipe!", C_RED)
            else:
                self.alive = False
                scene.emit(self.x, self.y, self.col, n=14)

        if multiplayer:
            for p in scene.pipes:
                if p.collides(self.x, self.y, self.radius):
                    if self.hit_timer <= 0:
                        self.hit_timer = 60
                        self.x = max(50, self.x - int(self.radius * 1.5))
                        scene.emit(self.x, self.y, self.col, n=14)
                        add_popup(f"{self.name} hit a pipe!", C_RED)
                    break
        else:
            for p in scene.pipes:
                if p.collides(self.x, self.y, self.radius):
                    self.alive = False
                    scene.emit(self.x, self.y, self.col, n=14)
                    break

    def draw(self, surf, ghost=False):
        if ghost:
            s = pygame.Surface((self.radius*2+30,
                                 self.radius*2+30),
                                pygame.SRCALPHA)
            draw_bird(s, self.radius+15, self.radius+15,
                      self.radius, (*self.col, 140))
            surf.blit(s, (int(self.x)-self.radius-15,
                          int(self.y)-self.radius-15))
        else:
            draw_bird(surf, self.x, self.y, self.radius, self.col)
        label = self.skin.upper()
        t = F_SM.render(label, True, C_WHITE)
        surf.blit(t, (int(self.x) - t.get_width() // 2,
                      int(self.y) - self.radius - 20))

# ─────────────────────────────────────────────
#  WEBSOCKET MULTIPLAYER CLIENT
# ─────────────────────────────────────────────
# Set this to your server URL after deploying
# Leave as empty string for single player only
SERVER_URL = ""   # e.g. "wss://your-app.railway.app"

ws_conn           = None
other_y           = None
other_score       = 0
other_alive       = True
other_skin        = "blue"
other_finished    = False
other_finish_time = None
ws_connected      = False

async def ws_connect():
    global ws_conn, ws_connected
    if not SERVER_URL:
        return
    try:
        import websockets
        ws_conn      = await websockets.connect(SERVER_URL)
        ws_connected = True
    except Exception as e:
        print("WS connect failed:", e)
        ws_connected = False

async def ws_send(y, score, alive):
    global ws_conn, ws_connected
    if not ws_conn or not ws_connected:
        return
    try:
        import websockets
        msg = json.dumps({"y": round(y,1),
                          "score": score,
                          "alive": alive})
        await ws_conn.send(msg)
    except Exception:
        ws_connected = False

async def ws_recv():
    global ws_conn, ws_connected, other_y, other_score, other_alive
    if not ws_conn or not ws_connected:
        return
    try:
        import websockets
        msg = await asyncio.wait_for(ws_conn.recv(), timeout=0.01)
        d   = json.loads(msg)
        other_y     = d.get("y",     other_y)
        other_score = d.get("score", other_score)
        other_alive = d.get("alive", other_alive)
    except Exception:
        pass

# ─────────────────────────────────────────────
#  SCREENS
# ─────────────────────────────────────────────
# screen names: menu | solo | multi | dead
current = "menu"
scene   = Scene()
p1      = Player(C_P1, "You")
p2      = Player(C_P2, "Rival")   # used in multi mode

# menu buttons
btn_solo  = Btn((W//2-130, 260, 260, 54), "SOLO PLAY",  C_GREEN, C_BLACK)
btn_multi = Btn((W//2-130, 330, 260, 54), "MULTIPLAYER",C_PANEL)
btn_scores= Btn((W//2-130, 400, 260, 54), "SCORES",     C_PANEL)
btn_quit  = Btn((W//2-130, 470, 260, 54), "QUIT",       C_RED,   C_WHITE)

btn_menu      = Btn((W//2-100, H//2+110, 200, 50), "MENU",      C_PANEL)
btn_again     = Btn((W//2-100, H//2+ 50, 200, 50), "PLAY AGAIN",C_GREEN, C_BLACK)
btn_start_race= Btn((W//2-100, H-170, 200, 50), "START RACE", C_GREEN, C_BLACK)
btn_back_wait = Btn((W//2-100, H-100, 200, 50), "BACK", C_PANEL)
btn_continue  = Btn((W//2-100, H-90, 200, 50), "CONTINUE", C_GREEN, C_BLACK)

# input box for name / server url
input_text  = ""
input_active= False
input_rect  = pygame.Rect(W//2-160, 540, 320, 38)

# score popup list
popups = []

def add_popup(txt, col=C_WHITE):
    popups.append({"txt": txt, "y": float(H//2-60),
                   "col": col, "life": 55})

def draw_popups(surf):
    dead = []
    for p in popups:
        p["y"]   -= 1.2
        p["life"] -= 1
        if p["life"] <= 0:
            dead.append(p); continue
        alpha = int(255 * p["life"] / 55)
        t = F_MD.render(p["txt"], True, p["col"])
        s = pygame.Surface(t.get_size(), pygame.SRCALPHA)
        s.fill((0,0,0,0))
        s.blit(t, (0,0))
        s.set_alpha(alpha)
        surf.blit(s, (W//2 - t.get_width()//2, int(p["y"])))
    for p in dead:
        popups.remove(p)

# ─────────────────────────────────────────────
#  DRAW MENU
# ─────────────────────────────────────────────
_mt = 0.0
def draw_menu(surf, events):
    global current, input_text, input_active, _mt, SERVER_URL
    _mt += 0.02
    # background
    draw_gradient(surf, (0,0,W,H), (15,22,48), (40,70,130))
    # stars
    random.seed(7)
    for i in range(35):
        sx = random.randint(0,W)
        sy = random.randint(0,H//2)
        br = int(160 + 90*math.sin(_mt*2+i))
        pygame.draw.circle(surf,(br,br,br),(sx,sy),1)
    random.seed()
    # animated birds
    bx1 = (W//2 - 60 + int(math.sin(_mt*1.2)*8))
    by1 = (130  + int(math.sin(_mt*1.8)*6))
    bx2 = (W//2 + 60 + int(math.sin(_mt*1.5)*8))
    by2 = (138  + int(math.sin(_mt*2.1)*6))
    draw_bird(surf, bx1, by1, 22, C_P1)
    draw_bird(surf, bx2, by2, 22, C_P2)
    # title
    draw_rect(surf, (15,22,55,220), (W//2-190,50,380,80), radius=14)
    draw_center(surf,"FLAPPY RACE",W//2, 90, F_XL, C_ACCENT)
    draw_center(surf,"Solo or 2-Player Online Race",
                W//2,148,F_SM,C_DIM,shadow=False)
    # stats
    draw_rect(surf,(20,28,60,200),(W//2-160,178,320,52),radius=10)
    draw_center(surf,
                f"Best: {save['high_score']}   "
                f"Wins: {save['wins']}   "
                f"Games: {save['games']}",
                W//2,204,F_SM,C_COIN,shadow=False)
    # buttons
    for b in (btn_solo, btn_multi, btn_scores, btn_quit):
        b.draw(surf)
    # server url input
    draw_rect(surf,(15,22,55,200),(W//2-190,510,380,26),radius=6)
    draw_text(surf,"Server URL (for multiplayer):",
              W//2-185,512,F_SM,C_DIM,shadow=False)
    bc = C_ACCENT if input_active else (50,60,90)
    draw_rect(surf,(30,40,75),input_rect,radius=6,border=2,bcol=bc)
    draw_text(surf, (input_text or SERVER_URL)+"_" if input_active
              else (input_text or SERVER_URL or "leave blank for solo"),
              input_rect.x+8, input_rect.y+8, F_SM, C_WHITE, shadow=False)
    # handle events
    for ev in events:
        if ev.type == pygame.MOUSEBUTTONDOWN:
            input_active = input_rect.collidepoint(ev.pos)
        if ev.type == pygame.KEYDOWN and input_active:
            if ev.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            elif ev.key == pygame.K_RETURN:
                SERVER_URL   = input_text
                input_active = False
            elif ev.unicode.isprintable():
                input_text += ev.unicode
    if btn_solo.clicked(events):
        start_solo()
    if btn_multi.clicked(events):
        current = "wait_multi"
    if btn_quit.clicked(events):
        write_save(save)
        pygame.quit()
        sys.exit()

# ─────────────────────────────────────────────
#  DRAW SCORES
def draw_wait_multi(surf, events):
    global current, selected_race_pipes, selected_skin, wait_skin_index

    draw_rect(surf,(15,22,55,220),(W//2-190,30,380,70),radius=14)
    draw_center(surf,"MULTIPLAYER LOBBY",W//2,65,F_XL,C_ACCENT)
    draw_text(surf,"Pick number of pipes for the race:",W//2-170,120,F_SM,C_WHITE,shadow=False)
    for i, count in enumerate(RACE_PIPE_OPTIONS):
        rect = pygame.Rect(W//2-150 + i*110, 150, 90, 50)
        col = C_GREEN if count == selected_race_pipes else C_PANEL
        draw_rect(surf,col,rect,radius=10,border=2,bcol=C_ACCENT)
        draw_center(surf,str(count),rect.centerx,rect.centery,F_LG,C_BLACK)
        if events and any(ev.type == pygame.MOUSEBUTTONDOWN and rect.collidepoint(ev.pos) for ev in events):
            selected_race_pipes = count
    draw_text(surf,"Choose your skin:",W//2-170,230,F_SM,C_WHITE,shadow=False)
    for i, skin in enumerate(skin_options):
        rect = pygame.Rect(W//2-150 + i*110, 260, 90, 50)
        col = skin_colors.get(skin, C_PANEL)
        border_col = C_ACCENT if skin == selected_skin else C_WHITE
        draw_rect(surf,col,rect,radius=10,border=3,bcol=border_col)
        draw_center(surf,skin.upper(),rect.centerx,rect.centery,F_SM,C_BLACK)
        if events and any(ev.type == pygame.MOUSEBUTTONDOWN and rect.collidepoint(ev.pos) for ev in events):
            selected_skin = skin
    draw_text(surf,"Players can see each other's skins during the race.",W//2,340,F_SM,C_DIM,shadow=False)
    btn_start_race.draw(surf)
    btn_back_wait.draw(surf)
    if btn_start_race.clicked(events):
        start_multi()
    if btn_back_wait.clicked(events):
        current = "menu"

# ─────────────────────────────────────────────
#  DRAW SCORES

def draw_scores(surf, events):
    global current
    draw_gradient(surf,(0,0,W,H),(15,22,48),(40,70,130))
    draw_rect(surf,(15,22,55,220),(W//2-190,40,380,70),radius=14)
    draw_center(surf,"SCORES",W//2,75,F_XL,C_ACCENT)
    rows = [
        ("Best Score", str(save["high_score"])),
        ("Total Wins",  str(save["wins"])),
        ("Games Played",str(save["games"])),
    ]
    for i,(label,val) in enumerate(rows):
        y = 150+i*80
        draw_rect(surf,(22,30,62,220),(W//2-170,y,340,60),radius=10)
        draw_text(surf,label,W//2-155,y+18,F_SM,C_DIM,shadow=False)
        draw_center(surf,val,W//2+80,y+30,F_LG,C_ACCENT)
    btn_back.draw(surf)
    if btn_back.clicked(events):
        current = "menu"

# ─────────────────────────────────────────────
#  START FUNCTIONS
# ─────────────────────────────────────────────
def start_solo():
    global current, scene, p1
    scene = Scene(seed=random.randint(1,99999))
    p1    = Player(C_P1, "You")
    scene.spawn_pipe()
    current = "solo"

def start_multi():
    global current, scene, p1, p2
    scene = Scene(seed=42)
    p1    = Player(C_P1, "You")
    p2    = Player(C_P2, "Rival")
    scene.spawn_pipe()
    current = "multi"

# ─────────────────────────────────────────────
#  DRAW GAME (solo)
# ─────────────────────────────────────────────
def draw_solo(surf, events):
    global current
    global current, other_y, other_score, other_alive, other_skin, other_finished, other_finish_time, race_results_open
    scene.update()
    p1.update(scene)
    p1.update(scene, multiplayer=True)
    if ws_connected and other_y is not None:
        p2.y           = other_y
        p2.score       = other_score
        p2.alive       = other_alive
        p2.set_skin(other_skin)
        p2.finished    = other_finished
        p2.finish_time = other_finish_time
        if other_finished:
            finish_times[p2.name] = other_finish_time
    else:
        # simple AI: flap when below gap centre
        for pipe in scene.pipes:
            if pipe.x < p2.x + 120:
                if p2.y > pipe.gap_y + 20:
                    p2.flap()
                break
        p2.update(scene, multiplayer=True)
    scene.draw_bg(surf)
    # draw rival as ghost
    if p2.alive:
        p2.draw(surf, ghost=not ws_connected)
    p1.draw(surf)
    draw_popups(surf)
    # HUD
    draw_rect(surf,(0,0,0,140),(0,0,W,52),radius=0)
    draw_center(surf,str(p1.score),W//2-60,25,F_LG,C_P1)
    draw_center(surf,"vs",W//2,25,F_MD,C_WHITE)
    draw_center(surf,str(p2.score),W//2+60,25,F_LG,C_P2)
    # connection status
    status = "ONLINE" if ws_connected else "VS AI"
    scol   = C_GREEN if ws_connected else C_COIN
    draw_text(surf,status,W-75,10,F_SM,scol,shadow=False)
    # speed ramp
    scene.speed = min(5.5, 3.0 + max(p1.score,p2.score)*0.08)
    # handle events
    for ev in events:
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                p1.flap()
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button==1:
            p1.flap()
    if not p1.alive:
        won = p1.score >= p2.score
        if won:
            save["wins"] = save.get("wins",0)+1
        if p1.score > save["high_score"]:
            save["high_score"] = p1.score
        save["games"] = save.get("games",0)+1
        write_save(save)
        current = "dead_multi"
        if multi: start_multi()
# ─────────────────────────────────────────────
#  DEAD SCREENS
# ─────────────────────────────────────────────
def draw_dead(surf, events, multi=False):
    global current
    scene.draw_bg(surf)
    # dim overlay
    ov = pygame.Surface((W,H), pygame.SRCALPHA)
    ov.fill((0,0,0,155))
    surf.blit(ov,(0,0))
    # panel
    draw_rect(surf,C_PANEL,(W//2-175,H//2-170,350,280),
              radius=14,border=2,bcol=C_ACCENT)
    draw_center(surf,"GAME OVER",W//2,H//2-130,F_XL,C_RED)
    draw_center(surf,f"Score: {p1.score}",W//2,H//2-75,F_LG,C_WHITE)
    draw_center(surf,f"Best:  {save['high_score']}",
                W//2,H//2-35,F_MD,C_ACCENT)
    if multi:
        result = "YOU WIN!" if p1.score>=p2.score else "RIVAL WINS"
        rcol   = C_GREEN if p1.score>=p2.score else C_RED
        draw_center(surf,result,W//2,H//2+5,F_MD,rcol)
    btn_again.draw(surf)
    btn_menu.draw(surf)
    for ev in events:
        if ev.type == pygame.KEYDOWN and ev.key==pygame.K_SPACE:
            if multi: start_multi()
            else:     start_solo()
    if btn_again.clicked(events):
        if multi: start_multi()
        else:     start_solo()
    if btn_menu.clicked(events):
        current = "menu"

# ─────────────────────────────────────────────
#  MAIN ASYNC LOOP  (required for pygbag/web)
# ─────────────────────────────────────────────
async def main():
    global current, ws_connected

    # try to connect websocket if URL set
    # panel
    if SERVER_URL:

    draw_center(surf,"GAME OVER",W//2,H//2-130,F_XL,C_RED)
        await ws_connect()
        # check scores button from menuasyncio.run(main())
                W//2,H//2-35,F_MD,C_ACCENT)

        for ev in events:
        rcol   = C_GREEN if p1.score>=p2.score else C_RED
    while True:
            if (ev.type == pygame.MOUSEBUTTONDOWN        await asyncio.sleep(0)   # required every frame for web
    btn_menu.draw(surf)
        events = pygame.event.get()
                    and current == "menu"        clock.tick(FPS)
            if multi: start_multi()
        for ev in events:
                    and btn_scores.rect.collidepoint(ev.pos)):        pygame.display.flip()
        if multi: start_multi()
            if ev.type == pygame.QUIT:
    if btn_menu.clicked(events):
        current = "menu"
                write_save(save)
                current = "scores"
#  MAIN ASYNC LOOP  (required for pygbag/web)
                pygame.quit()
        pygame.display.flip()                    and btn_scores.rect.collidepoint(ev.pos)):
    global current, ws_connected
                sys.exit()
        clock.tick(FPS)                    and current == "menu"
                pygame.quit()

        await asyncio.sleep(0)   # required every frame for web            if (ev.type == pygame.MOUSEBUTTONDOWN
                sys.exit()
        screen.fill(C_BG)
        for ev in events:


asyncio.run(main())        # check scores button from menu
        screen.fill(C_BG)
        if   current == "menu":
            if (ev.type == pygame.MOUSEBUTTONDOWN        await asyncio.sleep(0)   # required every frame for web

            draw_menu(screen, events)            draw_scores(screen, events)

        elif current == "solo":        elif current == "scores":

            draw_solo(screen, events)            draw_dead(screen, events, multi=True)

        elif current == "multi":        elif current == "dead_multi":

            draw_multi(screen, events)            draw_dead(screen, events, multi=False)
            draw_solo(screen, events)            draw_dead(screen, events, multi=True)
            # send/receive websocket data        elif current == "dead_solo":


            draw_multi(screen, events)            draw_dead(screen, events, multi=False)
            draw_multi(screen, events)            draw_dead(screen, events, multi=False)
                await ws_send(p1.y, p1.score, p1.alive)

            if ws_connected:                await ws_recv()
                pygame.quit()

            if ws_connected:                await ws_recv()            if ws_connected:                await ws_recv()

            if ws_connected:                await ws_recv()
        pygame.display.flip()                    and btn_scores.rect.collidepoint(ev.pos)):
            # send/receive websocket data        elif current == "dead_solo":
                await ws_send(p1.y, p1.score, p1.alive)


            # send/receive websocket data        elif current == "dead_solo":
            # send/receive websocket data        elif current == "dead_solo":
                sys.exit()
            if ws_connected:                await ws_recv()

        clock.tick(FPS)                    and current == "menu"
                await ws_send(p1.y, p1.score, p1.alive)            draw_multi(screen, events)            draw_dead(screen, events, multi=False)

            if ws_connected:                await ws_recv()

        elif current == "multi":        elif current == "dead_multi":

        await asyncio.sleep(0)   # required every frame for web            if (ev.type == pygame.MOUSEBUTTONDOWN

            draw_solo(screen, events)            draw_dead(screen, events, multi=True)

        screen.fill(C_BG)
        await asyncio.sleep(0)   # required every frame for web            if (ev.type == pygame.MOUSEBUTTONDOWN
        for ev in events:        elif current == "solo":        elif current == "scores":



            draw_menu(screen, events)            draw_scores(screen, events)
        for ev in events:        elif current == "solo":        elif current == "scores":
asyncio.run(main())        # check scores button from menu


        if   current == "menu":




        if   current == "menu":
            draw_menu(screen, events)            draw_scores(screen, events)

asyncio.run(main())        # check scores button from menu