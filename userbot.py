//developer - @qunixivll
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
notify_channel_id = int(os.getenv("NOTIFY_CHANNEL_ID"))

client = TelegramClient(StringSession(session_str), api_id, api_hash)

# -------------------------------
# Cache for known gifts & gift tracking
# -------------------------------
known_gifts = set()
# Example gifts data structure
gifts_tracking = {
    "Tonnel": {
        "emoji_id": 6010231763480088256,
        "url": "https://t.me/Tonnel_Network_bot/gifts?startapp=ref_5496411145",
        "last_price": 200,
        "current_price": 250
    },
    "Portals": {
        "emoji_id": 5300744024204798740,
        "url": "https://t.me/portals/market?startapp=1gajmy",
        "last_price": 500,
        "current_price": 550
    }
}
STAR_EMOJI_ID = 5472092560522511055  # Example Telegram star emoji ID

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
# Background gift watcher — detect new gifts
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
# Command: /send {emoji_id} -> send premium emoji
# -------------------------------
@client.on(events.NewMessage(pattern=r'^/send (\d+)$'))
async def send_premium_emoji(event):
    try:
        emoji_id = int(event.pattern_match.group(1))
        text = "❤️"
        await client(functions.messages.SendMessageRequest(
            peer=event.chat_id,
            message=text,
            entities=[
                types.MessageEntityCustomEmoji(offset=0, length=1, document_id=emoji_id)
            ]
        ))
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

# -------------------------------
# Command: /send2 {emoji_id} -> formatted message with mentions
# -------------------------------
@client.on(events.NewMessage(pattern=r'^/send2 (\d+)$'))
async def send_formatted_message(event):
    try:
        emoji_id = int(event.pattern_match.group(1))
        text = "Test\n\n•❤️ @telenewsmyanmar • ❤️ @gifts_myanmar"

        entities = [
            types.MessageEntityCustomEmoji(offset=text.index('❤️'), length=1, document_id=emoji_id),
            types.MessageEntityCustomEmoji(offset=text.rindex('❤️'), length=1, document_id=emoji_id)
        ]

        await client(functions.messages.SendMessageRequest(
            peer=event.chat_id,
            message=text,
            entities=entities
        ))
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

# -------------------------------
# Gift upgrade tracker — hourly
# -------------------------------
async def gift_upgrade_tracker():
    while True:
        try:
            for gift_name, gift in gifts_tracking.items():
                old_price = gift["last_price"]
                new_price = gift["current_price"]
                emoji_id = gift["emoji_id"]

                if new_price > old_price:
                    # Price changed
                    msg = f"ဈေးပြောင်းပြီဟေ့\n❤️ ({old_price}⭐️) → ({new_price}⭐️)"
                    entities = [
                        types.MessageEntityCustomEmoji(offset=0, length=1, document_id=emoji_id),
                        types.MessageEntityCustomEmoji(offset=msg.index('⭐️'), length=1, document_id=STAR_EMOJI_ID),
                        types.MessageEntityCustomEmoji(offset=msg.rindex('⭐️'), length=1, document_id=STAR_EMOJI_ID)
                    ]
                else:
                    # Upgrade available
                    msg = f"Upgrade လို့ရပြီဟေ့\n❤️ of {gift_name} can upgrade"
                    entities = [
                        types.MessageEntityCustomEmoji(offset=0, length=1, document_id=emoji_id)
                    ]

                await client.send_message(notify_channel_id, msg, entities=entities)

                # Update last price
                gifts_tracking[gift_name]["last_price"] = new_price

        except Exception as e:
            print(f"[Upgrade Tracker Error] {e}")

        await asyncio.sleep(3)  # every 3 seconds

# -------------------------------
# Telegram URL helper
# -------------------------------
def create_telegram_url(emoji_id, url):
    return f"[{emoji_id}]({url})"  # Send as markdown

# -------------------------------
# Start the userbot
# -------------------------------
async def main():
    # Initialize known gifts
    try:
        result = await client(functions.payments.GetStarGiftsRequest(hash=0))
        gifts = result.gifts
        for g in gifts:
            if not getattr(g, "sold_out", False):
                known_gifts.add(g.id)
        print(f"[Init] Loaded {len(known_gifts)} existing gifts")
    except Exception as e:
        print(f"[Init Error] {e}")

    # Start background tasks
    client.loop.create_task(gift_watcher())
    client.loop.create_task(gift_upgrade_tracker())

    print("✅ Userbot started...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
