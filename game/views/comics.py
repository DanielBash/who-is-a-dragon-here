"""СЦЕНА: интро
 - Демонстрация команды разработчиков"""

# -- импорт модулей
import math
import time
from math import sin
import arcade
import arcade.gui
from arcade.experimental import CRTFilter
from pyglet.math import Vec2
from .menu import Main as main_menu
from arcade.experimental import Shadertoy

sub_titles = ['на большой-пребольшой горе жил не менее огромный дракон',
              'а совсем рядом принцесса тосковала в родном замке',
              'только полный дурак не смог бы связать эти два факта с красочным объявлением на афише, появившимся там '
              'за одну ночь',
              'в общем, рыцари и были в основном дураками',
              'но Иванушка, проходя по главной площади сразу заприметил яркую листовку',
              'и ничто не могло сравнится с желанием вставить свой наточенный меч в принцесс- дракона',
              'долг рыцаря звал, и наш герой встал... на тропу к большой горе - месту обитания дракона']


# -- класс сцены
class Main(arcade.View):
    def __init__(self, config):
        super().__init__()

        self.conf = config
        self.scaling = self.width / 800

        # настройки сцены
        self.background_color = arcade.color.Color(33, 23, 41)
        self.wait_time = 2

        # спрайты
        self.slide_1 = arcade.Sprite(config.assets.texture('slide_1'),
                                     scale=0.25)
        self.slide_2 = arcade.Sprite(config.assets.texture('slide_2'),
                                     scale=0.25)
        self.slide_3 = arcade.Sprite(config.assets.texture('slide_3'),
                                     scale=0.25)
        self.slide_4 = arcade.Sprite(config.assets.texture('slide_4'),
                                     scale=0.25)
        self.slide_5 = arcade.Sprite(config.assets.texture('slide_5'),
                                     scale=0.25)
        self.slide_6 = arcade.Sprite(config.assets.texture('slide_6'),
                                     scale=0.25)
        self.slide_7 = arcade.Sprite(config.assets.texture('slide_7'),
                                     scale=0.25)
        self.slide_1.visible = True
        self.slide_2.visible = False
        self.slide_3.visible = False
        self.slide_4.visible = False
        self.slide_5.visible = False
        self.slide_6.visible = False
        self.slide_7.visible = False

        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.slide_1)
        self.sprite_list.append(self.slide_2)
        self.sprite_list.append(self.slide_3)
        self.sprite_list.append(self.slide_4)
        self.sprite_list.append(self.slide_5)
        self.sprite_list.append(self.slide_6)
        self.sprite_list.append(self.slide_7)

        self.slide_1.position = (-329, 683)
        self.slide_2.position = (71, 683)
        self.slide_3.position = (-129, 133)
        self.slide_4.position = (-229, -277)
        self.slide_5.position = (171, -277)
        self.slide_6.position = (371, -277)
        self.slide_7.position = (71, -667)

        self.current_speech = None

        self.ui = arcade.gui.UIManager()
        self.layout = arcade.gui.UIAnchorLayout()

        self.subtitles_label = arcade.gui.UILabel(text='', font_size=20)

        self.layout.add(self.subtitles_label, anchor_y='bottom', anchor_x='center')

        self.ui.add(self.layout)

        # флаги состояния
        self.start_time = time.time()
        self.danger_played = False

        self.camera = arcade.Camera2D()
        self.camera.position = (0, 50)
        self.camera.zoom = 0.5 * self.scaling

        self.current_slide = 0
        self.slide_playing = False

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    # -- отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.camera.use()

        self.clear()
        self.sprite_list.draw()

        self.ui.draw()

    # -- обновление состояния
    def on_update(self, delta_time: float):
        time_passed = time.time() - self.start_time
        if time_passed > self.wait_time:
            if self.current_slide == 0:
                self.conf.logger.log('Начало показа комикса')
                self.current_slide = 1
                self.subtitles_label.text = sub_titles[self.current_slide - 1]
            if self.current_slide > 0:
                if not self.slide_playing:
                    self.current_speech = self.conf.music.play_sound(f'slide_{self.current_slide}')
                    self.__getattribute__(f'slide_{self.current_slide}').visible = True
                    self.slide_playing = True

                if not self.current_speech[1].is_playing(self.current_speech[0]):
                    self.current_slide += 1
                    if self.current_slide == 8:
                        self.load_game()
                        return
                    self.slide_playing = False
                    self.subtitles_label.text = sub_titles[self.current_slide - 1]

    def load_game(self):
        from .game import Main as next_view
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)

    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.scaling = min(width / 800, height / 600)
        if hasattr(self, 'camera'):
            self.camera.match_window()
            self.camera.zoom = 0.3 * self.scaling

    def on_hide_view(self):
        self.ui.disable()

    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_music_stopped()
