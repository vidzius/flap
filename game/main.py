# main.py  –  Flappy Race  (N-player + Store + Coins)
import asyncio, pygame, random, json, math, os, sys

WEB = sys.platform == "emscripten"

W, H = 480, 640
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Flappy Race")
clock  = pygame.time.Clock()
FPS    = 60

def font(sz, bold=False): return pygame.font.SysFont("arial", sz, bold=bold)
F_SM = font(15); F_MD = font(22, True); F_LG = font(34, True); F_XL = font(50, True)

C_SKY=(110,190,255); C_SKY2=(180,225,255); C_GROUND=(220,185,105); C_GRDARK=(180,145,70)
C_PIPE=(80,200,90); C_PIPED=(50,155,60); C_PIPER=(220,255,180)
C_BG=(18,24,45); C_PANEL=(28,36,65); C_ACCENT=(255,210,30)
C_WHITE=(255,255,255); C_BLACK=(0,0,0); C_RED=(255,70,70); C_GREEN=(70,220,100)
C_COIN=(255,200,20); C_DIM=(150,165,195)

GROUND_H=80; PIPE_GAP=175; PIPE_W=68; GRAVITY=0.44; FLAP_STR=-9.2

# Hardcoded server – players never type a URL
SERVER_WS = "wss://flap--vaivada02.replit.app/ws"

# ── SKINS ────────────────────────────────────────────────
# eyes: 0=special-only  1=single cyclops  2=double round
SKINS = [
    {"name":"Yellow Minion",   "price":0,   "body":(255,220,40),  "suit":(30,85,175),  "eyes":1,"sp":None},
    {"name":"Blue Minion",     "price":5,   "body":(100,180,255), "suit":(30,85,175),  "eyes":1,"sp":None},
    {"name":"Purple Minion",   "price":5,   "body":(180,80,220),  "suit":(60,20,100),  "eyes":1,"sp":None},
    {"name":"Evil Minion",     "price":10,  "body":(110,40,200),  "suit":(70,15,130),  "eyes":1,"sp":"evil"},
    {"name":"Robot Minion",    "price":10,  "body":(160,165,175), "suit":(110,115,125),"eyes":1,"sp":"robot"},
    {"name":"Tralalero",       "price":15,  "body":(255,90,200),  "suit":(190,30,140), "eyes":2,"sp":"tralala"},
    {"name":"Bombardino",      "price":15,  "body":(55,140,55),   "suit":(35,90,30),   "eyes":2,"sp":"bomba"},
    {"name":"Tung Tung",       "price":20,  "body":(205,115,40),  "suit":(140,65,20),  "eyes":2,"sp":"tung"},
    {"name":"Cappuccino",      "price":20,  "body":(185,120,70),  "suit":(120,65,25),  "eyes":1,"sp":"capp"},
    {"name":"Brr Brr Patapim", "price":25,  "body":(45,215,200),  "suit":(20,155,145), "eyes":2,"sp":"brr"},
    {"name":"SpongeBob",       "price":20,  "body":(255,240,50),  "suit":(195,145,50), "eyes":2,"sp":"sponge"},
    {"name":"Patrick Star",    "price":25,  "body":(255,145,200), "suit":(225,75,130), "eyes":2,"sp":"patrick"},
    {"name":"Squidward",       "price":30,  "body":(125,185,200), "suit":(80,130,155), "eyes":2,"sp":"squid"},
    {"name":"Gary Snail",      "price":30,  "body":(220,150,190), "suit":(165,100,145),"eyes":2,"sp":"gary"},
    {"name":"Sandy Cheeks",    "price":35,  "body":(210,175,100), "suit":(175,135,70), "eyes":2,"sp":"sandy"},
    {"name":"Pikachu",         "price":30,  "body":(255,228,20),  "suit":(200,80,10),  "eyes":2,"sp":"pika"},
    {"name":"Among Us",        "price":40,  "body":(215,45,45),   "suit":(170,25,25),  "eyes":0,"sp":"among"},
    {"name":"Doge",            "price":50,  "body":(210,178,130), "suit":(175,140,95), "eyes":2,"sp":"doge"},
    {"name":"Shrek",           "price":75,  "body":(95,185,60),   "suit":(65,135,30),  "eyes":2,"sp":"shrek"},
    {"name":"Golden Minion",   "price":100, "body":(255,200,0),   "suit":(200,150,0),  "eyes":1,"sp":"gold"},
]

# ── SAVE DATA ────────────────────────────────────────────
DATA_FILE = "flappy_race_save.json"

def load_save():
    blank = {"high_score":0,"wins":0,"games":0,"coins":0,"owned":[0],"skin":0}
    if WEB:
        try:
            import platform as _p
            raw = _p.window.localStorage.getItem("flap_save")
            if raw and str(raw) not in ("null","undefined",""):
                d = json.loads(str(raw))
                for k,v in blank.items():
                    d.setdefault(k, v)
                return d
        except Exception:
            pass
        return blank
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                d = json.load(f)
            for k,v in blank.items():
                d.setdefault(k, v)
            return d
        except Exception:
            pass
    return blank

def write_save(d):
    if WEB:
        try:
            import platform as _p
            _p.window.localStorage.setItem("flap_save", json.dumps(d))
        except Exception:
            pass
        return
    try:
        with open(DATA_FILE,"w") as f: json.dump(d, f, indent=2)
    except Exception:
        pass

save = load_save()

# ── DRAWING HELPERS ──────────────────────────────────────
def draw_text(surf, txt, x, y, f=F_MD, col=C_WHITE, shadow=True):
    if shadow:
        surf.blit(f.render(txt, True, C_BLACK), (x+2, y+2))
    surf.blit(f.render(txt, True, col), (x, y))

