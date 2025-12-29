"""СЦЕНА: Выбор сохранения
 - Выбор из созданных миров
 - Создание новых
 - Возвращение на предыдущее меню"""

# -- импорт модулей
import math
import time
from math import sin
import arcade
import arcade.gui
import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.experimental import Shadertoy
from pyglet.math import Vec2

import config


# -- класс сцены
class Main(arcade.View):
    # -- инициализация
    def __init__(self, config):
        super().__init__()

        self.conf = config
        self.scaling = self.width / 800

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

        self.button_column.add(self.title)

        self.layout.add(self.button_column)

        self.exit_button = None
        self.add_button = None
        self.shadertoy = None

        self.setup()

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    def setup(self):
        data = config.Config.data

        # - Создание кнопок для каждого существующего мира
        if 'worlds' in data.data:
            c = 0
            for world in data.data['worlds']:
                button = arcade.gui.UITextureButton(
                    texture=self.conf.assets.texture('blank_button'),
                    text=world['name'],
                )
                button.on_click = lambda x, idx=c: self.load_save(idx)
                self.button_column.add(button)
                c += 1

        self.exit_button = arcade.gui.UITextureButton(
            texture=self.conf.assets.texture('back_button'),
        )

        self.exit_button.on_click = self.exit_button_click

        self.add_button = arcade.gui.UITextureButton(
            texture=self.conf.assets.texture('new_button'),
        )

        self.add_button.on_click = self.add_button_click

        self.button_column.add(self.add_button)
        self.button_column.add(self.exit_button)
        self.ui.add(self.layout)

    # -- отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.clear()
        self.shadertoy.render()
        self.ui.draw()

    # -- обновление
    def on_update(self, delta_time: float):
        self.shadertoy.program['time'] = int(time.time() * 10000)

    # -- обработка ввода
    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)

    # -- функции интерфейса
    def exit_button_click(self, event):
        from .menu import Main as next_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)
        return

    def add_button_click(self, event):
        from .create_save import Main as next_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)
        return

    # -- системные события
    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_playing('main_menu')
        self.on_resize(int(self.width), int(self.height))

    def on_hide_view(self):
        self.ui.disable()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.scaling = min(width / 800, height / 600)
        self.ui.camera.position = self.width / 2, self.height / 2
        self.ui.camera.zoom = self.scaling

        shader_file_path = self.conf.SHADER_FOLDER / 'background.glsl'
        window_size = self.window.get_size()
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

    # -- утилиты
    def load_save(self, data):
        self.conf.current_world = data

        from .editor import Main as next_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)
