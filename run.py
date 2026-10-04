import os
import sys
import webbrowser
import threading
import time
import uvicorn
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings

def open_dashboard():
    """Open desktop AI web dashboard in browser after server starts."""
    time.sleep(1.2)
    url = f"http://{settings.HOST}:{settings.PORT}"
    print(f"\n=======================================================")
    print(f"🚀 Universal Autonomous Desktop AI is running!")
    print(f"📡 API & Dashboard URL: {url}")
    print(f"📚 Interactive Swagger Docs: {url}/docs")
    print(f"=======================================================\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Note: Could not automatically open browser: {e}")

def main():
    threading.Thread(target=open_dashboard, daemon=True).start()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
