"""VIEW: Редактор миров
 - Основной интерфейс для редактирования игровых миров"""

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


class Main(arcade.View):
    def __init__(self, config):
        super().__init__()

        # Начальная конфигурация
        self.conf = config
        self.scaling = self.width / 800

        # НАСТРОЙКИ СЦЕНЫ
        self.background_color = arcade.color.Color(33, 23, 41)
        self.camera_speed = 100

        # Спрайты
        self.tiles = arcade.SpriteList(use_spatial_hash=True)
        self.portals = arcade.SpriteList(use_spatial_hash=True)
        self.ui = arcade.gui.UIManager()

        self.layout = arcade.gui.UIAnchorLayout()

        self.name_input = arcade.gui.UIInputText(width=200, height=30, text=self.conf.data.data['worlds'][self.conf.current_world]['name'])
        self.buttons = arcade.gui.UIButtonRow()

        self.save_button = arcade.gui.UIFlatButton(text='Сохранить')
        self.exit_button = arcade.gui.UIFlatButton(text='Выйти')

        self.exit_button.on_click = self.exit_button_click
        self.save_button.on_click = self.save_button_click

        self.buttons.add(self.save_button)
        self.buttons.add(self.exit_button)

        self.layout.add(self.name_input, anchor_x='left', anchor_y='top')
        self.layout.add(self.buttons, anchor_x='right', anchor_y='top')
        self.ui.add(self.layout)
        self.on_resize(int(self.width), int(self.height))

        # Данные текущего мира
        self.data = self.conf.data.data['worlds'][self.conf.current_world]
        self.tile_size = 32
        self.tile_texture_cache = {}

        self.camera = arcade.Camera2D()
        self.keys = set()
        self.setup()
        self.brush = 'portal'

    def setup(self):
        # - Загрузка тайлов пола
        for row in range(len(self.data['floor'])):
            for col in range(len(self.data['floor'][row])):
                sprite = self.data['floor'][row][col]
                tile = arcade.Sprite(self.load_texture(sprite['tex']))
                tile.center_x = self.tile_size * col
                tile.center_y = self.tile_size * row
                tile.r = row
                tile.c = col
                self.tiles.append(tile)

        # - Загрузка порталов
        for row in range(len(self.data['data'])):
            for col in range(len(self.data['data'][row])):
                sprite = self.data['data'][row][col]
                if sprite:
                    tile = arcade.Sprite(self.load_texture('portal'))
                    tile.r = row
                    tile.c = col
                    tile.center_x = self.tile_size * col
                    tile.center_y = self.tile_size * row
                    self.portals.append(tile)

    def load_texture(self, name='grass_tile1'):
        if name not in self.tile_texture_cache:
            self.tile_texture_cache[name] = self.conf.assets.texture(name)
        return self.tile_texture_cache[name]

    # -- Отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.camera.use()
        self.clear()
        self.shadertoy.render()
        self.tiles.draw(pixelated=True)
        self.portals.draw(pixelated=True)
        self.ui.draw()

    # -- Обновление состояния
    def on_update(self, delta_time: float):
        self.shadertoy.program['color'] = self.background_color.normalized[:3]
        self.shadertoy.program['time'] = int(time.time() * 10000)
        self.shadertoy.program['mouse'] = self.window.mouse['x'], self.window.mouse['y']

        pos = [self.camera.position.x, self.camera.position.y]
        if self.conf.KEYS['move_up'] in self.keys:
            pos[1] += delta_time * self.camera_speed * (5 / self.camera.zoom)

        if self.conf.KEYS['move_down'] in self.keys:
            pos[1] -= delta_time * self.camera_speed * (5 / self.camera.zoom)

        if self.conf.KEYS['move_left'] in self.keys:
            pos[0] -= delta_time * self.camera_speed * (5 / self.camera.zoom)

        if self.conf.KEYS['move_right'] in self.keys:
            pos[0] += delta_time * self.camera_speed * (5 / self.camera.zoom)

        # - Зум камеры
        if self.conf.KEYS['zoom_in'] in self.keys:
            self.camera.zoom *= 1.1

        if self.conf.KEYS['zoom_out'] in self.keys:
            self.camera.zoom *= 0.9

        self.camera.position = pos

    # -- Обработка ввода пользователя
    # buttons
    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)
        self.keys.add(key)

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in self.keys:
            self.keys.remove(symbol)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        shader_file_path = self.conf.SHADER_FOLDER / 'background.glsl'
        window_size = self.window.get_size()
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)
        if hasattr(self, 'camera'):
            self.camera.match_window()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        # - Преобразование координат мыши в мировые и применение порталов к тайлам
        x, y = self.camera.unproject((x, y)).x, self.camera.unproject((x, y)).y
        tiles = arcade.get_sprites_at_point((x, y), self.tiles)
        for i in tiles:
            i.texture = self.load_texture(self.brush)
            self.conf.data.data['worlds'][self.conf.current_world]['floor'][i.r][i.c]['tex'] = self.brush

    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        if scroll_y == 0:
            return

        factor = 1.1 if scroll_y > 0 else 0.9

        before = self.camera.unproject((x, y))

        self.camera.zoom *= factor

        after = self.camera.unproject((x, y))

        self.camera.position += before - after

    # -- Обработчики интерфейса
    def exit_button_click(self, event):
        from .save_select import Main as next_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)

    def save_button_click(self, event):
        arcade.play_sound(self.conf.assets.effect('button_click'))
        self.conf.data.data['worlds'][self.conf.current_world]['name'] = self.name_input.text

    # -- Системные события
    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_playing('editor_music')
        self.on_resize(int(self.width), int(self.height))

    def on_hide_view(self):
        self.ui.disable()