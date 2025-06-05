import unittest
from unittest.mock import MagicMock, mock_open, patch
import pygame
import socket
from engine import Game, Menu, Sprite, MultiSprite, button
from network import get_wlan_ip
from level import Level
from player import Player
import attacks


@patch("pygame.mixer")
class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))

    def test_init(self, *_):
        self.assertIsInstance(self.game.screen, pygame.Surface)
        self.assertEqual(self.game.screen.get_size(), (800, 600))
        self.assertEqual(self.game.objects, {})
        self.assertIsInstance(self.game.clock, pygame.time.Clock)
        self.assertTrue(self.game.running)
        self.assertEqual(self.game.dt, 0)

    def test_add_object(self, *_):
        def dummy_func(game):
            return 1

        self.game.add_object("dummy", dummy_func)
        self.assertIn("dummy", self.game.objects)
        self.assertEqual(self.game.objects["dummy"], 1)

    def test_remove_object(self, *_):
        dummy_sprite = Sprite(self.game, "images/level/0.png", 0, 0)
        self.game.objects["dummy"] = dummy_sprite
        self.game.remove_object(dummy_sprite)
        self.assertNotIn("dummy", self.game.objects)

    @patch("pygame.event.get")
    @patch("pygame.display.flip")
    def test_main(self, mock_flip, mock_event_get, *_):
        mock_event_get.return_value = [pygame.event.Event(pygame.QUIT)]
        self.game.main()
        self.assertFalse(self.game.running)
        mock_flip.assert_called_once()


class TestSprite(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.game.dt = 1
        self.sprite = Sprite(self.game, "images/level/0.png", x=100, y=100)

    def test_init(self, *_):
        self.assertEqual(self.sprite.pos.x, 100)
        self.assertEqual(self.sprite.pos.y, 100)
        self.assertTrue(self.sprite.collidable)
        self.assertEqual(self.sprite.rect.x, 100)
        self.assertEqual(self.sprite.rect.y, 100)

    def test_x_property(self, *_):
        self.sprite.x = 200
        self.assertEqual(self.sprite.x, 200)
        self.assertEqual(self.sprite.rect.x, 200)

    def test_y_property(self, *_):
        self.sprite.y = 200
        self.assertEqual(self.sprite.y, 200)
        self.assertEqual(self.sprite.rect.y, 200)

    def test_x_move(self, *_):
        self.sprite.x_move(10)
        self.assertNotEqual(self.sprite.x, 100)  # Since dt is not set, it will change

    def test_y_move(self, *_):
        self.sprite.y_move(10)
        self.assertNotEqual(self.sprite.y, 100)  # Since dt is not set, it will change

    def test_collides_with(self, *_):
        other_sprite = Sprite(self.game, "images/level/0.png", x=1000000, y=1000000)
        self.assertFalse(self.sprite.collides_with(other_sprite))
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.sprite.collides_with(other_sprite))

    def test_colliding(self, *_):
        other_sprite = Sprite(self.game, "images/level/0.png", x=1000000, y=1000000)
        self.game.add_object("other", lambda game: other_sprite)
        self.assertFalse(self.sprite.colliding())
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.sprite.colliding())

    def test_check_teleport_positive_x(self, *_):
        self.sprite.teleport = {"+x": {200: 0}}
        self.sprite.x = 200
        self.sprite.check_teleport()
        self.assertEqual(self.sprite.x, 0)

    def test_check_teleport_negative_x(self, *_):
        self.sprite.teleport = {"-x": {0: 200}}
        self.sprite.x = 0
        self.sprite.check_teleport()
        self.assertEqual(self.sprite.x, 200)

    def test_check_teleport_positive_y(self, *_):
        self.sprite.teleport = {"+y": {200: 0}}
        self.sprite.y = 200
        self.sprite.check_teleport()
        self.assertEqual(self.sprite.y, 0)

    def test_check_teleport_negative_y(self, *_):
        self.sprite.teleport = {"-y": {0: 200}}
        self.sprite.y = 0
        self.sprite.check_teleport()
        self.assertEqual(self.sprite.y, 200)

    def test_draw(self, *_):
        self.sprite.draw()
        # No assertion, just ensure no exceptions

    def test_flip_image(self, *_):
        self.sprite.direction = -1
        self.sprite.draw()
        self.assertEqual(self.sprite.image, self.sprite.image2)


