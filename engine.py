from functools import cached_property
import pygame


class Game:
    def __init__(self, screen_size, background_image_path=None):
        pygame.init()
        self.screen = pygame.display.set_mode(screen_size)
        self.objects = {}
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0
        self.background_image_path = background_image_path

    def main(self, func=None):
        while self.running:
            self.loop(func)
        pygame.quit()

    def loop(self, func=None):
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        try:
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill("black")
            if func:
                func()
            for obj in list(self.objects.values()).copy():
                if obj and obj.loop:
                    obj.loop()
            # flip() the display to put your work on screen
            pygame.display.flip()
        except pygame.error:
            pass
        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.
        self.dt = self.clock.tick(60) / 1000

    def add_object(self, name, func, *args, **kwargs):
        obj = func(self, *args, **kwargs)
        self.objects[name] = obj
        return obj

    def remove_object(self, obj):
        for name, value in self.objects.items():
            if value is obj:
                del self.objects[name]
                break

    @property
    def width(self):
        return self.screen.get_width()

    @property
    def height(self):
        return self.screen.get_height()

    @property
    def background(self):
        if self.background_image_path is not None:
            return pygame.transform.scale(
                pygame.image.load(self.background_image_path), (self.width, self.height)
            )


class Sprite:
    def __init__(
        self,
        game: Game,
        image_path: str,
        x=None,
        y=None,
        pos_vector=None,
        direction=1,
        collidable=True,
        teleport=dict(),
        animations=None,
    ):
        self.game = game
        self.image_path = image_path
        self.teleport = teleport
        self.direction = direction
        self.collidable = collidable
        self.normal_image = pygame.image.load(image_path) if not animations else None
        self.images = [self.normal_image]
        self.image = self.normal_image
        self.animations = (
            {
                name: self.load_frames(*animation)
                for name, animation in animations.items()
            }
            if animations
            else {}
        )
        if pos_vector is not None:
            self.pos = pos_vector
        elif x is not None and y is not None:
            self.pos = pygame.Vector2(x, y)
        else:
            self.pos = pygame.Vector2(0, 0)
        self.current_animation = "idle"
        self.current_frame = 0
        self.frame_rate = 12

    def loop(self):
        self.check_teleport()
        if self.animations:
            self.animate()
        self.draw()

    @property
    def x(self):
        return self.pos.x

    @x.setter
    def x(self, value):
        self.pos.x = value

    def x_move(self, value):
        for _ in range(abs(int(value))):
            self.x += abs(value) / value
        self.x += value - int(value)

    @property
    def y(self):
        return self.pos.y

    @y.setter
    def y(self, value):
        self.pos.y = value

    def y_move(self, value):
        for _ in range(abs(int(value))):
            self.y += abs(value) / value
        self.y += value - int(value)

    @property
    def rect(self):
        if self.image is None:
            return None
        rect = self.image.get_rect()
        rect.x = int(self.pos.x)
        rect.y = int(self.pos.y)
        return rect

    @property
    def flipped_image(self):
        if self.normal_image is not None:
            return pygame.transform.flip(self.normal_image, True, False)

    def collides_with(self, other):
        if isinstance(other, str):
            return self.collides_with(self.game.objects[other])
        if isinstance(other, MultiSprite):
            return self.collides_with(other.sprites)
        if isinstance(other, list):
            return any(self.collides_with(obj) for obj in other)
        if isinstance(other, Sprite):
            if self.rect is None or other.rect is None:
                return False
            return self.rect.colliderect(other.rect)

    def colliding(self, otherType=None):
        return [
            obj
            for obj in self.game.objects.values()
            if (
                isinstance(obj, otherType or object)
                and (
                    isinstance(obj, MultiSprite)
                    and any(
                        self.collides_with(obj)
                        for obj in obj.sprites
                        if obj is not self and obj.collidable
                    )
                )
                or (
                    isinstance(obj, Sprite)
                    and obj is not self
                    and obj.collidable
                    and self.collides_with(obj)
                )
            )
        ]

    def check_teleport(self):
        for direction, teleports in self.teleport.items():
            if direction == "+x":
                for a, b in teleports.items():
                    if self.x >= a:
                        self.x = b
            if direction == "-x":
                for a, b in teleports.items():
                    if self.x <= a:
                        self.x = b
            if direction == "+y":
                for a, b in teleports.items():
                    if self.y >= a:
                        self.y = b
            if direction == "-y":
                for a, b in teleports.items():
                    if self.y <= a:
                        self.y = b

    def draw(self):
        if self.normal_image is None:
            return
        self.image = (
            self.normal_image
            if self.direction == 1
            else pygame.transform.flip(self.normal_image, True, False)
        )
        self.game.screen.blit(self.image, (self.x, self.y))

    def load_frames(self, image_path, frame_count):
        sprite_sheet = pygame.image.load(image_path).convert_alpha()
        frame_width = sprite_sheet.get_width() // frame_count
        frames = [
            sprite_sheet.subsurface(
                pygame.Rect(i * frame_width, 0, frame_width, sprite_sheet.get_height())
            )
            for i in range(frame_count)
        ]
        return frames

    def animate(self):
        if not self.animations:
            return
        frames = self.animations[self.current_animation]
        frame = frames[int(self.current_frame)]
        self.current_frame = (self.current_frame + 1 / self.frame_rate) % len(frames)
        self.normal_image = pygame.transform.scale(frame, (65, 70))

    def set_animation(self, animation_name):
        if animation_name in self.animations:
            self.current_animation = animation_name


