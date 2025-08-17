# pip install telethon

import os
import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

# -------------------------------
# Environment variables (robust)
# -------------------------------
api_id_str = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_str = os.getenv("SESSION")
# Accept either -100... numeric ID or @username; don't cast to int to avoid TypeError
notify_target = os.getenv("NOTIFY_CHANNEL_ID")  # optional

if not api_id_str or not api_hash or not session_str:
    raise RuntimeError("Missing required env vars: API_ID, API_HASH, SESSION")

api_id = int(api_id_str)

# Use StringSession so no interactive login is needed
client = TelegramClient(StringSession(session_str), api_id, api_hash)

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
# .gifts command — shows available Telegram gifts (with emoji & title)
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
            emoji = getattr(gift, "emoji", "") or ""
            title = getattr(gift, "title", "Gift")
            stars = getattr(gift, "stars", "?")
            gid = getattr(gift, "id", "?")
            lines.append(f"• {emoji} **{title}** — `{gid}` — {stars} ⭐{limited}")

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
            current_ids = {getattr(g, "id", None) for g in gifts if not getattr(g, "sold_out", False)}
            current_ids.discard(None)

            # Detect new gifts
            new_gifts = current_ids - known_gifts
            if new_gifts:
                lines = ["**🆕 New Telegram Gifts Released!**"]
                for g in gifts:
                    if getattr(g, "id", None) in new_gifts:
                        limited = " - Limited" if getattr(g, "limited", False) else ""
                        emoji = getattr(g, "emoji", "") or ""
                        title = getattr(g, "title", "Gift")
                        stars = getattr(g, "stars", "?")
                        gid = getattr(g, "id", "?")
                        lines.append(f"• {emoji} **{title}** — `{gid}` — {stars} ⭐{limited}")
                msg = "\n".join(lines)

                # Only send if notify_target is set
                if notify_target:
                    await client.send_message(notify_target, msg)

                known_gifts |= new_gifts

        except Exception as e:
            print(f"[Watcher Error] {e}")

        await asyncio.sleep(600)  # check every 10 minutes

# -------------------------------
# Start the userbot
# -------------------------------
async def main():
    try:
        result = await client(functions.payments.GetStarGiftsRequest(hash=0))
        gifts = result.gifts
        for g in gifts:
            if not getattr(g, "sold_out", False):
                gid = getattr(g, "id", None)
                if gid is not None:
                    known_gifts.add(gid)
        print(f"[Init] Loaded {len(known_gifts)} existing gifts")
    except Exception as e:
        print(f"[Init Error] {e}")

    client.loop.create_task(gift_watcher())
    print("✅ Userbot started...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
