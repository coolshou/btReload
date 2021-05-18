
import sys
try:

    from PyQt5.QtWidgets import (QAction, qApp,
                                 QMenu, QSystemTrayIcon)
except ImportError:
    print("pip install PyQt5")
    raise SystemError


class SysTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        #SysTrayIcon.__init__(self, icon, parent)
        #menu = QMenu(parent)
        self.show_action = QAction("Show", self)
        self.hide_action = QAction("Hide", self)
        self.quit_action = QAction("Exit", self)
        self.quit_action.triggered.connect(qApp.quit)

        tray_menu = QMenu()
        tray_menu.addAction(self.show_action)
        tray_menu.addAction(self.hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.quit_action)

        self.setContextMenu(tray_menu)
