"""СЦЕНА: Выбор сохранения
 - Интерфейс создания новой записи прохождения
 - Возвращение в предыдущее меню"""

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

        self.exit_button = arcade.gui.UITextureButton(
            text='Назад',
            texture=self.conf.assets.texture('button'),
            texture_hovered=self.conf.assets.texture('button_hovered'),
            scale=0.5,
            style=default_button_styles
        )
        self.new_button = arcade.gui.UITextureButton(
            text='Новый',
            texture=self.conf.assets.texture('button'),
            texture_hovered=self.conf.assets.texture('button_hovered'),
            scale=0.5,
            style=default_button_styles
        )
        self.exit_button.on_click = self.exit_button_click
        self.new_button.on_click = self.new_button_click

        self.button_column.add(self.title)
        self.init_saves()
        self.button_column.add(self.new_button)
        self.button_column.add(self.exit_button)

        self.layout.add(self.button_column)

        self.ui.add(self.layout)

        if self.conf.DEBUG:
            self.panel = self.conf.utils.ui.DebugPanel(self.conf.logger)

        self.shadertoy = None

        self.mouse = arcade.Sprite(path_or_texture=self.conf.assets.texture('cursor'), scale=0.1)

        self.mouse_sprite_list = arcade.SpriteList()
        self.mouse_sprite_list.append(self.mouse)

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    # -- отрисовка
    def init_saves(self):
        data = self.conf.data.data

        # - Создание кнопок для каждого существующего мира
        if 'worlds' in data:
            c = 0
            for world in data['worlds']:
                button = arcade.gui.UITextureButton(
                    text=world['name'],
                    texture=self.conf.assets.texture('button'),
                    texture_hovered=self.conf.assets.texture('button_hovered'),
                    scale=0.5,
                    style=default_button_styles
                )
                button.on_click = lambda x, idx=c: self.load_save(idx)
                self.button_column.add(button)
                c += 1

    def load_save(self, data):
        self.conf.current_world = data
        self.conf.logger.log(f'Загрузка мира {data}')

        from .game import Main as next_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)

    def on_draw(self):
        self.draw_all()
        self.mouse_sprite_list.draw()

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
        from .menu import Main as play_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        next_view = play_view(self.conf)
        self.window.show_view(next_view)

    def new_button_click(self, event):
        from .create_save import Main as play_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        next_view = play_view(self.conf)
        self.window.show_view(next_view)

    # -- Системные события
    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_playing('menu')

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

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse.position = (x, y)
