import socket
import selectors
import json
import threading
from types import SimpleNamespace

import psutil
import pygame
import engine
from level import Level
from player import Player, get_controls

PORT = 65432


OK = b"OK"
UNKNOWN = b"unknown"
ECHO = b"echo"
JOIN_GAME = b"join_game:"
GET_FRAME = b"get_frame"
SEND_CONTROLS = b"controls:"
WAITING = b"waiting"
GAME_ALREADY_STARTED = b"game_already_started"


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
        self.players: dict[str, Player | None] = {"server": None}
        self.connections: list[socket.socket] = []
        self.online: bool = False
        self.selector = selectors.DefaultSelector()
        self.game: engine.Game = engine.Game((0, 0), "images/Menu/Background.png")
        self.waiting: bool = True

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
        print("Server stopped.")

    def main(self):
        self.event_thread = threading.Thread(target=self.event_loop)
        self.event_thread.start()
        self.game.add_object("lobby", ServerLobbyMenu, server=self)
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
                if self.waiting:
                    self.players[data.addr] = None
                    data.outb += OK
                else:
                    data.outb += GAME_ALREADY_STARTED
            elif recv_data == GET_FRAME:
                if self.waiting:
                    data.outb += WAITING
                else:
                    data.outb += self.serialize_game().encode()
            elif recv_data.startswith(SEND_CONTROLS):
                self.apply_controls(data.addr, recv_data[len(SEND_CONTROLS) :])
                data.outb += OK
            elif not recv_data:
                if data.addr in self.players:
                    del self.players[data.addr]
                self.connections.remove(sock)
                self.selector.unregister(sock)
                sock.close()
                print("Closed connection to", data.addr)
            else:
                data.outb += UNKNOWN
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

    def serialize_game(self):
        return json.dumps(
            {
                f"{n}{i}": {
                    "image_path": s.image_path,
                    "x": round(s.x),
                    "y": round(s.y),
                    "direction": s.direction,
                }
                for n, o in self.game.objects.items()
                for i, s in enumerate(getattr(o, "sprites", [o]))
            },
            separators=(",", ":"),
        )

    def game_loop(self):
        if self.waiting:
            ip_text = pygame.font.Font("images/Anta-Regular.ttf", 74).render(
                f"IP Address: {self.server.getsockname()[0]}", True, "white"
            )
            self.game.screen.blit(ip_text, (100, self.game.height / 2))
            return
        if (server_player := self.players["server"]) is not None:
            server_player.keyboard_control()

    def apply_controls(self, client, data: bytes):
        if (player := self.players[client]) is not None:
            player.controls = json.loads(data)


class Client:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client: socket.socket
        self.game: engine.Game = engine.Game((0, 0), "images/Menu/Background.png")

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
        data = self.client.recv(8138)
        return data

    def main(self):
        if (
            self.request(JOIN_GAME + f"images/player{0}.png".encode())
            == GAME_ALREADY_STARTED
        ):
            print("Game already started, please wait for the server to finish.")
            return
        self.next_draw = None
        self.controls = None
        self.sync_thread = threading.Thread(target=self.sync)
        self.sync_thread.start()
        self.game.main(self.game_loop)

    def sync(self):
        while self.game.running:
            self.next_draw = self.request(GET_FRAME)
            if self.controls is not None:
                self.request(SEND_CONTROLS + self.controls)

    def game_loop(self):
        if self.next_draw == WAITING:
            waiting_text = pygame.font.Font("images/Anta-Regular.ttf", 74).render(
                "Waiting for players...", True, "white"
            )
            self.game.screen.blit(waiting_text, (100, self.game.height / 2))
            return
        self.controls = json.dumps(get_controls()).encode()
        if self.next_draw is not None:
            self.game.screen.fill("black")
            self.game.objects.clear()
            for name, object in json.loads(self.next_draw.decode()).items():
                self.game.add_object(name, engine.Sprite, **object)


class ServerLobbyMenu(engine.Menu):
    button_distance = 100

    def __init__(self, *args, server: Server, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = server

    @engine.button("images/Menu/Start.png")
    def start(self):
        self.game.remove_object(self)
        self.game.add_object(
            "level",
            Level.load,
            pos_filepath="level.csv",
            image_filepath="images/level/{}.png",
            y_velocity=1,
            common_sprite_args={"teleport": {"+y": {1080: -440}}},
        )
        for i, id in enumerate(self.server.players):
            self.server.players[id] = self.game.add_object(
                f"player{i}",
                Player,
                image_path=f"images/player{i % 2}.png",
                x=self.game.width / 2 + 100 * int(i),
                y=200,
                move_acceleration=4,
                friction=0.25,
                jump_acceleration=24,
                gravity=2,
            )
        self.game.background = None
        self.server.waiting = False

    @engine.button("images/Menu/Cancel.png")
    def exit(self):
        self.game.running = False
