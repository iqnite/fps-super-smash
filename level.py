import pygame
from engine import MultiSprite


class Level(MultiSprite):
    @classmethod
    def load(cls, game, pos_filepath, image_filepath):
        with open(pos_filepath) as f:
            data = f.read().splitlines()
        return cls(
            game,
            [
                {
                    "image_path": image_filepath.format(i),
                    "pos_vector": pygame.Vector2(
                        game.screen.get_width() / 2 + int(pos.split(",")[0]),
                        game.screen.get_height() / 2 + int(pos.split(",")[1]),
                    ),
                }
                for i, pos in enumerate(data)
            ],
        )

    def __init__(self, game, sprite_args):
        super().__init__(game, sprite_args)
