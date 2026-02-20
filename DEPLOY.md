# 🚀 Deploy JobFeed to Railway — Step by Step

Total time: ~5 minutes.

---

## Step 1: Create a GitHub Repo

```bash
# Extract the project
tar xzf job-feed.tar.gz
cd job-feed

# Init git and push
git init
git add .
git commit -m "Initial commit: JobFeed app"

# Create repo on GitHub (or use gh cli)
gh repo create job-feed --private --source=. --push

# Or manually:
# 1. Go to github.com/new
# 2. Create "job-feed" (private)
# 3. Follow the push instructions
```

---

## Step 2: Create Railway Account & Project

1. Go to **[railway.app](https://railway.app)**
2. Sign up with your **GitHub account**
3. Click **"New Project"**
4. Select **"Deploy from GitHub Repo"**
5. Pick your **job-feed** repository
6. Railway auto-detects the Dockerfile and starts building

---

## Step 3: Add Persistent Volume (important!)

Without this, your SQLite database resets on every deploy.

1. In Railway dashboard → click your **job-feed service**
2. Go to **Settings** tab
3. Scroll to **Volumes** → click **"Add Volume"**
4. Set mount path: `/data`
5. Click **Add**
6. Go to **Variables** tab → click **"New Variable"**
7. Add: `RAILWAY_VOLUME_MOUNT_PATH` = `/data`

---

## Step 4: (Optional) Customize Search Terms

In Railway dashboard → **Variables** tab, add:

| Variable | Value | Purpose |
|----------|-------|---------|
| `SEARCH_TERMS` | `data analyst,bi engineer,power bi,analytics` | Comma-separated job search terms |
| `SCRAPE_INTERVAL_HOURS` | `12` | How often to auto-scrape (default: 12) |

---

## Step 5: Deploy

Railway auto-deploys when you push to GitHub. After the first build:

1. Click **"Generate Domain"** in Settings to get a public URL
2. Visit your URL — the app is live!
3. Jobs auto-scrape on startup and every 12 hours

Your URL will look like: `https://job-feed-production-xxxx.up.railway.app`

---

## That's it! 🎉

### What happens automatically:
- **On deploy/restart**: DB initializes + first scrape runs immediately
- **Every 12 hours**: Background thread scrapes all 4 APIs
- **On button click**: "Refresh Jobs" triggers a manual scrape

### Railway Free Tier Limits:
- **$5 free credit/month** (resets monthly)
- This app uses very little resources (~$1-2/month)
- If you exceed, Railway pauses the app until next month

### Redeploy anytime:
```bash
git add .
git commit -m "update"
git push
```
Railway auto-redeploys on push.

---

## Troubleshooting

**App shows 0 jobs after deploy:**
Wait 30-60 seconds — the initial scrape runs in the background on startup.

**Jobs disappear after redeploy:**
You forgot Step 3 (volume). Add the volume and redeploy.

**Want to check logs:**
Railway dashboard → your service → **Deployments** tab → click latest → **View Logs**

**Want to scrape different roles:**
Update the `SEARCH_TERMS` env var in Railway dashboard and redeploy.
