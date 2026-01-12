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

        self.ui.add(self.layout)

        if self.conf.DEBUG:
            self.panel = self.conf.utils.ui.DebugPanel(self.conf.logger)

        self.shadertoy = None

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    def load_save(self, data):
        self.conf.current_world = data
        self.conf.logger.log(f'Загрузка мира {data}')

        from .menu import Main as next_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)

    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.clear()
        self.shadertoy.render()
        self.ui.draw()

        if self.conf.DEBUG:
            self.panel.draw()

    # -- обновление состояния
    def on_update(self, delta_time):
        pass

    # -- обработка ввода пользователя
    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)

    def exit_button_click(self, event):
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
