import socketio

sio = socketio.Client()


@sio.event
def connect():
    print("Connected to server")
    sio.emit("join_room", {"room": "example_room"})


@sio.event
def room_message(data):
    print("Received message:", data)


@sio.event
def disconnect():
    print("Disconnected from server")


if __name__ == "__main__":
    sio.connect("http://localhost:5000")
