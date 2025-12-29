"""РЕСУРС: базовые классы для интерфейса
 - Панель разработчика"""

import arcade
from arcade.gui import UIWindowLikeMixin, UIWidget, UIBoxLayout, UILabel, UITextArea, UIInputText


# -- панель разработчика
class DebugPanel(arcade.gui.UIManager):
    def __init__(self, logger):
        super().__init__()
        self.layout = arcade.gui.UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, align='left')

        self.input_row = UIBoxLayout(vertical=False, space_between=0)

        self.text_area = UITextArea(width=600, height=200, text="")
        self.text_input = UIInputText(width=230, height=100, text="", multiline=True)
        self.send_button = arcade.gui.UIFlatButton(text='Отправить',
                                                   width=100, height=100)
        self.send_button.on_click = self.execute_script
        self.hide_button = arcade.gui.UIFlatButton(text='Скрыть',
                                                   width=50, height=20,)
        self.hide_button.on_click = self.toggle_menu
        self.hide_button.center_x = 25
        self.hide_button.center_y = 110
        self.add(self.hide_button)

        self.box_layout.add(self.text_area)
        self.input_row.add(self.text_input)
        self.input_row.add(self.send_button)

        self.box_layout.add(self.input_row)
        self.layout.add(self.box_layout, anchor_y="bottom", anchor_x="left")

        self.add(self.layout)

        self.logger = logger

        self.vis = True
        self.exec_globals = {}
        self.toggle_menu(0)

    def on_update(self, dt):
        self.text_area.text = self.logger.get_log()

    def execute_script(self, event):
        req = self.text_input.text
        self.text_input.text = ''
        print('>>> ' + req)
        try:
            exec(req, self.exec_globals)
        except Exception as e:
            print(f'{e}')

    def toggle_menu(self, event):
        self.vis = not self.vis
        if self.vis:
            self.layout.visible = True
            self.hide_button.center_x = 25
            self.hide_button.center_y = 110
        else:
            self.layout.visible = False
            self.hide_button.center_x = 25
            self.hide_button.center_y = 10
        self.hide_button.text = ['Показать', 'Скрыть'][int(self.vis)]