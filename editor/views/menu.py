"""VIEW: Menu
 - Provides friendly UI for settings and saves management"""

import math
import time
from math import sin
import arcade
import arcade.gui
import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.experimental import Shadertoy
from pyglet.math import Vec2



class Main(arcade.View):
    def __init__(self, config):
        super().__init__()

        # initial configuration
        self.conf = config
        self.scaling = self.width / 800

        # SCENE SETTINGS
        self.background_color = arcade.color.Color(33, 23, 41)

        # sprites
        self.ui = arcade.gui.UIManager()

        self.layout = arcade.gui.UIAnchorLayout()

        self.button_column = arcade.gui.UIBoxLayout(space_between=10)

        title_texture = self.conf.assets.texture('title')
        self.title = arcade.gui.UIImage(
            texture=title_texture,
        )

        self.exit_button = arcade.gui.UITextureButton(
            texture=self.conf.assets.texture('exit_button'),
        )
        self.start_button = arcade.gui.UITextureButton(
            texture=self.conf.assets.texture('start_button'),
        )

        self.exit_button.on_click = self.exit_button_click
        self.start_button.on_click = self.start_button_click

        self.button_column.add(self.title)
        self.button_column.add(self.start_button)
        self.button_column.add(self.exit_button)

        self.layout.add(self.button_column)

        self.ui.add(self.layout)
        self.on_resize(int(self.width), int(self.height))

    # -- handle drawing
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.clear()
        self.shadertoy.render()
        self.ui.draw()

    # -- handle updating
    def on_update(self, delta_time: float):
        self.shadertoy.program['color'] = self.background_color.normalized[:3]
        self.shadertoy.program['time'] = int(time.time() * 10000)
        self.shadertoy.program['mouse'] = self.window.mouse['x'], self.window.mouse['y']

    # -- handle user input
    # buttons
    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.scaling = min(width / 800, height / 600)
        self.ui.camera.position = self.width / 2, self.height / 2
        self.ui.camera.zoom = self.scaling
        shader_file_path = self.conf.SHADER_FOLDER / 'background.glsl'
        window_size = self.window.get_size()
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

    # gui
    def exit_button_click(self, event):
        arcade.exit()

    def start_button_click(self, event):
        from .save_select import Main as play_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        next_view = play_view(self.conf)
        self.window.show_view(next_view)

    # -- handle system events
    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_playing('main_menu')
        self.on_resize(int(self.width), int(self.height))

    def on_hide_view(self):
        self.ui.disable()
