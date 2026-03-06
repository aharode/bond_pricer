# Bond Analytics UI — Setup Instructions

## Drop into your existing repo

Your repo currently has the Python files. Add the React UI alongside them:

```
bond_pricer/              ← your existing folder
├── src/
│   └── bond.py
├── day1_problems.py
├── README.md
│
├── App.jsx               ← ADD THIS (the UI)
└── index.html            ← ADD THIS (only if not already present from Vite)
```

## If you haven't scaffolded Vite yet

```bash
# From inside your bond_pricer repo
npm create vite@latest . -- --template react
# (the . deploys into current folder — say YES to overwrite package.json)

npm install

# Replace src/App.jsx with the provided App.jsx
cp App.jsx src/App.jsx
```

## Run locally

```bash
npm run dev
# → http://localhost:5173
```

## Deploy to Vercel

Push to GitHub, then in Vercel:
- Framework: **Vite**
- Build command: `npm run build`
- Output directory: `dist`

That's it — Vercel auto-detects Vite.

## Dependencies

Only one non-standard dependency needed later (Day 2+ charts):
```bash
npm install recharts
```

Not needed yet for Day 1.
