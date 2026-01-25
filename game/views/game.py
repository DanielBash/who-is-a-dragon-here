"""СЦЕНА: Игра
 - Основной геймплей"""

# -- импорт модулей
import math, json, heapq, time
from math import sin
import arcade
import arcade.gui
import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.gui import UIStyleBase

DIRS = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
OPP = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
SIDES = list(DIRS)

W, H = 100, 100
VW, VH = 11, 11


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
    def __init__(self, x=0, y=0, inventory=None, health=100):
        if inventory is None:
            inventory = []
        self.x = x
        self.y = y
        self.inventory = inventory
        self.health = health


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

        self.mouse = arcade.Sprite(path_or_texture=self.conf.assets.texture('cursor'), scale=0.1)

        self.mouse_sprite_list = arcade.SpriteList()
        self.mouse_sprite_list.append(self.mouse)

        # камеры
        self.cursor_camera = arcade.Camera2D()
        self.camera = arcade.Camera2D()

        self.matching_cameras = [self.cursor_camera, self.camera]

        self.tile_sprite_list = arcade.SpriteList()
        self.entities_sprite_list = arcade.SpriteList()

        self.player = Player(50, 50)
        self.prev_player_pos = [self.player.x, self.player.y]
        self.player_sprite = arcade.Sprite(path_or_texture=self.conf.assets.texture('knight_standing'))
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

    def update_textures(self):
        if self.grid_data is None or [self.player.x, self.player.y] != self.prev_player_pos:
            self.grid_data = priority_flood(self.player.x, self.player.y)
            self.prev_player_pos = [self.player.x, self.player.y]
            self.conf.logger.log(f'Позиция игрока обновилась {self.prev_player_pos}')

        mapping = self.grid_data
        for sy in range(VH):
            for sx in range(VW):
                if (sx, sy) in mapping:
                    wx, wy, t, cost = mapping[(sx, VH - 1 - sy)]
                    if t['type'] != 'void':
                        if self.display_tiles_data[sy][sx].curr_tex != t['type']:
                            self.display_tiles_data[sy][sx].texture = self.conf.assets.texture(t['type'])
                            self.display_tiles_data[sy][sx].visible = True
                            self.display_tiles_data[sy][sx].curr_tex = t['type']
                    else:
                        self.display_tiles_data[sy][sx].visible = False
                        self.display_tiles_data[sy][sx].curr_tex = 'void'
                else:
                    self.display_tiles_data[sy][sx].visible = False
                    self.display_tiles_data[sy][sx].curr_tex = 'void'

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
            self.player.x, self.player.y = x, y
        elif key == self.conf.KEYS['move_down']:
            x, y = step(self.player.x, self.player.y, 'down')
            self.player.x, self.player.y = x, y
        elif key == self.conf.KEYS['move_left']:
            x, y = step(self.player.x, self.player.y, 'left')
            self.player.x, self.player.y = x, y
        elif key == self.conf.KEYS['move_right']:
            x, y = step(self.player.x, self.player.y, 'right')
            self.player.x, self.player.y = x, y
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
