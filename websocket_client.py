import asyncio

import socketio

sio = socketio.AsyncClient()


@sio.event
async def connect():
    print("Connected to server")
    await sio.emit("join_room", {"room": "example_room"})


@sio.event
async def room_message(data):
    print("Received message:", data)


@sio.event
async def disconnect():
    print("Disconnected from server")


async def main():
    await sio.connect(
        "ws://localhost:8000/",
        transports=["websocket"],
        headers={"X-Chat-Merger-Bot-Token": "replace_with_real_token"},  # TODO replace with real token
    )
    await sio.wait()


if __name__ == "__main__":
    asyncio.run(main())
