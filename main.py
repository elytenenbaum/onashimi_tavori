import subprocess
import sys
import threading
import time
import json



# ==============================================================================
# 🛠️ 1. SCRAPING RULES (How to fetch the messages)
# ==============================================================================
USER_RELATED_CHANNELS = [1477727056933556264, 1477727056933556265] # Requires '#'
STANDARD_CHANNELS = [1477727056933556268, 1477727056664985835] # Everything
DAILY_CHANNELS = [1477727056664985840, 1477727057306976265, 1477727057306976266, 1479053149212901510, 1501219031225597962, 1501219406632456253] # 24-Hour Everything

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
BOT_TOKEN = "MTUxMTI2ODc0MDMzNDA5NjQ5OA.GDN6z5.fJQ06qRuVr05Z46OG1KnjxHeqKdrmt1MuAmdkM" 

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
            "--ui_categories", json.dumps(UI_CATEGORIES) # Send categories to the bot
        ]
            
        subprocess.run(cmd)
        print("💤 [Orchestrator] Sync complete. Next update in 1 minute...")
        time.sleep(60) 

if __name__ == "__main__":
    print("🚀 Starting Multi-Channel Log Orchestrator...")
    bot_thread = threading.Thread(target=run_bot_periodically, daemon=True)
    bot_thread.start()

    time.sleep(5)

    print("🎨 Launching viewer.py UI...")
    subprocess.run([sys.executable, "viewer.py", "-f", OUTPUT_FILE, "-t", GUI_TITLE, "--token", BOT_TOKEN])