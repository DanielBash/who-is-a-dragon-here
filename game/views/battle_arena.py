"""СЦЕНА: Игра
 - Основной геймплей"""

# -- импорт модулей
import math
import random
import time

import arcade
import arcade.gui
import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.gui import UIStyleBase, Property, UISpace, bind
from arcade.types import Color


class CustomButtonStyle(UIStyleBase):
    font_size: float = 18
    font_color: tuple = (255, 255, 255, 255)
    font_name: tuple = ("Roboto", "Arial", "calibri")


default_button_styles = {
    "normal": CustomButtonStyle(),
    "hover": CustomButtonStyle(),
    "press": CustomButtonStyle()
}


class Progressbar(arcade.gui.UIAnchorLayout):
    value = Property(0.0)

    def __init__(
            self,
            value: float = 1.0,
            width=100,
            height=20,
            color: Color = arcade.color.GREEN,
    ) -> None:
        super().__init__(
            width=width,
            height=height,
            size_hint=None
        )
        self.with_background(color=arcade.uicolor.GRAY_CONCRETE)
        self.with_border(color=arcade.uicolor.BLACK)

        self._bar = UISpace(
            color=color,
            size_hint=(value, 1),
        )
        self.add(
            self._bar,
            anchor_x="left",
            anchor_y="top",
        )
        self.value = value

        bind(self, "value", self._update_bar)

    def _update_bar(self):
        self._bar.size_hint = (self.value, 1)
        self._bar.visible = self.value > 0


