import selectors
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch
import pygame
import socket
from engine import Button, Game, Menu, Sprite, MultiSprite, button
from network import ECHO, GET_FRAME, SEND_CONTROLS, Client, Server, get_wlan_ip
from level import Level
from player import Player
import attacks


class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))

    def test_init(self):
        self.assertIsInstance(self.game.screen, pygame.Surface)
        self.assertEqual(self.game.screen.get_size(), (800, 600))
        self.assertEqual(self.game.objects, {})
        self.assertIsInstance(self.game.clock, pygame.time.Clock)
        self.assertTrue(self.game.running)
        self.assertEqual(self.game.dt, 0)

    def test_add_object(self):
        def dummy_func(game):
            return 1

        self.game.add_object("dummy", dummy_func)
        self.assertIn("dummy", self.game.objects)
        self.assertEqual(self.game.objects["dummy"], 1)

    def test_remove_object(self):
        dummy_sprite = Sprite(self.game, "images/level/0.png", 0, 0)
        self.game.objects["dummy"] = dummy_sprite
        self.game.remove_object(dummy_sprite)
        self.assertNotIn("dummy", self.game.objects)

    @patch("pygame.event.get")
    @patch("pygame.display.flip")
    def test_main(self, mock_flip, mock_event_get):
        mock_event_get.return_value = [pygame.event.Event(pygame.QUIT)]
        self.game.main()
        self.assertFalse(self.game.running)
        mock_flip.assert_called_once()


class TestSprite(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.game.dt = 1
        self.sprite = Sprite(self.game, "images/level/0.png", x=100, y=100)

    def test_init(self):
        self.assertEqual(self.sprite.pos.x, 100)
        self.assertEqual(self.sprite.pos.y, 100)
        self.assertTrue(self.sprite.collidable)
        self.assertEqual(self.sprite.rect.x, 100)
        self.assertEqual(self.sprite.rect.y, 100)

    def test_x_property(self):
        self.sprite.x = 200
        self.assertEqual(self.sprite.x, 200)
        self.assertEqual(self.sprite.rect.x, 200)

    def test_y_property(self):
        self.sprite.y = 200
        self.assertEqual(self.sprite.y, 200)
        self.assertEqual(self.sprite.rect.y, 200)

    def test_x_move(self):
        self.sprite.x_move(10)
        self.assertNotEqual(self.sprite.x, 100)  # Since dt is not set, it will change

    def test_y_move(self):
        self.sprite.y_move(10)
        self.assertNotEqual(self.sprite.y, 100)  # Since dt is not set, it will change

    def test_collides_with(self):
        other_sprite = Sprite(self.game, "images/level/0.png", x=1000000, y=1000000)
        self.assertFalse(self.sprite.collides_with(other_sprite))
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.sprite.collides_with(other_sprite))

    def test_colliding(self):
        other_sprite = Sprite(self.game, "images/level/0.png", x=1000000, y=1000000)
        self.game.add_object("other", lambda game: other_sprite)
        self.assertFalse(self.sprite.colliding())
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.sprite.colliding())

    def test_check_teleport_positive_x(self):
        self.sprite.teleport = {"+x": {200: 0}}
        self.sprite.x = 200
        self.sprite.check_teleport()
        self.assertEqual(self.sprite.x, 0)

    def test_check_teleport_negative_x(self):
        self.sprite.teleport = {"-x": {0: 200}}
        self.sprite.x = 0
        self.sprite.check_teleport()
        self.assertEqual(self.sprite.x, 200)

    def test_check_teleport_positive_y(self):
        self.sprite.teleport = {"+y": {200: 0}}
        self.sprite.y = 200
        self.sprite.check_teleport()
        self.assertEqual(self.sprite.y, 0)

    def test_check_teleport_negative_y(self):
        self.sprite.teleport = {"-y": {0: 200}}
        self.sprite.y = 0
        self.sprite.check_teleport()
        self.assertEqual(self.sprite.y, 200)

    def test_draw(self):
        self.sprite.draw()
        # No assertion, just ensure no exceptions

    def test_flip_image(self):
        self.sprite.direction = -1
        self.sprite.draw()
        self.assertEqual(self.sprite.image, self.sprite.image2)


