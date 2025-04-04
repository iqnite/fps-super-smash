import socket
import json
import threading
import time
import pickle  # For binary serialization
import zlib  # For compression

import psutil
import pygame
import engine
from level import Level
from player import Player, get_controls

PORT = 65432

# Protocol constants
OK = b"OK"
UNKNOWN = b"unknown"
ECHO = b"echo"
JOIN_GAME = b"join_game:"
GET_FRAME = b"get_frame"
SEND_CONTROLS = b"controls:"
WAITING = b"waiting"
GAME_ALREADY_STARTED = b"game_already_started"

# UDP specific constants
BUFFER_SIZE = 65507  # Max UDP packet size
BROADCAST_INTERVAL = 1 / 60  # 60fps broadcast rate for smoother updates
MAX_PACKET_AGE = 1.0  # Discard packets older than this
USE_BINARY_PROTOCOL = True  # Use more efficient binary serialization
USE_COMPRESSION = True  # Compress network data


def get_wlan_ip():
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
        self.players: dict[tuple, Player | None] = {}
        self.client_addresses = []
        self.online: bool = False
        self.game: engine.Game = engine.Game((0, 0), "images/Menu/Background.png")
        self.waiting: bool = True
        self.last_broadcast = 0
        self.sequence_number = 0
        self.last_game_state = {}  # Store previous state for delta comparison

    def __enter__(self):
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_server()

    def start_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((get_wlan_ip(), PORT))
        self.online = True
        print("UDP Server started on", self.server.getsockname())

    def stop_server(self):
        self.online = False
        self.server.close()
        print("Server stopped.")

    def main(self):
        self.event_thread = threading.Thread(target=self.event_loop)
        self.event_thread.start()
        self.game.add_object("lobby", ServerLobbyMenu, server=self)
        self.players[self.server.getsockname()] = None
        self.game.main(self.game_loop)

    def event_loop(self):
        self.server.setblocking(False)
        while self.online:
            # Handle incoming messages
            try:
                self.process_incoming_messages()
            except (BlockingIOError, ConnectionResetError):
                pass

            # Broadcast game state periodically
            current_time = time.time()
            if (
                current_time - self.last_broadcast > BROADCAST_INTERVAL
                and not self.waiting
                and self.client_addresses  # Only broadcast if clients are connected
            ):
                self.broadcast_game_state()
                self.last_broadcast = current_time

            # Shorter sleep for more responsive server
            time.sleep(0.0005)

    def process_incoming_messages(self):
        data, client_address = self.server.recvfrom(BUFFER_SIZE)

        if data.startswith(JOIN_GAME):
            if self.waiting:
                if client_address not in self.client_addresses:
                    self.client_addresses.append(client_address)
                self.players[client_address] = None
                self.server.sendto(OK, client_address)
            else:
                self.server.sendto(GAME_ALREADY_STARTED, client_address)

        elif data.startswith(SEND_CONTROLS):
            self.apply_controls(client_address, data[len(SEND_CONTROLS) :])
            # No need to send OK for UDP

        elif data == GET_FRAME:
            # Legacy support for clients polling for game state
            if self.waiting:
                self.server.sendto(WAITING, client_address)
            else:
                self.server.sendto(self.serialize_game(), client_address)

        elif data == ECHO:
            self.server.sendto(data, client_address)

        else:
            self.server.sendto(UNKNOWN, client_address)

    def broadcast_game_state(self):
        """Send game state to all connected clients"""
        game_state = self.serialize_game()
        self.sequence_number += 1

        if USE_BINARY_PROTOCOL:
            # Binary format: (b'SEQ', sequence_number, game_state_bytes)
            data = pickle.dumps(("SEQ", self.sequence_number, game_state))
            if USE_COMPRESSION:
                data = zlib.compress(data, level=1)  # Use fast compression (level 1)
        else:
            # Legacy text format
            seq_header = f"seq:{self.sequence_number}:".encode()
            data = (
                seq_header + game_state.encode()
                if isinstance(game_state, str)
                else seq_header + game_state
            )

        # Send to all clients with error handling
        for client_address in self.client_addresses[
            :
        ]:  # Copy list to allow modification during iteration
            try:
                self.server.sendto(data, client_address)
            except Exception as e:
                print(f"Error sending to {client_address}: {e}")

    def serialize_game(self):
        """Create a compact representation of the game state"""
        # Collect current game state
        current_state = {
            f"{n}{i}": {
                "p": s.image_path,  # Shorter key names to reduce size
                "x": round(s.x),
                "y": round(s.y),
                "d": s.direction,
            }
            for n, o in self.game.objects.items()
            for i, s in enumerate(getattr(o, "sprites", [o]))
        }

        if USE_BINARY_PROTOCOL:
            return pickle.dumps(current_state)
        else:
            # Legacy JSON format
            return json.dumps(current_state, separators=(",", ":")).encode()

    def game_loop(self):
        if self.waiting:
            ip_text = pygame.font.Font("images/Anta-Regular.ttf", 74).render(
                f"IP Address: {self.server.getsockname()[0]}", True, "white"
            )
            self.game.screen.blit(ip_text, (100, self.game.height / 2))
            return
        if (server_player := self.players[self.server.getsockname()]) is not None:
            server_player.keyboard_control()

    def apply_controls(self, client, data: bytes):
        if client in self.players and (player := self.players[client]) is not None:
            try:
                player.controls = json.loads(data)
            except json.JSONDecodeError:
                # Ignore invalid JSON
                pass


