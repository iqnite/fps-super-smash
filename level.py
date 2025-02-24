import pygame
from engine import MultiSprite


class Level(MultiSprite):
    @classmethod
    def load(cls, ctx, pos_filepath, image_filepath):   
        with open(pos_filepath) as f:
            data = f.read().splitlines()
        return cls(
            ctx,
            [
                {
                    "image_path": image_filepath.format(i),
                    "pos_vector": pygame.Vector2(
                        ctx.screen.get_width() / 2 + int(pos.split(",")[0]),
                        ctx.screen.get_height() / 2 + int(pos.split(",")[1]),
                    ),
                }
                for i, pos in enumerate(data)
            ],
        )

    def __init__(self, ctx, sprite_args):
        super().__init__(ctx, sprite_args)
