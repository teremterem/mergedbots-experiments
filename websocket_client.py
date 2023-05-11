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
    await sio.connect("http://127.0.0.1:5000")
    await sio.wait()


if __name__ == "__main__":
    asyncio.run(main())
