import pygame
from engine import MultiSprite


class Level(MultiSprite):
    @classmethod
    def load(
        cls, ctx, pos_filepath, image_filepath, common_sprite_args={}, *args, **kwargs
    ):
        with open(pos_filepath) as f:
            data = f.read().splitlines()
        return cls(
            ctx,
            sprite_args=[
                (
                    {
                        "image_path": image_filepath.format(i),
                        "pos_vector": pygame.Vector2(
                            ctx.screen.get_width() / 2 + int(line.split(",")[0]),
                            ctx.screen.get_height() / 2 + int(line.split(",")[1]),
                        ),
                    }
                    | common_sprite_args
                )
                for i, line in enumerate(data)
                if line
            ],
            *args,
            **kwargs
        )

    def __init__(self, ctx, sprite_args=[], y_velocity=0):
        super().__init__(ctx, sprite_args)
        self.y_velocity = y_velocity

    def loop(self):
        self.y_move(self.y_velocity)
        self.check_teleport()
        self.draw()
