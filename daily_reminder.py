import discord
from discord.ext import commands, tasks
import datetime
import sys

# 🌍 Timezone Upgrade: Automatically handles Israel Summer/Winter time
try:
    from zoneinfo import ZoneInfo
    israel_tz = ZoneInfo("Asia/Jerusalem")
except ImportError:
    # Fallback just in case you are on an ancient Python version
    israel_tz = datetime.timezone(datetime.timedelta(hours=3))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 🎯 CHANNELS ---
SAHI_CHANNEL = 1477727056664985833
DOCH1_CHANNEL = 1477727056664985831
MI_CHANNEL = 1477727056664985834

# --- ⏰ TIMES ---
TIME_SAHI = datetime.time(hour=6, minute=0, second=0, tzinfo=israel_tz)
TIME_DOCH1 = datetime.time(hour=8, minute=0, second=0, tzinfo=israel_tz)
TIME_MI_EVENING = datetime.time(hour=20, minute=0, second=0, tzinfo=israel_tz)
TIME_MI_THU = datetime.time(hour=15, minute=30, second=0, tzinfo=israel_tz)

# ==========================================================
# 1. SAHI REMINDER (Monday - Thursday @ 06:00)
# ==========================================================
@tasks.loop(time=TIME_SAHI)
async def task_sahi():
    # weekday(): 0=Mon, 1=Tue, 2=Wed, 3=Thu
    if datetime.datetime.now(israel_tz).weekday() in [0, 1, 2, 3]:
        channel = bot.get_channel(SAHI_CHANNEL)
        if channel:
            await channel.send("סחי!")
            print("✅ [Reminder Bot] Sent Sahi reminder.")

# ==========================================================
# 2. DOCH 1 (Sunday @ 08:00)
# ==========================================================
@tasks.loop(time=TIME_DOCH1)
async def task_doch1():
    # weekday(): 6=Sun
    if datetime.datetime.now(israel_tz).weekday() == 6:
        channel = bot.get_channel(DOCH1_CHANNEL)
        if channel:
            await channel.send("@everyone דוח 1!!!!!!")
            print("✅ [Reminder Bot] Sent Doch 1 reminder.")

# ==========================================================
# 3. M.I. EVENING (Sunday - Wednesday @ 20:00)
# ==========================================================
@tasks.loop(time=TIME_MI_EVENING)
async def task_mi_evening():
    # weekday(): 6=Sun, 0=Mon, 1=Tue, 2=Wed
    if datetime.datetime.now(israel_tz).weekday() in [6, 0, 1, 2]:
        channel = bot.get_channel(MI_CHANNEL)
        if channel:
            await channel.send("זמן להכין את המ.י.!")
            print("✅ [Reminder Bot] Sent Evening M.I. reminder.")

# ==========================================================
# 4. M.I. THURSDAY (Thursday @ 15:30)
# ==========================================================
@tasks.loop(time=TIME_MI_THU)
async def task_mi_thursday():
    # weekday(): 3=Thu
    if datetime.datetime.now(israel_tz).weekday() == 3:
        channel = bot.get_channel(MI_CHANNEL)
        if channel:
            await channel.send("זמן להכין את המ.י.!")
            print("✅ [Reminder Bot] Sent Thursday M.I. reminder.")

# ==========================================================
# 🚀 BOT STARTUP
# ==========================================================
@bot.event
async def on_ready():
    print(f"☀️ [Reminder Bot] Logged in as {bot.user}. Starting schedules...")
    if not task_sahi.is_running(): task_sahi.start()
    if not task_doch1.is_running(): task_doch1.start()
    if not task_mi_evening.is_running(): task_mi_evening.start()
    if not task_mi_thursday.is_running(): task_mi_thursday.start()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
        bot.run(TOKEN)
    else:
        print("❌ [Reminder Bot] Please provide a bot token.")