@patch("pygame.mixer")
class TestMultiSprite(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.game.dt = 1
        sprite_args = [{"image_path": "images/level/0.png", "x": 100, "y": 100}]
        self.multi_sprite = MultiSprite(self.game, sprite_args)

    def test_init(self, *_):
        self.assertEqual(len(self.multi_sprite.sprites), 1)
        self.assertEqual(self.multi_sprite.sprites[0].x, 100)
        self.assertEqual(self.multi_sprite.sprites[0].y, 100)

    def test_x_property(self, *_):
        self.assertEqual(self.multi_sprite.x, 100)

    def test_x_move(self, *_):
        self.multi_sprite.x_move(10)
        self.assertNotEqual(
            self.multi_sprite.x, 100
        )  # Since dt is not set, it will change

    def test_y_property(self, *_):
        self.assertEqual(self.multi_sprite.y, 100)

    def test_y_move(self, *_):
        self.multi_sprite.y_move(10)
        self.assertNotEqual(
            self.multi_sprite.y, 100
        )  # Since dt is not set, it will change

    def test_collides_with(self, *_):
        other_sprite = Sprite(self.game, "images/level/0.png", x=1000000, y=1000000)
        self.assertFalse(self.multi_sprite.collides_with(other_sprite))
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.multi_sprite.collides_with(other_sprite))

    def test_colliding(self, *_):
        other_sprite = Sprite(self.game, "images/level/0.png", x=1000000, y=1000000)
        self.game.add_object("other", lambda game: other_sprite)
        self.assertFalse(self.multi_sprite.colliding())
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.multi_sprite.colliding())

    def test_check_teleport(self, *_):
        self.multi_sprite.sprites[0].teleport = {"+y": {-10: self.game.height}}
        self.multi_sprite.sprites[0].y = -10
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].y, self.game.height)

    def test_check_teleport_positive_x(self, *_):
        self.multi_sprite.sprites[0].teleport = {"+x": {200: 0}}
        self.multi_sprite.sprites[0].x = 200
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].x, 0)

    def test_check_teleport_negative_x(self, *_):
        self.multi_sprite.sprites[0].teleport = {"-x": {0: 200}}
        self.multi_sprite.sprites[0].x = 0
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].x, 200)

    def test_check_teleport_positive_y(self, *_):
        self.multi_sprite.sprites[0].teleport = {"+y": {200: 0}}
        self.multi_sprite.sprites[0].y = 200
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].y, 0)

    def test_check_teleport_negative_y(self, *_):
        self.multi_sprite.sprites[0].teleport = {"-y": {0: 200}}
        self.multi_sprite.sprites[0].y = 0
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].y, 200)

    def test_draw(self, *_):
        self.multi_sprite.draw()
        # No assertion, just ensure no exceptions

    def test_flip_image(self, *_):
        for sprite in self.multi_sprite.sprites:
            sprite.direction = -1
        self.multi_sprite.draw()
        for sprite in self.multi_sprite.sprites:
            self.assertEqual(sprite.image, sprite.image2)


@patch("pygame.mixer")
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

    def test_init(self, *_):
        self.assertIsInstance(self.menu.buttons, list)
        self.assertEqual(len(self.menu.buttons), 2)
        self.assertEqual(self.menu.buttons[0].func(), 1)
        self.assertEqual(self.menu.buttons[1].func(), 2)

    def test_loop(self, *_):
        self.menu.loop()
        # No assertion, just ensure no exceptions