class Client:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client: socket.socket
        self.game: engine.Game = engine.Game((0, 0), "images/Menu/Background.png")
        self.next_draw = None
        self.controls = None
        self.last_sequence = 0
        self.connected = False
        self.game_state = {}  # Current game state
        self.last_update_time = 0
        self.frame_buffer = []  # Buffer frames to smooth out network jitter

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.settimeout(5)
        # Send join message
        self.send_message(JOIN_GAME + f"images/player{0}.png".encode())
        # Wait for response
        response = self.receive_message()
        if response == GAME_ALREADY_STARTED:
            raise ConnectionRefusedError("Game already started")
        elif response == OK:
            self.connected = True
            self.client.settimeout(0.1)  # Shorter timeout for game loop
        else:
            raise ConnectionRefusedError("Unknown response from server")

    def disconnect(self):
        self.connected = False
        self.client.close()

    def send_message(self, data):
        try:
            self.client.sendto(
                data if isinstance(data, bytes) else data.encode(),
                (self.server_host, self.server_port),
            )
        except Exception as e:
            print(f"Error sending data: {e}")

    def receive_message(self):
        try:
            data, _ = self.client.recvfrom(BUFFER_SIZE)
            return data
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None

    def main(self):
        self.sync_thread = threading.Thread(target=self.sync)
        self.sync_thread.daemon = True  # Make thread exit when main thread exits
        self.sync_thread.start()
        self.game.main(self.game_loop)

    def sync(self):
        """Network synchronization thread"""
        last_control_send = 0
        control_send_interval = (
            1 / 30
        )  # Send controls at 30Hz to reduce network traffic

        while self.game.running and self.connected:
            try:
                # Send controls to server (less frequently than we receive updates)
                current_time = time.time()
                if (
                    self.controls is not None
                    and current_time - last_control_send > control_send_interval
                ):
                    self.send_message(SEND_CONTROLS + self.controls)
                    last_control_send = current_time

                # Receive game state
                data = self.receive_message()
                if data:
                    if data == WAITING:
                        self.next_draw = WAITING
                    else:
                        try:
                            # Try to parse as binary protocol first
                            if USE_BINARY_PROTOCOL:
                                try:
                                    if USE_COMPRESSION:
                                        data = zlib.decompress(data)
                                    msg_type, seq, game_state = pickle.loads(data)
                                    if msg_type == "SEQ" and seq > self.last_sequence:
                                        self.last_sequence = seq
                                        self.game_state = game_state
                                        self.last_update_time = time.time()
                                except Exception as e:
                                    # Fall back to text protocol
                                    if data.startswith(b"seq:"):
                                        parts = data.split(b":", 2)
                                        if len(parts) >= 3:
                                            seq = int(parts[1])
                                            if seq > self.last_sequence:
                                                self.last_sequence = seq
                                                self.game_state = json.loads(
                                                    parts[2].decode()
                                                )
                                                self.last_update_time = time.time()
                            else:
                                # Legacy text protocol
                                if data.startswith(b"seq:"):
                                    parts = data.split(b":", 2)
                                    if len(parts) >= 3:
                                        seq = int(parts[1])
                                        if seq > self.last_sequence:
                                            self.last_sequence = seq
                                            self.game_state = json.loads(
                                                parts[2].decode()
                                            )
                                            self.last_update_time = time.time()
                        except (
                            json.JSONDecodeError,
                            UnicodeDecodeError,
                            pickle.PickleError,
                        ) as e:
                            print(f"Error parsing game state: {e}")
                            pass
            except Exception as e:
                print(f"Error in sync thread: {e}")

            # Shorter sleep for more responsive client
            time.sleep(0.001)

    def game_loop(self):
        """Main game rendering and logic loop"""
        if (
            self.game_state is None
            or self.game_state == {}
            or self.next_draw == WAITING
        ):
            waiting_text = pygame.font.Font("images/Anta-Regular.ttf", 74).render(
                "Waiting for players...", True, "white"
            )
            self.game.screen.blit(waiting_text, (100, self.game.height / 2))
            return

        # Update controls - do this before rendering to ensure most recent input
        self.controls = json.dumps(get_controls()).encode()

        self.game.background_image_path = None
        # Update game objects from network state - only do this when needed
        # Check if we need to rebuild all objects
        if len(self.game_state) != len(self.game.objects):
            self.game.objects.clear()

        # Update or create objects from game state
        if isinstance(self.game_state, bytes):
            try:
                self.game_state = pickle.loads(self.game_state)
            except (json.JSONDecodeError, UnicodeDecodeError):
                print("Error decoding game state")
                self.game_state = {}

        for name, obj_data in self.game_state.items():
            # Convert short keys back to full names if needed
            image_path = obj_data.get("p", obj_data.get("image_path", ""))
            x = obj_data.get("x", 0)
            y = obj_data.get("y", 0)
            direction = obj_data.get("d", obj_data.get("direction", 1))

            if name in self.game.objects:
                # Update existing object
                sprite = self.game.objects[name]
                sprite.x = x
                sprite.y = y
                sprite.direction = direction
            else:
                # Create new object
                self.game.add_object(
                    name,
                    engine.Sprite,
                    image_path=image_path,
                    x=x,
                    y=y,
                    direction=direction,
                )


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
        self.game.background_image_path = None
        self.server.waiting = False

    @engine.button("images/Menu/Cancel.png")
    def exit(self):
        self.game.running = False
