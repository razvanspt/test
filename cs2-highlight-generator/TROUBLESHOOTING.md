# Troubleshooting Guide

Common issues and solutions for CS2 Highlight Generator.

---

## ❌ Error: "Required event 'round_officially_ended' is missing"

**What it means:** The demo file format doesn't match what awpy expects.

### **Solutions (try in order):**

### 1️⃣ Update awpy library

```bash
pip install --upgrade awpy
```

Then restart the server:
```bash
cd backend
python main.py
```

### 2️⃣ Make sure it's a CS2 demo (not CS:GO)

This tool **ONLY works with Counter-Strike 2**, not CS:GO.

**How to check:**
- CS2 was released in September 2023
- Demos from before that are CS:GO (won't work)
- File should come from: `steamapps/common/Counter-Strike Global Offensive/game/csgo/replays/`

### 3️⃣ Try a fresh demo file

Your demo might be:
- Corrupted
- Incomplete (match abandoned/crashed)
- From an unsupported CS2 version (early beta)

**Get a working demo:**

**Option A - Your Matches:**
1. Open CS2
2. Go to "Watch" → "Your Matches"
3. Find a recent completed competitive match
4. Download the demo

**Option B - Pro Matches:**
1. Visit https://www.hltv.org/
2. Find a 2024/2025 match
3. Download demo
4. Make sure it says "CS2" not "CS:GO"

### 4️⃣ Check your Python version

```bash
python --version
```

Should be **Python 3.11+**. If lower, update Python.

### 5️⃣ Reinstall dependencies

```bash
cd backend
pip uninstall awpy
pip install awpy
```

---

## ❌ Error: "Module not found: awpy" or "No module named..."

**Solution:**

```bash
cd backend
pip install -r requirements.txt
```

If still fails:
```bash
pip3 install -r requirements.txt
```

---

## ❌ Port 8000 already in use

**Error:** `Address already in use`

**Solution 1 - Use different port:**

Edit `backend/config.py`:
```python
API_PORT = 8001  # Change from 8000 to 8001
```

Edit `frontend/index.html` (line ~202):
```javascript
const API_URL = 'http://localhost:8001';  # Change to match
```

**Solution 2 - Stop the other process:**

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -ti:8000 | xargs kill -9
```

---

## ❌ CORS Error in Browser

**Error:** `Access to fetch... blocked by CORS policy`

This happens when opening `index.html` directly as a file.

**Solution - Use a web server:**

```bash
cd frontend
python -m http.server 3000
```

Then open: http://localhost:3000

---

## ✅ "No highlights detected" (Not an Error!)

The demo parsed successfully but didn't find aces/4Ks/3Ks.

**Why:**
- Match might not have had multi-kills
- Players might be low skill
- Practice/casual match

**Solutions:**
- Try a pro match demo (guaranteed highlights)
- Try your best performance demo
- Wait for Phase 2 (more highlight types: clutches, high damage, etc.)

---

## ❌ Demo Parsing Takes Forever (>60 seconds)

**Normal times:**
- Short match (10-20 rounds): 10-15 seconds
- Full match (30 rounds): 20-30 seconds
- Overtime: 30-40 seconds

**If >60 seconds:**
- Check demo file size (over 200MB is slow)
- Close other programs
- This is normal for very long demos
- Parsing is CPU-intensive (library limitation)

---

## ❌ Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

```bash
cd backend
pip install -r requirements.txt
```

**Error:** `python: command not found`

Try `python3`:
```bash
python3 main.py
```

**Error:** `Permission denied` (Linux/Mac)

```bash
chmod +x start.sh
./start.sh
```

---

## ❌ Upload Fails Immediately

**Error:** "Invalid file type"

- Make sure extension is `.dem`
- Not `.dem.txt` or `.zip`
- Enable "Show file extensions" in Windows

**Error:** "File too large"

Default max is 100MB.

To increase, edit `backend/config.py`:
```python
MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200MB
```

---

## ❌ Frontend Shows Blank Page

1. Check browser console (F12)
2. Make sure backend is running:
   ```bash
   curl http://localhost:8000/api/health
   ```
   Should return: `{"status":"healthy",...}`

3. Check CORS settings (see CORS Error above)

---

## 🔧 Quick Diagnostic Checklist

When something doesn't work:

- [ ] Python 3.11+ installed?
- [ ] Ran `pip install -r requirements.txt`?
- [ ] Backend server running? (should see "Uvicorn running on...")
- [ ] Demo is CS2 (not CS:GO)?
- [ ] awpy up to date? (`pip install --upgrade awpy`)
- [ ] Tried a different demo file?
- [ ] Checked backend logs for specific errors?

---

## 📚 Demo File Sources (Guaranteed to Work)

**✅ Recommended:**
1. **Your recent CS2 matches** (from Watch → Your Matches)
2. **HLTV pro matches** from 2024/2025
3. **FaceIt CS2 demos**

**❌ Might Not Work:**
- CS:GO demos (definitely won't work)
- CS2 Beta demos (before official release)
- Workshop/community server demos
- Corrupted downloads

---

## 🛠️ Advanced Debugging

### Enable Verbose Logging

Edit `backend/demo_parser_service.py` line ~81:
```python
demo = Demo(
    path=demo_file_path,
    tickrate=128,
    verbose=True  # Change from False to True
)
```

This will show detailed parsing output.

### Check awpy Version

```bash
pip show awpy
```

Latest is 1.3.1+ (as of Nov 2024)

### Test with Sample Demo

1. Download a known working demo from HLTV
2. Try it with the tool
3. If it works → your original demo is the issue
4. If it doesn't → awpy/Python installation issue

---

## 🆘 Still Stuck?

1. **Check the error message** in backend logs (terminal where you ran `python main.py`)
2. **Google the error** - might be a known awpy issue
3. **Try different demo** - isolates whether it's the demo or the tool
4. **Check awpy GitHub issues:** https://github.com/pnxenopoulos/awpy/issues

---

## 💡 Common Mistakes

1. **Using CS:GO demos** → Only CS2 works!
2. **Opening index.html as file** → Use http.server instead
3. **Forgetting to start backend** → Must run `python main.py` first
4. **Wrong Python version** → Need 3.11+
5. **Not updating awpy** → Run `pip install --upgrade awpy`

---

**Most issues are solved by:**
1. `pip install --upgrade awpy`
2. Restart server
3. Try fresh CS2 demo (not CS:GO!)
