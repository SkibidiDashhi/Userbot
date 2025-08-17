from telethon import TelegramClient, events

# Use the uploaded session file name (without .session)
SESSION = '1BVtsOG0Buwaq2R-8-WfZj5D96fTultnzzU0t0gg4W4WcKjYsAMGGWrFr6WySjBo0UyU9m85LlKFJcVZAyzhlhnAkYl27JsmA9Wh6tI2GlZaRj_rQl4snW3wYQsg5O3qoVQBLaytJPyKsN6RUYEh0bOh_rGdXEwVeK1nduBItxmtBnaAZkv_IQ6w3GI8lCQDKR06EHxXCB6pFMLoGmroPVUw1lINwmVKft5Wwrx171q_TYHuiNqXjruZhMsXsdxbew50gi95MZyTnu9DtA9uKg5Q_fpMdUUe97tprQQLz8Vd2zh6HJ_Zk9J5-IPbr4Psicz5h7FTuUP22gdLs243ngTEA66-PJzU='  # <-- the name of your uploaded session file
API_ID = 25301360             # <-- your uploaded API ID (0 if already in session)
API_HASH = 'a2de608dfb82a36ff0376e072520445f'           # <-- your uploaded API Hash (empty if already in session)

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
