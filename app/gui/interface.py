import threading
import flet as ft
from app.core.config import settings
from app.core.logger import gui_logger
from app.core.jobs import JobManager  # Import JobManager
from app.api.server import run_server

def main_gui(page: ft.Page):
    page.title = "Fog Node Manager (Linux)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 700
    page.window_height = 600
    
    # --- State ---
    current_job_id = [None]  # List to be mutable in closure

    # --- Components ---
    
    # 1. Status Header
    status_indicator = ft.Container(
        content=ft.Text("OFFLINE", color="white", weight="bold"),
        bgcolor="red", padding=10, border_radius=5
    )

    # 2. Job Status Panel
    job_filename = ft.Text("Esperando archivo...", size=16, weight="bold")
    job_progress_bar = ft.ProgressBar(width=400, value=0, color="orange")
    job_status_text = ft.Text("No job running", size=12, color="grey")
    job_details_text = ft.Text("-", size=12, italic=True)
    
    job_panel = ft.Container(
        content=ft.Column([
            ft.Text("PROCESAMIENTO ACTUAL", size=12, weight="bold", color="blue"),
            ft.Divider(height=5, color="transparent"),
            ft.Row([ft.Icon(ft.Icons.DESCRIPTION), job_filename]),
            job_progress_bar,
            ft.Row([
                job_status_text,
                ft.Container(expand=True), # Spacer
                job_details_text
            ])
        ]),
        bgcolor="#252525",
        padding=15,
        border_radius=10,
        visible=False # Hidden initially
    )

    # 3. Logs
    logs_view = ft.ListView(expand=1, spacing=5, padding=10, auto_scroll=True)
    logs_container = ft.Container(
        content=logs_view,
        bgcolor="#1A1A1A",
        border_radius=10,
        expand=True,
        border=ft.border.all(1, "#333333")
    )

    # --- Callbacks ---

    # Log Callback
    def add_log(msg):
        logs_view.controls.append(
            ft.Text(f"> {msg}", font_family="Monospace", size=12)
        )
        try:
            page.update()
        except:
            pass 

    gui_logger.set_callback(add_log)

    # Job Callback
    def on_job_update(job_id, event_type, data):
        # Always make panel visible on update
        job_panel.visible = True
        current_job_id[0] = job_id
        
        if event_type == "created":
            job_filename.value = data.get("filename", "Unknown")
            job_progress_bar.value = 0
            job_status_text.value = f"Status: {data.get('status', 'PENDING')}"
            job_details_text.value = "Iniciando..."
            
        elif event_type == "progress":
            processed = data.get("processed_chunks", 0)
            total = data.get("total_chunks")
            
            if total and total > 0:
                job_progress_bar.value = processed / total
                job_details_text.value = f"Chunks: {processed} / {total}"
            else:
                job_progress_bar.value = None # Indeterminate
                job_details_text.value = f"Chunks processed: {processed}"
            
            if data.get("message"):
                job_status_text.value = data["message"]

        elif event_type == "status_change":
            status = data.get("status")
            job_status_text.value = f"Status: {status}"
            if data.get("message"):
                job_status_text.value += f" - {data['message']}"
            
            if status == "completed":
                job_progress_bar.value = 1
                job_progress_bar.color = "green"
            elif status == "failed":
                job_progress_bar.color = "red"
                
        elif event_type == "new_file":
            # Optional: Show last generated file?
            pass

        try:
            page.update()
        except:
            pass

    # Register the callback hook
    JobManager.register_callback(on_job_update)


    def start_service(e):
        btn_start.disabled = True
        status_indicator.bgcolor = "green"
        status_indicator.content.value = "ONLINE"
        page.update()

        # Start API Server in Thread
        t = threading.Thread(target=run_server, daemon=True)
        t.start()
        
        status_indicator.content.value = "ONLINE (Listening)"
        page.update()

    btn_start = ft.ElevatedButton(
        "INICIAR SERVICIO",
        icon=ft.Icons.PLAY_ARROW,
        on_click=start_service,
        bgcolor="blue",
        color="white",
        height=50
    )

    # --- Layout ---
    page.add(
        ft.Row([
            ft.Text("FOG COMPUTING NODE", size=20, weight="bold"),
            status_indicator
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        job_panel, 
        ft.Text("Logs del Sistema", size=12, color="grey"),
        logs_container,
        ft.Container(content=btn_start, padding=10)
    )

