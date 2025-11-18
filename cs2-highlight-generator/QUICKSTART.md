# Quick Start Guide

Get the CS2 Highlight Generator running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd cs2-highlight-generator/backend
pip3 install -r requirements.txt
```

**Wait 2-5 minutes for installation to complete.**

## Step 2: Start the Server

**Option A: Using the start script (easiest)**
```bash
cd cs2-highlight-generator
./start.sh
```

**Option B: Manual start**
```bash
cd cs2-highlight-generator/backend
python3 main.py
```

You should see:
```
INFO:     Starting CS2 Highlight Generator v1.0.0
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 3: Open the Web Interface

Open this file in your browser:
```
cs2-highlight-generator/frontend/index.html
```

Or double-click `index.html` to open it.

## Step 4: Upload a Demo

1. Get a CS2 demo file (.dem)
   - From your matches in CS2 → Watch → Your Matches → Download
   - Or from https://www.hltv.org/

2. Drag and drop the .dem file onto the upload area

3. Click "Analyze Demo"

4. Wait 10-30 seconds

5. See your highlights!

## That's it!

You now have a working CS2 highlight detector.

---

## What Next?

- Read the full [README.md](README.md) for detailed documentation
- Check the [API docs](http://localhost:8000/api/docs) after starting the server
- Modify the code to add new features
- Try different demo files

## Troubleshooting

**"Module not found" error:**
```bash
cd backend
pip3 install -r requirements.txt
```

**"Port already in use":**
- Edit `backend/config.py`
- Change `API_PORT = 8001` (or any other port)

**Demo parsing fails:**
- Make sure it's a CS2 demo file (not CS:GO)
- Try a different demo file

---

## Testing Without a Demo File

If you don't have a demo file handy, you can test the API directly:

1. Visit http://localhost:8000/api/docs
2. Try the `/api/health` endpoint
3. See the interactive API documentation

---

## Monetization Ideas (Your Question)

Since you asked how to monetize this, here are specific strategies:

### 1. Freemium Model
- **Free**: 3 highlight videos/month with watermark
- **Pro ($6.99/month)**: Unlimited, no watermark, HD quality

### 2. Per-Video Pricing
- **Free**: 1 video/week
- **Pay**: $1.99 per video without watermark

### 3. Creator Tier
- **Free**: Basic features
- **Creator ($14.99/month)**: Custom branding, analytics, batch processing

### 4. Affiliate Revenue
- Partner with CS2 training sites (Refragg, aim trainers)
- Earn commission on referrals
- Low effort, passive income

### 5. White-Label for Coaches
- Coaches pay $99/month to rebrand your tool
- They offer it to students
- You handle tech, they handle customers

**My recommendation**: Start with freemium (#1). It's proven to work and users expect it.

---

**Need help? Check README.md for full documentation!**
