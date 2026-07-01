# momo-tracker

Simple Flask app for tracking momo (demo project).

## Prerequisites
- Python 3.10+ recommended
- Git

## Setup (local)
1. Create and activate a virtual environment:

   - Windows (PowerShell):

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

   - macOS / Linux:

     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

2. Install runtime dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install dev tools:

   ```bash
   pip install -r requirements-dev.txt
   ```

4. Copy environment example and set secrets:

   ```bash
   copy .env.example .env
   # then edit .env and set SECRET_KEY and other values
   ```

5. Run locally:

   ```bash
   # development
   flask run --host=0.0.0.0 --port=${PORT:-5000}

   # production (example)
   gunicorn --bind 0.0.0.0:5000 app:app
   ```

## Deployment
- This repository includes a `Procfile` for platforms like Heroku. Ensure you set production environment variables and secrets in the host.

## Tests & Formatting
- Run tests: `pytest`
- Lint/format: `flake8` / `black` (if installed)

## Notes
- Keep secrets out of source control. Use `.env` or platform secret storage.
