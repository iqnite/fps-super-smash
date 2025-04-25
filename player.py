from datetime import datetime

import pygame
import attacks
from engine import Game, Sprite


class Player(Sprite):
    def __init__(
        self,
        game: Game,
        move_acceleration: float,
        friction: float,
        jump_acceleration: float,
        gravity: float,
        image_path: str,
        **kwargs,
    ):
        super().__init__(game, image_path=image_path, **kwargs)
        self.move_acceleration = move_acceleration
        self.friction = friction
        self.jump_acceleration = jump_acceleration
        self.gravity = gravity
        self.x_velocity = 0
        self.y_velocity = -1
        self._backwards = 1
        self._shots = 0
        self.health = 100
        self.controls = {}

    def loop(self):
        self.read_controls()
        self.simulate()
        self.check_fall()
        self.check_health()
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
        if self.controls.get("left", False):
            self.direction = -1
            self.x_velocity -= self.move_acceleration
        if self.controls.get("right", False):
            self.direction = 1
            self.x_velocity += self.move_acceleration
        if self.controls.get("jump", False):
            self.y_move(10)
            if self.colliding():
                self.y_velocity = -self.jump_acceleration
            self.y_move(-10)
        if self.controls.get("shoot", False):
            if self._shots < 1:
                self._shots += 1
                self.shoot()

    def keyboard_control(self):
        self.controls = get_controls()

    def shoot(self):
        self.game.add_object(
            f"shoot_attack{datetime.now()}",
            attacks.ShootAttack,
            max_distance=400,
            parent=self,
            x_velocity=(10 + self.move_acceleration) * self.direction,
            y_velocity=0,
            image_path="images/attacks/shoot0.png",
            x=self.x,
            y=self.y,
            direction=self.direction,
            collidable=False,
        )

    def on_hit(self, attack: attacks.Attack):
        self.health -= attack.damage
        self.x_velocity += attack.x_velocity / 2

    def check_fall(self):
        if self.y >= self.game.height:
            self.health = 0

    def check_health(self):
        if self.health <= 0:
            self.game.remove_object(self)


def get_controls():
    key = pygame.key.get_pressed()
    return {
        "left": key[pygame.K_LEFT],
        "right": key[pygame.K_RIGHT],
        "jump": key[pygame.K_UP],
        "shoot": key[pygame.K_SPACE],
    }
