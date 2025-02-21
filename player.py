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
        self._backwards = 1

    def simulate(self):
        # X physics
        self.x_move_no_redraw(self.x_velocity)
        if self.collides_with_any():
            self.x_move_no_redraw(-self.x_velocity)
            self.x_velocity = 0
        self.x_velocity -= self.x_velocity * self.friction
        # Y physics
        self.y_move_no_redraw(self.y_velocity)
        if self.collides_with_any():
            if self.y_velocity > 0:
                self._backwards = -1
            else:
                self._backwards = 1
            while self.collides_with_any():
                self.y_move_no_redraw(self._backwards)
            self.y_velocity = 1
        else:
            self.y_velocity += self.gravity
        self.draw()

    def read_controls(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls["left"]]:
            self.image = self.flipped_image
            self.x_velocity -= self.move_acceleration
        if keys[self.controls["right"]]:
            self.image = self.default_image
            self.x_velocity += self.move_acceleration
        if keys[self.controls["jump"]]:
            self.y_move_no_redraw(1)
            if self.collides_with_any():
                self.y_velocity = -self.jump_acceleration
            self.y_move_no_redraw(-1)
        else:
            self.y_move_no_redraw(1)
            if self.collides_with_any():
                self._jumps = 0
            self.y_move_no_redraw(-1)
