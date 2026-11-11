# test v1 — Jungle Survival

A small browser‑playable survival game made with Python + Pygame and packaged
for the web using [pygbag](https://github.com/pygame-web/pygbag).

## Play

Once GitHub Pages is enabled, open:
`https://<your-username>.github.io/<your-repo>/`

## Controls

| Key | Action |
| --- | --- |
| WASD / Arrows | Move |
| E | Eat food |
| Q | Drink water |
| 1 | Craft Campfire (5 wood) |
| 2 | Craft Spear (3 wood, 2 stone) |
| 3 | Craft Food Storage (4 wood) |
| SPACE | Attack (needs spear) |
| R | Restart after win/lose |

## How it works

- The game (`main.py`) uses an async game loop (`async def run`) required for
  pygbag to run Python in the browser.
- The workflow `.github/workflows/deploy.yml` runs pygbag on every push and
  publishes the built WASM bundle to GitHub Pages.
