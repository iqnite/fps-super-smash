from engine import Game, Sprite


class Attack(Sprite):
    def __init__(self, game: Game, x_velocity=0, y_velocity=0, damage=5, **kwargs):
        super().__init__(game, **kwargs)
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.damage = damage


class ShootAttack(Attack):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_distance = kwargs.get("max_distance", 10000)
        self.distance = 0

    def loop(self):
        self.x_move(self.x_velocity)
        self.y_move(self.y_velocity)
        self.distance += self.x_velocity**2 + self.y_velocity**2
        if self.colliding():
            for obj in self.game.objects.values():
                if self.collides_with(obj) and hasattr(obj, "on_hit"):
                    obj.on_hit(self)
            self.game.remove_object(self)
        if (
            not int(self.x) in range(0, self.game.width)
            or self.distance > self.max_distance
        ):
            self.game.remove_object(self)
        for image in (self.image1, self.image2):
            image.set_alpha(max(0, 200 - 100 * abs(self.distance / self.max_distance)))
        super().loop()