class PlayerSprite(arcade.Sprite):
    def __init__(self, walking_anim: list):
        super().__init__()

        self.walking = False

        self.walking_animation = walking_anim

        self.local_time = 0
        self.frame_duration = 0.1

    def update_animation(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        super().update_animation()

        self.local_time += delta_time

        if self.walking:
            frame = (self.local_time // self.frame_duration) % len(self.walking_animation)
            self.texture = self.walking_animation[math.floor(frame)]
        else:
            self.texture = self.walking_animation[0]


# -- класс сцены
class Main(arcade.View):
    # -- инициализация
    def __init__(self, config):
        super().__init__()

        self.conf = config
        self.scaling = self.width / 800
        self.conf.assets.font('LeticeaBumsteadCyrillic')

        # настройки сцены
        self.background_color = arcade.color.Color.from_hex_string('#a5d5df')

        # настройка интерфейса
        self.ui = arcade.gui.UIManager()
        self.layout = arcade.gui.UIAnchorLayout()

        self.button_row = arcade.gui.UIBoxLayout(space_between=10, vertical=False)
        self.items_row = arcade.gui.UIBoxLayout(space_between=10, vertical=False)
        self.enemy_name_label = arcade.gui.UILabel(font_size=25, text=self.conf.enemy.name)

        self.fight_button = arcade.gui.UITextureButton(
            text='Ударить',
            texture=self.conf.assets.texture('button'),
            texture_hovered=self.conf.assets.texture('button_hovered'),
            scale=0.5,
            style=default_button_styles
        )
        self.fight_button.on_click = self.start_kicking
        self.action_button = arcade.gui.UITextureButton(
            text='Предметы',
            texture=self.conf.assets.texture('button'),
            texture_hovered=self.conf.assets.texture('button_hovered'),
            scale=0.5,
            style=default_button_styles
        )
        self.action_button.on_click = self.open_items_menu
        self.player_health_bar = Progressbar(value=0.5, width=300, height=50,
                                             color=arcade.color.Color.from_hex_string('#457a5f'))
        self.enemy_health_bar = Progressbar(value=0.5, width=300, height=50,
                                            color=arcade.color.Color.from_hex_string('#8d5180'))

        self.button_row.add(self.player_health_bar)
        self.button_row.add(self.fight_button)
        self.button_row.add(self.action_button)
        self.button_row.add(self.enemy_health_bar)

        self.layout.add(self.button_row, anchor_x='center', anchor_y='bottom')
        self.layout.add(self.items_row, anchor_x='center', anchor_y='center')
        self.layout.add(self.enemy_name_label, anchor_x='center', anchor_y='top')

        self.ui.add(self.layout)

        if self.conf.DEBUG:
            self.panel = self.conf.utils.ui.DebugPanel(self.conf.logger)

        self.mouse_sprite_list = arcade.SpriteList()
        self.background_sprite_list = arcade.SpriteList()
        self.attack_walls_list = arcade.SpriteList()

        self.mouse = arcade.Sprite(path_or_texture=self.conf.assets.texture('cursor'), scale=0.1)
        self.parallax_sprites = [arcade.Sprite(path_or_texture=self.conf.assets.texture(i)) for i in
                                 self.conf.enemy.background]
        self.enemy_sprite = arcade.Sprite(path_or_texture=self.conf.assets.texture(self.conf.enemy.texture))
        self.enemy_shadow = arcade.Sprite(
            path_or_texture=self.conf.assets.texture(random.choice(self.conf.enemy.shadows)))
        self.aim = arcade.Sprite(path_or_texture=self.conf.assets.texture('aim'))
        self.boundary_box = arcade.Sprite(
            path_or_texture=self.conf.assets.texture('boundary_box', hitbox_algo=arcade.hitbox.PymunkHitBoxAlgorithm()))
        self.boundary_box_1 = arcade.Sprite(path_or_texture=self.conf.assets.texture('boundary_box_1',
                                                                                     hitbox_algo=arcade.hitbox.PymunkHitBoxAlgorithm()))
        self.boundary_box_2 = arcade.Sprite(path_or_texture=self.conf.assets.texture('boundary_box_2',
                                                                                     hitbox_algo=arcade.hitbox.PymunkHitBoxAlgorithm()))
        self.boundary_box_3 = arcade.Sprite(path_or_texture=self.conf.assets.texture('boundary_box_3',
                                                                                     hitbox_algo=arcade.hitbox.PymunkHitBoxAlgorithm()))
        self.player_sprite = PlayerSprite(
            walking_anim=[
                self.conf.assets.texture('knight_standing'),
                self.conf.assets.texture('knight_walking_down_1'),
                self.conf.assets.texture('knight_standing'),
                self.conf.assets.texture('knight_walking_down_2'),
            ],
        )

        self.mouse_sprite_list.append(self.mouse)
        for i in self.parallax_sprites: self.background_sprite_list.append(i)
        self.background_sprite_list.append(self.enemy_sprite)
        self.background_sprite_list.append(self.enemy_shadow)
        self.background_sprite_list.append(self.aim)
        self.attack_walls_list.append(self.boundary_box)
        self.attack_walls_list.append(self.boundary_box_1)
        self.attack_walls_list.append(self.boundary_box_2)
        self.attack_walls_list.append(self.boundary_box_3)
        self.background_sprite_list.append(self.player_sprite)

        # камеры
        self.cursor_camera = arcade.Camera2D()
        self.camera = arcade.Camera2D()

        self.matching_cameras = [self.cursor_camera, self.camera]

        self.items_opened = False
        self.kicking = False
        self.attacking = False
        self.attack = None
        self.enemy_knockback = 0

        self.keys = set()

        self.attack_physics_engine = arcade.PhysicsEngineSimple(
            player_sprite=self.player_sprite,
            walls=self.attack_walls_list
        )

        self.setup()

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    def setup(self):
        self.update_gui()

    # -- отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.camera.use()

        self.clear()
        self.background_sprite_list.draw()
        self.attack_walls_list.draw()

        if self.attacking:
            self.attack.draw_projectiles()

        self.ui.draw()

        if self.conf.DEBUG:
            self.panel.draw()

        self.cursor_camera.use()

        self.mouse_sprite_list.draw()

    # -- обновление состояния
    def on_update(self, delta_time):
        self.camera.position = self.boundary_box.position
        # updating parallax
        c = 0
        for i in self.parallax_sprites:
            x = self.camera.position.x
            y = self.camera.position.y
            x += self.mouse.position[0] / self.width * (50 + c * 50) / 2
            y += self.mouse.position[1] / self.height * (50 + c * 50) / 2
            i.position = (x, y)
            w = i.width / i.scale[0]
            h = i.height / i.scale[0]
            i.scale = max((self.width + 100) / w, (self.height + 100) / h)
            c += 1

        # updating health bars
        self.enemy_health_bar.value = 0.01 * self.conf.enemy.health
        self.player_health_bar.value = 0.01 * self.conf.player.health

        self.enemy_sprite.scale = self.scaling * 0.2
        self.enemy_sprite.center_x = self.parallax_sprites[-1].center_x + math.sin(
            (self.conf.start_time - time.time()) * 3) * 30
        self.enemy_sprite.center_y = self.parallax_sprites[-1].center_y - 0.1 * self.parallax_sprites[-1].height

        self.enemy_shadow.position = self.camera.position
        self.enemy_shadow.scale = self.scaling * 0.6

        if self.kicking:
            if random.random() < delta_time / self.conf.enemy.speed:
                self.enemy_shadow.texture = self.conf.assets.texture(random.choice(self.conf.enemy.shadows))
            self.aim.position = self.enemy_shadow.position
            enemy_speed = self.conf.enemy.speed
            self.aim.center_x += math.sin((self.conf.start_time - time.time()) * 3.5 * enemy_speed) * 100 * self.scaling
            self.aim.center_y += math.sin(
                (self.conf.start_time - time.time()) * 2.5 * enemy_speed + 300) * 100 * self.scaling
            self.aim.scale = 0.2 * self.scaling
            self.aim.angle = self.aim.center_x % 360 + self.aim.center_y % 360

        if self.enemy_knockback > 0:
            self.enemy_knockback -= delta_time * 4
            self.enemy_sprite.angle = self.enemy_knockback * 30

        self.boundary_box.scale = self.scaling * 0.7
        self.boundary_box_1.scale = self.boundary_box.scale
        self.boundary_box_2.scale = self.boundary_box.scale
        self.boundary_box_3.scale = self.boundary_box.scale

        self.player_sprite.scale = self.scaling * 0.1

        self.background_sprite_list.update_animation(delta_time)

        if self.conf.KEYS['move_up'] in self.keys:
            self.player_sprite.change_y = self.conf.player.speed * delta_time * self.scaling
            self.player_sprite.walking = True
        if self.conf.KEYS['move_down'] in self.keys:
            self.player_sprite.change_y = -self.conf.player.speed * delta_time * self.scaling
            self.player_sprite.walking = True
        if self.conf.KEYS['move_right'] in self.keys:
            self.player_sprite.change_x = self.conf.player.speed * delta_time * self.scaling
            self.player_sprite.walking = True
        if self.conf.KEYS['move_left'] in self.keys:
            self.player_sprite.change_x = -self.conf.player.speed * delta_time * self.scaling
            self.player_sprite.walking = True

        if self.conf.KEYS['move_up'] not in self.keys and self.conf.KEYS['move_down'] not in self.keys:
            self.player_sprite.change_y = 0

        elif self.conf.KEYS['move_right'] not in self.keys and self.conf.KEYS['move_left'] not in self.keys:
            self.player_sprite.change_x = 0

        if self.conf.KEYS['move_up'] not in self.keys and self.conf.KEYS['move_down'] not in self.keys and \
                self.conf.KEYS['move_right'] not in self.keys and self.conf.KEYS['move_left'] not in self.keys:
            self.player_sprite.walking = False
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0

        if self.attacking and self.attack:
            self.attack_physics_engine.update()
            self.attack.update_projectiles()
            self.attack.set_scale(self.scaling * 0.1)

            try:
                if time.time() > self.attack.stop_time:
                    self.attacking = False
                    self.update_gui()
                    self.attack.clear()
            except Exception as e:
                pass

            for i in arcade.check_for_collision_with_list(self.player_sprite, self.attack.projectiles):
                i.remove_from_sprite_lists()
                self.conf.player.health -= i.damage
                if self.conf.player.health <= 0:
                    self.load_loose()

                arcade.play_sound(self.conf.assets.effect('air_punch'))

    # -- обработка ввода пользователя
    def on_key_press(self, key, key_modifiers):
        self.keys.add(key)
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)
        if key == self.conf.KEYS['action'] and self.kicking:
            if self.enemy_shadow.collides_with_point(self.aim.position):
                dmg = random.randint(1, 10)
                self.conf.enemy.health -= dmg
                arcade.play_sound(self.conf.assets.effect('air_punch'))
                self.enemy_knockback = 1

                if self.conf.enemy.health <= 0:
                    self.load_win()

            self.kicking = False
            self.attacking = True
            self.attack = random.choice(self.conf.enemy.attacks)
            self.attack.stop_time = random.randint(self.attack.attack_duration[0],
                                                   self.attack.attack_duration[1]) + time.time()
            self.player_sprite.position = self.boundary_box.position
            self.update_gui()

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in self.keys:
            self.keys.remove(symbol)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        wx, wy, _ = self.cursor_camera.unproject((x, y))
        self.mouse.position = (wx, wy)

    # -- Системные события
    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_playing('fight')

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

        for i in self.matching_cameras:
            i.match_window()

    def open_items_menu(self, event):
        arcade.play_sound(self.conf.assets.effect('button_click'))
        self.items_opened = not self.items_opened
        self.update_gui()

    def update_gui(self):
        if self.kicking:
            self.enemy_shadow.visible = True
            self.button_row.visible = False
            self.aim.visible = True
        else:
            self.enemy_shadow.visible = False
            self.aim.visible = False
        if self.items_opened:
            self.items_row.visible = True
            self.items_row.clear()
            c = 0
            for i in self.conf.player.inventory:
                use_item = arcade.gui.UITextureButton(texture=self.conf.assets.texture(i['texture']), scale=0.2)
                use_item.on_click = lambda event, indx=c: self.use_item(indx)
                self.items_row.add(use_item)
                c += 1
        else:
            self.items_row.visible = False
        if not self.kicking and not self.attacking:
            self.button_row.visible = True
        if self.attacking:
            self.boundary_box.visible = True
            self.player_sprite.visible = True
        else:
            self.boundary_box.visible = False
            self.player_sprite.visible = False

        self.boundary_box_1.visible = self.boundary_box.visible
        self.boundary_box_2.visible = self.boundary_box.visible
        self.boundary_box_3.visible = self.boundary_box.visible

    def start_kicking(self, event):
        arcade.play_sound(self.conf.assets.effect('button_click'))
        self.kicking = True
        self.items_opened = False
        self.update_gui()

    def use_item(self, id):
        item = self.conf.player.inventory[id]
        if item['type'] == 'heal':
            self.conf.player.health += item['heal']
            if self.conf.player.health > 100:
                self.conf.player.health = 100
            arcade.play_sound(self.conf.assets.effect('air_punch'))
        del self.conf.player.inventory[id]
        self.update_gui()

    def load_loose(self):
        from .game_over_menu import Main as play_view
        next_view = play_view(self.conf)
        self.window.show_view(next_view)

    def load_win(self):
        from .game import Main as play_view
        next_view = play_view(self.conf)
        self.window.show_view(next_view)
