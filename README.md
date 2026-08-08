# Colosseum

A sandboxed code execution engine that runs untrusted Python code safely inside isolated Docker containers and returns the output in real time.

Live demo: *(add your ngrok/deployment URL here)*

![status](https://img.shields.io/badge/status-active-brightgreen)

---

## What It Does

Colosseum accepts arbitrary Python code from a user, executes it inside a fresh, isolated Docker container, and streams the output back — similar to how an online code judge or compiler works. Every submission runs in a throwaway sandbox with strict resource limits so untrusted code can never affect the host system.

---

## How It Works

```
Browser (Monaco Editor)
        │  POST /submit { code }
        ▼
   FastAPI backend
        │  rate limited, length checked
        ▼
   executor.py
        │  writes code to a temp file
        ▼
   Docker container (python:3.11-slim)
        │  runs the code, streamed logs captured
        │  killed if it exceeds 5s (threading timeout)
        ▼
   Output + status + execution_time
        │
        ├──► stored in MongoDB Atlas
        └──► returned to frontend, displayed in the editor
```

---

## Security Measures

Every execution container runs with:

| Control | Purpose |
|---|---|
| `mem_limit="128m"` | Prevents memory exhaustion |
| `cpu_quota` / `cpu_period` | Caps CPU usage per submission |
| `pids_limit=50` | Blocks fork bombs |
| `network_disabled=True` | No outbound network access |
| `user="nobody"` | Runs as an unprivileged user, not root |
| 5-second thread-based timeout | Kills runaway/infinite loops |
| `remove=True` after execution | No leftover containers on disk |

Additional API-level protections:
- Rate limiting — 1 request per 3 seconds per IP (`slowapi`)
- Max code length enforced before it ever reaches Docker

---

## Tech Stack

- **Backend:** Python, FastAPI
- **Execution:** Docker SDK for Python
- **Database:** MongoDB Atlas
- **Frontend:** Monaco Editor (VS Code's editor), vanilla JS
- **CI/CD:** GitHub Actions → Docker Hub
- **Rate Limiting:** slowapi

---

## Running Locally

**1. Clone and install dependencies**
```bash
git clone https://github.com/Raiden1718x/Colosseum.git
cd Colosseum
pip install -r requirements.txt
```

**2. Set up environment variables**

Create a `.env` file:
```
DB_URI=your_mongodb_atlas_connection_string
```

**3. Run the server**
```bash
uvicorn main:app --reload
```

**4. Open the app**
```
http://localhost:8000
```

> Note: Colosseum needs access to Docker on the host machine to spawn execution containers, so it's run directly with uvicorn locally rather than inside its own container (see [Deployment](#deployment) for why).

---

## Deployment

Colosseum is containerized with a multi-stage `Dockerfile` and deployed via Docker, with the host's Docker socket mounted in so the app can spawn execution containers:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

This works cleanly on a Linux host (e.g. a VPS) where the app container and Docker daemon share the same filesystem. It does not work reliably on Docker Desktop for Windows due to the VM layer between the two, which is why local development uses `uvicorn` directly instead.

GitHub Actions automatically builds and pushes a new image to Docker Hub on every push to `main`.

---

## What's Next

- [ ] Redis-backed job queue for concurrent submissions at scale
- [ ] Support for additional languages (C++, Java, JavaScript)
- [ ] Permanent hosting on a Linux VPS
- [ ] Submission history page

---

## Author

Akshat Singh — [GitHub](https://github.com/Raiden1718x) · [LinkedIn](https://linkedin.com/in/akshat-singh-b12293383)
