"""СЦЕНА: Главное меню
 - Основной интерфейс меню
 - Выход из приложения
 - Запуск"""

# -- импорт модулей
import math
import time
from math import sin
import arcade
import arcade.gui
import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.experimental import Shadertoy
from arcade.gui import UIStyleBase
from pyglet.math import Vec2


class CustomButtonStyle(UIStyleBase):
    font_size: float = 18
    font_color: tuple = (255, 255, 255, 255)
    font_name: tuple = ("Roboto", "Arial", "calibri")


default_button_styles = {
    "normal": CustomButtonStyle(),
    "hover": CustomButtonStyle(),
    "press": CustomButtonStyle()
}


# -- класс сцены
class Main(arcade.View):
    # -- инициализация
    def __init__(self, config):
        super().__init__()

        self.conf = config
        self.scaling = self.width / 800
        self.conf.assets.font('LeticeaBumsteadCyrillic')

        # настройки сцены
        self.background_color = arcade.color.Color(33, 23, 41)

        # настройка интерфейса
        self.ui = arcade.gui.UIManager()

        self.layout = arcade.gui.UIAnchorLayout()

        self.button_column = arcade.gui.UIBoxLayout(space_between=10)

        title_texture = self.conf.assets.texture('title')
        self.title = arcade.gui.UIImage(
            texture=title_texture,
        )

        self.start_button = arcade.gui.UITextureButton(
            text='Начать',
            texture=self.conf.assets.texture('button'),
            texture_hovered=self.conf.assets.texture('button_hovered'),
            scale=0.5,
            style=default_button_styles
        )
        self.exit_button = arcade.gui.UITextureButton(
            text='Выйти',
            texture=self.conf.assets.texture('button'),
            texture_hovered=self.conf.assets.texture('button_hovered'),
            scale=0.5,
            style=default_button_styles
        )
        self.exit_button.on_click = self.exit_button_click
        self.start_button.on_click = self.start_button_click

        self.button_column.add(self.title)
        self.button_column.add(self.start_button)
        self.button_column.add(self.exit_button)

        self.layout.add(self.button_column)

        self.ui.add(self.layout)

        if self.conf.DEBUG:
            self.panel = self.conf.utils.ui.DebugPanel(self.conf.logger)

        self.shadertoy = None

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    # -- отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.clear()
        self.ui.draw()

        if self.conf.DEBUG:
            self.panel.draw()

    # -- обновление состояния
    def on_update(self, delta_time: float):
        self.shadertoy.program['time'] = int(time.time() * 10000)

    # -- обработка ввода пользователя
    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)

    def exit_button_click(self, event):
        arcade.exit()

    def start_button_click(self, event):
        from .save_select import Main as play_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        next_view = play_view(self.conf)
        self.window.show_view(next_view)

    # -- Системные события
    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_playing('main_menu')

        if self.conf.DEBUG:
            self.panel.enable()

        self.on_resize(int(self.width), int(self.height))

    def on_hide_view(self):
        self.ui.disable()

        if self.conf.DEBUG:
            self.panel.disable()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.scaling = min(width / 800, height / 600)
        shader_file_path = self.conf.SHADER_FOLDER / 'background.glsl'
        window_size = self.window.get_size()
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)
