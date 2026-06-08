import discord
import argparse
import datetime
import json
import re
import os

parser = argparse.ArgumentParser()
parser.add_argument("--user_channels", default="")
parser.add_argument("--standard_channels", default="")
parser.add_argument("--daily_channels", default="")
parser.add_argument("--ui_categories", default="{}")
parser.add_argument("-f", "--file", default="filtered_export.txt")
parser.add_argument("--token", required=True)
args = parser.parse_args()

def parse_id_list(arg_str):
    return [int(x) for x in arg_str.split(",") if x.strip()]

user_channels = parse_id_list(args.user_channels)
standard_channels = parse_id_list(args.standard_channels)
daily_channels = parse_id_list(args.daily_channels)

ui_map = {int(k): v for k, v in json.loads(args.ui_categories).items()}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

client = discord.Client(intents=intents)

# 🛡️ THE FIX: Array of all common Discord checkmarks and unicode variations
TARGET_EMOJIS = ["✅", "✔️", "✔", "☑️"]

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    all_channel_ids = user_channels + standard_channels + daily_channels
    
    temp_filepath = args.file + ".tmp"
    
    with open(temp_filepath, "w", encoding="utf-8") as file:
        file.write("Multi-Channel Export Logs\n")
        file.write("Dynamic Expiration Engine Active.\n")
        file.write("-" * 65 + "\n")
        
        if not all_channel_ids:
            print("❌ No channels provided to sync.")
            await client.close()
            return

        for channel_id in all_channel_ids:
            channel = client.get_channel(channel_id)
            if channel is None:
                print(f"❌ Could not find channel ID {channel_id}. Skipping...")
                continue
            
            cat_name = ui_map.get(channel_id, "כללי")
            file.write(f"--- CATEGORY: {cat_name} | CHANNEL: {channel.name} ---\n")
            
            is_expiring = channel_id in daily_channels
            requires_hashtag = channel_id in user_channels
            
            print(f"📥 Exporting channel: #{channel.name}...")
            
            history_iterator = channel.history(limit=None, oldest_first=True)
            
            async for message in history_iterator:
                if requires_hashtag and "#" not in message.content:
                    continue
                
                if is_expiring:
                    text = message.content.lower()
                    
                    d_match = re.search(r'\b(\d+)d\b', text)
                    h_match = re.search(r'\b(\d+)h\b', text)
                    m_match = re.search(r'\b(\d+)m\b', text)
                    
                    if d_match or h_match or m_match:
                        days = int(d_match.group(1)) if d_match else 0
                        hours = int(h_match.group(1)) if h_match else 0
                        minutes = int(m_match.group(1)) if m_match else 0
                        delta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
                    else:
                        delta = datetime.timedelta(hours=24)
                        
                    expiration_time = message.created_at + delta
                    
                    if discord.utils.utcnow() > expiration_time:
                        continue 
                
                # 🛡️ THE FIX: Now checks against the entire list of emojis
                has_target_reaction = any(str(r.emoji) in TARGET_EMOJIS for r in message.reactions)
                is_done = "1" if has_target_reaction else "0"
                
                author_name = message.author.nick if hasattr(message.author, 'nick') and message.author.nick else message.author.display_name
                
                log_line = f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] [{channel.name}] [{channel.id}] [{message.id}] [{is_done}] {author_name}: {message.clean_content}\n"
                file.write(log_line)
                
                if message.attachments:
                    for attachment in message.attachments:
                        file.write(f"   -> Attachment: {attachment.url}\n")
                            
    os.replace(temp_filepath, args.file)
    print("🎉 All channels successfully synced and file swapped atomically.")
    await client.close()

client.run(args.token)