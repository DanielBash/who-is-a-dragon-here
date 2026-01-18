"""view: редактор миров"""

import time
import json
from pathlib import Path
import arcade
import arcade.gui
import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.experimental import Shadertoy
import config


class Main(arcade.View):
    def __init__(self, config):
        super().__init__()
        self.conf = config
        self.scaling = self.width / 800

        self.background_color = arcade.color.Color(33, 23, 41)
        self.camera_speed = 100

        self.edit_mode = 'tile'
        self.selected_portal = 0
        self.portal_colors = [
            arcade.color.RED,
            arcade.color.ORANGE,
            arcade.color.GREEN,
            arcade.color.PURPLE,
        ]

        self.selected_tile = 'floor'

        self.tiles = arcade.SpriteList(use_spatial_hash=True)
        self.floor_sprites = arcade.SpriteList(use_spatial_hash=True)
        self.wall_sprites = arcade.SpriteList(use_spatial_hash=True)
        self.portal_sprites = arcade.SpriteList(use_spatial_hash=True)
        self.ui = arcade.gui.UIManager()

        self.layout = arcade.gui.UIAnchorLayout()

        # -- панель режимов
        self.tool_panel = arcade.gui.UIBoxLayout(vertical=False, space_between=5)

        self.tile_mode_btn = arcade.gui.UIFlatButton(text='тайлы', width=80)
        self.portal_mode_btn = arcade.gui.UIFlatButton(text='порталы', width=80)

        self.tile_mode_btn.on_click = lambda e: self.set_edit_mode('tile')
        self.portal_mode_btn.on_click = lambda e: self.set_edit_mode('portal')

        self.tool_panel.add(self.tile_mode_btn)
        self.tool_panel.add(self.portal_mode_btn)

        # -- панель выбора типа
        self.tile_panel = arcade.gui.UIBoxLayout(vertical=False, space_between=5)

        self.floor_btn = arcade.gui.UIFlatButton(text='пол', width=60, height=40)
        self.wall_btn = arcade.gui.UIFlatButton(text='стена', width=60, height=40)
        self.void_btn = arcade.gui.UIFlatButton(text='пустота', width=60, height=40)

        self.floor_btn.on_click = lambda e: self.select_tile('floor')
        self.wall_btn.on_click = lambda e: self.select_tile('wall')
        self.void_btn.on_click = lambda e: self.select_tile('void')

        self.tile_panel.add(self.floor_btn)
        self.tile_panel.add(self.wall_btn)
        self.tile_panel.add(self.void_btn)

        # -- панель порталов
        self.portal_panel = arcade.gui.UIBoxLayout(vertical=False, space_between=5)
        for i in range(len(self.portal_colors)):
            btn = arcade.gui.UIFlatButton(text=str(i), width=40, height=40)
            btn.on_click = lambda e, idx=i: self.select_portal(idx)
            self.portal_panel.add(btn)

        # -- кнопки управления
        world_data = self.conf.data.data['worlds'][self.conf.current_world]
        self.name_input = arcade.gui.UIInputText(width=200, height=30,
            text=world_data['name'])
        self.buttons = arcade.gui.UIButtonRow()

        self.export_button = arcade.gui.UIFlatButton(text='эксп.')
        self.save_button = arcade.gui.UIFlatButton(text='сохранить')
        self.exit_button = arcade.gui.UIFlatButton(text='выйти')

        self.exit_button.on_click = self.exit_button_click
        self.save_button.on_click = self.save_button_click
        self.export_button.on_click = self.export_button_click

        self.buttons.add(self.save_button)
        self.buttons.add(self.exit_button)
        self.buttons.add(self.export_button)

        # -- размещение ui
        top_layout = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        top_layout.add(self.tool_panel)

        self.portal_container = arcade.gui.UIBoxLayout(vertical=False, space_between=5)
        self.portal_container.add(self.portal_panel)
        self.portal_container.visible = False

        top_layout.add(self.portal_container)

        self.layout.add(top_layout, anchor_x='center', anchor_y='top')
        self.layout.add(self.tile_panel, anchor_x='center', anchor_y='bottom', align_y=40)
        self.layout.add(self.name_input, anchor_x='left', anchor_y='top', align_y=-40)
        self.layout.add(self.buttons, anchor_x='right', anchor_y='top')
        self.ui.add(self.layout)

        self.shadertoy = None

        self.on_resize(int(self.width), int(self.height))

        self.world_data = self.conf.data.data['worlds'][self.conf.current_world]

        self.tile_size = 50
        self.tile_texture_cache = {}

        self.camera = arcade.Camera2D()
        self.keys = set()

        self.status_text = ""
        self.status_timer = 0
        self.hover_tile = None

        self.setup()

        self.select_tile('floor')

    # -- смена режима
    def set_edit_mode(self, mode):
        self.edit_mode = mode
        self.status_text = f"режим: {mode}"
        self.status_timer = 2.0

        if mode == 'portal':
            self.portal_container.visible = True
        else:
            self.portal_container.visible = False

    # -- выбор портала
    def select_portal(self, portal_id):
        self.selected_portal = portal_id
        self.status_text = f"портал: {portal_id}"
        self.status_timer = 2.0

    # -- выбор тайла
    def select_tile(self, tile_type):
        self.selected_tile = tile_type
        self.status_text = f"тайл: {tile_type}"
        self.status_timer = 2.0

        self.floor_btn.disabled = (tile_type == 'floor')
        self.wall_btn.disabled = (tile_type == 'wall')
        self.void_btn.disabled = (tile_type == 'void')

    # -- настройка мира
    def setup(self):
        self.floor_sprites.clear()
        self.wall_sprites.clear()
        self.portal_sprites.clear()

        width = self.world_data['width']
        height = self.world_data['height']

        for y in range(height):
            for x in range(width):
                tile_data = self.world_data['floor'][y][x]
                tile_type = tile_data['type']

                if tile_type != 'void':
                    tile = arcade.Sprite(self.load_texture('grass_tile1'))
                    tile.center_x = x * self.tile_size + self.tile_size // 2
                    tile.center_y = y * self.tile_size + self.tile_size // 2
                    tile.tile_x = x
                    tile.tile_y = y
                    tile.tile_type = 'floor'
                    self.floor_sprites.append(tile)

                if tile_type == 'wall':
                    wall = arcade.Sprite(self.load_texture('portal'))
                    wall.center_x = x * self.tile_size + self.tile_size // 2
                    wall.center_y = y * self.tile_size + self.tile_size // 2
                    wall.tile_x = x
                    wall.tile_y = y
                    wall.tile_type = 'wall'
                    self.wall_sprites.append(wall)

                for side, portal_id in tile_data['portals'].items():
                    if portal_id is not None:
                        self.add_portal_sprite(x, y, side, portal_id)

    # -- добавить спрайт портала
    def add_portal_sprite(self, x, y, side, portal_id):
        color = self.portal_colors[portal_id % len(self.portal_colors)]
        portal_width = 3

        if side in ['up', 'down']:
            portal_sprite = arcade.SpriteSolidColor(self.tile_size, portal_width, color)
        else:
            portal_sprite = arcade.SpriteSolidColor(portal_width, self.tile_size, color)

        if side == 'up':
            portal_sprite.center_x = x * self.tile_size + self.tile_size // 2
            portal_sprite.center_y = y * self.tile_size + self.tile_size - portal_width // 2
        elif side == 'down':
            portal_sprite.center_x = x * self.tile_size + self.tile_size // 2
            portal_sprite.center_y = y * self.tile_size + portal_width // 2
        elif side == 'left':
            portal_sprite.center_x = x * self.tile_size + portal_width // 2
            portal_sprite.center_y = y * self.tile_size + self.tile_size // 2
        elif side == 'right':
            portal_sprite.center_x = x * self.tile_size + self.tile_size - portal_width // 2
            portal_sprite.center_y = y * self.tile_size + self.tile_size // 2

        portal_sprite.side = side
        portal_sprite.portal_id = portal_id
        portal_sprite.tile_x = x
        portal_sprite.tile_y = y
        self.portal_sprites.append(portal_sprite)

    # -- загрузка текстуры
    def load_texture(self, name='grass_tile1'):
        if name not in self.tile_texture_cache:
            try:
                self.tile_texture_cache[name] = self.conf.assets.texture(name)
            except:
                if name == 'grass_tile1':
                    color = arcade.color.GREEN
                elif name == 'wall_tile':
                    color = arcade.color.DARK_GRAY
                else:
                    color = arcade.color.WHITE

                self.tile_texture_cache[name] = arcade.Texture.create_empty(name, (64, 64), color)
        return self.tile_texture_cache[name]

    def on_draw(self):
        self.draw_all()

    def draw_all(self):
        self.camera.use()
        self.clear()

        if self.shadertoy:
            self.shadertoy.render()

        self.floor_sprites.draw(pixelated=True)
        self.wall_sprites.draw(pixelated=True)
        self.portal_sprites.draw(pixelated=True)

        width = self.world_data['width']
        height = self.world_data['height']

        for x in range(width + 1):
            start_x = x * self.tile_size
            arcade.draw_line(
                start_x, 0,
                start_x, height * self.tile_size,
                arcade.color.DARK_GRAY, 1
            )

        for y in range(height + 1):
            start_y = y * self.tile_size
            arcade.draw_line(
                0, start_y,
                width * self.tile_size, start_y,
                arcade.color.DARK_GRAY, 1
            )

        self.ui.draw()

        if self.status_timer > 0:
            screen_x, screen_y = self.camera.position
            arcade.draw_text(
                self.status_text,
                screen_x - self.width // 2 + 10,
                screen_y + self.height // 2 - 30,
                arcade.color.WHITE,
                14
            )

        if self.hover_tile:
            tile_x, tile_y = self.hover_tile
            if 0 <= tile_x < width and 0 <= tile_y < height:
                left = tile_x * self.tile_size
                bottom = tile_y * self.tile_size

                arcade.draw_lbwh_rectangle_outline(
                    left, bottom,
                    self.tile_size, self.tile_size,
                    arcade.color.YELLOW, 2
                )

                tile_data = self.world_data['floor'][tile_y][tile_x]
                info = f"{tile_x},{tile_y} - {tile_data['type']}"

                text_x = left + 5
                text_y = bottom + self.tile_size - 15

                arcade.draw_text(
                    info,
                    text_x, text_y,
                    arcade.color.YELLOW,
                    10
                )

    def on_update(self, delta_time: float):
        if self.shadertoy:
            self.shadertoy.program['time'] = int(time.time() * 10000)

        if self.status_timer > 0:
            self.status_timer -= delta_time

        pos = [self.camera.position.x, self.camera.position.y]
        if self.conf.KEYS['move_up'] in self.keys:
            pos[1] += delta_time * self.camera_speed * (5 / self.camera.zoom)

        if self.conf.KEYS['move_down'] in self.keys:
            pos[1] -= delta_time * self.camera_speed * (5 / self.camera.zoom)

        if self.conf.KEYS['move_left'] in self.keys:
            pos[0] -= delta_time * self.camera_speed * (5 / self.camera.zoom)

        if self.conf.KEYS['move_right'] in self.keys:
            pos[0] += delta_time * self.camera_speed * (5 / self.camera.zoom)

        if self.conf.KEYS['zoom_in'] in self.keys:
            self.camera.zoom *= 1.1

        if self.conf.KEYS['zoom_out'] in self.keys:
            self.camera.zoom *= 0.9

        self.camera.position = pos

    def on_key_press(self, key, key_modifiers):
        if key == self.conf.KEYS['fullscreen']:
            self.window.set_fullscreen(not self.window.fullscreen)
        self.keys.add(key)

        if key == self.conf.KEYS['mode_toggle']:
            self.set_edit_mode('portal' if self.edit_mode == 'tile' else 'tile')

        elif key == arcade.key.KEY_1:
            self.select_tile('floor')
        elif key == arcade.key.KEY_2:
            self.select_tile('wall')
        elif key == arcade.key.KEY_3:
            self.select_tile('void')

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in self.keys:
            self.keys.remove(symbol)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        world_pos = self.camera.unproject((x, y))

        if world_pos is None:
            self.hover_tile = None
            return

        tile_x = int(world_pos.x // self.tile_size)
        tile_y = int(world_pos.y // self.tile_size)

        width = self.world_data['width']
        height = self.world_data['height']

        if 0 <= tile_x < width and 0 <= tile_y < height:
            self.hover_tile = (tile_x, tile_y)
        else:
            self.hover_tile = None

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        world_pos = self.camera.unproject((x, y))

        if world_pos is None:
            return

        tile_x = int(world_pos.x // self.tile_size)
        tile_y = int(world_pos.y // self.tile_size)

        width = self.world_data['width']
        height = self.world_data['height']

        if not (0 <= tile_x < width and 0 <= tile_y < height):
            return

        tile_data = self.world_data['floor'][tile_y][tile_x]
        current_type = tile_data['type']

        if self.edit_mode == 'tile':
            if button == arcade.MOUSE_BUTTON_LEFT:
                if self.selected_tile == 'void':
                    tile_data['type'] = 'void'
                    tile_data['portals'] = {'up': None, 'down': None, 'left': None, 'right': None}
                elif self.selected_tile == 'floor':
                    if current_type != 'void':
                        tile_data['type'] = 'floor'
                    else:
                        tile_data['type'] = 'floor'
                        tile_data['portals'] = {'up': None, 'down': None, 'left': None, 'right': None}
                elif self.selected_tile == 'wall':
                    if current_type == 'void':
                        tile_data['type'] = 'wall'
                        tile_data['portals'] = {'up': None, 'down': None, 'left': None, 'right': None}
                    else:
                        tile_data['type'] = 'wall'

                self.setup()

            elif button == arcade.MOUSE_BUTTON_RIGHT:
                if current_type == 'wall':
                    tile_data['type'] = 'floor'
                else:
                    tile_data['type'] = 'wall'

                self.setup()

        elif self.edit_mode == 'portal':
            rel_x = world_pos.x % self.tile_size
            rel_y = world_pos.y % self.tile_size

            side = None
            if rel_y < self.tile_size * 0.2:
                side = 'up'
            elif rel_x < self.tile_size * 0.2:
                side = 'left'

            if side:
                if button == arcade.MOUSE_BUTTON_LEFT:
                    if tile_data['portals'][side] == self.selected_portal:
                        tile_data['portals'][side] = None
                    else:
                        tile_data['portals'][side] = self.selected_portal
                    self.setup()

                elif button == arcade.MOUSE_BUTTON_RIGHT:
                    if tile_data['portals'][side] is not None:
                        tile_data['portals'][side] = (tile_data['portals'][side] + 1) % len(self.portal_colors)
                        self.setup()

            elif button == arcade.MOUSE_BUTTON_MIDDLE:
                self.selected_portal = (self.selected_portal + 1) % len(self.portal_colors)
                self.status_text = f"портал: {self.selected_portal}"
                self.status_timer = 2.0

    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        if scroll_y == 0:
            return

        factor = 1.1 if scroll_y > 0 else 0.9

        before = self.camera.unproject((x, y))
        self.camera.zoom *= factor
        after = self.camera.unproject((x, y))
        self.camera.position += before - after

    def exit_button_click(self, event):
        from .save_select import Main as next_view
        arcade.play_sound(self.conf.assets.effect('button_click'))
        prev_view = next_view(self.conf)
        self.window.show_view(prev_view)

    def save_button_click(self, event):
        arcade.play_sound(self.conf.assets.effect('button_click'))
        self.conf.data.data['worlds'][self.conf.current_world]['name'] = self.name_input.text
        self.conf.data.save_data()
        self.status_text = "сохранено!"
        self.status_timer = 2.0

    def export_button_click(self, event):
        arcade.play_sound(self.conf.assets.effect('button_click'))

        width = self.world_data['width']
        height = self.world_data['height']

        export_world = []

        for x in range(width):
            column = []
            for y in range(height):
                tile = self.world_data['floor'][y][x]

                pygame_tile = {
                    'type': tile['type'],
                    'portals': {
                        'up': tile['portals']['up'],
                        'down': tile['portals']['down'],
                        'left': tile['portals']['left'],
                        'right': tile['portals']['right']
                    }
                }
                column.append(pygame_tile)
            export_world.append(column)

        world_name = self.world_data['name']
        safe_name = "".join(c for c in world_name if c.isalnum() or c in (' ', '_')).rstrip()
        if not safe_name:
            safe_name = "world"

        export_path = Path(f'{safe_name}.json')

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_world, f, indent=2, ensure_ascii=False)

        self.status_text = f"экспорт: {export_path.absolute()}"
        self.status_timer = 3.0
        self.conf.logger.log(f"мир '{world_name}' экспорт в {export_path.absolute()}")


    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_playing('editor_music')
        self.on_resize(int(self.width), int(self.height))

    def on_hide_view(self):
        self.ui.disable()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        shader_file_path = self.conf.SHADER_FOLDER / 'background.glsl'
        window_size = self.window.get_size()
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

        if hasattr(self, 'camera'):
            self.camera.match_window()