import pygame
from sprite import Sprite


class Player(Sprite):
    def __init__(
        self,
        *,
        controls: dict,
        move_acceleration,
        friction,
        jump_acceleration,
        gravity,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.controls = controls
        self.move_acceleration = move_acceleration
        self.friction = friction
        self.jump_acceleration = jump_acceleration
        self.gravity = gravity
        self.x_velocity = 0
        self.y_velocity = 0

    def read_controls(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls["left"]]:
            self.x_velocity -= self.move_acceleration
        if keys[self.controls["right"]]:
            self.x_velocity += self.move_acceleration
        if keys[self.controls["jump"]]:
            self.y_velocity -= self.jump_acceleration

    def simulate_x(self):
        self.x += self.x_velocity * self.ctx.dt
        self.x_velocity -= self.x_velocity * self.friction

    def simulate_y(self):
        self.y += self.y_velocity * self.ctx.dt
        self.y_velocity -= self.y_velocity
