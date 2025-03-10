from engine import Game, Sprite


class Attack(Sprite):
    def __init__(self, game: Game, x_velocity=0, y_velocity=0, damage=5, **kwargs):
        super().__init__(game, **kwargs)
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.damage = damage


class ShootAttack(Attack):
    def loop(self):
        self.x_move(self.x_velocity)
        self.y_move(self.y_velocity)
        if self.colliding():
            for obj in self.game.objects:
                if self.collides_with(obj) and hasattr(obj, "on_hit"):
                    obj.on_hit(self)
            self.game.remove_object(self)
        if not int(self.x) in range(0,self.game.screen.get_width()):
            self.game.remove_object(self)
        super().loop()