def draw_center(surf, txt, cx, cy, f=F_MD, col=C_WHITE, shadow=True):
    t = f.render(txt, True, col)
    x, y = cx - t.get_width()//2, cy - t.get_height()//2
    if shadow:
        surf.blit(f.render(txt, True, C_BLACK), (x+2, y+2))
    surf.blit(t, (x, y))

def draw_rect(surf, col, rect, radius=8, border=0, bcol=None):
    pygame.draw.rect(surf, col, rect, border_radius=radius)
    if border and bcol:
        pygame.draw.rect(surf, bcol, rect, border, border_radius=radius)

def draw_gradient(surf, rect, c1, c2, vertical=True):
    r = pygame.Rect(rect)
    span = r.height if vertical else r.width
    for i in range(span):
        t = i / max(span-1, 1)
        c = tuple(int(c1[j]+(c2[j]-c1[j])*t) for j in range(3))
        if vertical: pygame.draw.line(surf,c,(r.x,r.y+i),(r.x+r.w,r.y+i))
        else:        pygame.draw.line(surf,c,(r.x+i,r.y),(r.x+i,r.y+r.h))

# ── BUTTON ───────────────────────────────────────────────
class Btn:
    def __init__(self, rect, txt, col=C_PANEL, tcol=C_WHITE):
        self.rect=pygame.Rect(rect); self.txt=txt; self.col=col; self.tcol=tcol
    def draw(self, surf):
        mx,my=pygame.mouse.get_pos(); hov=self.rect.collidepoint(mx,my)
        c=tuple(min(255,v+30) for v in self.col) if hov else self.col
        draw_rect(surf,c,self.rect,radius=10,border=2,bcol=C_ACCENT)
        draw_center(surf,self.txt,self.rect.centerx,self.rect.centery,F_MD,self.tcol)
    def clicked(self, events):
        for ev in events:
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1 and self.rect.collidepoint(ev.pos):
                return True
        return False