class TestMultiSprite(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.game.dt = 1
        sprite_args = [{"image_path": "images/level/0.png", "x": 100, "y": 100}]
        self.multi_sprite = MultiSprite(self.game, sprite_args)

    def test_init(self):
        self.assertEqual(len(self.multi_sprite.sprites), 1)
        self.assertEqual(self.multi_sprite.sprites[0].x, 100)
        self.assertEqual(self.multi_sprite.sprites[0].y, 100)

    def test_x_property(self):
        self.assertEqual(self.multi_sprite.x, 100)

    def test_x_move(self):
        self.multi_sprite.x_move(10)
        self.assertNotEqual(
            self.multi_sprite.x, 100
        )  # Since dt is not set, it will change

    def test_y_property(self):
        self.assertEqual(self.multi_sprite.y, 100)

    def test_y_move(self):
        self.multi_sprite.y_move(10)
        self.assertNotEqual(
            self.multi_sprite.y, 100
        )  # Since dt is not set, it will change

    def test_collides_with(self):
        other_sprite = Sprite(self.game, "images/level/0.png", x=1000000, y=1000000)
        self.assertFalse(self.multi_sprite.collides_with(other_sprite))
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.multi_sprite.collides_with(other_sprite))

    def test_colliding(self):
        other_sprite = Sprite(self.game, "images/level/0.png", x=1000000, y=1000000)
        self.game.add_object("other", lambda game: other_sprite)
        self.assertFalse(self.multi_sprite.colliding())
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.multi_sprite.colliding())

    def test_check_teleport(self):
        self.multi_sprite.sprites[0].teleport = {"+y": {-10: self.game.height}}
        self.multi_sprite.sprites[0].y = -10
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].y, self.game.height)

    def test_check_teleport_positive_x(self):
        self.multi_sprite.sprites[0].teleport = {"+x": {200: 0}}
        self.multi_sprite.sprites[0].x = 200
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].x, 0)

    def test_check_teleport_negative_x(self):
        self.multi_sprite.sprites[0].teleport = {"-x": {0: 200}}
        self.multi_sprite.sprites[0].x = 0
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].x, 200)

    def test_check_teleport_positive_y(self):
        self.multi_sprite.sprites[0].teleport = {"+y": {200: 0}}
        self.multi_sprite.sprites[0].y = 200
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].y, 0)

    def test_check_teleport_negative_y(self):
        self.multi_sprite.sprites[0].teleport = {"-y": {0: 200}}
        self.multi_sprite.sprites[0].y = 0
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].y, 200)

    def test_draw(self):
        self.multi_sprite.draw()
        # No assertion, just ensure no exceptions

    def test_flip_image(self):
        for sprite in self.multi_sprite.sprites:
            sprite.direction = -1
        self.multi_sprite.draw()
        for sprite in self.multi_sprite.sprites:
            self.assertEqual(sprite.image, sprite.image2)


