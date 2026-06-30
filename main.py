import subprocess
import sys
import threading
import time
import json
import os
import secrets

# ==============================================================================
# 🛠️ 1. SCRAPING RULES (How to fetch the messages)
# ==============================================================================
USER_RELATED_CHANNELS = [1477727056933556264, 1477727056933556265]
STANDARD_CHANNELS = [1477727056933556268, 1477727056664985835]
DAILY_CHANNELS = [1477727056664985840, 1477727057306976265, 1477727057306976266, 1479053149212901510, 1501219031225597962, 1501219406632456253]

# ==============================================================================
# 🎨 2. UI CATEGORIES (Where to display them on the website)
# ==============================================================================
UI_CATEGORIES = {
    1477727056933556264: "משמעת",
    1477727056933556265: "משמעת", 
    1477727056933556268: "דיונים",
    1477727056664985835: "דיונים",
    1477727056664985840: "אישורים",
    1477727057306976265: "אישורים",
    1477727057306976266: "אישורים",
    1479053149212901510: "אישורים",
    1501219031225597962: "אישורים",
    1501219406632456253: "אישורים",
}

# 🛠️ HARDCODE YOUR CONFIGURATION HERE
OUTPUT_FILE = "filtered_export.txt"
GUI_TITLE = "עונשימי טבורי"
BOT_TOKEN = "XXXXXX" 

def run_bot_periodically():
    while True:
        print("\n🔄 [Orchestrator] Running bot.py to sync all channels...")
        
        cmd = [
            sys.executable, "bot.py", 
            "-f", OUTPUT_FILE, 
            "--token", BOT_TOKEN,
            "--user_channels", ",".join(map(str, USER_RELATED_CHANNELS)),
            "--standard_channels", ",".join(map(str, STANDARD_CHANNELS)),
            "--daily_channels", ",".join(map(str, DAILY_CHANNELS)),
            "--ui_categories", json.dumps(UI_CATEGORIES)
        ]
            
        subprocess.run(cmd)
        print("💤 [Orchestrator] Sync complete. Next update in 5 minutes...")
        time.sleep(300) 

if __name__ == "__main__":
    print("🚀 Starting Multi-Channel Log Orchestrator...")
    
    # 1. Start the scraper thread
    bot_thread = threading.Thread(target=run_bot_periodically, daemon=True)
    bot_thread.start()

    # 2. Launch the new 24/7 Daily bot in the background
    print("☀️ Launching daily messaging bot...")
    daily_bot_process = subprocess.Popen([sys.executable, "daily_reminder.py", BOT_TOKEN])

    time.sleep(5)

    # 3. Launch the UI using Gunicorn
    print("🎨 Launching viewer.py UI via Gunicorn...")
    
    # Copy current environment and inject our configuration
    env = os.environ.copy()
    env["BOT_TOKEN"] = BOT_TOKEN
    env["EXPORT_FILE"] = OUTPUT_FILE
    env["GUI_TITLE"] = GUI_TITLE
    env["FLASK_SECRET_KEY"] = secrets.token_hex(24)
    
    # Launch Gunicorn with 3 asynchronous workers and SSL enabled
    try:
        subprocess.run([
            "gunicorn", # Use "sys.executable, '-m', 'gunicorn'" if installed via pip instead of apt
            "--certfile=cert.pem", 
            "--keyfile=key.pem", 
            "-w", "3", 
            "--timeout", "120", 
            "-b", "0.0.0.0:5000", 
            "viewer:app"
        ], env=env)
    finally:
        # 4. Clean up the background bot when Gunicorn stops
        daily_bot_process.terminate()