class MultiSprite:
    def __init__(self, game: Game, sprite_args):
        self.game = game
        self.sprites = [Sprite(game=game, **arg) for arg in sprite_args]

    def loop(self):
        for sprite in self.sprites:
            sprite.loop()

    @property
    def x(self):
        return self.sprites[0].x

    def x_move(self, value):
        for sprite in self.sprites:
            sprite.x_move(value)

    @property
    def y(self):
        return self.sprites[0].y

    def y_move(self, value):
        for sprite in self.sprites:
            sprite.y_move(value)

    def collides_with(self, other):
        return any(sprite.collides_with(other) for sprite in self.sprites)

    def colliding(self, otherType=None):
        return [
            collision
            for sprite in self.sprites
            for collision in sprite.colliding(otherType)
        ]

    def check_teleport(self):
        for sprite in self.sprites:
            sprite.check_teleport()

    def draw(self):
        for sprite in self.sprites:
            sprite.draw()


class Menu:
    button_distance: int = 100

    def __init__(self, game: Game, x=None, y=None):
        if x is None:
            x = game.width / 2
        if y is None:
            y = game.height / 2 - 100
        self.game = game
        self.buttons = [
            func._engine_type_(
                **getattr(self, name)._engine_kwargs_,
                func=func,
                game=game,
                menu=self,
                x=x
                - pygame.image.load(
                    getattr(self, name)._engine_kwargs_["image_path"]
                ).get_width()
                / 2,
                y=y + i * self.button_distance,
            )
            for i, (name, func) in enumerate(self.__class__.__dict__.items())
            if hasattr(func, "_engine_type_")
        ]

    def loop(self):
        for button in self.buttons:
            button.loop()


class Button(Sprite):
    def __init__(self, game: Game, menu: Menu, image_path: str, x, y, func):
        super().__init__(game, image_path, x=x, y=y, collidable=False)
        self.menu = menu
        self.func = func
        self.click_flag = 0
        assert self.normal_image is not None
        self.images.append(
            pygame.transform.scale(
                self.normal_image,
                (
                    self.normal_image.get_width() * 1.3,
                    self.normal_image.get_height() * 1.3,
                ),
            )
        )

    def loop(self):
        super().loop()
        if self.rect is not None and self.rect.collidepoint(pygame.mouse.get_pos()):
            self.normal_image = self.images[1]
            if pygame.mouse.get_pressed()[0]:
                self.click_flag = 1
            elif self.click_flag == 1:
                self.click_flag = 2
            if self.click_flag == 2:
                self.click_flag = 0
                self.func(self.menu)
        else:
            self.normal_image = self.images[0]


def button(image_path: str):
    def decorator(func):
        func._engine_type_ = Button
        func._engine_kwargs_ = {"image_path": image_path}
        return func

    return decorator
