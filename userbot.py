from telethon import TelegramClient, events
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION = os.getenv('SESSION')

client = TelegramClient(SESSION, API_ID, API_HASH)

# Premium emoji IDs (replace with your own)
EMOJI_IDS = [
    5283228279988309088,
    5280598054901145762,
    5280615440928758599,
    5280947338821524402,
    5280659198055572187
]

@client.on(events.NewMessage(pattern='/sendemoji'))
async def send_emoji(event):
    """
    Just send emojis in the same chat where the command is used.
    """
    for emoji_id in EMOJI_IDS:
        # Placeholder for testing
        await event.reply("😀")  # Replace with actual premium emoji sending if available
        # For real premium emojis:
        # await client.send_file(event.chat_id, emoji_id)

    await event.reply("All emojis sent!")

print("Userbot is running...")
client.start()
client.run_until_disconnected()
