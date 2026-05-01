"""Entry point for the SimuBomber project."""

from game.game_loop import GameLoop


def main() -> None:
    """Start and run the game loop."""
    game = GameLoop()
    game.run()


if __name__ == "__main__":
    main()