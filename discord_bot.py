"""A simple Discord bot that reverses messages."""
import asyncio
import os

import discord
import httpx
import socketio
from discord import Message
from dotenv import load_dotenv

load_dotenv()

httpx_client = httpx.AsyncClient()
discord_client = discord.Client(intents=discord.Intents.default())

BOT_TOKEN_HEADER = "X-Chat-Merger-Bot-Token"

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]
CHAT_MERGER_BOT_TOKEN = os.environ["CHAT_MERGER_BOT_TOKEN"]

sio = socketio.AsyncClient()


async def connect_to_chat_merger_websocket():
    """Connect the bot to the ChatMerger websocket."""
    await sio.connect(
        "ws://localhost:8000/",
        transports=["websocket"],
        headers={BOT_TOKEN_HEADER: CHAT_MERGER_BOT_TOKEN},
    )


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    asyncio.create_task(connect_to_chat_merger_websocket())


@discord_client.event
async def on_message(message: Message) -> None:
    """Called when a message is created and sent by a user."""
    if message.author != discord_client.user:
        await httpx_client.post(
            "http://localhost:8000/bot_update",
            json={"message": message.content},
            headers={BOT_TOKEN_HEADER: CHAT_MERGER_BOT_TOKEN},
        )

        # TODO this should be initiated by ChatMerger
        await message.channel.send(message.content[::-1])


@sio.event
async def connect():
    print("Connected to server")


@sio.event
async def bot_update(data):
    print("Received message:", type(data), data)


@sio.event
async def disconnect():
    print("Disconnected from server")


if __name__ == "__main__":
    discord_client.run(DISCORD_BOT_SECRET)
