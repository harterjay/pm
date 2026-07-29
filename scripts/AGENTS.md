# Scripts

Start/stop the Dockerized app. Both pairs just wrap `docker compose up --build -d` / `docker compose down` from the repo root.

- `start.sh` / `stop.sh` — Mac and Linux (POSIX shell)
- `start.ps1` / `stop.ps1` — Windows (PowerShell)

After `start`, the app is served at http://localhost:8000.