import socket
import selectors
import json
import threading
from types import SimpleNamespace

import psutil
import engine
from player import Player, get_controls

PORT = 65432


ECHO = b"echo"
JOIN_GAME = b"join_game:"
GET_FRAME = b"get_frame"
SEND_CONTROLS = b"controls:"


def get_wlan_ip():
    # Credit to Paul
    for interface, addrs in psutil.net_if_addrs().items():
        if any(
            name in interface
            for name in ("Wi-Fi", "wlan", "wlp", "wlx", "wlan0", "WLAN", "WiFi")
        ):  # Adjust for your OS naming
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4 address
                    return addr.address
    return None


class Server:
    def __init__(self):
        self.server: socket.socket
        self.players: dict[str, Player] = {}
        self.connections: list[socket.socket] = []
        self.online: bool = False
        self.accepts_new_clients: bool = False
        self.selector = selectors.DefaultSelector()
        self.game: engine.Game = engine.Game((0, 0))

    def __enter__(self):
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_server()

    def start_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((get_wlan_ip(), PORT))
        self.server.listen()
        self.server.setblocking(False)
        self.selector.register(self.server, selectors.EVENT_READ, data=None)
        self.online = True
        print("Server started on", self.server.getsockname())

    def stop_server(self):
        self.online = False
        self.server.close()
        self.selector.close()

    def main(self):
        self.event_thread = threading.Thread(target=self.event_loop)
        self.event_thread.start()
        self.game.main(self.game_loop)

    def event_loop(self):
        while self.online:
            events = self.selector.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    self.accept_wrapper(key.fileobj)
                else:
                    self.service_connection(key, mask)

    def accept_wrapper(self, sock):
        try:
            connection, address = sock.accept()
        except OSError:
            return
        print("Accepted connection from", address)
        connection.setblocking(False)
        data = SimpleNamespace(addr=address, inb=b"", outb=b"")
        self.connections.append(connection)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(connection, events, data=data)

    def service_connection(self, key, mask):
        sock: socket.socket = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            try:
                recv_data = sock.recv(1024)  # Should be ready to read
            except ConnectionResetError:
                recv_data = b""
            if recv_data == ECHO:
                data.outb += recv_data
            elif recv_data.startswith(JOIN_GAME):
                self.add_player(data.addr, recv_data[len(JOIN_GAME) :].decode())
                data.outb += b"OK"
            elif recv_data == GET_FRAME:
                data.outb += self.serialize_game().encode()
            elif recv_data.startswith(SEND_CONTROLS):
                self.apply_controls(data.addr, recv_data[len(SEND_CONTROLS) :])
                data.outb += b"OK"
            elif not recv_data:
                self.connections.remove(sock)
                del self.players[f"player{data.addr}"]
                self.selector.unregister(sock)
                sock.close()
                print("Closed connection to", data.addr)
            else:
                data.outb += b"Unknown command"
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

    def serialize_game(self):
        return json.dumps(
            {
                f"{name}{i}": {
                    "image_path": sprite.image_path,
                    "x": sprite.x,
                    "y": sprite.y,
                    "direction": sprite.direction,
                }
                for name, obj in self.game.objects.items()
                for i, sprite in enumerate(getattr(obj, "sprites", [obj]))
            }
        )
    
    def game_loop(self):
        self.game.screen.fill("black")
        self.players["player0"].keyboard_control()

    def apply_controls(self, client, data: bytes):
        self.players[f"player{client}"].controls = json.loads(data)

    def add_player(self, client, image_path):
        player_str = f"player{client}"
        player = self.game.add_object(
            player_str,
            Player,
            image_path=image_path,
            x=self.game.width / 2 + 100,
            y=200,
            move_acceleration=4,
            friction=0.25,
            jump_acceleration=24,
            gravity=2,
        )
        self.players[player_str] = player
        return player


class Client:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client: socket.socket
        self.game: engine.Game = engine.Game((0, 0))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(5)
        self.client.connect((self.server_host, self.server_port))

    def disconnect(self):
        self.client.close()

    def request(self, data: str | bytes):
        self.client.sendall(data.encode() if isinstance(data, str) else data)
        data = self.client.recv(4096)
        return data

    def main(self):
        self.game.main(self.sync)

    def sync(self):
        next_draw = self.request(GET_FRAME).decode()
        self.game.screen.fill("black")
        self.game.objects.clear()
        for name, object in json.loads(next_draw).items():
            self.game.add_object(name, engine.Sprite, **object)
        self.request(SEND_CONTROLS + json.dumps(get_controls()).encode())
