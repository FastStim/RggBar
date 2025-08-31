import uuid

from PyQt6 import QtWidgets, QtCore, QtGui
from functools import partial

from rggbar import state, __version__
from rggbar.websocketclient import WebsocketClient


class Platform(QtWidgets.QHBoxLayout):
    def __init__(self, uid, title, count, current, lock, change_count, delete_platform, activate_platform,
                 set_position, work_dir):
        super().__init__()

        self.work_dir = work_dir

        self.uid = uid
        self.delete_platform = delete_platform
        self.change_count = change_count
        self.activate_platform = activate_platform
        self.set_position = set_position

        self.radio = QtWidgets.QRadioButton(title)
        self.radio.setFixedWidth(200)
        self.radio.setChecked(current)
        self.radio.clicked.connect(self._checked_radio)

        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(0, 100)
        self.spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        # self.spin.setFixedWidth(50)
        self.spin.setValue(count)
        self.spin.valueChanged.connect(self._change_spin)

        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setIcon(QtGui.QIcon(f"{self.work_dir}/images/icons8-trash-384.png"))
        self.delete_button.clicked.connect(self._delete_button_clicked)

        self.up_button = QtWidgets.QPushButton()
        self.up_button.setIcon(QtGui.QIcon(f"{self.work_dir}/images/icons8-up-384.png"))
        self.up_button.clicked.connect(self._up_button_clicked)

        self.down_button = QtWidgets.QPushButton()
        self.down_button.setIcon(QtGui.QIcon(f"{self.work_dir}/images/icons8-down-384.png"))
        self.down_button.clicked.connect(self._down_button_clicked)

        self._layout()
        self.setSpacing(0)

    def _layout(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)

        self.addWidget(self.radio, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.spin)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.up_button)
        layout.addWidget(self.down_button)

        self.addLayout(layout)

    def _delete_button_clicked(self):
        self.delete_platform(self.uid)

        self.removeWidget(self.radio)
        self.removeWidget(self.spin)
        self.removeWidget(self.delete_button)
        self.removeWidget(self.up_button)
        self.removeWidget(self.down_button)

        del self.radio
        del self.spin
        del self.delete_button
        del self.up_button
        del self.down_button

    def _up_button_clicked(self):
        self.set_position(self.uid, True)

    def _down_button_clicked(self):
        self.set_position(self.uid, False)

    def _change_spin(self, count):
        self.change_count(self.uid, count)

    def _checked_radio(self, current):
        self.activate_platform(self.uid)


class Platforms(QtWidgets.QGroupBox):
    def __init__(self, cfg, ws, work_dir):
        super().__init__()
        self.cfg = cfg
        self.ws = ws
        self.work_dir = work_dir

        self.platforms = {}

        self._layout = QtWidgets.QVBoxLayout()

        self.init()

    def init(self):
        platforms = sorted(self.cfg["platforms"].values(), key=lambda platform: platform['position'])
        for platform in platforms:
            self.add_platform(platform["uuid"], platform["title"], platform["count"], platform["current"])

    def add_platform(self, uid, title, count, current, reverse=False):
        platform = Platform(uid, title, count, current, self.cfg["lock"], self.change_count, self.delete_platform,
                            self.activate_platform, self.set_position, self.work_dir)
        self.platforms[uid] = platform

        if not reverse:
            self._layout.addLayout(platform)
        else:
            self._layout.insertLayout(0, platform)

        self.setLayout(self._layout)

        self.locked(self.cfg['lock'])

    def delete_platform(self, uid):
        del self.cfg["platforms"][uid]

        state.save(self.cfg)
        self.ws.send(self.cfg)

        del self.platforms[uid]

    def change_count(self, uid, count):
        self.cfg["platforms"][uid]["count"] = count

        state.save(self.cfg)
        self.ws.send(self.cfg)

    def activate_platform(self, uid):
        for platform in self.cfg["platforms"].values():
            platform["current"] = False

        self.cfg["platforms"][uid]["current"] = True

        state.save(self.cfg)
        self.ws.send(self.cfg)

    def locked(self, lock):
        for platform in self.platforms.values():
            platform.delete_button.setVisible(not lock)
            platform.up_button.setVisible(not lock)
            platform.down_button.setVisible(not lock)

    def set_position(self, uid, is_up):
        widgets = {v: k for k, v in self.platforms.items()}

        current_platform = self.platforms[uid]

        current_widget_position = self._layout.indexOf(current_platform)
        next_widget_position = current_widget_position - 1 if is_up else current_widget_position + 1

        next_platform = self._layout.itemAt(next_widget_position)
        if next_platform is None:
            return

        next_uid = widgets[next_platform]

        position = self.cfg['platforms'][uid]['position']
        self.cfg['platforms'][uid]['position'] = self.cfg['platforms'][next_uid]['position']
        self.cfg['platforms'][next_uid]['position'] = position

        self._layout.removeItem(current_platform)
        self._layout.insertLayout(next_widget_position, current_platform)

        state.save(self.cfg)
        self.ws.send(self.cfg)


