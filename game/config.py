"""СКРИПТ: Настройки/Конфигурация приложения
 - Управление глобальными переменными
 - Объявление констант
 - Менеджмент асетов и других ресурсов"""

# -- импорт модулей
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

from views import menu, intro, comics, battle_arena
import utilities as u


# === КЛАССЫ БЫСТРОГО ДОСТУПА К РЕСУРСАМ ===
# -- менеджер путей
class PathConfig:
    def __init__(self, data_file: Path, asset_folder: Path, shader_folder: Path):
        self.supported_ext = ['.png', '.jpg', '.jpeg', '.ico', '.json', '.mp3', '.wav', '.ogg', '.otf']

        # основные пути
        self.data_file = data_file
        self.asset_folder = asset_folder
        self.shader_folder = shader_folder

        # ярлыки обращения к ресурсам
        self.shortcuts = {
            'icon': self.asset_folder / Path('images/icons'),
            'effect': self.asset_folder / Path('sounds/effects'),
            'music': self.asset_folder / Path('sounds/music'),
            'texture': self.asset_folder / Path('images/textures'),
            'font': self.asset_folder / Path('fonts/')
        }

        # определение системы сборки
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            os.chdir(sys._MEIPASS)

    # - метод поиска файла в директории
    def get(self, folder: Path, name: str | Path) -> Optional[Path]:
        path = folder / Path(name)

        if not path.exists():
            for i in self.supported_ext:
                path = folder / Path(name + i)
                if path.exists():
                    return path

        return None

    # - доступ к ярлыкам
    def short(self, short: str, name: str | Path) -> Path:
        return self.get(self.shortcuts[short], name)


# -- подгрузка асетов
class AssetsConfig:
    def __init__(self, paths: PathConfig):
        self.paths = paths

    # - получение иконки
    def icon(self, name: str) -> pyglet.image.AbstractImage:
        image_path = self.paths.short('icon', name)

        return pyglet.image.load(str(image_path))

    # - получение музыки
    def music(self, name: str, streaming: bool = True) -> arcade.Sound:
        music_path = self.paths.short('music', name)

        return arcade.load_sound(music_path, streaming=streaming)

    # - получение звукового эффекта
    def effect(self, name: str, streaming: bool = True) -> arcade.Sound:
        music_path = self.paths.short('effect', name)

        return arcade.load_sound(music_path, streaming=streaming)

    # - получение текстуры
    def texture(self, name: str) -> arcade.Texture:
        return arcade.load_texture(self.paths.short('texture', name))

    # - получение шрифта
    def font(self, name: str) -> str:
        arcade.load_font(self.paths.short('font', name))


# -- обработка сохранений
class DataConfig:
    def __init__(self, paths):
        self.paths = paths
        self.data = {}
        self.load_data()

    # - создание целевой директории
    def prepare(self):
        self.paths.data_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.paths.data_file.exists():
            self.save_data()

    # - загрузка данных, распаковка
    def load_data(self):
        self.prepare()

        try:
            with gzip.open(self.paths.data_file, "rt", encoding="utf-8") as f:
                self.data = json.load(f)
                return
        except Exception as e:
            try:
                with self.paths.data_file.open("r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.save_data()
            except Exception as e:
                self.data = {}
                return

    # - сохранение данных
    def save_data(self):
        tmp = self.paths.data_file.with_suffix(".tmp")

        with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as f:
            json.dump(
                self.data,
                f,
                ensure_ascii=False,
                separators=(",", ":"),
            )

        tmp.replace(self.paths.data_file)


# -- управление воспроизведением музыки
class MusicConfig:
    def __init__(self, assets: AssetsConfig):
        self.assets = assets

        self.playing_name = ''
        self.music = None

    # -- выключение предыдущей музыки, если нужна другая, запуск следующей
    def ensure_playing(self, name, loop=True):
        if self.playing_name == name:
            return
        if self.music:
            arcade.stop_sound(self.music)
        self.playing_name = name
        self.music = arcade.play_sound(self.assets.music(name), loop=loop, volume=0.3)

    def ensure_music_stopped(self):
        if self.music:
            arcade.stop_sound(self.music)
            self.music = None
            self.playing_name = ''

    # -- звуковые эффекты
    def play_sound(self, name):
        effect = self.assets.effect(name, streaming=False)
        return arcade.play_sound(effect), effect


class Enemy:
    def __init__(self, tex, health):
        self.texture = tex
        self.health = health
        self.shadows = ['figure_1', 'figure_2', 'figure_3', 'figure_4']
        self.speed = 1
        self.name = 'Слайм'


class Player:
    def __init__(self, health=50, name='Иванушка'):
        self.health = health
        self.name = name
        self.inventory = [{'type': 'heal', 'heal': 20, 'texture': 'bottle_20'},
                          {'type': 'heal', 'heal': 10, 'texture': 'bottle_10'},
                          {'type': 'heal', 'heal': 10, 'texture': 'bottle_10'}]


# === ХРАНЕНИЕ ДАННЫХ ===
# -- класс настроек
@dataclass
class Config:
    # - константы
    # параметры окна
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 400
    WINDOW_RESIZABLE = True
    WINDOW_NAME = 'Окно в мир'

    WINDOW_MINIMAL_WIDTH = 200
    WINDOW_MINIMAL_HEIGHT = 200

    WINDOW_ICON = 'window_icon'

    # сцена запуска
    LAUNCH_VIEW = battle_arena.Main

    # пути
    DATA_FILE = Path('saves/save.json')
    ASSETS_FOLDER = Path('assets')
    SHADER_FOLDER = Path('shaders')

    # пользовательский ввод
    KEYS = {'fullscreen': arcade.key.F11,
            'move_up': arcade.key.W,
            'move_down': arcade.key.S,
            'move_left': arcade.key.A,
            'move_right': arcade.key.D,
            'zoom_in': arcade.key.UP,
            'zoom_out': arcade.key.DOWN,
            'action': arcade.key.Z,
            'escape': arcade.key.ESCAPE}

    # вспомогательный флаг отладки
    DEBUG = False

    # доступные сложности
    DIFFICULTIES = ['Прогулка', 'Приключение', 'Пытка', 'Шашлыки']

    CUSTOM_CURSOR = True

    # - динамические модули
    # быстрый доступ к ресурсам
    paths: PathConfig = PathConfig(DATA_FILE, ASSETS_FOLDER, SHADER_FOLDER)
    assets: AssetsConfig = AssetsConfig(paths)
    data: DataConfig = DataConfig(paths)
    music: MusicConfig = MusicConfig(assets)
    logger = u.archive_logging.Logger()
    utils = u

    player = Player()
    enemy = Enemy('enemy', 100)

    start_time = time.time()

    current_world = 0

    logger.log(
        f'Настройки заданы. Базовые модули функционируют. Файл сохранения содержит {len(data.data)} аттрибута(ов)')
