# Qt
from PyQt5.QtWidgets import QApplication

# Basics
import sys

# Dependencies
from panel.panelMain import PanelMain


def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    # Loading main widget
    si_simulator = PanelMain()
    si_simulator.show()

    app.exec_()


if __name__ == "__main__":
    main()
