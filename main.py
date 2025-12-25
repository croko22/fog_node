import flet as ft
from app.core.config import Settings
from app.gui.interface import main_gui

if __name__ == "__main__":
    Settings.validate()
    ft.app(target=main_gui)