class TestMenu(unittest.TestCase):
    class Menu1(Menu):
        @button("images/level/0.png")
        def dummy1():
            return 1

        @button("images/level/0.png")
        def dummy2():
            return 2

    def setUp(self):
        self.game = Game((800, 600))
        self.button_distance = 10
        self.menu = self.Menu1(self.game)

    def test_init(self):
        self.assertIsInstance(self.menu.buttons, list)
        self.assertEqual(len(self.menu.buttons), 2)
        self.assertEqual(self.menu.buttons[0].func(), 1)
        self.assertEqual(self.menu.buttons[1].func(), 2)

    def test_loop(self):
        self.menu.loop()
        # No assertion, just ensure no exceptions


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.game.dt = 1  # Add delta time for simulation
        self.player = Player(
            game=self.game,
            move_acceleration=0.5,
            friction=0.1,
            jump_acceleration=10,
            gravity=0.5,
            image_path="images/level/0.png",
            x=100,
            y=100,
        )

    def test_init(self):
        self.assertEqual(self.player.controls, {})
        self.assertEqual(self.player.move_acceleration, 0.5)
        self.assertEqual(self.player.friction, 0.1)
        self.assertEqual(self.player.jump_acceleration, 10)
        self.assertEqual(self.player.gravity, 0.5)
        self.assertEqual(self.player.x_velocity, 0)
        self.assertEqual(self.player.y_velocity, -1)
        self.assertEqual(self.player._backwards, 1)

    def test_read_controls(self):
        self.player.controls = {
            "left": True,
            "right": False,
            "jump": False,
            "shoot": False,
        }
        self.player.read_controls()
        self.assertEqual(self.player.x_velocity, -0.5)

        self.player.controls = {
            "left": False,
            "right": True,
            "jump": False,
            "shoot": False,
        }
        self.player.read_controls()
        self.assertEqual(self.player.x_velocity, 0.0)  # -0.5 + 0.5

        self.player.controls = {
            "left": False,
            "right": False,
            "jump": True,
            "shoot": False,
        }
        with patch.object(self.player, "colliding", return_value=True):
            self.player.read_controls()
            self.assertEqual(self.player.y_velocity, -10)

    def test_simulate_x_physics(self):
        self.player.x_velocity = 5
        self.player.simulate()
        self.assertEqual(self.player.x_velocity, 4.5)  # 5 - 5 * 0.1

    def test_simulate_y_physics(self):
        self.player.y_velocity = 5
        self.player.simulate()
        self.assertEqual(self.player.y_velocity, 5.5)  # 5 + 0.5

    def test_loop(self):
        with patch.object(
            self.player, "read_controls"
        ) as mock_read_controls, patch.object(
            self.player, "simulate"
        ) as mock_simulate, patch.object(
            Sprite, "loop"
        ) as mock_super_loop:
            self.player.loop()
            mock_read_controls.assert_called_once()
            mock_simulate.assert_called_once()
            mock_super_loop.assert_called_once()

    def test_x_move_collision(self):
        self.player.x_velocity = 5
        self.game.add_object("mock_sprite0", Sprite, "images/level/0.png", x=100, y=100)
        self.player.simulate()
        self.assertEqual(self.player.x_velocity, 0)
        del self.game.objects["mock_sprite0"]

    def test_y_move_collision(self):
        self.game.add_object("mock_sprite0", Sprite, "images/level/0.png", x=100, y=100)
        self.player.y_velocity = 5
        self.player.simulate()
        self.assertEqual(self.player.y_velocity, 1)
        del self.game.objects["mock_sprite0"]

    def test_y_move_no_collision(self):
        self.player.y_velocity = 5
        with patch.object(self.player, "colliding", return_value=False):
            self.player.simulate()
            self.assertEqual(self.player.y_velocity, 5.5)

    def test_read_controls_no_jump(self):
        self.player.controls = {
            "left": False,
            "right": False,
            "jump": True,
            "shoot": False,
        }
        self.player.read_controls()
        self.assertEqual(self.player.y_velocity, -1)

    def test_read_controls_jump(self):
        self.player.controls = {
            "left": False,
            "right": False,
            "jump": True,
            "shoot": False,
        }
        with patch.object(self.player, "colliding", return_value=True):
            self.player.read_controls()
            self.assertEqual(self.player.y_velocity, -10)

    def test_shoot(self):
        self.player.controls = {
            "left": False,
            "right": False,
            "jump": False,
            "shoot": True,
        }
        self.player.read_controls()
        self.player.read_controls()
        attack_count = 0
        for obj in self.game.objects.values():
            if isinstance(obj, attacks.ShootAttack):
                attack_count += 1
        self.assertEqual(attack_count, 1)

    def test_check_fall(self):
        self.player.y = 10000000
        self.player.check_fall()
        self.assertEqual(self.player.health, 0)

    def test_check_health(self):
        self.game.objects["player"] = self.player
        self.player.health = 0
        self.player.check_health()
        self.assertNotIn("player", self.game.objects)

    def test_on_hit(self):
        self.player.on_hit(
            attacks.Attack(self.game, parent=self, image_path="images/level/0.png")
        )
        self.assertEqual(self.player.health, 95)