# ── BIRD DRAWING ─────────────────────────────────────────
def _draw_bird_surface(surf, cx, cy, r, skin, alpha=255):
    """Draw a bird using skin dict onto surf at (cx, cy) with radius r."""
    body = skin["body"]; suit = skin["suit"]; sp = skin["sp"]

    def col(c): return (*c, alpha) if alpha < 255 else c

    # ── Among Us: completely different shape ──
    if sp == "among":
        body_rect = pygame.Rect(cx-r, cy-r, 2*r, int(2.4*r))
        pygame.draw.ellipse(surf, col(body), body_rect)
        pygame.draw.ellipse(surf, col(C_BLACK), body_rect, 2)
        visor = pygame.Rect(cx-int(r*0.7), cy-int(r*0.5), int(r*1.4), int(r*0.75))
        pygame.draw.ellipse(surf, col((150,225,255)), visor)
        bp_rect = pygame.Rect(cx+int(r*0.45), cy+int(r*0.3), int(r*0.6), int(r*0.65))
        pygame.draw.rect(surf, col(suit), bp_rect, border_radius=4)
        return

    # ── Main body ──
    if sp == "sponge":
        pygame.draw.rect(surf, col(body), (cx-r, cy-r, 2*r, 2*r), border_radius=r//3)
        pygame.draw.rect(surf, col(C_BLACK), (cx-r, cy-r, 2*r, 2*r), 2, border_radius=r//3)
    elif sp == "patrick":
        pygame.draw.circle(surf, col(body), (cx, cy), r)
        for a in range(0, 360, 72):
            rad=math.radians(a)
            px,py=cx+int(math.cos(rad)*(r+6)),cy+int(math.sin(rad)*(r+6))
            pygame.draw.circle(surf, col(body), (px,py), r//5)
        pygame.draw.circle(surf, col(C_BLACK), (cx,cy), r, 2)
    else:
        pygame.draw.circle(surf, col(body), (cx,cy), r)
        pygame.draw.circle(surf, col(C_BLACK), (cx,cy), r, 2)

    # ── Suit/overalls ──
    ob = pygame.Rect(cx-r, cy+int(r*0.2), 2*r, int(r*0.9))
    pygame.draw.ellipse(surf, col(suit), ob)

    # ── Eyes ──
    eyes = skin["eyes"]
    if eyes == 1:
        # Cyclops minion
        strap_col = (20,20,20) if sp != "evil" else (180,0,0)
        pygame.draw.rect(surf, col(strap_col), (cx-r-1, cy-int(r*0.28), 2*r+2, max(3,r//5)))
        gr = int(r*0.42); ex,ey = cx, cy-int(r*0.1)
        pygame.draw.circle(surf, col((110,110,110)), (ex,ey), gr+3)
        pygame.draw.circle(surf, col((185,185,185)), (ex,ey), gr)
        pygame.draw.circle(surf, col(C_WHITE),       (ex,ey), int(gr*0.62))
        iris = (180,0,0) if sp=="evil" else (75,42,12)
        pygame.draw.circle(surf, col(iris),    (ex,ey), int(gr*0.3))
        pygame.draw.circle(surf, col(C_BLACK), (ex,ey), int(gr*0.14))
        pygame.draw.circle(surf, col(C_WHITE), (ex-int(gr*0.12),ey-int(gr*0.12)), max(1,int(gr*0.08)))
    elif eyes == 2:
        gr = int(r*0.3)
        for ex,ey in ((cx-int(r*0.38),cy-int(r*0.18)),(cx+int(r*0.38),cy-int(r*0.18))):
            pygame.draw.circle(surf, col(C_WHITE), (ex,ey), gr)
            pygame.draw.circle(surf, col(C_BLACK), (ex,ey), int(gr*0.55))
            pygame.draw.circle(surf, col(C_WHITE), (ex-int(gr*0.2),ey-int(gr*0.2)), max(1,int(gr*0.22)))

    # ── Mouth ──
    pygame.draw.arc(surf, col((110,45,15)),
                    (cx-int(r*0.38),cy+int(r*0.16),int(r*0.76),int(r*0.46)),
                    math.radians(15), math.radians(165), 2)

    # ── Arms ──
    pygame.draw.line(surf, col(body), (cx-r+3,cy+int(r*0.05)), (cx-r-14,cy+int(r*0.05)), 5)
    pygame.draw.line(surf, col(body), (cx+r-3,cy+int(r*0.05)), (cx+r+14,cy+int(r*0.05)), 5)

    # ── Specials ──
    if sp == "pika":
        for sign,ear_x in ((-1, cx-int(r*0.6)), (1, cx+int(r*0.6))):
            pts = [(ear_x-8,cy-r),(ear_x,cy-r-20),(ear_x+8,cy-r)]
            pygame.draw.polygon(surf, col(C_BLACK), pts)
            inner = [(ear_x-5,cy-r),(ear_x,cy-r-13),(ear_x+5,cy-r)]
            pygame.draw.polygon(surf, col(body), inner)
        pygame.draw.circle(surf, col((255,100,100)), (cx-int(r*0.6),cy+int(r*0.1)), int(r*0.2))
        pygame.draw.circle(surf, col((255,100,100)), (cx+int(r*0.6),cy+int(r*0.1)), int(r*0.2))
    elif sp == "shrek":
        pygame.draw.ellipse(surf, col(body), (cx-r-10,cy-r+5,18,14))
        pygame.draw.ellipse(surf, col(body), (cx+r- 8,cy-r+5,18,14))
    elif sp == "robot":
        pygame.draw.line(surf, col((200,200,200)), (cx,cy-r),(cx,cy-r-10), 3)
        pygame.draw.circle(surf, col((255,80,80)), (cx,cy-r-13), 4)
    elif sp == "gold":
        for a in (45,135,225,315):
            rad=math.radians(a)
            pygame.draw.circle(surf, col(C_WHITE),
                (cx+int(math.cos(rad)*r), cy+int(math.sin(rad)*r)), 3)
    elif sp == "doge":
        pygame.draw.ellipse(surf, col(suit), (cx-r-7,cy-r- 6,18,28))
        pygame.draw.ellipse(surf, col(suit), (cx+r-11,cy-r- 6,18,28))
    elif sp == "sponge":
        # freckles
        for fx,fy in ((cx-int(r*0.55),cy+int(r*0.3)),(cx+int(r*0.55),cy+int(r*0.3))):
            pygame.draw.circle(surf, col((200,140,30)), (fx,fy), int(r*0.15))
    elif sp == "tralala":
        pygame.draw.circle(surf, col((255,40,40)), (cx,cy+int(r*0.45)), int(r*0.22))
    elif sp == "bomba":
        pygame.draw.rect(surf, col((180,130,0)), (cx-int(r*0.5),cy-r-8,int(r),8))
    elif sp == "capp":
        pygame.draw.rect(surf, col((80,40,0)),   (cx-int(r*0.7),cy-r-4,int(r*1.4),8), border_radius=3)
    elif sp == "sandy":
        pygame.draw.circle(surf, col((180,230,255)), (cx,cy-int(r*0.3)), int(r*0.6), 3)
    elif sp == "gary":
        pygame.draw.line(surf, col((150,100,140)),(cx,cy+r),(cx,cy+r+14),3)
        pygame.draw.circle(surf, col((200,150,180)),(cx,cy+r+17),5)
    elif sp == "squid":
        pygame.draw.ellipse(surf, col(body),(cx-int(r*0.4),cy-r-8,int(r*0.8),10))
    elif sp == "brr":
        for a in range(0,360,60):
            rad=math.radians(a)
            pygame.draw.circle(surf, col(C_WHITE),
                (cx+int(math.cos(rad)*int(r*0.7)),cy+int(math.sin(rad)*int(r*0.7))),4)
    elif sp == "tung":
        pygame.draw.rect(surf, col(C_ACCENT),(cx-int(r*0.3),cy+int(r*0.35),int(r*0.6),int(r*0.4)),border_radius=3)
    elif sp == "evil":
        # angry eyebrows
        pygame.draw.line(surf, col(C_BLACK),(cx-int(r*0.5),cy-int(r*0.55)),(cx-int(r*0.1),cy-int(r*0.35)),3)
        pygame.draw.line(surf, col(C_BLACK),(cx+int(r*0.1),cy-int(r*0.35)),(cx+int(r*0.5),cy-int(r*0.55)),3)

def draw_bird(surf, x, y, r, skin_id=0, ghost=False):
    skin = SKINS[min(skin_id, len(SKINS)-1)]
    if ghost:
        s = pygame.Surface((r*2+34, r*2+34), pygame.SRCALPHA)
        _draw_bird_surface(s, r+17, r+17, r, skin, alpha=140)
        surf.blit(s, (int(x)-r-17, int(y)-r-17))
    else:
        _draw_bird_surface(surf, int(x), int(y), r, skin)

# ── GOLD COIN (in-game collectible) ─────────────────────
class GameCoin:
    RADIUS = 11
    def __init__(self, x, y):
        self.x=float(x); self.y=float(y); self.taken=False; self._anim=0
    def update(self, spd):
        self.x -= spd; self._anim += 1
    def draw(self, surf):
        if self.taken: return
        cx,cy=int(self.x),int(self.y)
        r=self.RADIUS; pulse=max(1,int(r*0.25*abs(math.sin(self._anim*0.08))))
        pygame.draw.circle(surf, C_COIN,  (cx,cy), r)
        pygame.draw.circle(surf, (200,155,0),(cx,cy), r, 2)
        pygame.draw.circle(surf, (255,235,100),(cx-2,cy-2), pulse+2)
        draw_center(surf,"¢",cx,cy,F_SM,(120,80,0),shadow=False)
    def check(self, bx, by, br):
        if self.taken: return False
        if math.hypot(bx-self.x, by-self.y) < br+self.RADIUS:
            self.taken=True; return True
        return False

# ── PIPE ─────────────────────────────────────────────────
class Pipe:
    def __init__(self, x, seed):
        self.x=float(x); random.seed(seed)
        self.gap_y=random.randint(160, H-GROUND_H-160); self.passed=False
    def update(self, spd): self.x -= spd
    def top_rect(self): return pygame.Rect(int(self.x),0,PIPE_W,self.gap_y-PIPE_GAP//2)
    def bot_rect(self):
        by=self.gap_y+PIPE_GAP//2
        return pygame.Rect(int(self.x),by,PIPE_W,H-GROUND_H-by)
    def draw(self, surf):
        for rect in (self.top_rect(), self.bot_rect()):
            if rect.height<=0: continue
            draw_gradient(surf,rect,C_PIPE,C_PIPED)
            rim_h=16
            rim=pygame.Rect(rect.x-4,rect.bottom-rim_h if rect.y==0 else rect.y,rect.w+8,rim_h)
            draw_rect(surf,C_PIPER,rim,radius=4); pygame.draw.rect(surf,C_PIPED,rim,2,border_radius=4)
    def collides(self, bx, by, br):
        r=pygame.Rect(int(bx)-br+3,int(by)-br+3,(br-3)*2,(br-3)*2)
        return r.colliderect(self.top_rect()) or r.colliderect(self.bot_rect())

# ── PARTICLE ─────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, col):
        a=random.uniform(0,math.tau); s=random.uniform(1,4)
        self.x=float(x); self.y=float(y); self.vx=math.cos(a)*s; self.vy=math.sin(a)*s
        self.col=col; self.life=random.randint(20,40); self.max=self.life; self.r=random.randint(3,6)
    def update(self): self.x+=self.vx; self.y+=self.vy; self.vy+=0.18; self.life-=1
    def draw(self, surf):
        t=self.life/self.max; r=max(1,int(self.r*t))
        s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(*self.col,int(255*t)),(r,r),r)
        surf.blit(s,(int(self.x)-r,int(self.y)-r))

# ── CLOUDS ───────────────────────────────────────────────
clouds=[{"x":random.randint(0,W),"y":random.randint(30,H//2-60),
         "w":random.randint(70,160),"h":random.randint(28,55),"s":random.uniform(0.25,0.6)}
        for _ in range(6)]

def update_clouds():
    for c in clouds:
        c["x"]-=c["s"]
        if c["x"]+c["w"]<0: c["x"]=W+10; c["y"]=random.randint(30,H//2-60)

def draw_clouds(surf):
    for c in clouds:
        cx,cy,cw,ch=int(c["x"]),int(c["y"]),c["w"],c["h"]
        pygame.draw.ellipse(surf,C_WHITE,(cx,cy,cw,ch))
        pygame.draw.ellipse(surf,C_WHITE,(cx+cw//4,cy-ch//3,cw//2,ch))

# ── SCENE ────────────────────────────────────────────────
class Scene:
    def __init__(self, seed=42):
        self.seed=seed; self.pipes=[]; self.coins=[]; self.frame=0
        self.pipe_seed=seed; self.speed=3.0; self.particles=[]; self.ground_x=0.0
    def spawn_pipe(self):
        self.pipe_seed+=1; self.pipes.append(Pipe(W+10, self.pipe_seed))
        if random.random() < 0.6:
            p=self.pipes[-1]; mid=p.gap_y; half=PIPE_GAP//2
            cy=random.randint(mid-half+25, mid+half-25)
            self.coins.append(GameCoin(W+10+PIPE_W//2+40, cy))
    def update(self):
        self.frame+=1
        if self.frame%95==0: self.spawn_pipe()
        for p in self.pipes: p.update(self.speed)
        self.pipes=[p for p in self.pipes if p.x+PIPE_W>-20]
        for c in self.coins: c.update(self.speed)
        self.coins=[c for c in self.coins if c.x>-20]
        self.ground_x=(self.ground_x-self.speed)%48
        for pt in self.particles: pt.update()
        self.particles=[pt for pt in self.particles if pt.life>0]
    def emit(self, x, y, col, n=8):
        for _ in range(n): self.particles.append(Particle(x,y,col))
    def draw_bg(self, surf):
        draw_gradient(surf,(0,0,W,H-GROUND_H),C_SKY,C_SKY2)
        draw_clouds(surf)
        for p in self.pipes: p.draw(surf)
        for c in self.coins: c.draw(surf)
        pygame.draw.rect(surf,C_GROUND,(0,H-GROUND_H,W,GROUND_H))
        pygame.draw.rect(surf,C_GRDARK,(0,H-GROUND_H,W,8))
        gx=int(self.ground_x)
        while gx<W:
            pygame.draw.line(surf,C_GRDARK,(gx,H-GROUND_H+10),(gx+22,H-GROUND_H+10),2)
            gx+=48
        for pt in self.particles: pt.draw(surf)

# ── PLAYER ───────────────────────────────────────────────
class Player:
    def __init__(self, skin_id=0):
        self.skin_id=skin_id; self.reset()
    def reset(self):
        self.x=90; self.y=float(H//2); self.vel=0.0
        self.score=0; self.alive=True; self.radius=22; self.coins_got=0
    def flap(self):
        if self.alive: self.vel=FLAP_STR
    def update(self, scene):
        if not self.alive: return
        self.vel+=GRAVITY; self.y+=self.vel
        for p in scene.pipes:
            if not p.passed and p.x+PIPE_W<self.x:
                p.passed=True; self.score+=1
                scene.emit(self.x,self.y,C_ACCENT,n=10)
        for c in scene.coins:
            if c.check(self.x,self.y,self.radius):
                self.coins_got+=1; scene.emit(c.x,c.y,C_COIN,n=6)
        if self.y-self.radius<=0 or self.y+self.radius>=H-GROUND_H:
            self.alive=False; scene.emit(self.x,self.y,SKINS[self.skin_id]["body"],n=14)
        for p in scene.pipes:
            if p.collides(self.x,self.y,self.radius):
                self.alive=False; scene.emit(self.x,self.y,SKINS[self.skin_id]["body"],n=14)
    def draw(self, surf, ghost=False):
        draw_bird(surf, self.x, self.y, self.radius, self.skin_id, ghost=ghost)

# ── WEBSOCKET ─────────────────────────────────────────────
my_id            = None
other_players    = {}   # id -> {y, score, alive, skin}
waiting_players  = {}   # id -> name (shown in waiting room)
server_game_state = "waiting"
ws_connected     = False
ws_connecting    = False

if WEB:
    import platform as _plt

    def _jseval(code):
        try: return _plt.window.eval(code)
        except Exception: return None

    async def ws_do_connect():
        global ws_connected, ws_connecting
        ws_connecting = True
        try:
            url = SERVER_WS.replace("'","\\'")
            _jseval(f"""
                (function(){{
                  if(window.__pyws){{try{{window.__pyws.ws.close()}}catch(e){{}}}}
                  var ws=new WebSocket('{url}');
                  window.__pyws={{ws:ws,connected:false,msgs:[]}};
                  ws.onopen=function(){{window.__pyws.connected=true;}};
                  ws.onclose=function(){{window.__pyws.connected=false;}};
                  ws.onerror=function(){{window.__pyws.connected=false;}};
                  ws.onmessage=function(e){{window.__pyws.msgs.push(e.data);}};
                }})();
            """)
            for _ in range(50):
                await asyncio.sleep(0.1)
                ok = _jseval("window.__pyws?window.__pyws.connected:false")
                if ok:
                    ws_connected = True
                    ws_connecting = False
                    return
            ws_connected = False
        except Exception as e:
            print("WS connect failed:", e)
            ws_connected = False
        ws_connecting = False

    def ws_send_json(d):
        if not ws_connected: return
        try:
            msg = json.dumps(d).replace("'","\\'")
            _jseval(f"if(window.__pyws&&window.__pyws.ws.readyState===1)window.__pyws.ws.send('{msg}');")
        except Exception: pass

    async def ws_send_state(y, score, alive, skin):
        ws_send_json({"type":"state","y":round(y,1),"score":score,"alive":alive,"skin":skin})

    async def ws_process():
        global ws_connected, my_id, other_players, waiting_players
        global server_game_state, current
        if not ws_connected: return
        connected = _jseval("window.__pyws?window.__pyws.connected:false")
        ws_connected = bool(connected)
        for _ in range(30):
            raw = _jseval("window.__pyws&&window.__pyws.msgs.length>0?window.__pyws.msgs.shift():'__empty__'")
            if not raw or str(raw)=="__empty__": break
            try:
                d=json.loads(str(raw)); t=d.get("type")
                _handle_msg(d)
            except Exception: pass

else:
    # Desktop version (not used in browser build)
    _ws_obj = None

    async def ws_do_connect():
        global ws_connected, ws_connecting, _ws_obj
        ws_connecting=True
        try:
            import websockets as _ws
            _ws_obj = await _ws.connect(SERVER_WS)
            ws_connected=True
        except Exception as e:
            print("WS connect failed:", e); ws_connected=False
        ws_connecting=False

    def ws_send_json(d):
        pass  # handled in ws_send_state

    async def ws_send_state(y, score, alive, skin):
        global ws_connected
        if not ws_connected or not _ws_obj: return
        try:
            import websockets
            await _ws_obj.send(json.dumps({"type":"state","y":round(y,1),"score":score,"alive":alive,"skin":skin}))
        except Exception: ws_connected=False

    async def ws_process():
        global ws_connected, _ws_obj
        if not ws_connected or not _ws_obj: return
        try:
            import websockets
            while True:
                msg=await asyncio.wait_for(_ws_obj.recv(), timeout=0.01)
                _handle_msg(json.loads(msg))
        except Exception: pass

def _handle_msg(d):
    global my_id, other_players, waiting_players, server_game_state, current
    t = d.get("type")
    if t == "welcome":
        my_id = d.get("id")
        server_game_state = d.get("game_state","waiting")
        waiting_players = {int(k): v.get("name",f"P{k}") for k,v in d.get("players",{}).items()}
        if server_game_state == "playing":
            _begin_multi()
    elif t == "join":
        pid = d.get("id")
        waiting_players[pid] = d.get("name", f"Player {pid+1}")
    elif t == "leave":
        pid = d.get("id")
        waiting_players.pop(pid,None); other_players.pop(pid,None)
    elif t == "start":
        server_game_state = "playing"
        _begin_multi()
    elif t == "state":
        pid = d.get("id")
        if pid != my_id:
            other_players[pid] = {"y":d.get("y",H//2),"score":d.get("score",0),
                                   "alive":d.get("alive",True),"skin":d.get("skin",0)}
    elif t == "name":
        pid=d.get("id"); waiting_players[pid]=d.get("name",f"P{pid+1}")
    elif t == "reset":
        server_game_state="waiting"; other_players.clear()
        global current
        if current in ("multi","dead_multi"): current="waiting"

# ── GAME STATE ───────────────────────────────────────────
current = "menu"
scene   = Scene()
p1      = Player(save.get("skin",0))

def _begin_multi():
    global current, scene, p1, other_players
    scene = Scene(seed=42); scene.spawn_pipe()
    p1 = Player(save.get("skin",0))
    other_players = {k:v for k,v in other_players.items()}
    current = "multi"

def start_solo():
    global current, scene, p1
    scene=Scene(seed=random.randint(1,99999)); scene.spawn_pipe()
    p1=Player(save.get("skin",0)); current="solo"

def start_multi():
    global ws_connecting, current
    if not ws_connected and not ws_connecting:
        current = "connecting"
        asyncio.get_event_loop().create_task(ws_do_connect_then_wait())
    elif ws_connected:
        current = "waiting"
        ws_send_json({"type":"name","name":f"Player {(my_id or 0)+1}","skin":save.get("skin",0)})

async def ws_do_connect_then_wait():
    global current
    await ws_do_connect()
    if ws_connected:
        ws_send_json({"type":"name","name":f"Player {(my_id or 0)+1}","skin":save.get("skin",0)})
        current = "waiting"
    else:
        current = "menu"

# ── POPUPS ───────────────────────────────────────────────
popups=[]
def add_popup(txt, col=C_WHITE):
    popups.append({"txt":txt,"y":float(H//2-60),"col":col,"life":55})
def draw_popups(surf):
    dead=[]
    for p in popups:
        p["y"]-=1.2; p["life"]-=1
        if p["life"]<=0: dead.append(p); continue
        alpha=int(255*p["life"]/55)
        t=F_MD.render(p["txt"],True,p["col"])
        s=pygame.Surface(t.get_size(),pygame.SRCALPHA); s.blit(t,(0,0)); s.set_alpha(alpha)
        surf.blit(s,(W//2-t.get_width()//2,int(p["y"])))
    for p in dead: popups.remove(p)

# ── BUTTONS ──────────────────────────────────────────────
btn_solo  = Btn((W//2-130,250,260,52),"SOLO PLAY",  C_GREEN,    C_BLACK)
btn_multi = Btn((W//2-130,312,260,52),"MULTIPLAYER", C_PANEL)
btn_store = Btn((W//2-130,374,260,52),"STORE 🛒",   (60,40,100))
btn_scores= Btn((W//2-130,436,260,52),"SCORES",      C_PANEL)
btn_quit  = Btn((W//2-130,498,260,52),"QUIT",        C_RED,      C_WHITE)
btn_menu  = Btn((W//2-100,H//2+110,200,50),"MENU",      C_PANEL)
btn_again = Btn((W//2-100,H//2+ 50,200,50),"PLAY AGAIN",C_GREEN,C_BLACK)
btn_back  = Btn((W//2-100,H-85,200,50),   "Back",      C_PANEL)
btn_start = Btn((W//2-130,H-100,260,56),  "START GAME",C_GREEN,C_BLACK)

# ── MENU ─────────────────────────────────────────────────
_mt=0.0
def draw_menu(surf, events):
    global current, _mt
    _mt+=0.02
    draw_gradient(surf,(0,0,W,H),(15,22,48),(40,70,130))
    random.seed(7)
    for i in range(35):
        sx=random.randint(0,W); sy=random.randint(0,H//2)
        br=int(160+90*math.sin(_mt*2+i))
        pygame.draw.circle(surf,(br,br,br),(sx,sy),1)
    random.seed()
    bx1=W//2-55+int(math.sin(_mt*1.2)*8); by1=125+int(math.sin(_mt*1.8)*6)
    bx2=W//2+55+int(math.sin(_mt*1.5)*8); by2=133+int(math.sin(_mt*2.1)*6)
    draw_bird(surf,bx1,by1,22,save.get("skin",0))
    draw_bird(surf,bx2,by2,22,1)
    draw_rect(surf,(15,22,55,220),(W//2-190,44,380,80),radius=14)
    draw_center(surf,"FLAPPY RACE",W//2,84,F_XL,C_ACCENT)
    draw_center(surf,"N-Player Online Race",W//2,143,F_SM,C_DIM,shadow=False)
    draw_rect(surf,(20,28,60,200),(W//2-160,170,320,52),radius=10)
    coins_disp=f"💰 {save['coins']} coins  |  Best: {save['high_score']}  |  Wins: {save['wins']}"
    draw_center(surf,f"Coins: {save['coins']}   Best: {save['high_score']}   Wins: {save['wins']}",
                W//2,196,F_SM,C_COIN,shadow=False)
    for b in (btn_solo,btn_multi,btn_store,btn_scores,btn_quit): b.draw(surf)
    if btn_solo.clicked(events):  start_solo()
    if btn_multi.clicked(events): start_multi()
    if btn_store.clicked(events): current="store"
    if btn_scores.clicked(events): current="scores"
    if btn_quit.clicked(events):
        write_save(save); pygame.quit(); sys.exit()

# ── STORE ────────────────────────────────────────────────
store_page=0   # 0 or 1  (10 skins per page)
store_msg=""
store_msg_timer=0

def draw_store(surf, events):
    global current, store_page, store_msg, store_msg_timer
    draw_gradient(surf,(0,0,W,H),(15,22,48),(40,70,130))
    draw_rect(surf,(15,22,55,220),(W//2-185,5,370,60),radius=12)
    draw_center(surf,"STORE",W//2,35,F_LG,C_ACCENT)
    draw_center(surf,f"Coins: {save['coins']}",W//2,60,F_SM,C_COIN,shadow=False)

    per_page=10; start=store_page*per_page
    cols=2; rows=5; cw=228; ch=56; mx=12; my=72

    for idx,sk in enumerate(SKINS[start:start+per_page]):
        real_idx=start+idx
        col_i=idx%cols; row_i=idx//cols
        x=mx+col_i*(cw+8); y=my+row_i*(ch+6)
        owned  = real_idx in save["owned"]
        equipped = save["skin"]==real_idx
        affordable = save["coins"]>=sk["price"]
        if equipped:    bc=(50,200,80)
        elif owned:     bc=(60,100,200)
        elif affordable: bc=(180,140,20)
        else:           bc=(60,60,80)
        draw_rect(surf,(22,30,62),pygame.Rect(x,y,cw,ch),radius=8,border=2,bcol=bc)
        # mini bird
        draw_bird(surf,x+28,y+ch//2,18,real_idx)
        # name
        draw_text(surf,sk["name"],x+54,y+8,F_SM,C_WHITE,shadow=False)
        # status line
        if equipped:     tag="✓ EQUIPPED"
        elif owned:      tag="OWNED – tap equip"
        else:            tag=f"{sk['price']} coins"
        draw_text(surf,tag,x+54,y+28,F_SM,C_COIN if not owned else C_DIM,shadow=False)
        # click
        r=pygame.Rect(x,y,cw,ch)
        for ev in events:
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1 and r.collidepoint(ev.pos):
                if equipped:
                    pass
                elif owned:
                    save["skin"]=real_idx; write_save(save); store_msg="Equipped!"; store_msg_timer=90
                elif affordable:
                    save["coins"]-=sk["price"]; save["owned"].append(real_idx)
                    save["skin"]=real_idx; write_save(save)
                    store_msg=f"Bought {sk['name']}!"; store_msg_timer=90
                else:
                    store_msg=f"Need {sk['price']-save['coins']} more coins"; store_msg_timer=90

    # page buttons
    if store_page==0:
        btn_pg = Btn((W//2+30,H-62,130,44),"Next ▶",C_PANEL)
        btn_pg.draw(surf)
        if btn_pg.clicked(events): store_page=1
    else:
        btn_pg2=Btn((W//2-160,H-62,130,44),"◀ Back",C_PANEL)
        btn_pg2.draw(surf)
        if btn_pg2.clicked(events): store_page=0
    btn_back2=Btn((W//2-160 if store_page==1 else W//2-160,H-62,120,44),"Menu",C_PANEL)
    btn_back2=Btn((8,H-62,110,44),"Menu",C_PANEL)
    btn_back2.draw(surf)
    if btn_back2.clicked(events): current="menu"

    if store_msg_timer>0:
        store_msg_timer-=1
        draw_center(surf,store_msg,W//2,H-90,F_SM,C_GREEN,shadow=False)

# ── CONNECTING ───────────────────────────────────────────
def draw_connecting(surf, events):
    draw_gradient(surf,(0,0,W,H),(15,22,48),(40,70,130))
    draw_center(surf,"Connecting…",W//2,H//2-30,F_LG,C_WHITE)
    draw_center(surf,"Joining multiplayer server",W//2,H//2+20,F_SM,C_DIM,shadow=False)
    # spinner
    t=pygame.time.get_ticks()/1000
    for i in range(8):
        a=math.radians(i*45+t*200)
        alpha=int(255*(i+1)/8)
        px=W//2+int(math.cos(a)*30); py=H//2+80+int(math.sin(a)*30)
        s=pygame.Surface((8,8),pygame.SRCALPHA)
        pygame.draw.circle(s,(255,210,30,alpha),(4,4),4)
        surf.blit(s,(px-4,py-4))

# ── WAITING ROOM ─────────────────────────────────────────
def draw_waiting(surf, events):
    global current
    draw_gradient(surf,(0,0,W,H),(15,22,48),(40,70,130))
    draw_rect(surf,(15,22,55),(W//2-200,8,400,58),radius=12)
    draw_center(surf,"WAITING ROOM",W//2,37,F_LG,C_ACCENT)
    # status
    n=len(waiting_players)
    draw_center(surf,f"{n} player{'s' if n!=1 else ''} connected",W//2,80,F_SM,C_DIM,shadow=False)

    # player list
    y0=100
    for i,(pid,name) in enumerate(list(waiting_players.items())[:8]):
        row_y=y0+i*52
        you=(pid==my_id)
        bc=C_ACCENT if you else C_PANEL
        draw_rect(surf,(22,30,62),(W//2-180,row_y,360,46),radius=8,border=2 if you else 0,bcol=bc)
        sk=other_players.get(pid,{}).get("skin",0) if pid!=my_id else save.get("skin",0)
        draw_bird(surf,W//2-155,row_y+23,17,sk)
        label=f"{name}  (You)" if you else name
        draw_text(surf,label,W//2-130,row_y+12,F_SM,C_WHITE if you else C_DIM,shadow=False)

    btn_start.draw(surf)
    if btn_start.clicked(events):
        ws_send_json({"type":"start"})

    draw_center(surf,"Press START GAME to begin for everyone",W//2,H-110,F_SM,C_DIM,shadow=False)

    # allow going back
    btn_leave=Btn((8,8,90,36),"Leave",C_RED,C_WHITE)
    btn_leave.draw(surf)
    if btn_leave.clicked(events):
        current="menu"

# ── SOLO GAME ────────────────────────────────────────────
def draw_solo(surf, events):
    global current
    update_clouds(); scene.update(); p1.update(scene)
    scene.draw_bg(surf); p1.draw(surf); draw_popups(surf)
    draw_rect(surf,(0,0,0,130),(0,0,W,46),radius=0)
    draw_center(surf,str(p1.score),W//2,22,F_LG,C_WHITE)
    draw_text(surf,f"Best:{save['high_score']}",W-115,10,F_SM,C_COIN,shadow=False)
    draw_text(surf,f"💰{p1.coins_got}",8,10,F_SM,C_COIN,shadow=False)
    scene.speed=min(5.5,3.0+p1.score*0.08)
    for ev in events:
        if ev.type==pygame.KEYDOWN and ev.key in(pygame.K_SPACE,pygame.K_UP,pygame.K_w): p1.flap()
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1: p1.flap()
    if not p1.alive:
        earned=p1.score+p1.coins_got*3
        save["coins"]=save.get("coins",0)+earned
        if p1.score>save["high_score"]: save["high_score"]=p1.score
        save["games"]=save.get("games",0)+1
        write_save(save); current="dead_solo"

# ── MULTI GAME ───────────────────────────────────────────
def draw_multi(surf, events):
    global current
    update_clouds(); scene.update(); p1.update(scene)
    scene.draw_bg(surf)
    # draw others as ghosts
    for pid,op in list(other_players.items()):
        draw_bird(surf,90,op["y"],22,op.get("skin",0),ghost=True)
    p1.draw(surf); draw_popups(surf)
    # HUD top bar
    draw_rect(surf,(0,0,0,150),(0,0,W,52),radius=0)
    draw_center(surf,f"You: {p1.score}",W//2,15,F_MD,C_ACCENT)
    draw_text(surf,f"💰{p1.coins_got}",8,8,F_SM,C_COIN,shadow=False)
    # mini leaderboard right side
    scores=[("You",p1.score)]+[(f"P{pid+1}",op["score"]) for pid,op in other_players.items()]
    scores.sort(key=lambda x:-x[1])
    for i,(name,sc) in enumerate(scores[:4]):
        draw_text(surf,f"{i+1}.{name}:{sc}",W-110,6+i*10,F_SM,
                  C_ACCENT if name=="You" else C_DIM,shadow=False)
    scene.speed=min(5.5,3.0+p1.score*0.08)
    for ev in events:
        if ev.type==pygame.KEYDOWN and ev.key in(pygame.K_SPACE,pygame.K_UP,pygame.K_w): p1.flap()
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1: p1.flap()
    if not p1.alive:
        best_other=max((op["score"] for op in other_players.values()),default=0)
        won=p1.score>=best_other
        earned=p1.score+p1.coins_got*3+(10 if won else 0)
        save["coins"]=save.get("coins",0)+earned
        if won: save["wins"]=save.get("wins",0)+1
        if p1.score>save["high_score"]: save["high_score"]=p1.score
        save["games"]=save.get("games",0)+1
        write_save(save); current="dead_multi"

# ── DEAD SCREENS ─────────────────────────────────────────
def draw_dead(surf, events, multi=False):
    global current
    scene.draw_bg(surf)
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,155)); surf.blit(ov,(0,0))
    draw_rect(surf,C_PANEL,(W//2-175,H//2-175,350,295),radius=14,border=2,bcol=C_ACCENT)
    draw_center(surf,"GAME OVER",W//2,H//2-135,F_XL,C_RED)
    draw_center(surf,f"Score: {p1.score}",W//2,H//2-80,F_LG,C_WHITE)
    draw_center(surf,f"Best: {save['high_score']}",W//2,H//2-42,F_MD,C_ACCENT)
    earned=p1.score+p1.coins_got*3
    if multi: earned+= 10 if p1.score>=max((op["score"] for op in other_players.values()),default=0) else 0
    draw_center(surf,f"+{earned} coins earned",W//2,H//2-8,F_SM,C_COIN,shadow=False)
    if multi:
        best=max((op["score"] for op in other_players.values()),default=0)
        result="YOU WIN! 🏆" if p1.score>=best else "Better luck next time"
        draw_center(surf,result,W//2,H//2+22,F_MD,C_GREEN if p1.score>=best else C_RED)
    btn_again.draw(surf); btn_menu.draw(surf)
    for ev in events:
        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_SPACE:
            if multi: _begin_multi()
            else: start_solo()
    if btn_again.clicked(events):
        if multi:
            ws_send_json({"type":"reset"})
            other_players.clear()
            current="waiting"
        else: start_solo()
    if btn_menu.clicked(events):
        if multi: ws_send_json({"type":"reset"})
        current="menu"

# ── SCORES ───────────────────────────────────────────────
def draw_scores(surf, events):
    global current
    draw_gradient(surf,(0,0,W,H),(15,22,48),(40,70,130))
    draw_rect(surf,(15,22,55),(W//2-185,40,370,70),radius=14)
    draw_center(surf,"SCORES",W//2,75,F_XL,C_ACCENT)
    rows=[("Best Score",str(save["high_score"])),
          ("Total Wins",str(save["wins"])),
          ("Games Played",str(save["games"])),
          ("Total Coins",str(save["coins"]))]
    for i,(label,val) in enumerate(rows):
        y=160+i*72
        draw_rect(surf,(22,30,62),(W//2-165,y,330,58),radius=10)
        draw_text(surf,label,W//2-150,y+14,F_SM,C_DIM,shadow=False)
        draw_center(surf,val,W//2+80,y+28,F_LG,C_ACCENT)
    btn_back.draw(surf)
    if btn_back.clicked(events): current="menu"

# ── MAIN LOOP ────────────────────────────────────────────
async def main():
    while True:
        events=pygame.event.get()
        for ev in events:
            if ev.type==pygame.QUIT:
                write_save(save); pygame.quit(); sys.exit()

        screen.fill(C_BG)

        if   current=="menu":       draw_menu(screen,events)
        elif current=="store":      draw_store(screen,events)
        elif current=="connecting": draw_connecting(screen,events)
        elif current=="waiting":    draw_waiting(screen,events)
        elif current=="solo":       draw_solo(screen,events)
        elif current=="multi":
            draw_multi(screen,events)
            if ws_connected:
                await ws_send_state(p1.y,p1.score,p1.alive,save.get("skin",0))
        elif current=="dead_solo":  draw_dead(screen,events,multi=False)
        elif current=="dead_multi": draw_dead(screen,events,multi=True)
        elif current=="scores":     draw_scores(screen,events)

        if ws_connected: await ws_process()

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

asyncio.run(main())
