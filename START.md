# How to Start the CS2 Highlight Generator

Quick guide to get the application running.

## Prerequisites

Make sure you have Python installed:
```bash
python --version
```

Should show Python 3.11 or higher.

## Starting the Application

### Option 1: Using the Start Script (Easiest)

```bash
# From the project root directory
cd cs2-highlight-generator
./start.sh
```

### Option 2: Manual Start

```bash
# Navigate to the backend directory
cd cs2-highlight-generator/backend

# Start the server
python main.py
```

You should see:
```
INFO:     Starting CS2 Highlight Generator v1.0.0
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The server is now running!

## Opening the Frontend

1. Open your web browser
2. Navigate to or open this file:
   ```
   cs2-highlight-generator/frontend/index.html
   ```
3. Or just double-click `index.html` in your file explorer

## Using the Application

1. Get a CS2 demo file (.dem):
   - From CS2: Watch → Your Matches → Download
   - Or download from https://www.hltv.org/

2. In the web interface:
   - Drag and drop the .dem file
   - Click "Analyze Demo"
   - Wait 10-30 seconds
   - View your highlights!

## API Documentation

While the server is running, visit:
```
http://localhost:8000/api/docs
```

For interactive API documentation (Swagger UI).

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

### "Port already in use"
Another process is using port 8000. Either:
- Stop that process
- Or edit `backend/config.py` and change `API_PORT = 8001`

### "Module not found" errors
Install dependencies:
```bash
cd cs2-highlight-generator/backend
pip install -r requirements.txt
```

### Python not found
If you get "python: command not found", try:
```bash
python3 main.py
```

Or on Windows with full path:
```bash
"%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe" main.py
```

### Demo parsing fails
- Ensure the file is a CS2 demo (not CS:GO)
- File should be under 100MB
- Try a different demo file

## Server Locations

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/docs
- **Frontend:** Open `frontend/index.html` in browser

## Next Steps

See `CLAUDE.md` for detailed architecture documentation and development information.
