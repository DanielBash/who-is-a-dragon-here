"""РЕСУРС: функции для вывода текста, красивого вывода
 - Класс журнала приложения"""

import sys
import inspect
import datetime
from pathlib import Path


# -- класс журнала приложения
class Logger:
    def __init__(self):
        self._real_stdout = sys.__stdout__
        self._lines = []
        sys.stdout = self

    def write(self, text: str):
        self._real_stdout.write(text)
        self._real_stdout.flush()

        self._lines.append(text)

    def flush(self):
        self._real_stdout.flush()

    def get_log(self) -> str:
        return "".join(self._lines)

    def clear(self):
        self._lines.clear()

    def log(self, *args, **kwargs):
        frame = inspect.stack()[1]

        filename = Path(frame.filename)
        filename = Path(*filename.parts[-2:])

        lineno = frame.lineno

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = " ".join(str(x) for x in args)
        formatted = f"[{timestamp}] {filename}:{lineno} | {message}"

        print(formatted, **kwargs)

    def split_log(self, message=''):
        print('*-' * 10 + message.upper() + '-*' * 10)
