from telethon import TelegramClient, events

# Use the uploaded session file name (without .session)
SESSION = 'my_session'  # <-- the name of your uploaded session file
API_ID = 0              # <-- your uploaded API ID (0 if already in session)
API_HASH = ''           # <-- your uploaded API Hash (empty if already in session)

client = TelegramClient(SESSION, API_ID, API_HASH)

# Premium emoji IDs
EMOJI_IDS = [
    5283228279988309088,
    5280598054901145762,
    5280615440928758599,
    5280947338821524402,
    5280659198055572187
]

@client.on(events.NewMessage(pattern='/sendemoji'))
async def send_emoji(event):
    for emoji_id in EMOJI_IDS:
        # Placeholder
        await event.reply("😀")  # Replace with actual premium emoji logic
    await event.reply("All emojis sent!")

print("Userbot is running...")
client.start()
client.run_until_disconnected()
