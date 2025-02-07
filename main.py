import pygame
from sprite import GameContext, Sprite
from player import Player

# pygame setup
pygame.init()
ctx = GameContext(screen=pygame.display.set_mode((1920, 1080)))

level_map = [
    Sprite(ctx=ctx, image_path="images/level0.png", pos_vector=pygame.Vector2(0, 0))
]

player = Player(
    ctx=ctx,
    image_path="images/player0.png",
    pos_vector=pygame.Vector2(ctx.screen.get_width() / 2, ctx.screen.get_height() / 2),
    controls={"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w},
    move_acceleration=300,
    friction=0.1,
    jump_acceleration=300,
    gravity=300,
)

ctx.objects["player"] = player
ctx.objects["level_map"] = level_map

while ctx.running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            ctx.running = False

    # fill the screen with a color to wipe away anything from last frame
    ctx.screen.fill("black")

    for obj in level_map:
        obj.draw()
    player.read_controls()
    player.simulate_x()

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    ctx.dt = ctx.clock.tick(60) / 1000

pygame.quit()
