import re
import os
import argparse
import socket
import requests
import urllib.parse
import secrets
from flask import Flask, render_template_string, jsonify, session, redirect, request

# --- COMMAND LINE ARGUMENTS ---
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", default="filtered_export.txt")
parser.add_argument("-t", "--title", default="Live Logs")
parser.add_argument("-p", "--port", type=int, default=5000)
parser.add_argument("--token", required=True) 
args = parser.parse_args()

app = Flask(__name__)
app.secret_key = secrets.token_hex(24) # Random key for session security

# --- 🔐 SECURITY CONFIGURATION ---
DISCORD_CLIENT_ID = "1511268740334096498"
DISCORD_CLIENT_SECRET = "eqjSKQITQMXz4W_3_z3LmBZLY0jC2-j6"
ALLOWED_SERVER_ID = "1477727055910146101"
# REDIRECT_URI = "http://localhost:5000/callback"
REDIRECT_URI = "https://onashimi-tavori.co.il/callback"

# --- HELPER FUNCTIONS ---
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
    filepath = args.file
    if not os.path.exists(filepath):
        return {"Error": [{"ts": "-", "usr": "System", "msg": "File not found.", "cid": "", "mid": "", "done": "0"}]}
        
    pattern = re.compile(r"^\[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(0|1)\] (.*?): (.*)$")
    parsed_data = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines[3:]:
            line = line.strip()
            if not line: continue
            
            if line.startswith("--- CHANNEL:"):
                ch = line.replace("--- CHANNEL: ", "").replace(" ---", "").strip()
                if ch not in parsed_data:
                    parsed_data[ch] = []
                continue
                
            match = pattern.match(line)
            if match:
                ts, ch, cid, mid, is_done, usr, msg = match.groups()
                if ch not in parsed_data:
                    parsed_data[ch] = []
                parsed_data[ch].append({"ts": ts, "usr": usr, "msg": msg, "cid": cid, "mid": mid, "done": is_done})
                
        return parsed_data
    except Exception as e:
        return {"Error": [{"ts": "-", "usr": "System", "msg": f"Error: {str(e)}", "cid": "", "mid": "", "done": "0"}]}

# --- OAUTH SECURITY ROUTES ---
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
    
    if not token: return "Failed to retrieve access token.", 403
    guilds = requests.get("https://discord.com/api/users/@me/guilds", headers={"Authorization": f"Bearer {token}"}).json()
    
    if any(str(g.get('id')) == str(ALLOWED_SERVER_ID) for g in guilds):
        session['authorized'] = True
        return redirect('/')
    return "Access Denied: Not a member of the required server.", 403

@app.route("/react/<channel_id>/<message_id>", methods=["POST"])
def react_to_message(channel_id, message_id):
    if not session.get('authorized'): return jsonify({"status": "error"}), 403
    headers = {"Authorization": f"Bot {args.token}"}
    emoji = urllib.parse.quote("✅") 
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
    
    response = requests.put(url, headers=headers)
    return jsonify({"status": "success" if response.status_code == 204 else "error"})

