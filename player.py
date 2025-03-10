from datetime import datetime
import pygame
import attacks
from engine import Game, Sprite


class Player(Sprite):
    def __init__(
        self,
        game: Game,
        controls: dict,
        move_acceleration: float,
        friction: float,
        jump_acceleration: float,
        gravity: float,
        **kwargs,
    ):
        super().__init__(game, **kwargs)
        self.controls = controls
        self.move_acceleration = move_acceleration
        self.friction = friction
        self.jump_acceleration = jump_acceleration
        self.gravity = gravity
        self.x_velocity = 0
        self.y_velocity = -1
        self._backwards = 1
        self._shots = 0
        self.life = 100

    def loop(self):
        self.read_controls()
        self.simulate()
        self.check_fall()
        self.check_life()
        super().loop()

    def simulate(self):
        # X physics
        self.x_move(self.x_velocity)
        if self.colliding():
            self.x_move(-self.x_velocity)
            self.x_velocity = 0
        self.x_velocity -= self.x_velocity * self.friction
        # Y physics
        self.y_move(self.y_velocity)
        if self.colliding():
            if self.y_velocity < 0:
                self._backwards = 1
            else:
                self._backwards = -1
            while self.colliding():
                self.y_move(self._backwards)
            self.y_velocity = 1
        else:
            self.y_velocity += self.gravity

    def read_controls(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls.get("left", 0)]:
            self.direction = -1
            self.x_velocity -= self.move_acceleration
        if keys[self.controls.get("right", 0)]:
            self.direction = 1
            self.x_velocity += self.move_acceleration
        if keys[self.controls.get("jump", 0)]:
            self.y_move(10)
            if self.colliding():
                self.y_velocity = -self.jump_acceleration
            self.y_move(-10)
        if keys[self.controls.get("shoot", 0)]:
            if self._shots < 1:
                self._shots += 1
                self.shoot()
        else:
            self._shots = 0

    def shoot(self):
        bullet = self.game.add_object(
            f"shoot_attack{datetime.now()}",
            attacks.ShootAttack,
            x_velocity=10 * self.direction,
            y_velocity=0,
            image_path="images/attacks/shoot0.png",
            x=self.x,
            y=self.y,
            direction=self.direction,
            collidable=False,
        )
        while self.collides_with(bullet):
            bullet.x_move(bullet.direction)

    def on_hit(self, attack: attacks.Attack):
        self.life -= attack.damage
        if self.life <= 0:
            print("despawn")
            # Simon pack hier deathscreen rein bidde
        self.x_velocity += attack.x_velocity / 2

    def check_life(self):
        if self.life <= 0:
            self.game.remove_object(self)

    def check_fall(self):
        if self.y >= self.game.height:
            self.life = 0
            print("fall")
