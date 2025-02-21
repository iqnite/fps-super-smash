import pygame
from sprite import GameContext
from level import Level
from player import Player

# pygame setup
pygame.init()
ctx = GameContext(screen=pygame.display.set_mode((0, 0)))  # (0, 0) means full screen

level = Level.load(ctx, "level.txt", "images/level{}.png")
players = []
players.append (Player(
    ctx=ctx,
    image_path="images/player0.png",
    pos_vector=pygame.Vector2(ctx.screen.get_width() / 2, ctx.screen.get_height() / 2),
    controls={"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w},
    move_acceleration=300,
    friction=0.25,
    jump_acceleration=3000,
    gravity=300,
))

players.append (Player(
    ctx=ctx,
    image_path="images/player1.png",
    pos_vector=pygame.Vector2(ctx.screen.get_width() / 2 + 100, ctx.screen.get_height() / 2 + 100),
    controls={"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "jump": pygame.K_UP},
    move_acceleration=300,
    friction=0.25,
    jump_acceleration=3000,
    gravity=300,
))

ctx.objects["players"] = players
ctx.objects["level"] = level

while ctx.running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            ctx.running = False

    # fill the screen with a color to wipe away anything from last frame
    ctx.screen.fill("black")

    level.draw()
    for i in range (0, len(players)):
        players[i].read_controls()
        players[i].simulate()
    


    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    ctx.dt = ctx.clock.tick(60) / 1000

pygame.quit()
