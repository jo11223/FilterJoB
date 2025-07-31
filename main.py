
import re
import requests
import nest_asyncio
import asyncio
from telethon import TelegramClient, events
import os
from dotenv import load_dotenv


load_dotenv()
nest_asyncio.apply()

# === CONFIG ===

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_NAME = os.getenv("SESSION_NAME")
DEST_GROUP_USERNAME = os.getenv("DEST_GROUP_USERNAME")
SOURCE_CHANNELS = os.getenv("SOURCE_CHANNELS").split(",")
# === KEYWORDS TO MATCH ===
KEYWORDS = [
    "python", "javascript", "react", "node",
    "flutter", "Frontend", "Backend", "Fullstack",
    "devops", "Computer science"
]
pattern = re.compile(r"\b(" + "|".join(KEYWORDS) + r")\b", flags=re.IGNORECASE)

def is_match(text):
    return bool(text and pattern.search(text))

# === Send message via BOT
def send_via_bot(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": DEST_GROUP_USERNAME,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print("⚠️ Failed to send via bot:", response.text)
    else:
        print("✅ Sent:", text[:60])

# === Telegram Client Setup ===
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def main():
    await client.start()
    me = await client.get_me()
    print(f"✅ Logged in as {me.first_name} (@{me.username})")

    # Log destination group info
    destination_entity = await client.get_entity(DEST_GROUP_USERNAME)
    print(f"✅ Destination group ID: {destination_entity.id}")

    # Backfill last messages for each source channel
    for channel in SOURCE_CHANNELS:
        print(f"📥 Checking last 10 messages from {channel}...")
        count = 0
        async for msg in client.iter_messages(channel, limit=40):
            if is_match(msg.raw_text):
                send_via_bot(msg.raw_text)
                count += 1
        print(f"✅ Backfill complete for {channel}. {count} messages matched.")

    # Monitor new messages for each source channel
    @client.on(events.NewMessage(chats=SOURCE_CHANNELS))
    async def handler(event):
        text = event.raw_text
        if is_match(text):
            print(f"🔥 Live match from {event.chat.username or event.chat_id}: {text[:70]}")
            send_via_bot(text)

    print(f"🚨 Monitoring started for: {', '.join(SOURCE_CHANNELS)}")
    await client.run_until_disconnected()

# === Run Script ===
if __name__ == "__main__":
    asyncio.run(main())
