import flet as ft
import subprocess
import asyncio
import sys
import websockets
import json
import re
import os


def get_resource_path(relative_path: str) -> str:
    """
    Obtiene la ruta absoluta al recurso.
    Compatible con el entorno de desarrollo local y el empaquetado de PyInstaller.
    """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Si _MEIPASS no existe, estamos en desarrollo local
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


async def main(page: ft.Page):
    page.title = "YT Audio Downloader"
    page.theme_mode = "dark"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    server_process = None

    async def window_event(e):
        if e.data == "close":
            if server_process:
                server_process.terminate()
            page.window_destroy()

    page.window_prevent_close = True
    page.on_window_event = window_event

    url_input = ft.TextField(label="URL de YouTube", width=400, disabled=True)
    status_text = ft.Text("Servidor apagado.", color="red")
    progress_bar = ft.ProgressBar(width=400, value=0, visible=False)
    progress_details = ft.Text("", visible=False)

    async def start_server(e):
        nonlocal server_process
        if server_process is None:
            status_text.value = "Iniciando motor local..."
            status_text.color = "orange"
            page.update()

            # 1. Resolvemos la ruta absoluta del microservicio
            api_script_path = get_resource_path("backend/api.py")

            # 2. Lanzamos el proceso hijo asegurando compatibilidad de empaquetado
            server_process = subprocess.Popen([sys.executable, api_script_path])

            url_input.disabled = False
            start_btn.disabled = True
            status_text.value = "🟢 Servidor en línea (localhost:8000)"
            status_text.color = "green"
            page.update()

    async def download_clicked(e):
        if not url_input.value:
            return

        progress_bar.visible = True
        progress_details.visible = True
        download_btn.disabled = True
        page.update()

        try:
            async with websockets.connect(
                "ws://127.0.0.1:8000/ws/download"
            ) as websocket:
                await websocket.send(json.dumps({"url": url_input.value}))

                while True:
                    message = await websocket.recv()
                    data = json.loads(message)

                    if data["status"] == "downloading":
                        percent_str = data.get("progress", "0.0%").strip()
                        match = re.search(r"(\d+(\.\d+)?)", percent_str)
                        if match:
                            percent = float(match.group(1))
                            progress_bar.value = percent / 100

                        eta = data.get("eta", 0)
                        speed = data.get("speed", "N/A")
                        progress_details.value = f"ETA: {eta}s - Velocidad: {speed}"
                        status_text.value = f"Descargando: {percent_str}"
                        status_text.color = "blue"

                    elif data["status"] == "finished":
                        status_text.value = "Finalizando descarga..."
                        progress_bar.value = 1

                    elif data["status"] == "success":
                        status_text.value = f"✅ Éxito: {data['file_path']}"
                        status_text.color = "green"
                        break
                    elif data["status"] == "error":
                        status_text.value = f"❌ Error: {data['message']}"
                        status_text.color = "red"
                        break
                    page.update()

        except Exception as ex:
            status_text.value = f"❌ Error de conexión: {ex}"
            status_text.color = "red"
        finally:
            progress_bar.visible = False
            progress_details.visible = False
            download_btn.disabled = False
            url_input.value = ""
            page.update()

    start_btn = ft.Button("Arrancar Motor", icon="play_arrow", on_click=start_server)
    download_btn = ft.Button(
        "Descargar MP3", icon="download", on_click=download_clicked
    )

    page.add(
        ft.Column(
            [
                ft.Text("YT Downloader", size=32, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                start_btn,
                status_text,
                ft.Divider(),
                url_input,
                download_btn,
                ft.Column(
                    [progress_bar, progress_details],
                    spacing=5,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP)
