from engine import Game, Sprite
from player import Player


class ShootAttack(Sprite):
    def __init__(self, game: Game, x_velocity=0, y_velocity=0, **kwargs):
        super().__init__(game, **kwargs)
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity

    def loop(self):
        self.x_move(self.x_velocity)
        self.y_move(self.y_velocity)
        if self.colliding():
            for obj in self.game.objects:
                if self.collides_with(obj) and isinstance(obj, Player):
                    obj.on_hit()
            self.game.remove_object(self)
        super().loop()
