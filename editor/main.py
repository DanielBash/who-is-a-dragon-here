"""СКРИПТ: главный файл
 - Содержит триггеры для запуска приложения
 - Запустить его, чтобы начать"""
import inspect
from pathlib import Path

# -- импорт модулей
import arcade
import pyglet
from arcade import View

from config import Config as conf


# -- класс окна
class Window(arcade.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def show_view(self, new_view: View):
        conf.logger.log(f'Переключение на сцену {Path(inspect.getfile(new_view.__class__)).stem}')
        super().show_view(new_view)


# - функция инициализации главного окна
def main():
    window = Window(conf.WINDOW_WIDTH,
                    conf.WINDOW_HEIGHT,
                    conf.WINDOW_NAME,
                    resizable=conf.WINDOW_RESIZABLE)
    window.set_minimum_size(conf.WINDOW_MINIMAL_WIDTH,
                            conf.WINDOW_MINIMAL_HEIGHT)
    window.show_view(conf.LAUNCH_VIEW(conf))
    window.set_icon(conf.assets.icon(conf.WINDOW_ICON))
    if conf.DEBUG:
        arcade.enable_timings()
    conf.logger.log(f'Успешная инициализация DEBUG={conf.DEBUG}')
    arcade.run()


# - запуск проекта
if __name__ == "__main__":
    main()
    conf.logger.log('Выключение')
