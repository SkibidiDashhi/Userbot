# pip install telethon

import os
import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

# -------------------------------
# Load from environment variables
# -------------------------------
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_str = os.getenv("SESSION")
notify_channel_id = int(os.getenv("NOTIFY_CHANNEL_ID"))  # must be set in Sevalla env

# Use StringSession so no input() is needed
client = TelegramClient(StringSession(session_str), api_id, api_hash)

# Cache for known gift IDs
known_gifts = set()

# -------------------------------
# .data command
# -------------------------------
@client.on(events.NewMessage(pattern=r"^\.data$"))
async def data_handler(event):
    chat = await event.get_chat()

    if isinstance(chat, types.User):
        chat_type = "Private"
        name = f"{chat.first_name or ''} {chat.last_name or ''}".strip() or "N/A"
    elif isinstance(chat, types.Channel):
        chat_type = "Supergroup" if chat.megagroup else "Channel"
        name = chat.title or "N/A"
    elif isinstance(chat, types.Chat):
        chat_type = "Group"
        name = chat.title or "N/A"
    else:
        chat_type = "Unknown"
        name = getattr(chat, "title", "N/A")

    username = getattr(chat, "username", None)
    username_display = f"@{username}" if username else "N/A"

    details = (
        f"**Chat Data:**\n"
        f"📌 **Chat ID:** `{event.chat_id}`\n"
        f"📛 **Name:** {name}\n"
        f"🔗 **Username:** {username_display}\n"
        f"📂 **Type:** {chat_type}"
    )

    await event.reply(details)

# -------------------------------
# .gifts command
# -------------------------------
@client.on(events.NewMessage(pattern=r"^\.gifts$"))
async def gifts_handler(event):
    try:
        result = await client(functions.payments.GetStarGiftsRequest(hash=0))
        gifts = result.gifts
        available_gifts = [g for g in gifts if not getattr(g, "sold_out", False)]

        if not available_gifts:
            return await event.reply("No gifts are currently available for purchase.")

        lines = ["**🎁 Available Telegram Gifts:**"]
        for gift in available_gifts:
            limited = " - Limited" if getattr(gift, "limited", False) else ""
            lines.append(f"• ID: `{gift.id}` — {gift.stars} ⭐{limited}")

        await event.reply("\n".join(lines))

    except Exception as e:
        await event.reply(f"⚠️ Error fetching gifts: `{e}`")

# -------------------------------
# Background task — notify when new gifts are released
# -------------------------------
async def gift_watcher():
    global known_gifts
    await client.start()
    while True:
        try:
            result = await client(functions.payments.GetStarGiftsRequest(hash=0))
            gifts = result.gifts
            current_ids = {g.id for g in gifts if not getattr(g, "sold_out", False)}

            # Detect new gifts
            new_gifts = current_ids - known_gifts
            if new_gifts:
                lines = ["**🆕 Gifts အသစ်ထွက်ပြီဟေ့**"]
                for g in gifts:
                    if g.id in new_gifts:
                        limited = " - Limited" if getattr(g, "limited", False) else ""
                        lines.append(f"• ID: `{g.id}` — {g.stars} ⭐{limited}")
                msg = "\n".join(lines)

                await client.send_message(notify_channel_id, msg)
                known_gifts |= new_gifts

        except Exception as e:
            print(f"[Watcher Error] {e}")

        await asyncio.sleep(3)  # check every 3 seconds

# -------------------------------
# Start the userbot
# -------------------------------
async def main():
    try:
        result = await client(functions.payments.GetStarGiftsRequest(hash=0))
        gifts = result.gifts
        for g in gifts:
            if not getattr(g, "sold_out", False):
                known_gifts.add(g.id)
        print(f"[Init] Loaded {len(known_gifts)} existing gifts")
    except Exception as e:
        print(f"[Init Error] {e}")

    client.loop.create_task(gift_watcher())
    print("✅ Userbot started...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
