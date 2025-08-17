from telethon import TelegramClient, events
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

API_ID = int(os.getenv('API_ID'))      # Make sure API_ID is an integer
API_HASH = os.getenv('API_HASH')
SESSION = os.getenv('SESSION')

# Create the client
client = TelegramClient(SESSION, API_ID, API_HASH)

# Start the client
async def main():
    print("Userbot is running...")

    @client.on(events.NewMessage(pattern='.emoji'))
    async def send_emoji(event):
        # Example premium emoji IDs
        emoji_ids = [
            5283228279988309088,
            5280598054901145762,
            5280615440928758599,
            5280947338821524402,
            5280659198055572187
        ]

        # Send each premium emoji
        for emoji_id in emoji_ids:
            # Placeholder for testing
            await event.reply(f'\U0001F600')  
            # Real premium emojis require InputDocument objects
            # await client.send_file(event.chat_id, emoji_id)

        await event.reply("All emojis sent!")

# Run the client
with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
