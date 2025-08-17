# pip install telethon

import asyncio
import os
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

# ================================
# Load credentials from environment
# ================================
api_id = int(os.environ.get("API_ID", "0"))
api_hash = os.environ.get("API_HASH", "")
session_string = os.environ.get("SESSION", "")

# Channel/group ID where notifications will be sent
# Example: -1001234567890  (for channels/supergroups)
# Or "me" for Saved Messages
notify_channel_id = os.environ.get("NOTIFY_CHANNEL_ID", "me")

client = TelegramClient(StringSession(session_string), api_id, api_hash)

# Cache for known gift IDs
known_gifts = set()

# Premium emoji IDs
PREMIUM_EMOJIS = [
    5283228279988309088,
    5280598054901145762,
    5280615440928758599,
    5280947338821524402,
    5280659198055572187,
    5280774333243873175,
    5283080528818360566,
    5280769763398671636,
    5280651583078556009,
    5280922999241859582,
    5451905784734574339,
]

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
        for i, gift in enumerate(available_gifts):
            limited = " - Limited" if getattr(gift, "limited", False) else ""
            emoji_id = PREMIUM_EMOJIS[i % len(PREMIUM_EMOJIS)]
            custom_emoji = f"<emoji id={emoji_id}>💎</emoji>"

            lines.append(
                f"{custom_emoji} **{gift.title or 'Gift'}** — `{gift.id}` — {gift.stars} ⭐{limited}"
            )

        await event.reply("\n".join(lines), parse_mode="html")

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
                for i, g in enumerate(gifts):
                    if g.id in new_gifts:
                        limited = " - Limited" if getattr(g, "limited", False) else ""
                        emoji_id = PREMIUM_EMOJIS[i % len(PREMIUM_EMOJIS)]
                        custom_emoji = f"<emoji id={emoji_id}>💎</emoji>"
                        lines.append(
                            f"{custom_emoji} **{g.title or 'Gift'}** — `{g.id}` — {g.stars} ⭐{limited}"
                        )
                msg = "\n".join(lines)

                await client.send_message(notify_channel_id, msg, parse_mode="html")

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
                known_gifts.add(g.id)
        print(f"[Init] Loaded {len(known_gifts)} existing gifts")
    except Exception as e:
        print(f"[Init Error] {e}")

    client.loop.create_task(gift_watcher())
    print("Userbot started...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
