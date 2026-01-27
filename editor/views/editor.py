import time
import json
from pathlib import Path
import arcade
import arcade.gui
from arcade.experimental import Shadertoy
import config

import tkinter as tk
from tkinter import filedialog


class Main(arcade.View):
    def __init__(self, config):
        super().__init__()
        self.conf = config

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
        self.custom_tile_texture = None
        self.custom_tile_name = None

        self.floor_sprites = arcade.SpriteList(use_spatial_hash=True)
        self.wall_sprites = arcade.SpriteList(use_spatial_hash=True)
        self.portal_sprites = arcade.SpriteList(use_spatial_hash=True)
        self.enemy_sprites = arcade.SpriteList(use_spatial_hash=True)
        self.item_sprites = arcade.SpriteList(use_spatial_hash=True)

        self.ui = arcade.gui.UIManager()
        self.layout = arcade.gui.UIAnchorLayout()

        self.tool_panel = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        self.custom_tile_container = arcade.gui.UIBoxLayout(vertical=False)
        self.control_buttons_container = arcade.gui.UIBoxLayout(vertical=True, space_between=5)
        self.tile_type_container = arcade.gui.UIBoxLayout(vertical=False, space_between=10)

        self.tile_mode_btn = arcade.gui.UIFlatButton(text='тайлы', width=80)
        self.portal_mode_btn = arcade.gui.UIFlatButton(text='порталы', width=80)
        self.enemy_mode_btn = arcade.gui.UIFlatButton(text='враги', width=80)

        def set_tile_mode(event):
            self.set_edit_mode('tile')

        def set_portal_mode(event):
            self.set_edit_mode('portal')

        def set_enemy_mode(event):
            self.set_edit_mode('enemy')

        self.tile_mode_btn.on_click = set_tile_mode
        self.portal_mode_btn.on_click = set_portal_mode
        self.enemy_mode_btn.on_click = set_enemy_mode

        self.tool_panel.add(self.tile_mode_btn)
        self.tool_panel.add(self.portal_mode_btn)
        self.tool_panel.add(self.enemy_mode_btn)

        self.custom_tile_btn = arcade.gui.UIFlatButton(text='выбрать тайл', width=120)
        self.custom_tile_btn.on_click = self.select_custom_tile
        self.custom_tile_container.add(self.custom_tile_btn)

        self.floor_btn = arcade.gui.UIFlatButton(text='пол', width=80, height=40)
        self.wall_btn = arcade.gui.UIFlatButton(text='стена', width=80, height=40)
        self.void_btn = arcade.gui.UIFlatButton(text='пустота', width=80, height=40)
        self.item_btn = arcade.gui.UIFlatButton(text='предмет', width=80, height=40)

        def select_floor(event):
            self.select_tile('floor')

        def select_wall(event):
            self.select_tile('wall')

        def select_void(event):
            self.select_tile('void')

        def select_item(event):
            self.select_tile('item')

        self.floor_btn.on_click = select_floor
        self.wall_btn.on_click = select_wall
        self.void_btn.on_click = select_void
        self.item_btn.on_click = select_item

        self.tile_type_container.add(self.floor_btn)
        self.tile_type_container.add(self.wall_btn)
        self.tile_type_container.add(self.void_btn)
        self.tile_type_container.add(self.item_btn)

        self.portal_container = arcade.gui.UIBoxLayout(vertical=False, space_between=5)
        self.portal_container.visible = False
        self.enemy_container = arcade.gui.UIBoxLayout(vertical=False, space_between=5)
        self.enemy_container.visible = False

        world_data = self.conf.data.data['worlds'][self.conf.current_world]
        self.name_input = arcade.gui.UIInputText(width=200, height=30, text=world_data['name'])

        self.save_button = arcade.gui.UIFlatButton(text='сохранить', width=100)
        self.exit_button = arcade.gui.UIFlatButton(text='выйти', width=100)
        self.export_button = arcade.gui.UIFlatButton(text='экспорт', width=100)

        self.exit_button.on_click = self.exit_button_click
        self.save_button.on_click = self.save_button_click
        self.export_button.on_click = self.export_button_click

        self.control_buttons_container.add(self.save_button)
        self.control_buttons_container.add(self.export_button)
        self.control_buttons_container.add(self.exit_button)

        self.layout.add(
            self.tool_panel,
            anchor_x='left',
            anchor_y='top',
            align_x=135,
            align_y=0
        )

        self.layout.add(
            self.custom_tile_container,
            anchor_x='left',
            anchor_y='top',
            align_x=0,
            align_y=0
        )

        self.layout.add(
            self.name_input,
            anchor_x='left',
            anchor_y='top',
            align_x=20,
            align_y=-60
        )

        self.layout.add(
            self.control_buttons_container,
            anchor_x='right',
            anchor_y='top',
            align_x=0,
            align_y=0
        )

        self.layout.add(
            self.tile_type_container,
            anchor_x='left',
            anchor_y='bottom',
            align_y=0
        )

        self.layout.add(
            self.portal_container,
            anchor_x='center',
            anchor_y='top',
            align_y=-80
        )

        self.layout.add(
            self.enemy_container,
            anchor_x='center',
            anchor_y='top',
            align_y=-80
        )

        self.ui.add(self.layout)
        self.shadertoy = None
        self.on_resize(int(self.width), int(self.height))

        self.world_data = self.conf.data.data['worlds'][self.conf.current_world]
        self.tile_size = 32
        self.tile_texture_cache = {}

        self.custom_textures = {}

        self.initialize_tile_data()

        self.camera = arcade.Camera2D()
        self.keys = set()

        self.status_text = ''
        self.status_timer = 0
        self.hover_tile = None

        self.editing_dialog = False
        self.dialog_input = None
        self.dialog_window = None
        self.enemy_tile = None

        self.setup()
        self.select_tile('floor')

    def initialize_tile_data(self):
        for y in range(self.world_data['height']):
            for x in range(self.world_data['width']):
                tile_data = self.world_data['floor'][y][x]

                if 'type' not in tile_data:
                    tile_data['type'] = 'floor'

                if 'portals' not in tile_data:
                    tile_data['portals'] = {'up': None, 'down': None, 'left': None, 'right': None}

                if 'enemy' not in tile_data:
                    tile_data['enemy'] = None

                if 'wall' not in tile_data:
                    tile_data['wall'] = None

                if 'item' not in tile_data:
                    tile_data['item'] = None

                if tile_data['type'] == 'floor' and 'texture' not in tile_data:
                    tile_data['texture'] = 'grass_tile1.png'

    def load_custom_texture(self, filename):
        if filename not in self.custom_textures:
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                filename = f"{filename}.png"

            texture_path = self.conf.ASSETS_FOLDER / 'images' / 'textures' / filename
            if texture_path.exists():
                texture = arcade.load_texture(texture_path)
                self.custom_textures[filename] = texture
            else:
                base_name = Path(filename).stem
                for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                    alt_path = self.conf.ASSETS_FOLDER / 'images' / 'textures' / f"{base_name}{ext}"
                    if alt_path.exists():
                        texture = arcade.load_texture(alt_path)
                        self.custom_textures[filename] = texture
                        return texture
                return None
        return self.custom_textures.get(filename)

    def select_custom_tile(self, event):
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            title="Выберите изображение для тайла",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("Все файлы", "*.*")
            ]
        )

        if file_path:
            texture = arcade.load_texture(file_path)
            self.custom_tile_texture = texture
            filename = Path(file_path).name
            self.custom_tile_name = filename
            self.custom_textures[filename] = texture

            self.status_text = f'Выбран тайл: {filename}'
            self.status_timer = 2.0

        root.destroy()

    def open_dialog_editor(self, tile_x, tile_y):
        tile_data = self.world_data['floor'][tile_y][tile_x]
        if not tile_data.get('enemy'):
            return

        enemy_data = tile_data['enemy']

        self.dialog_window = arcade.gui.UIManager()
        dialog_box = arcade.gui.UIBoxLayout(vertical=True)

        title_label = arcade.gui.UILabel(
            text=f"Редактор диалогов врага",
            width=400,
            height=30,
            font_size=16,
            align="center",
            text_color=arcade.color.WHITE
        )
        dialog_box.add(title_label)

        dialog_text = ""
        if 'data' in enemy_data and 'dialog' in enemy_data['data']:
            dialog_dict = enemy_data['data']['dialog']
            lines = []
            for key in sorted(dialog_dict.keys()):
                lines.append(f"{key}: {dialog_dict[key]}")
            dialog_text = "\n".join(lines)

        self.dialog_input = arcade.gui.UIInputText(
            text=dialog_text,
            width=400,
            height=200,
            multiline=True
        )
        dialog_box.add(self.dialog_input)

        hint_label = arcade.gui.UILabel(
            text="Формат: номер: текст\nПример:\n1: Привет!\n2: Как дела?",
            width=400,
            height=60,
            font_size=12,
            align="left",
            text_color=arcade.color.LIGHT_GRAY
        )
        dialog_box.add(hint_label)

        button_row = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        save_btn = arcade.gui.UIFlatButton(text="Сохранить", width=120)
        cancel_btn = arcade.gui.UIFlatButton(text="Отмена", width=120)
        clear_btn = arcade.gui.UIFlatButton(text="Очистить", width=120)

        def save_dialog(event):
            dialog_text = self.dialog_input.text.strip()
            dialog_dict = {}

            if dialog_text:
                lines = dialog_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key and value:
                            dialog_dict[key] = value

            if 'data' not in enemy_data:
                enemy_data['data'] = {}

            if dialog_dict:
                enemy_data['data']['dialog'] = dialog_dict
            elif 'dialog' in enemy_data['data']:
                del enemy_data['data']['dialog']

            self.editing_dialog = False
            self.dialog_window.disable()
            self.dialog_window = None

            self.status_text = f'Диалог сохранён'
            self.status_timer = 2.0

        def cancel_dialog(event):
            self.editing_dialog = False
            self.dialog_window.disable()
            self.dialog_window = None

        def clear_dialog(event):
            self.dialog_input.text = ""

        save_btn.on_click = save_dialog
        cancel_btn.on_click = cancel_dialog
        clear_btn.on_click = clear_dialog

        button_row.add(save_btn)
        button_row.add(clear_btn)
        button_row.add(cancel_btn)
        dialog_box.add(button_row)

        modal = arcade.gui.UIAnchorLayout()
        modal.add(dialog_box)
        self.dialog_window.add(modal)
        self.dialog_window.enable()
        self.editing_dialog = True
        self.enemy_tile = (tile_x, tile_y)

    def set_edit_mode(self, mode):
        self.edit_mode = mode
        self.status_text = f'режим: {mode}'
        self.status_timer = 2.0
        self.portal_container.visible = (mode == 'portal')
        self.enemy_container.visible = (mode == 'enemy')

    def select_tile(self, tile_type):
        self.selected_tile = tile_type
        self.status_text = f'тайл: {tile_type}'
        self.status_timer = 2.0
        self.floor_btn.disabled = (tile_type == 'floor')
        self.wall_btn.disabled = (tile_type == 'wall')
        self.void_btn.disabled = (tile_type == 'void')
        self.item_btn.disabled = (tile_type == 'item')

    def setup(self):
        self.floor_sprites.clear()
        self.wall_sprites.clear()
        self.portal_sprites.clear()
        self.enemy_sprites.clear()
        self.item_sprites.clear()

        width = self.world_data['width']
        height = self.world_data['height']

        for y in range(height):
            for x in range(width):
                tile_data = self.world_data['floor'][y][x]
                tile_type = tile_data['type']

                if tile_type == 'floor':
                    texture_name = tile_data.get('texture', 'grass_tile1.png')

                    if not texture_name.lower().endswith('.png'):
                        texture_name = f"{texture_name}.png"

                    texture = None

                    if texture_name == 'grass_tile1.png':
                        texture = self.load_texture('grass_tile1')
                    elif texture_name in self.custom_textures:
                        texture = self.custom_textures[texture_name]
                    else:
                        texture = self.load_custom_texture(texture_name)

                    if texture is None:
                        texture = self.load_texture('grass_tile1')

                    floor_sprite = arcade.Sprite(
                        texture,
                        center_x=x * self.tile_size + self.tile_size // 2,
                        center_y=y * self.tile_size + self.tile_size // 2,
                        scale=self.tile_size / texture.width
                    )

                    floor_sprite.tile_x = x
                    floor_sprite.tile_y = y
                    floor_sprite.tile_type = 'floor'
                    self.floor_sprites.append(floor_sprite)

                elif tile_type == 'void':
                    pass

                if tile_data.get('wall'):
                    wall_data = tile_data['wall']

                    wall_texture = None
                    if wall_data.get('texture'):
                        texture_name = wall_data['texture']
                        if not texture_name.lower().endswith('.png'):
                            texture_name = f"{texture_name}.png"

                        if texture_name in self.custom_textures:
                            wall_texture = self.custom_textures[texture_name]
                        else:
                            wall_texture = self.load_custom_texture(texture_name)

                    if wall_texture:
                        wall_sprite = arcade.Sprite(
                            wall_texture,
                            center_x=x * self.tile_size + self.tile_size // 2,
                            center_y=y * self.tile_size + self.tile_size // 2
                        )
                    else:
                        wall_sprite = arcade.SpriteSolidColor(
                            self.tile_size, self.tile_size,
                            arcade.color.DARK_GRAY
                        )
                        wall_sprite.center_x = x * self.tile_size + self.tile_size // 2
                        wall_sprite.center_y = y * self.tile_size + self.tile_size // 2

                    wall_sprite.tile_x = x
                    wall_sprite.tile_y = y
                    wall_sprite.wall_type = 'wall'
                    self.wall_sprites.append(wall_sprite)

                if tile_data.get('item'):
                    item_data = tile_data['item']
                    item_texture = None
                    if item_data.get('texture'):
                        texture_name = item_data['texture']
                        if not texture_name.lower().endswith('.png'):
                            texture_name = f"{texture_name}.png"

                        if texture_name in self.custom_textures:
                            item_texture = self.custom_textures[texture_name]
                        else:
                            item_texture = self.load_custom_texture(texture_name)

                    if item_texture:
                        item_sprite = arcade.Sprite(
                            item_texture,
                            center_x=x * self.tile_size + self.tile_size // 2,
                            center_y=y * self.tile_size + self.tile_size // 2,
                            scale=(self.tile_size - 15) / item_texture.width
                        )
                    else:
                        item_sprite = arcade.SpriteSolidColor(
                            self.tile_size - 15, self.tile_size - 15,
                            arcade.color.GOLD
                        )
                        item_sprite.center_x = x * self.tile_size + self.tile_size // 2
                        item_sprite.center_y = y * self.tile_size + self.tile_size // 2

                    item_sprite.tile_x = x
                    item_sprite.tile_y = y
                    item_sprite.item_type = 'item'
                    self.item_sprites.append(item_sprite)

                if tile_data.get('enemy') and tile_type != 'void' and not tile_data.get('wall') and not tile_data.get('item'):
                    enemy_data = tile_data['enemy']
                    enemy_type = enemy_data.get('type', 'basic')

                    enemy_texture = None
                    if enemy_data.get('texture'):
                        texture_name = enemy_data['texture']
                        if not texture_name.lower().endswith('.png'):
                            texture_name = f"{texture_name}.png"

                        if texture_name in self.custom_textures:
                            enemy_texture = self.custom_textures[texture_name]
                        else:
                            enemy_texture = self.load_custom_texture(texture_name)

                    if enemy_texture:
                        enemy_sprite = arcade.Sprite(
                            enemy_texture,
                            center_x=x * self.tile_size + self.tile_size // 2,
                            center_y=y * self.tile_size + self.tile_size // 2,
                            scale=(self.tile_size + 5) / enemy_texture.width
                        )
                    else:
                        if enemy_type == 'basic':
                            enemy_color = arcade.color.RED
                        elif enemy_type == 'fast':
                            enemy_color = arcade.color.ORANGE
                        elif enemy_type == 'strong':
                            enemy_color = arcade.color.PURPLE
                        else:
                            enemy_color = arcade.color.GRAY

                        enemy_sprite = arcade.SpriteSolidColor(
                            self.tile_size - 10, self.tile_size - 10,
                            enemy_color
                        )
                        enemy_sprite.center_x = x * self.tile_size + self.tile_size // 2
                        enemy_sprite.center_y = y * self.tile_size + self.tile_size // 2

                    enemy_sprite.tile_x = x
                    enemy_sprite.tile_y = y
                    enemy_sprite.enemy_type = enemy_type
                    self.enemy_sprites.append(enemy_sprite)

                for side, portal_id in tile_data['portals'].items():
                    if portal_id is not None:
                        self.add_portal_sprite(x, y, side, portal_id)

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

    def load_texture(self, name='grass_tile1'):
        if name not in self.tile_texture_cache:
            texture = self.conf.assets.texture(name)
            self.tile_texture_cache[name] = texture
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
        self.item_sprites.draw(pixelated=True)
        self.portal_sprites.draw(pixelated=True)
        self.enemy_sprites.draw(pixelated=True)

        width = self.world_data['width']
        height = self.world_data['height']

        for y in range(height):
            for x in range(width):
                tile_data = self.world_data['floor'][y][x]
                if tile_data.get('enemy'):
                    enemy_data = tile_data['enemy']
                    if 'data' in enemy_data and 'dialog' in enemy_data['data']:
                        indicator_x = x * self.tile_size + self.tile_size - 8
                        indicator_y = y * self.tile_size + self.tile_size - 8
                        arcade.draw_circle_filled(
                            indicator_x, indicator_y, 4,
                            arcade.color.CYAN
                        )

        if self.edit_mode == 'portal':
            for x in range(width + 1):
                start_x = x * self.tile_size
                arcade.draw_line(start_x, 0, start_x, height * self.tile_size, arcade.color.DARK_GRAY, 1)

            for y in range(height + 1):
                start_y = y * self.tile_size
                arcade.draw_line(0, start_y, width * self.tile_size, start_y, arcade.color.DARK_GRAY, 1)
        else:
            arcade.draw_lbwh_rectangle_outline(0, 0, width * self.tile_size, height * self.tile_size,
                                               arcade.color.DARK_GRAY, 2)

        self.ui.draw()

        if self.editing_dialog and self.dialog_window:
            self.dialog_window.draw()

        if self.status_timer > 0:
            screen_x, screen_y = self.camera.position
            arcade.draw_text(self.status_text, screen_x - self.width // 2 + 10, screen_y + self.height // 2 - 30,
                             arcade.color.WHITE, 14)

        if self.hover_tile:
            tile_x, tile_y = self.hover_tile
            if 0 <= tile_x < width and 0 <= tile_y < height:
                left = tile_x * self.tile_size
                bottom = tile_y * self.tile_size
                arcade.draw_lbwh_rectangle_outline(left, bottom, self.tile_size, self.tile_size, arcade.color.YELLOW, 2)

    def on_update(self, delta_time):
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
            modes = ['tile', 'portal', 'enemy']
            current_idx = modes.index(self.edit_mode)
            next_idx = (current_idx + 1) % len(modes)
            self.set_edit_mode(modes[next_idx])
        elif key == arcade.key.KEY_1:
            self.select_tile('floor')
        elif key == arcade.key.KEY_2:
            self.select_tile('wall')
        elif key == arcade.key.KEY_3:
            self.select_tile('void')
        elif key == arcade.key.KEY_4:
            self.select_tile('item')

    def on_key_release(self, symbol, modifiers):
        if symbol in self.keys:
            self.keys.remove(symbol)

    def on_mouse_motion(self, x, y, dx, dy):
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

    def on_mouse_press(self, x, y, button, modifiers):
        if self.editing_dialog:
            return

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
                    tile_data['wall'] = None
                    tile_data['enemy'] = None
                    tile_data['item'] = None
                    if 'texture' in tile_data:
                        del tile_data['texture']

                elif self.selected_tile == 'floor':
                    if current_type == 'void':
                        tile_data['portals'] = {'up': None, 'down': None, 'left': None, 'right': None}
                        tile_data['texture'] = 'grass_tile1.png'

                    tile_data['type'] = 'floor'

                    if self.custom_tile_texture and self.custom_tile_name:
                        tile_data['texture'] = self.custom_tile_name
                        if not self.custom_tile_name.lower().endswith('.png'):
                            tile_data['texture'] = f"{self.custom_tile_name}.png"
                    elif 'texture' not in tile_data:
                        tile_data['texture'] = 'grass_tile1.png'

                elif self.selected_tile == 'wall':
                    if current_type == 'void':
                        self.status_text = 'Пол верни'
                        self.status_timer = 2.0
                        return

                    if tile_data.get('enemy'):
                        self.status_text = 'Баран, так незя'
                        self.status_timer = 2.0
                        return

                    if tile_data.get('wall'):
                        tile_data['wall'] = None
                    else:
                        wall_data = {
                            'type': 'wall',
                            'texture': None
                        }
                        if self.custom_tile_texture and self.custom_tile_name:
                            wall_data['texture'] = self.custom_tile_name
                            if not self.custom_tile_name.lower().endswith('.png'):
                                wall_data['texture'] = f"{self.custom_tile_name}.png"

                        tile_data['wall'] = wall_data

                elif self.selected_tile == 'item':
                    if current_type == 'void':
                        self.status_text = 'Пол верни'
                        self.status_timer = 2.0
                        return

                    if tile_data.get('enemy'):
                        self.status_text = 'На предмет нельзя поставить врага'
                        self.status_timer = 2.0
                        return

                    if tile_data.get('wall'):
                        self.status_text = 'На предмет нельзя поставить стену'
                        self.status_timer = 2.0
                        return

                    if tile_data.get('item'):
                        tile_data['item'] = None
                    else:
                        item_data = {
                            'type': 'item',
                            'texture': None
                        }
                        if self.custom_tile_texture and self.custom_tile_name:
                            item_data['texture'] = self.custom_tile_name
                            if not self.custom_tile_name.lower().endswith('.png'):
                                item_data['texture'] = f"{self.custom_tile_name}.png"

                        tile_data['item'] = item_data

                self.setup()

            elif button == arcade.MOUSE_BUTTON_RIGHT:
                if 'texture' in tile_data and tile_data['type'] == 'floor':
                    tile_data['texture'] = 'grass_tile1.png'
                    self.setup()

        elif self.edit_mode == 'portal':
            rel_x = world_pos.x % self.tile_size
            rel_y = world_pos.y % self.tile_size
            side = None

            if rel_y > self.tile_size * 0.8:
                side = 'up'
            elif rel_y < self.tile_size * 0.2:
                side = 'down'
            elif rel_x < self.tile_size * 0.2:
                side = 'left'
            elif rel_x > self.tile_size * 0.8:
                side = 'right'

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
                self.status_text = f'портал: {self.selected_portal}'
                self.status_timer = 2.0

        elif self.edit_mode == 'enemy':
            if button == arcade.MOUSE_BUTTON_LEFT:
                if current_type != 'void':
                    if tile_data.get('wall'):
                        self.status_text = 'Ты куку, так незя'
                        self.status_timer = 2.0
                        return

                    if tile_data.get('item'):
                        self.status_text = 'На предмет нельзя поставить врага'
                        self.status_timer = 2.0
                        return

                    if not tile_data.get('enemy'):
                        enemy_data = {
                            'type': 'basic',
                            'health': 100,
                            'damage': 10,
                            'hitbox': [0.1, 0.1, 0.8, 0.8],
                            'data': {}
                        }

                        if self.custom_tile_texture and self.custom_tile_name:
                            enemy_data['texture'] = self.custom_tile_name
                            if not self.custom_tile_name.lower().endswith('.png'):
                                enemy_data['texture'] = f"{self.custom_tile_name}.png"

                        tile_data['enemy'] = enemy_data
                        self.setup()
                    else:
                        tile_data['enemy'] = None
                        self.setup()
                else:
                    self.status_text = 'На пустоте нельзя ставить врага!'
                    self.status_timer = 2.0

            elif button == arcade.MOUSE_BUTTON_RIGHT:
                if tile_data.get('enemy'):
                    tile_data['enemy'] = None
                    self.setup()

            elif button == arcade.MOUSE_BUTTON_MIDDLE:
                if tile_data.get('enemy'):
                    self.open_dialog_editor(tile_x, tile_y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
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
        self.status_text = 'сохранено!'
        self.status_timer = 2.0

    def export_button_click(self, event):
        arcade.play_sound(self.conf.assets.effect('button_click'))

        width = self.world_data['width']
        height = self.world_data['height']

        export_data = {
            'metadata': {
                'name': self.world_data['name'],
                'width': width,
                'height': height,
                'export_date': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'tiles': []
        }

        for y in range(height):
            row = []
            for x in range(width):
                tile = self.world_data['floor'][y][x]
                tile_export = {
                    'type': tile['type'],
                    'portals': tile['portals'].copy()
                }

                if tile['type'] == 'floor':
                    tile_export['texture'] = tile.get('texture', 'grass_tile1.png')
                elif tile['type'] == 'void':
                    pass

                if tile.get('wall'):
                    wall_data = tile['wall'].copy()
                    tile_export['wall'] = wall_data

                if tile.get('item'):
                    item_data = tile['item'].copy()
                    tile_export['item'] = item_data

                if tile.get('enemy'):
                    enemy_data = tile['enemy'].copy()
                    if 'x' in enemy_data:
                        del enemy_data['x']
                    if 'y' in enemy_data:
                        del enemy_data['y']
                    tile_export['enemy'] = enemy_data

                row.append(tile_export)
            export_data['tiles'].append(row)

        world_name = self.world_data['name']
        safe_name = ''.join(c for c in world_name if c.isalnum() or c in (' ', '_')).rstrip()
        if not safe_name:
            safe_name = 'world'

        export_path = Path(f'{safe_name}.json')

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump({'template_world': export_data}, f, indent=2, ensure_ascii=False)

        self.status_text = f'экспорт: {export_path.absolute()}'
        self.status_timer = 3.0
        self.conf.logger.log(f"мир '{world_name}' экспорт в {export_path.absolute()}")

    def on_show_view(self):
        self.ui.enable()
        self.conf.music.ensure_playing('editor_music')
        self.on_resize(int(self.width), int(self.height))

    def on_hide_view(self):
        self.ui.disable()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        shader_file_path = self.conf.SHADER_FOLDER / 'background.glsl'
        window_size = self.window.get_size()
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

        if hasattr(self, 'camera'):
            self.camera.match_window()