class TestLevel(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.sprite_args = [
            {
                "image_path": "images/level/0.png",
                "pos_vector": pygame.Vector2(400, 300),
            }
        ]
        self.level = Level(self.game, self.sprite_args)

    def test_init(self):
        self.assertEqual(len(self.level.sprites), 1)
        self.assertEqual(self.level.sprites[0].x, 400)
        self.assertEqual(self.level.sprites[0].y, 300)

    @patch("builtins.open", new_callable=mock_open, read_data="0,0\n100,100")
    def test_load(self, mock_file):
        image_filepath = "images/level/{}.png"
        level = Level.load(self.game, "level.csv", image_filepath)
        self.assertEqual(len(level.sprites), 2)
        self.assertEqual(level.sprites[0].x, 400)
        self.assertEqual(level.sprites[0].y, 0)
        self.assertEqual(level.sprites[1].x, 500)
        self.assertEqual(level.sprites[1].y, 100)
        mock_file.assert_called_once_with("level.csv")

    def test_loop(self):
        with patch.object(self.level, "y_move") as mock_y_move, patch.object(
            self.level, "check_teleport"
        ) as mock_check_teleport, patch.object(self.level, "draw") as mock_draw:
            self.level.loop()
            mock_y_move.assert_called_once_with(0)
            mock_check_teleport.assert_called_once()
            mock_draw.assert_called_once()


class TestShootAttack(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.dummy_player = self.game.add_object(
            "player",
            Player,
            move_acceleration=0.5,
            friction=0.1,
            jump_acceleration=10,
            gravity=0.5,
            image_path="images/level/0.png",
            x=0,
            y=0,
        )
        self.attack = attacks.ShootAttack(
            self.game,
            parent=self.dummy_player,
            x_velocity=10,
            y_velocity=10,
            image_path="images/level/0.png",
            x=0,
            y=0,
        )

    def test_init(self):
        self.assertEqual(self.attack.x_velocity, 10)

    def test_loop(self):
        self.game.objects["shoot_attack"] = self.attack
        dummy_sprite = self.game.add_object(
            "sprite",
            Player,
            image_path="images/level/0.png",
            x=0,
            y=0,
            move_acceleration=0,
            friction=0,
            jump_acceleration=0,
            gravity=0,
        )
        with patch.object(dummy_sprite, "on_hit") as mock_on_hit:
            self.attack.loop()
            self.assertEqual(self.attack.x, self.attack.x_velocity)
            self.assertEqual(self.attack.y, self.attack.y_velocity)
            mock_on_hit.assert_called_once()
            self.assertNotIn("shoot_attack", self.game.objects)
        self.game.objects["shoot_attack"] = self.attack
        self.attack.x = 1000000
        self.attack.loop()
        self.assertNotIn("shoot_attack", self.game.objects)


class TestServer(unittest.TestCase):
    @patch("network.psutil.net_if_addrs")
    def test_get_wlan_ip(self, mock_net_if_addrs):
        # Test successful IP retrieval
        mock_addr = Mock(family=socket.AF_INET, address="192.168.1.100")
        mock_net_if_addrs.return_value = {"Wi-Fi": [mock_addr]}
        self.assertEqual(get_wlan_ip(), "192.168.1.100")

        # Test when no WiFi interfaces are found
        mock_net_if_addrs.return_value = {"Ethernet": [mock_addr]}
        self.assertIsNone(get_wlan_ip())

        # Test when WiFi interface has no IPv4 address
        non_ipv4_addr = Mock(family=socket.AF_INET6, address="::1")
        mock_net_if_addrs.return_value = {"Wi-Fi": [non_ipv4_addr]}
        self.assertIsNone(get_wlan_ip())

    @patch("network.selectors.DefaultSelector")
    @patch("network.socket.socket")
    @patch("network.engine.Game")
    @patch("network.get_wlan_ip", return_value="192.168.1.100")
    def test_server_init(self, mock_get_ip, mock_game, mock_socket, mock_selector):
        server = Server()
        self.assertEqual(server.players, {"server": None})
        self.assertEqual(server.connections, [])
        self.assertFalse(server.online)
        self.assertTrue(server.waiting)

    @patch("network.selectors.DefaultSelector")
    @patch("network.socket.socket")
    @patch("network.engine.Game")
    @patch("network.get_wlan_ip", return_value="192.168.1.100")
    def test_server_context_manager(
        self, mock_get_ip, mock_game, mock_socket, mock_selector
    ):
        mock_socket_instance = mock_socket.return_value
        mock_selector_instance = mock_selector.return_value

        with Server() as server:
            self.assertTrue(server.online)
            mock_socket.assert_called_once()
            mock_socket_instance.bind.assert_called_once_with(("192.168.1.100", 65432))
            mock_socket_instance.listen.assert_called_once()
            mock_socket_instance.setblocking.assert_called_once_with(False)
            mock_selector_instance.register.assert_called_once()

        # After context exit
        self.assertFalse(server.online)
        mock_socket_instance.close.assert_called_once()
        mock_selector_instance.close.assert_called_once()

    @patch("network.selectors.DefaultSelector")
    @patch("network.socket.socket")
    @patch("network.engine.Game")
    @patch("network.get_wlan_ip", return_value="192.168.1.100")
    def test_start_stop_server(
        self, mock_get_ip, mock_game, mock_socket, mock_selector
    ):
        server = Server()
        server.start_server()

        mock_socket.assert_called_once()
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.bind.assert_called_once_with(("192.168.1.100", 65432))
        mock_socket_instance.listen.assert_called_once()
        mock_socket_instance.setblocking.assert_called_once_with(False)
        self.assertTrue(server.online)

        server.stop_server()
        self.assertFalse(server.online)
        mock_socket_instance.close.assert_called_once()

    @patch("network.json.dumps")
    def test_serialize_game(self, mock_dumps):
        server = Server()
        mock_sprite = MagicMock(image_path="img.png", x=100, y=200, direction=1)
        server.game.objects = {"player1": mock_sprite}

        expected_data = {
            "player10": {"image_path": "img.png", "x": 100, "y": 200, "direction": 1}
        }
        mock_dumps.return_value = "serialized_data"

        result = server.serialize_game()

        mock_dumps.assert_called_once()
        self.assertEqual(result, "serialized_data")

    @patch("network.selectors.DefaultSelector")
    def test_service_connection_echo(self, mock_selector):
        server = Server()
        mock_sock = MagicMock()
        mock_data = SimpleNamespace(addr=("127.0.0.1", 12345), inb=b"", outb=b"")
        mock_key = MagicMock(fileobj=mock_sock, data=mock_data)

        mock_sock.recv.return_value = ECHO

        server.service_connection(mock_key, selectors.EVENT_READ)

        self.assertEqual(mock_data.outb, ECHO)
        mock_sock.recv.assert_called_once_with(1024)

    @patch("network.selectors.DefaultSelector")
    def test_service_connection_send_controls(self, mock_selector):
        server = Server()
        server.apply_controls = MagicMock()

        mock_sock = MagicMock()
        client_addr = ("127.0.0.1", 12345)
        mock_data = SimpleNamespace(addr=client_addr, inb=b"", outb=b"")
        mock_key = MagicMock(fileobj=mock_sock, data=mock_data)

        control_data = b'{"left": true}'
        mock_sock.recv.return_value = SEND_CONTROLS + control_data

        server.service_connection(mock_key, selectors.EVENT_READ)

        server.apply_controls.assert_called_once_with(client_addr, control_data)
        self.assertEqual(mock_data.outb, b"OK")

    @patch("network.selectors.DefaultSelector")
    def test_service_connection_disconnect(self, mock_selector):
        server = Server()
        mock_sock = MagicMock()
        client_addr = ("127.0.0.1", 12345)
        mock_data = SimpleNamespace(addr=client_addr, inb=b"", outb=b"")
        mock_key = MagicMock(fileobj=mock_sock, data=mock_data)

        # Mock player and connections
        mock_player = MagicMock()
        server.players[f"player{client_addr}"] = mock_player
        server.connections = [mock_sock]

        mock_sock.recv.return_value = b""

        server.service_connection(mock_key, selectors.EVENT_READ)

        self.assertEqual(server.connections, [])
        mock_selector_instance = mock_selector.return_value
        mock_selector_instance.unregister.assert_called_once_with(mock_sock)
        mock_sock.close.assert_called_once()

    @patch("network.selectors.DefaultSelector")
    def test_service_connection_unknown_command(self, mock_selector):
        server = Server()
        mock_sock = MagicMock()
        mock_data = SimpleNamespace(addr=("127.0.0.1", 12345), inb=b"", outb=b"")
        mock_key = MagicMock(fileobj=mock_sock, data=mock_data)

        mock_sock.recv.return_value = b"unknown_command"

        server.service_connection(mock_key, selectors.EVENT_READ)

        self.assertEqual(mock_data.outb, b"unknown")

    @patch("network.selectors.DefaultSelector")
    def test_service_connection_write_data(self, mock_selector):
        server = Server()
        mock_sock = MagicMock()
        mock_data = SimpleNamespace(
            addr=("127.0.0.1", 12345), inb=b"", outb=b"test_data"
        )
        mock_key = MagicMock(fileobj=mock_sock, data=mock_data)

        mock_sock.send.return_value = 5  # Partial send of "test_"

        server.service_connection(mock_key, selectors.EVENT_WRITE)

        mock_sock.send.assert_called_once_with(b"test_data")
        self.assertEqual(mock_data.outb, b"data")  # Remaining data


class TestNetwork(unittest.TestCase):
    @patch("psutil.net_if_addrs")
    def test_get_wlan_ip(self, mock_net_if_addrs):
        mock_net_if_addrs.return_value = {
            "Wi-Fi": [MagicMock(family=socket.AF_INET, address="192.168.1.1")]
        }
        self.assertEqual(get_wlan_ip(), "192.168.1.1")

    @patch("psutil.net_if_addrs")
    def test_get_wlan_ip_no_wlan(self, mock_net_if_addrs):
        mock_net_if_addrs.return_value = {}
        self.assertIsNone(get_wlan_ip())

    @patch("socket.socket")
    @patch("selectors.DefaultSelector")
    @patch("network.get_wlan_ip", return_value="192.168.1.1")
    def test_server_start_stop(self, mock_get_wlan_ip, mock_selector, mock_socket):
        server = Server()
        server.start_server()
        self.assertTrue(server.online)
        server.stop_server()
        self.assertFalse(server.online)

    @patch("socket.socket")
    @patch("selectors.DefaultSelector")
    @patch("network.get_wlan_ip", return_value="192.168.1.1")
    def test_server_accept_wrapper(self, mock_get_wlan_ip, mock_selector, mock_socket):
        server = Server()
        server.start_server()
        mock_sock = MagicMock()
        mock_sock.accept.return_value = (MagicMock(), ("127.0.0.1", 12345))
        server.accept_wrapper(mock_sock)
        self.assertEqual(len(server.connections), 1)

    @patch("socket.socket")
    @patch("selectors.DefaultSelector")
    @patch("network.get_wlan_ip", return_value="192.168.1.1")
    def test_client_connect_disconnect(
        self, mock_get_wlan_ip, mock_selector, mock_socket
    ):
        client = Client("127.0.0.1", 65432)
        client.connect()
        self.assertIsNotNone(client.client)
        client.disconnect()

    @patch("socket.socket")
    @patch("selectors.DefaultSelector")
    @patch("network.get_wlan_ip", return_value="192.168.1.1")
    def test_client_request(self, mock_get_wlan_ip, mock_selector, mock_socket):
        client = Client("127.0.0.1", 65432)
        client.connect()
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.recv.return_value = b"OK"
        response = client.request("test")
        self.assertEqual(response, b"OK")


if __name__ == "__main__":
    unittest.main()
