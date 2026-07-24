# Flappy Race

A Flappy Bird multiplayer game built with pygame.

## Stack
- Python 3.13
- pygame 2.6.1
- websockets (for optional online multiplayer)
- numpy

## How to run
The **Start application** workflow runs `python main.py`. The game opens in the VNC desktop view (select VNC in the preview pane).

## Game modes
- **Solo** — classic Flappy Bird with speed ramping and a high-score tracker
- **Multiplayer (VS AI)** — race against a simple AI rival
- **Multiplayer (Online)** — enter a WebSocket server URL in the menu to race a real opponent

## Save data
Scores, wins, and games played are saved to `flappy_race_save.json` locally.

## Online multiplayer
Set `SERVER_URL` in `main.py` (or paste a WebSocket server URL into the in-game input box) to enable real-time online play. Leave blank to play VS AI.

## User preferences
