from time import sleep
import unittest
from unittest.mock import mock_open, patch
import pygame
from engine import Button, Game, Menu, Sprite, MultiSprite, button
from level import Level
from network import NetworkGame
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
        self.assertEqual(self.sprite.image, self.sprite.flipped_image)


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
            self.assertEqual(sprite.image, sprite.flipped_image)


class TestButton(unittest.TestCase):

    def setUp(self):
        self.game = Game((800, 600))
        self.button = Button(
            self.game, "images/level/0.png", x=100, y=100, func=self.dummy_func
        )
        self.dummy_var = 0

    def dummy_func(self):
        self.dummy_var = 1

    def test_init(self):
        self.assertEqual(self.button.func, self.dummy_func)

    def test_loop(self):
        with patch.object(Sprite, "loop") as mock_super_loop:
            self.button.loop()
            mock_super_loop.assert_called_once()
            # Mock mouse click on button
        with patch(
            "pygame.mouse.get_pressed", return_value=[True, False, False]
        ), patch("pygame.mouse.get_pos", return_value=(100, 100)):
            self.button.loop()
            # Assert function was called
            self.assertEqual(self.dummy_var, 1)


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
        self.menu = self.Menu1(self.game, 10)

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
        self.controls = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "jump": pygame.K_SPACE,
            "shoot": pygame.K_m,
        }
        self.player = Player(
            game=self.game,
            controls=self.controls,
            move_acceleration=0.5,
            friction=0.1,
            jump_acceleration=10,
            gravity=0.5,
            image_path="images/level/0.png",
            x=100,
            y=100,
        )

    def test_init(self):
        self.assertEqual(self.player.controls, self.controls)
        self.assertEqual(self.player.move_acceleration, 0.5)
        self.assertEqual(self.player.friction, 0.1)
        self.assertEqual(self.player.jump_acceleration, 10)
        self.assertEqual(self.player.gravity, 0.5)
        self.assertEqual(self.player.x_velocity, 0)
        self.assertEqual(self.player.y_velocity, -1)
        self.assertEqual(self.player._backwards, 1)

    @patch("pygame.key.get_pressed")
    def test_read_controls(self, mock_get_pressed):
        mock_get_pressed.return_value = {
            self.controls["left"]: True,
            self.controls["right"]: False,
            self.controls["jump"]: False,
            self.controls["shoot"]: False,
        }
        self.player.read_controls()
        self.assertEqual(self.player.x_velocity, -0.5)

        mock_get_pressed.return_value = {
            self.controls["left"]: False,
            self.controls["right"]: True,
            self.controls["jump"]: False,
            self.controls["shoot"]: False,
        }
        self.player.read_controls()
        self.assertEqual(self.player.x_velocity, 0.0)  # -0.5 + 0.5

        mock_get_pressed.return_value = {
            self.controls["left"]: False,
            self.controls["right"]: False,
            self.controls["jump"]: True,
            self.controls["shoot"]: False,
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
        with patch(
            "pygame.key.get_pressed",
            return_value={
                self.controls["left"]: False,
                self.controls["right"]: False,
                self.controls["jump"]: True,
                self.controls["shoot"]: False,
            },
        ):
            self.player.read_controls()
            self.assertEqual(self.player.y_velocity, -1)

    def test_read_controls_jump(self):
        with patch(
            "pygame.key.get_pressed",
            return_value={
                self.controls["left"]: False,
                self.controls["right"]: False,
                self.controls["jump"]: True,
                self.controls["shoot"]: False,
            },
        ):
            with patch.object(self.player, "colliding", return_value=True):
                self.player.read_controls()
                self.assertEqual(self.player.y_velocity, -10)

    def test_shoot(self):
        with patch(
            "pygame.key.get_pressed",
            return_value={
                self.controls["left"]: False,
                self.controls["right"]: False,
                self.controls["jump"]: False,
                self.controls["shoot"]: True,
            },
        ):
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
        self.player.on_hit(attacks.Attack(self.game, image_path="images/level/0.png"))
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
        self.attack = attacks.ShootAttack(
            self.game,
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
        dummy_player = self.game.add_object(
            "player",
            Player,
            controls=dict(),
            move_acceleration=0.5,
            friction=0.1,
            jump_acceleration=10,
            gravity=0.5,
            image_path="images/level/0.png",
            x=0,
            y=0,
        )
        with patch.object(dummy_player, "on_hit") as mock_on_hit:
            self.attack.loop()
            self.assertEqual(self.attack.x, self.attack.x_velocity)
            self.assertEqual(self.attack.y, self.attack.y_velocity)
            mock_on_hit.assert_called_once()
            self.assertNotIn("shoot_attack", self.game.objects)
        self.game.objects["shoot_attack"] = self.attack
        self.attack.x = 1000000
        self.attack.loop()
        self.assertNotIn("shoot_attack", self.game.objects)


class TestNetworkGame(unittest.TestCase):
    def setUp(self):
        self.game = NetworkGame((800, 600))
        self.game.add_object("sprite1", Sprite, "images/level/0.png", x=100, y=100)
        self.game.add_object("sprite2", Sprite, "images/level/0.png", x=250, y=200)
        self.game.add_object("sprite3", Sprite, "images/level/0.png", x=350, y=300)

    def test_serialize(self):
        serialized = self.game.serialize()
        self.assertEqual(
            serialized,
            '[{"name": "sprite1", "image_path": "images/level/0.png", "x": 100.0, "y": 100.0, "direction": 1, "collidable": true}, {"name": "sprite2", "image_path": "images/level/0.png", "x": 250.0, "y": 200.0, "direction": 1, "collidable": true}, {"name": "sprite3", "image_path": "images/level/0.png", "x": 350.0, "y": 300.0, "direction": 1, "collidable": true}]',
        )

    def test_deserialize(self):
        serialized = '[{"name": "sprite1", "image_path": "images/level/0.png", "x": 100, "y": 100, "direction": 1, "collidable": true}]'
        self.game.deserialize(serialized)
        self.assertIn("sprite1", self.game.objects)
        self.assertNotIn("sprite2", self.game.objects)
        self.assertNotIn("sprite3", self.game.objects)


if __name__ == "__main__":
    unittest.main()
