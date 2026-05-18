# DR05 PokeChat 2026

## Getting started

1. **Makefile — student info**  
   Open the project `Makefile` and set your name and email (the lines that assign `DEFAULT_STUDENT_NAME` and `DEFAULT_STUDENT_EMAIL`). These defaults are used when you run `make submit`. You can still override them on the command line when needed.

2. **Environment — Azure OpenAI**  
   Copy `.env.example` to `.env` in the project root:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and paste the endpoint, API key, API version, and deployment name from the **Google Doc design brief** (Azure / OpenAI section). The file `.env` is gitignored; never commit secrets.

3. **Install and run**  
   From the project root:
   ```bash
   make install    # Python + npm dependencies (loads .env if present)
   make backend    # Flask API (one terminal)
   make frontend   # React dev server (another terminal)
   ```

## Makefile

Run these from the project root (where `Makefile` lives).

| Command | Description |
|--------|-------------|
| `make install` | Creates `backend/.venv` if needed (avoids Homebrew / PEP 668 “externally managed” pip errors), installs Python deps into that venv, then runs `npm install`. |
| `make frontend` | Starts the React app in development mode (`npm start`). |
| `make backend` | Starts the Flask API on **port 3001** (avoids macOS AirPlay on 5000) using `backend/.venv`’s Python (`make install` once first). |
| `make submit` | Builds a submission zip from **only files Git tracks** (excludes untracked items such as `node_modules` and `.env`). Uses `STUDENT_NAME` and `STUDENT_EMAIL` from the Makefile unless you override them. |

**Submit**

After you update `DEFAULT_STUDENT_NAME` and `DEFAULT_STUDENT_EMAIL` in the Makefile:

```bash
make submit
```

Or pass values once without editing the file:

```bash
make submit STUDENT_NAME="Ada Lovelace" STUDENT_EMAIL="ada@example.edu"
```

This creates `pokechat-submit-<name>-<email>.zip` in the project root.