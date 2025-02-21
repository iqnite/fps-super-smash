import unittest
import pygame
from level import Level
from sprite import GameContext


class TestLevel(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.ctx = GameContext(screen=self.screen)

    def test_init_level(self):
        sprite_args = [
            {"image_path": "images/level0.png", "pos_vector": pygame.Vector2(100, 100)},
            {"image_path": "images/level1.png", "pos_vector": pygame.Vector2(200, 200)},
        ]
        level = Level(ctx=self.ctx, sprite_args=sprite_args)
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
            ctx=self.ctx, pos_filepath=pos_filepath, image_filepath=image_filepath
        )
        self.assertIsInstance(level, Level)
        self.assertEqual(len(level.sprites), len(positions))
        for i, pos in enumerate(positions):
            self.assertEqual(
                level.sprites[i].pos,
                pygame.Vector2(
                    level.ctx.screen.get_width() / 2 + int(pos.split(",")[0]),
                    level.ctx.screen.get_height() / 2 + int(pos.split(",")[1]),
                ),
            )


if __name__ == "__main__":
    unittest.main()