class Window(QtWidgets.QWidget):
    def __init__(self, cfg, ws, work_dir, change_theme):
        super().__init__(parent=None)
        self.setWindowTitle(f"RGGBar v{__version__}")
        self.setWindowIcon(QtGui.QIcon('images/rggbar_logo.png'))

        self.cfg = cfg
        self.ws = ws

        self.change_theme = change_theme
        self.lock = self.cfg["lock"]
        self.reverse = self.cfg["reverse"]
        self.is_dark = self.cfg["theme"]['is_dark']

        self.menu = QtWidgets.QMenuBar()

        self.platform = QtWidgets.QLineEdit()
        self.platform.setPlaceholderText("platform")
        self.platform.setFixedWidth(200)
        self.platform.setMaxLength(10)

        self.platform.returnPressed.connect(self._add_button_clicked)

        self.platforms = Platforms(self.cfg, self.ws, work_dir)
        self.add_button = QtWidgets.QPushButton("+")
        self.add_button.setFixedWidth(100)

        self.add_button.clicked.connect(self._add_button_clicked)

        self._menu()
        self._layout()
        self._locked(self.lock)

    def _menu(self):
        file = QtWidgets.QMenu("&file", self)

        exit_action = QtGui.QAction("e&xit", self)
        exit_action.triggered.connect(self._exit)
        file.addAction(exit_action)

        edit = QtWidgets.QMenu("&edit", self)

        edit_mode_action = QtGui.QAction("edit &mode", self)
        edit_mode_action.setCheckable(True)
        edit_mode_action.setChecked(not self.lock)
        edit_mode_action.triggered.connect(self._check_edit_mode)
        edit.addAction(edit_mode_action)

        theme_action = QtGui.QAction("&theme dark", self)
        theme_action.setCheckable(True)
        theme_action.setChecked(self.is_dark)
        theme_action.triggered.connect(self._check_theme)
        edit.addAction(theme_action)

        reverse_action = QtGui.QAction("&reverse adding", self)
        reverse_action.setCheckable(True)
        reverse_action.setChecked(self.reverse)
        reverse_action.triggered.connect(self._check_reverse)
        edit.addAction(reverse_action)

        colors = QtWidgets.QMenu("&colors", edit)

        colors_action = QtGui.QAction("&default", self)
        colors_action.triggered.connect(partial(self._set_color, "default"))
        colors.addAction(colors_action)

        colors_action = QtGui.QAction("c&urrent", self)
        colors_action.triggered.connect(partial(self._set_color, "current"))
        colors.addAction(colors_action)

        colors_action = QtGui.QAction("&end", self)
        colors_action.triggered.connect(partial(self._set_color, "end"))
        colors.addAction(colors_action)

        edit.addMenu(colors)

        fonts_action = QtGui.QAction("&fonts", self)
        fonts_action.triggered.connect(self._set_font)

        edit.addAction(fonts_action)

        _help = QtWidgets.QMenu("&help", self)

        help_action = QtGui.QAction("&url", self)
        help_action.triggered.connect(self._set_alert_url)
        _help.addAction(help_action)

        self.menu.addMenu(file)
        self.menu.addMenu(edit)
        self.menu.addMenu(_help)

    def _layout(self):
        layout = QtWidgets.QVBoxLayout()

        layout.setMenuBar(self.menu)

        layout.addWidget(self.platforms)

        add_layout = QtWidgets.QHBoxLayout()
        add_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        add_layout.addWidget(self.platform)
        add_layout.addWidget(self.add_button)

        layout.addLayout(add_layout)
        layout.addStretch()
        self.setLayout(layout)

    def _locked(self, lock):
        self.platform.setVisible(not lock)
        self.add_button.setVisible(not lock)

    def _add_button_clicked(self):
        title = self.platform.text()
        if title:
            _uuid = uuid.uuid4().hex
            count = 1
            current = not bool(len(self.cfg["platforms"]))

            if self.cfg['platforms'].values():
                platforms = sorted(self.cfg["platforms"].values(), key=lambda p: p['position'], reverse=self.reverse)
                position = platforms[-1]['position']
                position += 1 if not self.reverse else -1
            else:
                position = 0

            self.cfg["platforms"][_uuid] = {
                "uuid": _uuid,
                "title": title,
                "count": count,
                "position": position,
                "current": current
            }

            self.platforms.add_platform(_uuid, title, count, current, self.reverse)
            self.platform.setText("")

            state.save(self.cfg)
            self.ws.send(self.cfg)

    def _exit(self):
        self.close()

    def _check_edit_mode(self, checked):
        self.lock = not checked

        self.cfg["lock"] = self.lock
        state.save(self.cfg)

        self.platform.setVisible(not self.lock)
        self.add_button.setVisible(not self.lock)
        self.platforms.locked(self.lock)

    def _check_theme(self, checked):
        self.is_dark = checked
        self.cfg['theme']['is_dark'] = self.is_dark

        state.save(self.cfg)

        self.change_theme(self.is_dark)

    def _check_reverse(self, checked):
        self.reverse = checked

        self.cfg["reverse"] = self.reverse
        state.save(self.cfg)

    def _set_color(self, type_color):
        last_color = self.cfg["color"][type_color]

        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(last_color))
        if color.isValid():
            self.cfg["color"][type_color] = color.name()
            state.save(self.cfg)
            self.ws.send(self.cfg)

    def _set_alert_url(self):
        QtWidgets.QMessageBox.information(self, "url", "localhost:6660")

    def _set_font(self):
        current_font = QtGui.QFont(self.cfg['font']['family'], 12)
        current_font.weight = self.cfg['font']['weight']
        current_font.setItalic(self.cfg['font']['italic'])
        current_font.setBold(self.cfg['font']['bold'])

        font, ok = QtWidgets.QFontDialog.getFont(current_font)
        if not ok:
            return None

        self.cfg["font"] = {
            "family": font.family(),
            "weight": font.weight(),
            "bold": font.bold(),
            "italic": font.italic()
        }

        state.save(self.cfg)
        self.ws.send(self.cfg)


