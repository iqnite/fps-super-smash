import pygame
import engine
from level import Level
from player import Player

game = engine.Game((0, 0))  # (0, 0) means full screen

PLAYER_DEFAULTS = {
    "move_acceleration": 300,
    "friction": 0.25,
    "jump_acceleration": 1200,
    "gravity": 100,
    "teleport": {"+y": {game.screen.get_height(): 0}},
}
game.add_object(
    "player0",
    Player,
    image_path="images/player0.png",
    x=game.screen.get_width() / 2,
    y=game.screen.get_height() / 2,
    controls={"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w},
    **PLAYER_DEFAULTS,
)
game.add_object(
    "player1",
    Player,
    image_path="images/player1.png",
    x=100 + game.screen.get_width() / 2,
    y=game.screen.get_height() / 2,
    controls={"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "jump": pygame.K_UP},
    **PLAYER_DEFAULTS,
)
game.add_object(
    "level", Level.load, pos_filepath="level.txt", image_filepath="images/level{}.png"
)

game.main(
    # fill the screen with a color to wipe away anything from last frame
    lambda: game.screen.fill("black")
)
