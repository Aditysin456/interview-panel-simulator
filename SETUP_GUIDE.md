# Setup Guide (Beginner Friendly)

This guide assumes: you have a Linux terminal and VS Code, and **zero** prior
experience with Git, GitHub, or deployment tools. Follow it top to bottom —
every command is copy-pasteable.

---

## Part A — Run the App Locally (do this first, before touching Git)

### A1. Check Python is installed

Open your terminal and run:

```bash
python3 --version
```

You should see something like `Python 3.10` or higher. If it says "command
not found", install it with:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### A2. Open the project folder in VS Code

```bash
cd path/to/interview-panel
code .
```

(`code .` opens the current folder in VS Code. If that command doesn't work,
just open VS Code normally and use File → Open Folder.)

### A3. Set up and run the backend

In the VS Code terminal (Terminal → New Terminal), run these one at a time:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

Your terminal prompt should now show `(venv)` at the start — that means
you're inside an isolated Python environment, so nothing you install here
affects the rest of your system.

```bash
pip install -r requirements.txt
cp .env.example .env
```

The app will run in **mock mode** by default (fake but realistic responses,
so you can test everything for free). To use the real Claude API later,
open `.env` in VS Code and:
1. Set `ANTHROPIC_API_KEY=` to your real key
2. Change `MOCK_MODE=true` to `MOCK_MODE=false`

Now start the backend:

```bash
uvicorn main:app --reload --port 8000
```

Leave this terminal running. You should see `Uvicorn running on
http://127.0.0.1:8000`.

### A4. Run the frontend

Open a **second** terminal (don't close the first one) in VS Code:

```bash
cd frontend
python3 -m http.server 5500
```

Now open your browser and go to: `http://localhost:5500`

Click **"Load Sample Data"** then **"Run Interview Panel"**. You should see
the full pipeline appear: profile → 4 agent opinions → debate → final
decision. This works instantly in mock mode with no API key.

---

## Part B — Git & GitHub From Absolute Zero

### B1. Install Git

```bash
git --version
```

If not installed:

```bash
sudo apt update
sudo apt install git
```

### B2. Tell Git who you are (one-time setup)

```bash
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Use the same email you used to sign up for GitHub.

### B3. Create the repository on GitHub (in your browser)

1. Go to [github.com](https://github.com) and log in
2. Click the **+** icon (top right) → **New repository**
3. Name it something like `interview-panel-simulator`
4. Make sure **Public** is selected (required by the challenge rules)
5. **Do NOT** check "Add a README" — we already have one, and having
   GitHub create one too will cause a conflict later
6. Click **Create repository**
7. GitHub will show you a page with a URL like:
   `https://github.com/your-username/interview-panel-simulator.git`
   Keep this page open, you'll need that URL in a moment.

### B4. Turn your local project folder into a Git repository

Back in your terminal, go to the **root** of the project (the
`interview-panel` folder, not `backend` or `frontend`):

```bash
cd path/to/interview-panel
git init
```

This creates a hidden `.git` folder — your project is now tracked by Git.

### B5. Check what Git sees

```bash
git status
```

You'll see a list of files in red (untracked). This is normal — Git is just
telling you it noticed these files but isn't tracking them yet.

### B6. Stage and commit your files

"Staging" means telling Git "include these files in my next snapshot."
"Committing" means actually taking that snapshot.

```bash
git add .
git commit -m "Initial commit: multi-agent interview panel simulator"
```

If Git complains about identity, go back to step B2.

### B7. Connect your local folder to the GitHub repo you created

Copy the URL from step B3, then run (replace with your actual URL):

```bash
git remote add origin https://github.com/your-username/interview-panel-simulator.git
```

### B8. Make sure you're on a single branch called "main"

The challenge requires exactly one branch. Force the branch name to be `main`:

```bash
git branch -M main
```

### B9. Push your code to GitHub

```bash
git push -u origin main
```

The first time, it may open a browser window asking you to log in to
GitHub and authorize Git — follow the prompts. After that, refresh your
GitHub repository page in the browser — your code should now be there.

### B10. Making further changes later

Every time you make changes and want to save them to GitHub:

```bash
git add .
git commit -m "Describe what you changed"
git push
```

That's the entire day-to-day workflow — you'll use these three commands
(`add`, `commit`, `push`) constantly. `git status` is also useful any time
you want to check what's changed since your last commit.

### B11. Double-check the hard requirements before submitting

```bash
# Confirm you only have one branch:
git branch -a

# Check your repo size is under 10MB (run from inside the project folder):
du -sh .git
du -sh .
```

If the size looks too large, make sure `.env`, `venv/`, and `__pycache__/`
were never committed (they're excluded by `.gitignore`, but if you ran
`git add .` before creating the `.gitignore`, you may need to remove them —
ask if this happens and we'll fix it together).

---

## Part C — About Deployment (Vercel/Netlify)

You mentioned no experience with Vercel or Netlify. **Good news: you don't
need them for this challenge.** The submission only requires a public
GitHub repo with working code and a README — judges will run it locally
themselves following your README instructions (which is exactly what we
wrote above). Don't spend hackathon time on deployment; it adds risk for
zero required benefit here. If you want a live demo link later purely as a
bonus, that's a separate, optional step we can do after the core
submission is safely in place.

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| `git: command not found` | Run the install command in B1 |
| `Please tell me who you are` | Run the commands in B2 |
| `fatal: remote origin already exists` | Run `git remote remove origin` then redo B7 |
| `failed to push some refs` | Someone/something changed the GitHub repo after you created it locally (e.g. you accidentally checked "Add a README"). Run `git pull origin main --allow-unrelated-histories`, resolve any conflicts, then push again |
| Browser shows "Could not reach backend" | Make sure the `uvicorn` terminal (Part A3) is still running |
| `ModuleNotFoundError` when running uvicorn | Make sure you ran `source venv/bin/activate` in that terminal before `pip install` |