def start(work_dir):
    ws = WebsocketClient("localhost", 6660)

    app = QtWidgets.QApplication([])

    cfg = state.load()

    if cfg is None:
        cfg = {"platforms": {}}
        state.save(cfg)

    if "color" not in cfg:
        cfg["color"] = {
            "default": "#fafaed",
            "current": "#23dbb7",
            "end": "#525350"
        }
        state.save(cfg)

    if "font" not in cfg:
        cfg["font"] = {
            "family": "Open Sans",
            "weight": "800",
            "bold": True,
            "italic": True
        }
        state.save(cfg)

    if "lock" not in cfg:
        cfg["lock"] = False
        state.save(cfg)

    if "reverse" not in cfg:
        cfg["reverse"] = False
        state.save(cfg)

    if 'theme' not in cfg:
        cfg["theme"] = {'is_dark': app.styleHints().colorScheme() == QtCore.Qt.ColorScheme.Dark}
        state.save(cfg)

    app.styleHints().setColorScheme(
        QtCore.Qt.ColorScheme.Dark if cfg['theme']['is_dark'] else QtCore.Qt.ColorScheme.Light)

    def _change_theme(is_dark):
        if is_dark:
            app.styleHints().setColorScheme(QtCore.Qt.ColorScheme.Dark)
        else:
            app.styleHints().setColorScheme(QtCore.Qt.ColorScheme.Light)

    window = Window(cfg, ws, work_dir, _change_theme)
    window.show()

    app.exec()
