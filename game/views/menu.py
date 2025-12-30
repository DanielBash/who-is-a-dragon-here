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
from pyglet.math import Vec2


# -- класс сцены
class Main(arcade.View):
    # -- инициализация
    def __init__(self, config):
        super().__init__()

        self.conf = config
        self.scaling = self.width / 800
        self.window.set_mouse_visible(False)

        # настройки сцены
        self.background_color = arcade.color.Color(33, 23, 41)

        # инициализация объектов
        if self.conf.DEBUG:
            self.panel = self.conf.utils.ui.DebugPanel(self.conf.logger)

        self.shadertoy = None

        # спрайты
        self.all_sprites = arcade.SpriteList()

        self.background_sprite = arcade.Sprite(self.conf.assets.texture('background'))
        self.background_sign_sprite = arcade.Sprite(self.conf.assets.texture('background_sign'))
        self.background_exit_sign_sprite = arcade.Sprite(self.conf.assets.texture('background_exit_sign'))
        self.background_start_sign_sprite = arcade.Sprite(self.conf.assets.texture('background_start_sign'))
        self.mouse_sprite = arcade.Sprite(self.conf.assets.texture('cursor'))

        self.all_sprites.append(self.background_sprite)
        self.all_sprites.append(self.background_sign_sprite)
        self.all_sprites.append(self.background_exit_sign_sprite)
        self.all_sprites.append(self.background_start_sign_sprite)
        self.all_sprites.append(self.mouse_sprite)

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    # -- отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.clear()
        self.shadertoy.render()
        self.all_sprites.draw(pixelated=True)

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

    # -- cистемные события
    def on_show_view(self):
        self.conf.music.ensure_playing('main_menu')

        if self.conf.DEBUG:
            self.panel.enable()

        self.on_resize(int(self.width), int(self.height))

    def on_hide_view(self):
        if self.conf.DEBUG:
            self.panel.disable()

    def scale_to_fit_screen(self, sprite):
        fit_x = self.width / (sprite.width / sprite.scale_x)
        fit_y = self.height / (sprite.height / sprite.scale_y)
        sprite.scale = max(fit_x, fit_y)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.scaling = min(width / 800, height / 600)
        shader_file_path = self.conf.SHADER_FOLDER / 'background.glsl'
        window_size = self.window.get_size()
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

        x, y = self.width / 2, self.height / 2
        self.background_sprite.position = (x, y)
        self.scale_to_fit_screen(self.background_sprite)

        self.background_sign_sprite.position = (x, y)
        self.scale_to_fit_screen(self.background_sign_sprite)

        self.background_exit_sign_sprite.position = (x, y)
        self.scale_to_fit_screen(self.background_exit_sign_sprite)

        self.background_start_sign_sprite.position = (x, y)
        self.scale_to_fit_screen(self.background_start_sign_sprite)

    def on_mouse_motion(self, x, y, w, h):
        self.mouse_sprite.position = (x, y)
        self.mouse_sprite.scale = self.scaling
