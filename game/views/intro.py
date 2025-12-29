"""СЦЕНА: интро
 - Демонстрация команды разработчиков"""

# -- импорт модулей
import math
import time
from math import sin
import arcade
from arcade.experimental import CRTFilter
from pyglet.math import Vec2
from .menu import Main as main_menu
from arcade.experimental import Shadertoy


# -- класс сцены
class Main(arcade.View):
    def __init__(self, config):
        super().__init__()

        self.conf = config
        self.scaling = self.width / 800

        # настройки сцены
        self.background_color = arcade.color.Color(33, 23, 41)
        self.jump_time = 3.5
        self.title_time = 3
        self.wait_time = 2
        self.filter_on = False

        # спрайты
        self.credits_sprite = arcade.Sprite(config.assets.texture('credits'),
                                            scale=self.scaling)
        self.credits_sprite.center_y = self.height // 2
        self.credits_sprite.center_x = self.width // 2

        self.title_sprite = arcade.Sprite(config.assets.texture('title'),
                                          scale=self.scaling)
        self.title_sprite.center_y = self.height // 2
        self.title_sprite.center_x = self.width // 2
        self.title_sprite.visible = False

        self.text_list = arcade.SpriteList()
        self.text_list.append(self.credits_sprite)
        self.text_list.append(self.title_sprite)

        self.shadertoy = None

        # флаги состояния
        self.start_time = time.time()
        self.danger_played = False

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    # -- отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.clear()
        self.shadertoy.render()
        self.text_list.draw(pixelated=True)

    # -- обновление состояния
    def on_update(self, delta_time: float):
        self.shadertoy.program['time'] = int(time.time() * 10000)
        time_passed = time.time() - self.start_time
        self.credits_sprite.angle = self.title_sprite.angle = math.sin(time_passed * 3) * 3

        if time_passed > self.jump_time + self.title_time + self.wait_time:
            next_view = main_menu(self.conf)
            self.window.show_view(next_view)

        elif time_passed > self.jump_time + self.title_time:
            self.credits_sprite.visible = False
            self.title_sprite.visible = True
            if self.danger_played:
                self.danger_played = False
                arcade.play_sound(self.conf.assets.effect('impact'))

        elif time_passed > self.jump_time:
            time_passed = self.jump_time
            if not self.danger_played:
                self.danger_played = True
                arcade.play_sound(self.conf.assets.effect('air_punch'))

        self.credits_sprite.center_y = self.title_sprite.center_y = self.height // 2
        self.credits_sprite.center_x = self.title_sprite.center_x = self.width // 2
        self.credits_sprite.scale = self.scaling + math.sin(time_passed) * self.scaling * 0.5
        self.title_sprite.scale = self.scaling

    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.scaling = min(width / 800, height / 600)

        shader_file_path = self.conf.SHADER_FOLDER / 'background.glsl'
        window_size = self.window.get_size()
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

    def on_show_view(self):
        arcade.play_sound(self.conf.assets.effect('danger'))
        self.start_time = time.time()
