import threading
import flet as ft
import flet as ft
# from pyngrok import ngrok # Moved to server.py
from app.core.config import settings
from app.core.logger import gui_logger
from app.api.server import run_server

def main_gui(page: ft.Page):
    page.title = "Fog Node Manager (Linux)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_height = 500
    
    # Components
    logs_view = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    
    status_indicator = ft.Container(
        content=ft.Text("OFFLINE", color="white", weight="bold"),
        bgcolor="red", padding=10, border_radius=5
    )

    # Logging Callback
    def add_log(msg):
        logs_view.controls.append(
            ft.Text(f"> {msg}", font_family="Monospace", size=12)
        )
        try:
            page.update()
        except:
            pass # Handle edge case where page is closed

    gui_logger.set_callback(add_log)

    def start_service(e):
        btn_start.disabled = True
        status_indicator.bgcolor = "green"
        status_indicator.content.value = "ONLINE"
        page.update()

        # Start API Server in Thread
        t = threading.Thread(target=run_server, daemon=True)
        t.start()
        # La lógica de Ngrok y Logs ahora es manejada por el lifespan del server
        status_indicator.content.value = "ONLINE..." # Will update with logs

    btn_start = ft.ElevatedButton(
        "INICIAR SERVICIO",
        icon=ft.Icons.PLAY_ARROW,
        on_click=start_service,
        bgcolor="blue",
        color="white"
    )

    # Layout
    page.add(
        ft.Row([
            ft.Text("FOG COMPUTING NODE", size=20, weight="bold"),
            status_indicator
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Container(
            content=logs_view,
            bgcolor="#1A1A1A",
            border_radius=10,
            expand=True
        ),
        ft.Container(content=btn_start, padding=10)
    )
