# pip install telethon

import asyncio
from telethon import TelegramClient, events, functions, types

# Your Telegram API credentials
api_id = 29489874                # <- replace with your own
api_hash = "db43f929f9eb42017a9b3c7e149036d9" # <- replace with your own
session_name = "my_userbot"

# Channel ID where notifications will be sent (replace with your channel/group ID)
notify_channel_id = -1001929013406

client = TelegramClient(session_name, api_id, api_hash)

# Cache for known gift IDs
known_gifts = set()

# -------------------------------
# .data command — works for everyone
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
# .gifts command — shows available Telegram gifts purchasable with Stars
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
                lines = ["**🆕 New Telegram Gifts Released!**"]
                for g in gifts:
                    if g.id in new_gifts:
                        limited = " - Limited" if getattr(g, "limited", False) else ""
                        lines.append(f"• ID: `{g.id}` — {g.stars} ⭐{limited}")
                msg = "\n".join(lines)

                # Send notification to the channel
                await client.send_message(notify_channel_id, msg)

                # Update cache
                known_gifts |= new_gifts

        except Exception as e:
            print(f"[Watcher Error] {e}")

        await asyncio.sleep(600)  # check every 10 minutes

# -------------------------------
# Start the userbot
# -------------------------------
async def main():
    # Load initial gifts into cache
    try:
        result = await client(functions.payments.GetStarGiftsRequest(hash=0))
        gifts = result.gifts
        for g in gifts:
            if not getattr(g, "sold_out", False):
                known_gifts.add(g.id)
        print(f"[Init] Loaded {len(known_gifts)} existing gifts")
    except Exception as e:
        print(f"[Init Error] {e}")

    # Run background watcher
    client.loop.create_task(gift_watcher())
    print("Userbot started...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())