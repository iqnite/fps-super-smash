import socket
import selectors
import json
import engine
from level import Level

HOST = "127.0.0.1"
PORT = 65432


ECHO = b"echo"
GET_GAME = b"get_game"


class NetworkGame(engine.Game):
    def __init__(self, screen_size):
        super().__init__(screen_size)

    def serialize(self):
        serialized = []
        for name, obj in self.objects.items():
            if isinstance(obj, engine.Sprite):
                serialized_obj = {"name": name} | {
                    attr: getattr(obj, attr)
                    for attr in ("image_path", "x", "y", "direction", "collidable")
                }
            elif isinstance(obj, engine.MultiSprite):
                serialized_obj = {"name": name} | {
                    attr: getattr(sprite, attr)
                    for sprite in obj.sprites
                    for attr in ("image_path", "x", "y", "direction", "collidable")
                }
            else:
                continue
            serialized.append(serialized_obj)
        return json.dumps(serialized)

    def deserialize(self, data):
        loaded_data = json.loads(data)
        for obj in loaded_data:
            self.add_object(func=engine.Sprite, **obj)
        for name in list(self.objects).copy():
            for loaded_obj in loaded_data:
                if loaded_obj["name"] == name:
                    break
            else:
                del self.objects[name]


class Server:
    def __init__(self):
        self.server: socket.socket
        self.clients: list[socket.socket] = []
        self.online: bool = False
        self.accepts_new_clients: bool = False
        self.selector = selectors.DefaultSelector()
        self.game: NetworkGame = NetworkGame((0, 0))

    def start_server(self):
        self.online = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen()
        self.server.setblocking(False)
        self.selector.register(self.server, selectors.EVENT_READ)
        self.online = True
        self.event_loop()

    def stop_server(self):
        self.online = False
        self.server.close()

    def event_loop(self):
        try:
            while True:
                events = self.selector.select()
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        finally:
            self.stop_server()
            self.selector.close()

    def accept_wrapper(self, sock):
        connection, _ = sock.accept()
        connection.setblocking(False)
        self.clients.append(connection)
        self.selector.register(connection, selectors.EVENT_READ)

    def service_connection(self, key, mask):
        sock: socket.socket = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data == ECHO:
                data.outb += recv_data
            elif recv_data == GET_GAME:
                data.outb += self.game.serialize().encode()
            elif not recv_data:
                self.selector.unregister(sock)
                sock.close()
            else:
                data.outb += b"Unknown command"
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

    def start_game(self):
        self.game.add_object(
            "level",
            Level.load,
            pos_filepath="level.csv",
            image_filepath="images/level/{}.png",
            y_velocity=1,
            common_sprite_args={"teleport": {"+y": {720: 200}}},
        )


class Client:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client: socket.socket
        self.game: NetworkGame = NetworkGame((0, 0))

    def request(self, data: str | bytes):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.client:
            self.client.connect((self.server_host, self.server_port))
            self.client.sendall(data.encode() if isinstance(data, str) else data)
            data = self.client.recv(1024)
        return data

    def update(self):
        self.game.deserialize(self.request(GET_GAME))

    def main(self):
        self.game.main(self.update)