# --- DASHBOARD TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Discord Viewer</title>
    <style>
        :root { --bg-main: #2b2d31; --bg-panel: #2b2d31; --bg-header: #232428; --bg-odd: #313338; --blurple: #5865f2; --text-main: #ffffff; --text-muted: #b5bac1; --bg-input: #1e1f22; }
        body { background-color: var(--bg-main); color: var(--text-main); font-family: sans-serif; margin: 0; padding: 20px; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; gap: 15px; }
        .controls { display: flex; gap: 15px; align-items: center; }
        .search-box { background-color: var(--bg-input); color: var(--text-main); border: 1px solid var(--bg-header); padding: 10px; border-radius: 4px; }
        .refresh-btn { background-color: var(--blurple); color: white; border: none; padding: 10px 16px; border-radius: 4px; cursor: pointer; }
        .dropdown-wrapper { position: relative; }
        .drop-btn { background-color: #4f545c; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; }
        .dropdown-content { display: none; position: absolute; right: 0; background-color: var(--bg-header); padding: 12px; z-index: 100; border: 1px solid #1e1f22; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .channel-panel { background-color: var(--bg-panel); border-radius: 8px; border: 1px solid #1e1f22; overflow: hidden; }
        .channel-header { background-color: var(--bg-header); color: var(--blurple); padding: 12px; font-weight: bold; border-bottom: 2px solid #1e1f22; display: flex; align-items: center; }
        .msg-badge { background-color: var(--bg-main); font-size: 13px; padding: 3px 10px; border-radius: 12px; margin-left: 12px; }
        .table-container { max-height: 70vh; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; }
        th { background-color: var(--bg-header); color: var(--text-muted); padding: 10px; position: sticky; top: 0; }
        td { padding: 10px; vertical-align: top; }
        .is-done { opacity: 0.5; text-decoration: line-through; }
        .check-btn { background-color: #2b2d31; border: 1px solid #4f545c; color: transparent; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
        .check-btn:hover { background-color: #2ecc71; color: white; }
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>💬 {{ title }}</h1>
        <div class="controls">
            <div class="dropdown-wrapper">
                <button class="drop-btn" onclick="toggleMenu(event)">📊 Columns ▾</button>
                <div id="colDropdown" class="dropdown-content">
                    {% for channel in data.keys() %}
                    <label><input type="checkbox" class="col-toggle-checkbox" data-channel="{{ channel }}" checked onchange="updateColumnVisibility()"> # {{ channel }}</label><br>
                    {% endfor %}
                </div>
            </div>
            <label><input type="checkbox" id="showDoneToggle" onchange="applyFilters()"> Show Completed</label>
            <input type="text" id="searchInput" class="search-box" placeholder="Search...">
            <button class="refresh-btn" onclick="silentlyUpdate();">↻ Refresh</button>
        </div>
    </div>
    <div class="dashboard">
        {% for channel, messages in data.items() %}
        <div class="channel-panel" data-channel="{{ channel }}">
            <div class="channel-header"># {{ channel }} <span class="msg-badge">0</span></div>
            <div class="table-container" id="scroll-{{ loop.index }}">
                <table>
                    <thead><tr><th>Time</th><th>User</th><th>Message</th><th>Done</th></tr></thead>
                    <tbody class="message-body">
                        {% for msg in messages %}
                        <tr class="visible-row {% if msg.done == '1' %}is-done{% endif %}" id="row-{{ msg.mid }}" data-done="{{ msg.done }}">
                            <td class="time-cell" data-timestamp="{{ msg.ts }}">{{ msg.ts }}</td>
                            <td class="user-cell">{{ msg.usr }}</td>
                            <td class="msg-cell">{{ msg.msg }}</td>
                            <td class="action-cell">
                                {% if msg.done == '0' %}
                                <button class="check-btn" onclick="markDone('{{ msg.cid }}', '{{ msg.mid }}')">✔</button>
                                {% else %}
                                <span class="done-icon">✅</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endfor %}
    </div>
    <script>
        function toggleMenu(e) { e.stopPropagation(); document.getElementById("colDropdown").classList.toggle("show-menu"); }
        window.addEventListener('click', () => document.getElementById("colDropdown").classList.remove("show-menu"));
        
        function updateColumnVisibility() {
            const layout = {};
            document.querySelectorAll('.col-toggle-checkbox').forEach(box => {
                const chan = box.getAttribute('data-channel');
                layout[chan] = box.checked;
                document.querySelector(`.channel-panel[data-channel="${chan}"]`).style.display = box.checked ? '' : 'none';
            });
            sessionStorage.setItem('colLayout', JSON.stringify(layout));
        }

        function applyTimeColors(doc = document) {
            const now = new Date();
            doc.querySelectorAll('.time-cell').forEach(cell => {
                const ts = cell.getAttribute('data-timestamp');
                if(!ts || ts === "-") return;
                const d = new Date(ts.replace(' ', 'T') + 'Z');
                const timeStr = d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: false});
                cell.innerText = (now.toDateString() === d.toDateString()) ? `Today at ${timeStr}` : `${d.toISOString().split('T')[0]} ${timeStr}`;
            });
        }

        function applyFilters(doc = document) {
            const q = document.getElementById('searchInput').value.toLowerCase();
            const showDone = document.getElementById('showDoneToggle').checked;
            doc.querySelectorAll('.channel-panel').forEach(panel => {
                let cnt = 0;
                panel.querySelectorAll('.message-body tr').forEach(row => {
                    const isDone = row.getAttribute('data-done') === '1' || row.classList.contains('is-done');
                    const show = (row.innerText.toLowerCase().includes(q)) && (showDone || !isDone);
                    row.style.display = show ? '' : 'none';
                    if(show) cnt++;
                });
                const badge = panel.querySelector('.msg-badge');
                if(badge) badge.innerText = cnt;
            });
        }

        async function markDone(cid, mid) {
            const row = document.getElementById(`row-${mid}`);
            row.style.opacity = '0.5';
            const res = await fetch(`/react/${cid}/${mid}`, {method: 'POST'});
            if((await res.json()).status === 'success') {
                row.classList.add('is-done');
                row.setAttribute('data-done', '1');
                row.querySelector('.action-cell').innerHTML = '✅';
                let done = JSON.parse(localStorage.getItem('doneMsgs') || '[]');
                done.push(mid);
                localStorage.setItem('doneMsgs', JSON.stringify(done));
                applyFilters();
            }
        }

        async function silentlyUpdate() {
            try {
                const res = await fetch(window.location.href);
                const text = await res.text();
                const newDoc = new DOMParser().parseFromString(text, 'text/html');
                const scroll = {};
                document.querySelectorAll('.table-container').forEach(el => scroll[el.id] = el.scrollTop);
                
                // Keep local done-states
                let done = JSON.parse(localStorage.getItem('doneMsgs') || '[]');
                newDoc.querySelectorAll('.message-body tr').forEach(row => {
                    if(done.includes(row.id.replace('row-', ''))) {
                        row.classList.add('is-done');
                        row.setAttribute('data-done', '1');
                        row.querySelector('.action-cell').innerHTML = '✅';
                    }
                });
                
                applyTimeColors(newDoc);
                applyFilters(newDoc);
                document.querySelector('.dashboard').innerHTML = newDoc.querySelector('.dashboard').innerHTML;
                document.querySelectorAll('.table-container').forEach(el => { if(scroll[el.id]) el.scrollTop = scroll[el.id]; });
            } catch(e) {}
        }
        setInterval(silentlyUpdate, 5000);
        document.getElementById('searchInput').addEventListener('input', () => applyFilters());
        window.addEventListener('DOMContentLoaded', () => {
            applyTimeColors(); applyFilters();
            if(sessionStorage.getItem('colLayout')) {
                const layout = JSON.parse(sessionStorage.getItem('colLayout'));
                document.querySelectorAll('.col-toggle-checkbox').forEach(box => {
                    box.checked = layout[box.getAttribute('data-channel')] !== false;
                });
                updateColumnVisibility();
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    if not session.get('authorized'):
        return redirect('/login')
    return render_template_string(HTML_TEMPLATE, title=args.title, data=parse_logs())

if __name__ == "__main__":
    port = args.port
    print(f"\n🚀 Live: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)