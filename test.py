import unittest
import pygame
from level import Level
from engine import Game, Sprite, MultiSprite


class TestGame(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.game = Game((800, 600))

    def test_init_game(self):
        self.assertIsInstance(self.game, Game)
        self.assertEqual(self.game.screen.get_width(), 800)
        self.assertEqual(self.game.screen.get_height(), 600)
        self.assertEqual(self.game.objects, {})

    def test_add_object(self):
        self.game.add_object(
            "player", Sprite, image_path="images/player0.png", x=50, y=50
        )
        self.assertEqual(len(self.game.objects), 1)
        self.assertIsInstance(self.game.objects["player"], Sprite)
        self.assertEqual(self.game.objects["player"].x, 50)
        self.assertEqual(self.game.objects["player"].y, 50)


class TestLevel(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.Game = Game((0, 0))

    def test_init_level(self):
        sprite_args = [
            {"image_path": "images/level0.png", "pos_vector": pygame.Vector2(100, 100)},
            {"image_path": "images/level1.png", "pos_vector": pygame.Vector2(200, 200)},
        ]
        level = Level(game=self.Game, sprite_args=sprite_args)
        self.assertIsInstance(level, Level)
        self.assertEqual(len(level.sprites), 2)
        self.assertEqual(level.sprites[0].pos, pygame.Vector2(100, 100))
        self.assertEqual(level.sprites[1].pos, pygame.Vector2(200, 200))

    def test_load_level(self):
        pos_filepath = "level.txt"
        image_filepath = "images/level{}.png"
        with open(pos_filepath) as f:
            positions = f.read().splitlines()
        level = Level.load(
            game=self.Game, pos_filepath=pos_filepath, image_filepath=image_filepath
        )
        self.assertIsInstance(level, Level)
        self.assertEqual(len(level.sprites), len(positions))
        for i, pos in enumerate(positions):
            self.assertEqual(
                level.sprites[i].pos,
                pygame.Vector2(
                    level.game.screen.get_width() / 2 + int(pos.split(",")[0]),
                    level.game.screen.get_height() / 2 + int(pos.split(",")[1]),
                ),
            )


class TestSprite(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.game = Game((0, 0))
        self.sprite1 = Sprite(
            game=self.game, image_path="images/player0.png", x=50, y=50
        )
        self.sprite2 = Sprite(
            game=self.game, image_path="images/player0.png", x=100, y=100
        )
        self.sprite3 = Sprite(
            game=self.game, image_path="images/player0.png", x=150, y=150
        )
        self.game.objects = {
            "sprite1": self.sprite1,
            "sprite2": self.sprite2,
            "sprite3": self.sprite3,
        }

    def test_collides_with_any_no_collision(self):
        self.sprite1.x = 300
        self.sprite1.y = 300
        self.assertFalse(self.sprite1.collides_with_any())

    def test_collides_with_any_with_collision(self):
        self.sprite1.x = 100
        self.sprite1.y = 100
        self.assertTrue(self.sprite1.collides_with_any())

    def test_collides_with_any_multisprite(self):
        multisprite = MultiSprite(
            game=self.game,
            sprite_args=[
                {"image_path": "images/player0.png", "x": 200, "y": 200},
                {"image_path": "images/player0.png", "x": 250, "y": 250},
            ],
        )
        self.game.objects["multisprite"] = multisprite
        self.sprite1.x = 250
        self.sprite1.y = 250
        self.assertTrue(self.sprite1.collides_with_any())


if __name__ == "__main__":
    unittest.main()
