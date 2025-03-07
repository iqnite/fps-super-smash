from engine import Game, Sprite


class MeleeAttack(Sprite):
    def __init__(self, game: Game, **kwargs):
        super().__init__(game, **kwargs)
        self.x_velocity = 0
        self.y_velocity = 0

    def loop(self):
        self.x_move(self.x_velocity)
        self.y_move(self.y_velocity)
        if self.collides_with_any():
            self.game.remove_object(self)
        super().loop()