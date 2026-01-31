"""СЦЕНА: Игра
 - Основной геймплей"""

# -- импорт модулей
import math, heapq
import random
import time

import arcade
import arcade.gui
import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.gui import UIStyleBase

DIRS = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
OPP = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
SIDES = list(DIRS)

W, H = 100, 100
VW, VH = 23, 13


class PlayerSprite(arcade.Sprite):
    def __init__(self, walking_anim: list):
        super().__init__()

        self.walking = 0

        self.walking_animation = walking_anim

        self.local_time = 0
        self.frame_duration = 0.1
        self.texture = walking_anim[0]

    def update_animation(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        super().update_animation()

        self.local_time += delta_time

        if self.walking > 0:
            frame = (self.local_time // self.frame_duration) % len(self.walking_animation)
            self.texture = self.walking_animation[math.floor(frame)]
            self.walking -= delta_time
        else:
            self.texture = self.walking_animation[0]


def tile(x, y):
    if 0 <= x < W and 0 <= y < H:
        return world[x][y]
    return {'type': 'void', 'portals': {s: None for s in SIDES}}


def edge_owner(wx, wy, side):
    t = tile(wx, wy)
    if t['portals'][side] is not None: return t['portals'][side], wx, wy, side
    dx, dy = DIRS[side]
    nt = tile(wx + dx, wy + dy)
    pid = nt['portals'][OPP[side]]
    if pid is not None: return pid, wx + dx, wy + dy, OPP[side]
    return None, None, None, None


def find_partner(pid, ox, oy, oside):
    for y in range(H):
        for x in range(W):
            for s, v in world[x][y]['portals'].items():
                if v == pid and not (x == ox and y == oy and s == oside):
                    return x, y, s
    return None


def land(side, partner):
    px, py, ps = partner
    if side == OPP[ps]:
        return px, py
    dx, dy = DIRS[ps]
    return px + dx, py + dy


def step(wx, wy, side):
    pid, ox, oy, os = edge_owner(wx, wy, side)
    dx, dy = DIRS[side]
    if pid is None:
        return wx + dx, wy + dy
    p = find_partner(pid, ox, oy, os)
    if not p:
        return wx + dx, wy + dy
    return land(side, p)


def priority_flood(px, py):
    cx, cy = VW // 2, VH // 2
    pq = []
    heapq.heappush(pq, (0.0, px, py, cx, cy, None))
    mapping = {}
    seen = set()
    while pq:
        cost, wx, wy, sx, sy, prev = heapq.heappop(pq)
        if not (0 <= sx < VW and 0 <= sy < VH): continue
        if (sx, sy) in mapping: continue
        t = tile(wx, wy)
        mapping[(sx, sy)] = (wx, wy, t, cost)
        if t['type'] != 'floor': continue
        for d in SIDES:
            dx, dy = DIRS[d]
            nsx, nsy = sx + dx, sy + dy
            nwx, nwy = step(wx, wy, d)
            if not (0 <= nsx < VW and 0 <= nsy < VH): continue
            turn_penalty = 0.0 if prev is None or prev == d else 0.4
            ncost = cost + 1.0 + turn_penalty
            key = (nwx, nwy, nsx, nsy, d)
            if key in seen: continue
            seen.add(key)
            heapq.heappush(pq, (ncost, nwx, nwy, nsx, nsy, d))
    return mapping


class CustomButtonStyle(UIStyleBase):
    font_size: float = 18
    font_color: tuple = (255, 255, 255, 255)
    font_name: tuple = ("Roboto", "Arial", "calibri")


default_button_styles = {
    "normal": CustomButtonStyle(),
    "hover": CustomButtonStyle(),
    "press": CustomButtonStyle()
}


class Player:
    def __init__(self, x=0, y=0, inventory=None, health=100, speed=300, name='Иванушка'):
        if inventory is None:
            inventory = []
        self.x = x
        self.y = y
        self.inventory = inventory
        self.health = health
        self.speed = speed
        self.name = name


class EnemyAttack:
    def __init__(self, assets, interval=(0.3, 0.5), texture=('aim',), life_time=(2, 3), damage=(10, 20),
                 attack_duration=(10, 11), scale=1):
        self.interval = interval
        self.texture = texture
        self.life_time = life_time
        self.damage = damage

        self.projectiles = arcade.SpriteList()
        self.assets = assets
        self.attack_duration = attack_duration
        self.scale = scale

        self.last_spawn = time.time()
        self.spawning_in = interval[0] + (interval[1] - interval[0]) * random.random()

    def update_projectile(self, proj, delta_time=1/60):
        angular_speed = 4
        radial_speed = 60

        if not hasattr(proj, "angle_"):
            proj.angle_ = random.uniform(0, 2 * math.pi)
            proj.radius = 0

        proj.angle += angular_speed * delta_time
        proj.radius += radial_speed * delta_time

        proj.center_x += math.cos(proj.angle_) * proj.radius * delta_time
        proj.center_y += math.sin(proj.angle_) * proj.radius * delta_time

        return proj

    def update_projectiles(self, delta_time=1 / 60):
        for proj in self.projectiles:
            self.update_projectile(proj, delta_time)
            if proj.spawn_time + proj.life_time < time.time():
                proj.remove_from_sprite_lists()

        if self.last_spawn + self.spawning_in < time.time():
            self.spawn_projectile()
            self.last_spawn = time.time()
            self.spawning_in = self.interval[0] + (self.interval[1] - self.interval[0]) * random.random()

    def spawn_projectile(self):
        proj = arcade.Sprite(path_or_texture=self.assets.texture(random.choice(self.texture)))
        proj.spawn_time = time.time()
        proj.life_time = random.randint(self.life_time[0], self.life_time[1])
        proj.damage = random.randint(self.damage[0], self.damage[1])
        proj.scale = 0.1

        self.projectiles.append(proj)

    def draw_projectiles(self):
        self.projectiles.draw()

    def clear(self):
        self.projectiles.clear()

    def set_scale(self, scale):
        for i in self.projectiles:
            i.scale = scale * self.scale

class WaveAttack(EnemyAttack):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interval = (1, 3)
        self.life_time = (3, 5)


    def update_projectile(self, proj, delta_time=1/60):
        amplitude = 200
        frequency = 4


        if not hasattr(proj, "base_y"):
            proj.base_y = proj.center_y
            proj.base_x = proj.center_x
            proj.time_alive = 0

        proj.time_alive += delta_time
        proj.center_y = proj.base_y + math.sin(proj.time_alive * frequency * 0.3) * amplitude
        proj.center_x = proj.base_x + math.sin(proj.time_alive * frequency * 0.7 + 117) * amplitude * 1.3

        return proj


class Enemy:
    def __init__(self, tex, health, assets, attacks=None):
        if attacks is None:
            attacks = [EnemyAttack(assets), WaveAttack(assets)]
        self.attacks = attacks
        self.texture = tex
        self.health = health
        self.shadows = ['figure_1', 'figure_2', 'figure_3', 'figure_4']
        self.speed = 1
        self.name = 'Враг Нападает!'
        self.background = ['parallax_layer_0',
                           'parallax_layer_1']



# -- класс сцены
class Main(arcade.View):
    # -- инициализация
    def __init__(self, config):
        super().__init__()

        self.conf = config
        self.scaling = self.width / 800
        self.conf.assets.font('LeticeaBumsteadCyrillic')
        self.fix_json()

        if not self.conf.player:
            self.player = Player(**self.conf.data.data['worlds'][self.conf.current_world]['player'])
            self.conf.player = self.player
            self.save_all()
        else:
            self.player = self.conf.player

        # настройки сцены
        self.background_color = arcade.color.Color(33, 23, 41)

        # настройка интерфейса
        self.ui = arcade.gui.UIManager()
        self.layout = arcade.gui.UIAnchorLayout()
        self.ui.add(self.layout)

        if self.conf.DEBUG:
            self.panel = self.conf.utils.ui.DebugPanel(self.conf.logger)

        self.mouse = arcade.Sprite(path_or_texture=self.conf.assets.texture('cursor'), scale=0.1)

        self.mouse_sprite_list = arcade.SpriteList()
        self.enemy_sprite_list = arcade.SpriteList()
        self.mouse_sprite_list.append(self.mouse)

        # камеры
        self.cursor_camera = arcade.Camera2D()
        self.camera = arcade.Camera2D()

        self.matching_cameras = [self.cursor_camera, self.camera]

        self.tile_sprite_list = arcade.SpriteList()
        self.entities_sprite_list = arcade.SpriteList()

        self.prev_player_pos = [self.player.x, self.player.y]
        self.player_sprite = self.player_sprite = PlayerSprite(
            walking_anim=[
                self.conf.assets.texture('knight_standing'),
                self.conf.assets.texture('knight_walking_down_1'),
                self.conf.assets.texture('knight_standing'),
                self.conf.assets.texture('knight_walking_down_2'),
            ],
        )
        self.entities_sprite_list.append(self.player_sprite)

        self.display_tiles_data = []
        self.base_tile_size = 50
        self.tile_size = self.base_tile_size

        self.grid_data = None

        self.setup()

        # вызов on_resize, для финальной инициализации
        self.on_resize(int(self.width), int(self.height))

    def setup(self):
        for h in range(VH):
            row = []
            for w in range(VW):
                sprite = arcade.Sprite(path_or_texture=self.conf.assets.texture('floor'), scale=0.1)
                sprite.curr_tex = ''

                self.tile_sprite_list.append(sprite)
                row.append(sprite)
            self.display_tiles_data.append(row)

    # -- отрисовка
    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.camera.use()

        self.clear()
        self.ui.draw()
        self.tile_sprite_list.draw()
        self.entities_sprite_list.draw()

        if self.conf.DEBUG:
            self.panel.draw()

        self.cursor_camera.use()

        self.mouse_sprite_list.draw()

    # -- обновление состояния
    def on_update(self, delta_time):
        self.update_positions()
        self.update_textures()
        self.entities_sprite_list.update_animation(delta_time)

    def update_textures(self):
        def cost_to_alpha(cost, mcost):
            cost = max(0, min(cost, mcost))
            min_alpha = 100
            max_alpha = 255

            return max_alpha - (cost / mcost) * (max_alpha - min_alpha)

        if self.grid_data is None or [self.player.x, self.player.y] != self.prev_player_pos:
            self.grid_data = priority_flood(self.player.x, self.player.y)
            self.prev_player_pos = [self.player.x, self.player.y]

        mapping = self.grid_data
        for sy in range(VH):
            for sx in range(VW):
                if (sx, VH - 1 - sy) in mapping:
                    wx, wy, t, cost = mapping[(sx, VH - 1 - sy)]
                    mcost = 10
                    self.display_tiles_data[sy][sx].alpha = cost_to_alpha(cost, mcost)
                    if 'texture' in t and '.' in t['texture']:
                        t['texture'] = t['texture'].split('.')[0]
                    if t['type'] != 'void':
                        if self.display_tiles_data[sy][sx].curr_tex != t['texture']:
                            try:
                                if t['type'] == 'enemy':
                                    self.display_tiles_data[sy][sx].texture = self.conf.assets.texture(
                                        t['enemy']['texture'].split('.')[0])
                                    self.display_tiles_data[sy][sx].curr_tex = t['enemy']['texture'].split('.')[0]
                                else:
                                    self.display_tiles_data[sy][sx].texture = self.conf.assets.texture(t['texture'])
                                    self.display_tiles_data[sy][sx].curr_tex = t['texture']
                            except Exception as e:
                                self.display_tiles_data[sy][sx].texture = self.conf.assets.texture('grass_tile1')
                                self.display_tiles_data[sy][sx].curr_tex = t['texture']
                            self.display_tiles_data[sy][sx].visible = True
                    else:
                        self.display_tiles_data[sy][sx].visible = False
                        self.display_tiles_data[sy][sx].curr_tex = 'void'
                else:
                    self.display_tiles_data[sy][sx].visible = False
                    self.display_tiles_data[sy][sx].curr_tex = 'void'
        self.update_positions()

    def update_positions(self):
        center_x, center_y = self.camera.position
        start_y = (self.tile_size * len(self.display_tiles_data)) / -2 + self.tile_size / 2
        start_x = (self.tile_size * len(self.display_tiles_data[0])) / -2 + self.tile_size / 2

        for col in range(len(self.display_tiles_data)):
            for row in range(len(self.display_tiles_data[col])):
                tile = self.display_tiles_data[col][row]

                tile.center_x = center_x + start_x + row * self.tile_size
                tile.center_y = center_y + start_y + col * self.tile_size

                tile.scale = (self.tile_size + 1) / (tile.width / tile.scale[0])

        self.player_sprite.position = self.camera.position
        self.player_sprite.scale = (self.tile_size + 1) / (self.player_sprite.height / self.player_sprite.scale[0])

    # -- обработка ввода пользователя
    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif key == self.conf.KEYS['move_up']:
            x, y = step(self.player.x, self.player.y, 'up')
            if tile(x, y)['type'] != 'wall':
                self.player.x, self.player.y = x, y
                self.player_sprite.walking = 0.5
            if tile(x, y)['type'] == 'enemy':
                self.load_enemy_fight()
        elif key == self.conf.KEYS['move_down']:
            x, y = step(self.player.x, self.player.y, 'down')
            if tile(x, y)['type'] != 'wall':
                self.player.x, self.player.y = x, y
                self.player_sprite.walking = 0.5
            if tile(x, y)['type'] == 'enemy':
                self.load_enemy_fight()
        elif key == self.conf.KEYS['move_left']:
            x, y = step(self.player.x, self.player.y, 'left')
            if tile(x, y)['type'] != 'wall':
                self.player.x, self.player.y = x, y
                self.player_sprite.walking = 0.5
            if tile(x, y)['type'] == 'enemy':
                self.load_enemy_fight()
        elif key == self.conf.KEYS['move_right']:
            x, y = step(self.player.x, self.player.y, 'right')
            if tile(x, y)['type'] != 'wall':
                self.player.x, self.player.y = x, y
                self.player_sprite.walking = 0.5
            if tile(x, y)['type'] == 'enemy':
                self.load_enemy_fight()
        elif key == self.conf.KEYS['escape']:
            self.go_to_menu()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        wx, wy, _ = self.cursor_camera.unproject((x, y))
        self.mouse.position = (wx, wy)

    # -- Системные события
    def on_show_view(self):
        global world, W, H

        self.ui.enable()
        self.conf.music.ensure_playing('game')

        if self.conf.DEBUG:
            self.panel.enable()

        self.on_resize(int(self.width), int(self.height))

        world = self.conf.data.data['worlds'][self.conf.current_world]['tiles']
        W, H = len(world), len(world[0])

    def on_hide_view(self):
        self.ui.disable()
        self.save_all()

        if self.conf.DEBUG:
            self.panel.disable()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.scaling = min(width / 800, height / 600)
        self.tile_size = self.base_tile_size * self.scaling

        for i in self.matching_cameras:
            i.match_window()

    # вспомогательные функции
    def go_to_menu(self):
        from .game_menu import Main as play_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        next_view = play_view(self.conf)
        self.window.show_view(next_view)

    def fix_json(self):
        if 'cleanuped' in self.conf.data.data['worlds'][self.conf.current_world]:
            return
        for i in range(len(self.conf.data.data['worlds'][self.conf.current_world]['tiles'])):
            for j in range(len(self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i])):
                til = self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i][j]
                if 'wall' in til and til['wall']['texture'] != '2026-01-30_21-02-15.png':
                    self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i][j]['type'] = 'wall'
                    tex = self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i][j]['wall']['texture']
                    self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i][j]['texture'] = tex
                if 'enemy' in til:
                    if til['enemy']['texture'] not in ['2026-01-30_21-03-01.png', '2026-01-30_21-02-15.png']:
                        self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i][j]['type'] = 'wall'
                        tex = self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i][j]['enemy']['texture']
                        self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i][j]['texture'] = tex
                    else:
                        self.conf.data.data['worlds'][self.conf.current_world]['tiles'][i][j]['type'] = 'enemy'


        self.conf.data.data['worlds'][self.conf.current_world]['tiles'] = \
            self.conf.data.data['worlds'][self.conf.current_world]['tiles'][::-1]

        self.conf.data.data['worlds'][self.conf.current_world]['cleanuped'] = True
        self.conf.data.data['worlds'][self.conf.current_world]['player'] = {'health': 100,
                                                                            'x': 11,
                                                                            'y': 11,
                                                                            'name': 'Иванушка',
                                                                            'inventory': [{'type': 'heal', 'heal': 20,
                                                                                           'texture': 'bottle_20'},
                                                                                          {'type': 'heal', 'heal': 10,
                                                                                           'texture': 'bottle_10'},
                                                                                          {'type': 'heal', 'heal': 10,
                                                                                           'texture': 'bottle_10'},
                                                                                          {'type': 'heal', 'heal': 20,
                                                                                           'texture': 'bottle_10'}
                                                                                          ],
                                                                            'speed': 300}

        self.conf.data.save_data()

    def save_all(self):
        self.conf.data.data['worlds'][self.conf.current_world]['player'] = {'health': self.player.health,
                                                                            'x': self.player.x,
                                                                            'y': self.player.y,
                                                                            'name': 'Иванушка',
                                                                            'inventory': self.player.inventory,
                                                                            'speed': self.player.speed}
        self.conf.data.save_data()

    def load_enemy_fight(self):
        from .battle_arena import Main as play_view
        self.conf.enemy = Enemy(tile(self.player.x, self.player.y)['enemy']['texture'].split('.')[0], 100, self.conf.assets)
        arcade.play_sound(self.conf.assets.effect('danger'))
        next_view = play_view(self.conf)
        self.window.show_view(next_view)