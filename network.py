import socket
import selectors
import json

import pygame
import engine
from level import Level
from player import Player

HOST = "127.0.0.1"
PORT = 65432


ECHO = b"echo"
GET_GAME = b"get_game"


class NetworkGame(engine.Game):
    def __init__(self, screen_size):
        super().__init__(screen_size)

    def add_object(self, name, func, *args, **kwargs):
        obj = super().add_object(name, func, *args, **kwargs)
        obj._network_sync_ = kwargs.get("network_sync", True)
        return obj

    def serialize(self):
        serialized = []
        for name, obj in self.objects.items():
            if isinstance(obj, engine.Sprite) and hasattr(obj, "_network_sync_"):
                serialized_obj = {"name": name} | {
                    attr: getattr(obj, attr)
                    for attr in ("image_path", "x", "y", "direction", "collidable")
                }
            elif isinstance(obj, engine.MultiSprite) and hasattr(obj, "_network_sync_"):
                serialized_obj = [
                    {"name": name + str(i)}
                    | {
                        attr: getattr(sprite, attr)
                        for attr in ("image_path", "x", "y", "direction", "collidable")
                    }
                    for i, sprite in enumerate(obj.sprites)
                ]
            else:
                continue
            serialized.append(serialized_obj)
        return json.dumps(serialized)

    def deserialize(self, data):
        loaded_data = json.loads(data)
        for obj in loaded_data:
            self.add_object(func=engine.Sprite, **obj)
        for name in list(self.objects).copy():
            if not hasattr(self.objects[name], "_network_sync_"):
                continue
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
        self.game.main()


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
        self.game.screen.fill("black")
        self.game.deserialize(self.request(GET_GAME))

    def main(self):
        self.game.main(self.update)

    def create_player(self):
        self.game.add_object(
            "player",
            Player,
            image_path="images/player1.png",
            x=self.game.width / 2 + 100,
            y=200,
            controls={
                "left": pygame.K_LEFT,
                "right": pygame.K_RIGHT,
                "jump": pygame.K_UP,
                "shoot": pygame.K_DOWN,
            },
            move_acceleration=4,
            friction=0.25,
            jump_acceleration=24,
            gravity=2,
        )