@patch("pygame.mixer")
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

    def test_init(self, *_):
        self.assertEqual(self.player.controls, {})
        self.assertEqual(self.player.move_acceleration, 0.5)
        self.assertEqual(self.player.friction, 0.1)
        self.assertEqual(self.player.jump_acceleration, 10)
        self.assertEqual(self.player.gravity, 0.5)
        self.assertEqual(self.player.x_velocity, 0)
        self.assertEqual(self.player.y_velocity, -1)
        self.assertEqual(self.player._backwards, 1)

    def test_read_controls(self, *_):
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

    def test_simulate_x_physics(self, *_):
        self.player.x_velocity = 5
        self.player.simulate()
        self.assertEqual(self.player.x_velocity, 4.5)  # 5 - 5 * 0.1

    def test_simulate_y_physics(self, *_):
        self.player.y_velocity = 5
        self.player.simulate()
        self.assertEqual(self.player.y_velocity, 5.5)  # 5 + 0.5

    def test_loop(self, *_):
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

    def test_x_move_collision(self, *_):
        self.player.x_velocity = 5
        self.game.add_object("mock_sprite0", Sprite, "images/level/0.png", x=100, y=100)
        self.player.simulate()
        self.assertEqual(self.player.x_velocity, 0)
        del self.game.objects["mock_sprite0"]

    def test_y_move_collision(self, *_):
        self.game.add_object("mock_sprite0", Sprite, "images/level/0.png", x=100, y=100)
        self.player.y_velocity = 5
        self.player.simulate()
        self.assertEqual(self.player.y_velocity, 1)
        del self.game.objects["mock_sprite0"]

    def test_y_move_no_collision(self, *_):
        self.player.y_velocity = 5
        with patch.object(self.player, "colliding", return_value=False):
            self.player.simulate()
            self.assertEqual(self.player.y_velocity, 5.5)

    def test_read_controls_no_jump(self, *_):
        self.player.controls = {
            "left": False,
            "right": False,
            "jump": True,
            "shoot": False,
        }
        self.player.read_controls()
        self.assertEqual(self.player.y_velocity, -1)

    def test_read_controls_jump(self, *_):
        self.player.controls = {
            "left": False,
            "right": False,
            "jump": True,
            "shoot": False,
        }
        with patch.object(self.player, "colliding", return_value=True):
            self.player.read_controls()
            self.assertEqual(self.player.y_velocity, -10)

    def test_shoot(self, *_):
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

    def test_check_fall(self, *_):
        self.player.y = 10000000
        self.player.check_fall()
        self.assertEqual(self.player.health, 0)

    def test_check_health(self, *_):
        self.game.objects["player"] = self.player
        self.player.health = 0
        self.player.check_health()
        self.assertNotIn("player", self.game.objects)

    def test_on_hit(self, *_):
        self.player.on_hit(
            attacks.Attack(self.game, parent=self, image_path="images/level/0.png")
        )
        self.assertEqual(self.player.health, 95)


@patch("pygame.mixer")
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

    def test_init(self, *_):
        self.assertEqual(len(self.level.sprites), 1)
        self.assertEqual(self.level.sprites[0].x, 400)
        self.assertEqual(self.level.sprites[0].y, 300)

    @patch("builtins.open", new_callable=mock_open, read_data="0,0\n100,100")
    def test_load(self, mock_file, *_):
        image_filepath = "images/level/{}.png"
        level = Level.load(self.game, "level.csv", image_filepath)
        self.assertEqual(len(level.sprites), 2)
        self.assertEqual(level.sprites[0].x, 400)
        self.assertEqual(level.sprites[0].y, 0)
        self.assertEqual(level.sprites[1].x, 500)
        self.assertEqual(level.sprites[1].y, 100)
        mock_file.assert_called_once_with("level.csv")

    def test_loop(self, *_):
        with patch.object(self.level, "y_move") as mock_y_move, patch.object(
            self.level, "check_teleport"
        ) as mock_check_teleport, patch.object(self.level, "draw") as mock_draw:
            self.level.loop()
            mock_y_move.assert_called_once_with(0)
            mock_check_teleport.assert_called_once()
            mock_draw.assert_called_once()


@patch("pygame.mixer")
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

    def test_init(self, *_):
        self.assertEqual(self.attack.x_velocity, 10)

    def test_loop(self, *_):
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


@patch("pygame.mixer")
class TestNetwork(unittest.TestCase):
    @patch("psutil.net_if_addrs")
    def test_get_wlan_ip(self, mock_net_if_addrs, *_):
        mock_net_if_addrs.return_value = {
            "Wi-Fi": [MagicMock(family=socket.AF_INET, address="192.168.1.1")]
        }
        self.assertEqual(get_wlan_ip(), "192.168.1.1")

    @patch("psutil.net_if_addrs")
    def test_get_wlan_ip_no_wlan(self, mock_net_if_addrs, *_):
        mock_net_if_addrs.return_value = {}
        self.assertIsNone(get_wlan_ip())


if __name__ == "__main__":
    unittest.main()
