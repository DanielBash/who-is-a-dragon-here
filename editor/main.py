"""FILE: Main
 - Run game instance"""

import arcade
import pyglet

from config import Config as conf


class Window(arcade.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def main():
    window = Window(conf.WINDOW_WIDTH,
                    conf.WINDOW_HEIGHT,
                    conf.WINDOW_NAME,
                    resizable=conf.WINDOW_RESIZABLE)
    window.set_minimum_size(conf.WINDOW_MINIMAL_WIDTH,
                            conf.WINDOW_MINIMAL_HEIGHT)
    window.show_view(conf.LAUNCH_VIEW(conf))
    window.set_icon(conf.assets.icon(conf.WINDOW_ICON))
    if conf.DEBUG:
        arcade.enable_timings()
    arcade.run()


if __name__ == "__main__":
    main()
