import re
import os
import argparse
import socket
import requests
import urllib.parse
import secrets
from flask import Flask, render_template, jsonify, session, redirect, request

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", default="filtered_export.txt")
parser.add_argument("-t", "--title", default="עונשימי טבורי")
parser.add_argument("-p", "--port", type=int, default=5000)
parser.add_argument("--token", required=True) 
args = parser.parse_args()

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)

# --- SERVER-SIDE STATIC CACHE MEMORY ---
CACHED_LOG_DATA = {}
LAST_FILE_MTIME = 0

# --- 🔐 SECURITY CONFIGURATION ---
DISCORD_CLIENT_ID = "1511268740334096498"
DISCORD_CLIENT_SECRET = "eqjSKQITQMXz4W_3_z3LmBZLY0jC2-j6"
ALLOWED_SERVER_ID = "1477727055910146101"
REDIRECT_URI = "http://localhost:5000/callback"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def parse_logs():
    global CACHED_LOG_DATA, LAST_FILE_MTIME
    filepath = args.file
    
    parsed_data = {
        "משמעת": {},
        "אישורים": {},
        "דיונים": {}
    }
    
    if not os.path.exists(filepath):
        return parsed_data
    
    try:
        current_mtime = os.path.getmtime(filepath)
        if current_mtime == LAST_FILE_MTIME and CACHED_LOG_DATA:
            return CACHED_LOG_DATA
            
        pattern = re.compile(r"^\[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(0|1)\] (.*?): (.*)$")
        channel_to_category = {} 
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines[3:]:
            line = line.strip()
            if not line: continue
            
            if line.startswith("--- CATEGORY:"):
                parts = line.replace("--- CATEGORY: ", "").replace(" ---", "").split(" | CHANNEL: ")
                cat = parts[0].strip()
                ch = parts[1].strip()
                
                channel_to_category[ch] = cat
                if cat not in parsed_data: parsed_data[cat] = {}
                if ch not in parsed_data[cat]: parsed_data[cat][ch] = []
                continue
                
            match = pattern.match(line)
            if match:
                ts, ch, cid, mid, is_done, usr, msg = match.groups()
                cat = channel_to_category.get(ch, "כללי")
                
                if cat not in parsed_data: parsed_data[cat] = {}
                if ch not in parsed_data[cat]: parsed_data[cat][ch] = []
                parsed_data[cat][ch].append({"ts": ts, "usr": usr, "msg": msg, "cid": cid, "mid": mid, "done": is_done})
        
        CACHED_LOG_DATA = parsed_data
        LAST_FILE_MTIME = current_mtime
            
        return CACHED_LOG_DATA
    except Exception as e:
        if CACHED_LOG_DATA:
            return CACHED_LOG_DATA
        return parsed_data

@app.route("/login")
def login():
    oauth_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code&scope=identify%20guilds"
    return redirect(oauth_url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    if not code: return "Authentication Failed.", 403
    
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_resp = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    token = token_resp.json().get('access_token')
    if not token: return "Failed to retrieve token.", 403
    
    guilds = requests.get("https://discord.com/api/users/@me/guilds", headers={"Authorization": f"Bearer {token}"}).json()
    if any(str(g.get('id')) == str(ALLOWED_SERVER_ID) for g in guilds):
        session['authorized'] = True
        return redirect('/')
    return "Access Denied.", 403

@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')

@app.route("/react/<channel_id>/<message_id>", methods=["POST"])
def react_to_message(channel_id, message_id):
    if not session.get('authorized'): return jsonify({"status": "unauthorized"}), 403
    headers = {"Authorization": f"Bot {args.token}"}
    emoji = urllib.parse.quote("✅") 
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
    
    response = requests.put(url, headers=headers)
    return jsonify({"status": "success" if response.status_code == 204 else "error"})

@app.route("/unreact/<channel_id>/<message_id>", methods=["POST"])
def unreact_to_message(channel_id, message_id):
    if not session.get('authorized'): return jsonify({"status": "unauthorized"}), 403
    headers = {"Authorization": f"Bot {args.token}"}
    emoji = urllib.parse.quote("✅") 
    
    # 🛡️ THE FIX: Removed "/@me" from the end of this URL. 
    # This tells Discord to wipe ALL reactions of this specific emoji from the message.
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/reactions/{emoji}"
    
    response = requests.delete(url, headers=headers)
    return jsonify({"status": "success" if response.status_code == 204 else "error"})

@app.route("/")
def index():
    if not session.get('authorized'):
        return redirect('/login')
    return render_template("index.html", title=args.title, data=parse_logs())

if __name__ == "__main__":
    port = args.port
    print("\n" + "="*50)
    print("🚀 SECURE DISCORD WEB DASHBOARD IS LIVE!")
    print(f"💻 Local Port: {port}")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)