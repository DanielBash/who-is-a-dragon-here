"""СЦЕНА: Создание нового мира
 - Интерфейс для создания нового мира с удобными настройками"""

# -- импорт модулей
import math
import random
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
    def __init__(self, config):
        super().__init__()

        self.conf = config
        self.scaling = self.width / 800

        # настройки сцены
        self.background_color = arcade.color.Color(33, 23, 41)

        # спрайты
        self.ui = arcade.gui.UIManager()

        self.layout = arcade.gui.UIAnchorLayout()

        self.button_column = arcade.gui.UIBoxLayout(space_between=10)

        title_texture = self.conf.assets.texture('title')
        self.title = arcade.gui.UIImage(
            texture=title_texture,
        )

        self.exit_button = arcade.gui.UITextureButton(
            texture=self.conf.assets.texture('back_button'),
        )

        self.exit_button.on_click = self.exit_button_click

        self.add_button = arcade.gui.UITextureButton(
            texture=self.conf.assets.texture('new_button'),
        )

        self.add_button.on_click = self.add_button_click

        self.name_label = arcade.gui.UILabel(text='Название', align='center')
        self.width_label = arcade.gui.UILabel(text='Ширина', align='center')
        self.height_label = arcade.gui.UILabel(text='Высота', align='center')

        self.name_edit = arcade.gui.UIInputText(width=300)
        self.width_edit = arcade.gui.UIInputText(width=300)
        self.height_edit = arcade.gui.UIInputText(width=300)

        self.button_column.add(self.title)
        self.button_column.add(self.name_label)
        self.button_column.add(self.name_edit)
        self.button_column.add(self.width_label)
        self.button_column.add(self.width_edit)
        self.button_column.add(self.height_label)
        self.button_column.add(self.height_edit)
        self.button_column.add(self.add_button)
        self.button_column.add(self.exit_button)

        self.layout.add(self.button_column)

        self.ui.add(self.layout)

        self.shadertoy = None

        self.on_resize(int(self.width), int(self.height))

    # -- отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.clear()
        self.shadertoy.render()
        self.ui.draw()

    # -- обновление состояний
    def on_update(self, delta_time: float):
        self.shadertoy.program['time'] = int(time.time() * 10000)

    # -- Обработка ввода пользователя
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

    # -- Обработчики интерфейса
    def exit_button_click(self, event):
        from .save_select import Main as next_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)
        return

    def add_button_click(self, event):
        from .editor import Main as next_view

        w = self.width_edit.text
        h = self.height_edit.text
        try:
            w = int(w)
        except:
            w = 100
        try:
            h = int(h)
        except:
            h = 100
        w = max(3, w)
        h = max(3, h)
        w, h = min(1000, w), min(1000, h)
        if 'worlds' not in self.conf.data.data:
            self.conf.data.data['worlds'] = []

        # - новая структура мира
        new_world = {
            'name': self.name_edit.text or f"Мир {len(self.conf.data.data['worlds']) + 1}",
            'width': w,
            'height': h,
            'data': [[None] * w for _ in range(h)],
            'floor': [[{
                'type': 'floor',
                'portals': {'up': None, 'down': None, 'left': None, 'right': None}
            } for _ in range(w)] for _ in range(h)]
        }

        self.conf.data.data['worlds'].append(new_world)
        self.conf.data.save_data()
        self.conf.current_world = len(self.conf.data.data['worlds']) - 1
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
