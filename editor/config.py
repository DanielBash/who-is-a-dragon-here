"""FILE: Конфигурация
 - Управление глобальными данными и настройками приложения"""

import gzip
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import arcade
import pyglet

from views import intro, menu


class PathConfig:
    def __init__(self, data_file: Path, asset_folder: Path, shader_folder: Path):
        self.supported_ext = ['.png', '.jpg', '.jpeg', '.ico', '.json', '.mp3', '.wav']

        # Корневые директории
        self.data_file = data_file
        self.asset_folder = asset_folder
        self.shader_folder = shader_folder

        # Ярлыки для быстрого доступа к ресурсам
        self.shortcuts = {
            'icon': self.asset_folder / Path('images/icons'),
            'effect': self.asset_folder / Path('sounds/effects'),
            'music': self.asset_folder / Path('sounds/music'),
            'texture': self.asset_folder / Path('images/textures'),
        }

        self.icon_folder = self.asset_folder / Path('images/icons')

        self.music_folder = self.asset_folder / Path('sounds/music')
        self.sound_effects_folder = self.asset_folder / Path('sounds/effects')

        # реконфигурация файловой системы сборки
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            os.chdir(sys._MEIPASS)

    # -- Базовый метод поиска файла
    def get(self, folder, name) -> Optional[Path]:
        path = folder / Path(name)

        if not path.exists():
            for i in self.supported_ext:
                path = folder / Path(name + i)
                if path.exists():
                    return path

        return None

    # -- Сокращенные обращения
    def short(self, short, name) -> Path:
        return self.get(self.shortcuts[short], name)


# -- Загрузка различных элементов
class AssetsConfig:
    def __init__(self, paths: PathConfig):
        self.paths = paths

    def icon(self, name: str) -> pyglet.image.AbstractImage:
        image_path = self.paths.short('icon', name)

        return pyglet.image.load(str(image_path))

    def music(self, name: str, streaming: bool = True) -> arcade.Sound:
        music_path = self.paths.short('music', name)

        return arcade.load_sound(music_path, streaming=streaming)

    def effect(self, name: str, streaming: bool = True) -> arcade.Sound:
        music_path = self.paths.short('effect', name)

        return arcade.load_sound(music_path, streaming=streaming)

    def texture(self, name: str) -> arcade.Texture:
        return arcade.load_texture(self.paths.short('texture', name))



class DataConfig:
    def __init__(self, paths):
        self.paths = paths
        self.data = {}
        self.load_data()

    def prepare(self):
        self.paths.data_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.paths.data_file.exists():
            self._write_gz({})

    def load_data(self):
        # -- Загрузка данных из файла
        self.prepare()

        try:
            with gzip.open(self.paths.data_file, "rt", encoding="utf-8") as f:
                self.data = json.load(f)
                return
        except OSError:
            pass
        except json.JSONDecodeError:
            self.data = {}
            return

        try:
            # - Резервная загрузка из несжатого файла
            with self.paths.data_file.open("r", encoding="utf-8") as f:
                self.data = json.load(f)

            self.save_data()

        except Exception:
            self.data = {}

    def save_data(self):
        self._write_gz(self.data)

    def _write_gz(self, data: dict):
        # - Запись с сжатием
        tmp = self.paths.data_file.with_suffix(".tmp")

        with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                separators=(",", ":"),
            )

        tmp.replace(self.paths.data_file)


# -- Управление воспроизведением музыки
class MusicConfig:
    def __init__(self, assets: AssetsConfig):
        self.assets = assets

        self.playing_name = ''
        self.music = None

    def ensure_playing(self, name, loop=True):
        if self.playing_name == name:
            return
        if self.music:
            arcade.stop_sound(self.music)
        self.playing_name = name
        self.music = arcade.play_sound(self.assets.music(name), loop=loop)

    def play_sound(self, name):
        arcade.play_sound(self.assets.effect(name))


@dataclass
class Config:
    # -- КОНСТАНТЫ

    # window params
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 400
    WINDOW_RESIZABLE = True
    WINDOW_NAME = 'Редактор странных карт'

    WINDOW_MINIMAL_WIDTH = 200
    WINDOW_MINIMAL_HEIGHT = 200

    WINDOW_ICON = 'window_icon'

    # Управление видами
    LAUNCH_VIEW = menu.Main

    # Пути
    DATA_FILE = Path('saves/save.json')
    ASSETS_FOLDER = Path('assets')
    SHADER_FOLDER = Path('shaders')

    # Управление
    KEYS = {'fullscreen': arcade.key.F11,
            'move_up': arcade.key.W,
            'move_down': arcade.key.S,
            'move_left': arcade.key.A,
            'move_right': arcade.key.D,
            'zoom_in': arcade.key.UP,
            'zoom_out': arcade.key.DOWN,
            'action': arcade.key.Z}

    # Общие настройки отладки
    DEBUG = True

    # - ДИНАМИЧЕСКИЕ КОНФИГУРАЦИОННЫЕ МОДУЛИ
    paths: PathConfig = PathConfig(DATA_FILE, ASSETS_FOLDER, SHADER_FOLDER)
    assets: AssetsConfig = AssetsConfig(paths)
    data: DataConfig = DataConfig(paths)
    music: MusicConfig = MusicConfig(assets)

    start_time = time.time()

    current_world = 0