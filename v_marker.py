import discord
import datetime
import asyncio

# --- CONFIGURATION ---
BOT_TOKEN = "MTUxMTI2ODc0MDMzNDA5NjQ5OA.G4zV6J.cpIR4ix3rtHAYngkxaI-1MBiOIOLYNukWBumdw" 

# Add the specific channel IDs you want to scan
CHANNEL_IDS = [1477727056933556264, 1477727056933556265] 

# Array of all common Discord checkmarks to respect user reactions
TARGET_EMOJIS = ["✅", "✔️", "✔", "☑️"]

# The Cutoff: June 21, 2026 (Discord API requires UTC timezone-aware objects)
CUTOFF_DATE = datetime.datetime(2026, 6, 21, tzinfo=datetime.timezone.utc)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🚀 Logged in as {client.user}")
    print(f"📅 Targeting messages strictly older than {CUTOFF_DATE.strftime('%Y-%m-%d')}...")
    
    for channel_id in CHANNEL_IDS:
        channel = client.get_channel(channel_id)
        if not channel:
            print(f"❌ Could not find channel {channel_id}")
            continue
            
        print(f"📥 Scanning channel: #{channel.name}")
        
        async for message in channel.history(limit=None, before=CUTOFF_DATE):
            
            # 🛡️ THE FIX: Checks if ANY user has reacted with ANY valid checkmark
            is_already_marked = any(str(r.emoji) in TARGET_EMOJIS for r in message.reactions)
            
            if not is_already_marked:
                try:
                    await message.add_reaction("✅")
                    print(f"   -> ✅ Reacted to message from {message.author.display_name}")
                    
                    # Sleep to respect Discord's reaction rate limits
                    await asyncio.sleep(0.05) 
                    
                except discord.Forbidden:
                    print(f"   -> ❌ Missing permissions to react in {channel.name}")
                except discord.HTTPException as e:
                    print(f"   -> ⚠️ HTTP Exception: {e}")

    print("🎉 Finished reacting to all older messages!")
    await client.close()

if __name__ == "__main__":
    # Keeping .strip() here permanently to protect against invisible spaces!
    client.run(BOT_TOKEN.strip())