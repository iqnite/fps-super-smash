import unittest
from unittest.mock import mock_open, patch
import pygame
from engine import Game, Sprite, MultiSprite
from level import Level
from player import Player


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
        self.sprite = Sprite(self.game, "images/level0.png", x=100, y=100)

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
        other_sprite = Sprite(self.game, "images/level0.png", x=1000000, y=1000000)
        self.assertFalse(self.sprite.collides_with(other_sprite))
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.sprite.collides_with(other_sprite))

    def test_collides_with_any(self):
        other_sprite = Sprite(self.game, "images/level0.png", x=1000000, y=1000000)
        self.game.add_object("other", lambda game: other_sprite)
        self.assertFalse(self.sprite.collides_with_any())
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.sprite.collides_with_any())

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
        self.sprite.image = self.sprite.flipped_image
        self.sprite.draw()
        self.assertEqual(self.sprite.image, self.sprite.flipped_image)


class TestMultiSprite(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.game.dt = 1
        sprite_args = [{"image_path": "images/level0.png", "x": 100, "y": 100}]
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
        other_sprite = Sprite(self.game, "images/level0.png", x=1000000, y=1000000)
        self.assertFalse(self.multi_sprite.collides_with(other_sprite))
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.multi_sprite.collides_with(other_sprite))

    def test_collides_with_any(self):
        other_sprite = Sprite(self.game, "images/level0.png", x=1000000, y=1000000)
        self.game.add_object("other", lambda game: other_sprite)
        self.assertFalse(self.multi_sprite.collides_with_any())
        other_sprite.x = 100
        other_sprite.y = 100
        self.assertTrue(self.multi_sprite.collides_with_any())

    def test_check_teleport(self):
        self.multi_sprite.sprites[0].teleport = {
            "+y": {-10: self.game.screen.get_height()}
        }
        self.multi_sprite.sprites[0].y = -10
        self.multi_sprite.check_teleport()
        self.assertEqual(self.multi_sprite.sprites[0].y, self.game.screen.get_height())

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
            sprite.image = sprite.flipped_image
        self.multi_sprite.draw()
        for sprite in self.multi_sprite.sprites:
            self.assertEqual(sprite.image, sprite.flipped_image)


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.game.dt = 1  # Add delta time for simulation
        self.controls = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "jump": pygame.K_SPACE,
        }
        self.player = Player(
            game=self.game,
            controls=self.controls,
            move_acceleration=0.5,
            friction=0.1,
            jump_acceleration=10,
            gravity=0.5,
            image_path="images/level0.png",
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
        }
        self.player.read_controls()
        self.assertEqual(self.player.x_velocity, -0.5)

        mock_get_pressed.return_value = {
            self.controls["left"]: False,
            self.controls["right"]: True,
            self.controls["jump"]: False,
        }
        self.player.read_controls()
        self.assertEqual(self.player.x_velocity, 0.0)  # -0.5 + 0.5

        mock_get_pressed.return_value = {
            self.controls["left"]: False,
            self.controls["right"]: False,
            self.controls["jump"]: True,
        }
        with patch.object(self.player, "collides_with_any", return_value=True):
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
        self.game.add_object("mock_sprite0", Sprite, "images/level0.png", x=100, y=100)
        self.player.simulate()
        self.assertEqual(self.player.x_velocity, 0)
        del self.game.objects["mock_sprite0"]

    def test_y_move_collision(self):
        self.game.add_object("mock_sprite0", Sprite, "images/level0.png", x=100, y=100)
        self.player.y_velocity = 5
        self.player.simulate()
        self.assertEqual(self.player.y_velocity, 1)
        del self.game.objects["mock_sprite0"]

    def test_y_move_no_collision(self):
        self.player.y_velocity = 5
        with patch.object(self.player, "collides_with_any", return_value=False):
            self.player.simulate()
            self.assertEqual(self.player.y_velocity, 5.5)

    def test_read_controls_no_jump(self):
        with patch(
            "pygame.key.get_pressed",
            return_value={
                self.controls["left"]: False,
                self.controls["right"]: False,
                self.controls["jump"]: True,
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
            },
        ):
            with patch.object(self.player, "collides_with_any", return_value=True):
                self.player.read_controls()
                self.assertEqual(self.player.y_velocity, -10)


class TestLevel(unittest.TestCase):
    def setUp(self):
        self.game = Game((800, 600))
        self.sprite_args = [
            {"image_path": "images/level0.png", "pos_vector": pygame.Vector2(400, 300)}
        ]
        self.level = Level(self.game, self.sprite_args)

    def test_init(self):
        self.assertEqual(len(self.level.sprites), 1)
        self.assertEqual(self.level.sprites[0].x, 400)
        self.assertEqual(self.level.sprites[0].y, 300)

    @patch("builtins.open", new_callable=mock_open, read_data="0,0\n100,100")
    def test_load(self, mock_file):
        image_filepath = "images/level{}.png"
        level = Level.load(self.game, "level.txt", image_filepath)
        self.assertEqual(len(level.sprites), 2)
        self.assertEqual(level.sprites[0].x, 400)
        self.assertEqual(level.sprites[0].y, 300)
        self.assertEqual(level.sprites[1].x, 500)
        self.assertEqual(level.sprites[1].y, 400)
        mock_file.assert_called_once_with("level.txt")

    def test_loop(self):
        with patch.object(self.level, "y_move") as mock_y_move, patch.object(
            self.level, "check_teleport"
        ) as mock_check_teleport, patch.object(self.level, "draw") as mock_draw:
            self.level.loop()
            mock_y_move.assert_called_once_with(0)
            mock_check_teleport.assert_called_once()
            mock_draw.assert_called_once()


if __name__ == "__main__":
    unittest.main()
