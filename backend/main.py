import flet as ft
import subprocess
import sys
import asyncio
import websockets
import json
import re
import os
import signal


def get_resource_path(*path_parts):
    base_path = getattr(
        sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(base_path, *path_parts)


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

    default_download_dir = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "downloads")
    )

    url_input = ft.TextField(label="URL de YouTube", width=400, disabled=True)
    output_dir_input = ft.TextField(
        label="Carpeta destino",
        width=400,
        value=default_download_dir,
        hint_text="Escribe ruta absoluta de carpeta",
    )
    select_folder_btn = ft.Button("Elegir ruta", icon="folder_open")
    status_text = ft.Text("Servidor apagado.", color="red")
    progress_bar = ft.ProgressBar(width=400, value=0, visible=False)
    progress_details = ft.Text("", visible=False)
    theme_btn = ft.Button("Cambiar tema", icon="dark_mode")

    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_btn.icon = "light_mode"
            theme_btn.text = "Tema oscuro"
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_btn.icon = "dark_mode"
            theme_btn.text = "Tema claro"
        page.update()

    theme_btn.on_click = toggle_theme

    def open_folder_dialog():
        if sys.platform == "darwin":
            script = 'POSIX path of (choose folder with prompt "Selecciona carpeta destino")'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        if sys.platform.startswith("win"):
            script = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$f=New-Object System.Windows.Forms.FolderBrowserDialog;"
                "$f.Description='Selecciona carpeta destino';"
                "if($f.ShowDialog() -eq 'OK'){Write-Output $f.SelectedPath}"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        result = subprocess.run(
            ["zenity", "--file-selection", "--directory", "--title=Selecciona carpeta destino"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    async def pick_folder_clicked(e):
        try:
            selected_dir = await asyncio.to_thread(open_folder_dialog)
            if selected_dir:
                output_dir_input.value = selected_dir
                status_text.value = f"Destino actualizado: {selected_dir}"
                status_text.color = "green"
                page.update()
        except Exception as ex:
            status_text.value = f"❌ Error al abrir selector: {ex}"
            status_text.color = "red"
            page.update()

    select_folder_btn.on_click = pick_folder_clicked

    async def start_server(e):
        nonlocal server_process
        if server_process is None:
            status_text.value = "Iniciando motor local..."
            status_text.color = "orange"
            page.update()

            # Mata proceso viejo escuchando en 8000 para evitar conectar con server desactualizado.
            try:
                lsof_result = subprocess.run(
                    ["lsof", "-ti", "tcp:8000"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                stale_pids = [
                    int(pid.strip())
                    for pid in lsof_result.stdout.splitlines()
                    if pid.strip().isdigit()
                ]
                for pid in stale_pids:
                    if pid != os.getpid():
                        os.kill(pid, signal.SIGTERM)
            except Exception:
                pass

            api_path = get_resource_path("backend", "api.py")

            server_process = subprocess.Popen([sys.executable, api_path])
            await asyncio.sleep(0.6)

            if server_process.poll() is not None:
                status_text.value = "❌ Error: no se pudo iniciar motor local."
                status_text.color = "red"
                server_process = None
                page.update()
                return

            url_input.disabled = False
            status_text.value = "🟢 Servidor en línea"
            status_text.color = "green"
            page.update()

    async def download_clicked(e):
        if not url_input.value:
            return

        output_path = output_dir_input.value.strip() or default_download_dir
        if not os.path.isabs(output_path):
            status_text.value = "❌ Error: usa ruta absoluta para carpeta destino."
            status_text.color = "red"
            page.update()
            return

        try:
            os.makedirs(output_path, exist_ok=True)
        except Exception as ex:
            status_text.value = f"❌ Error carpeta destino: {ex}"
            status_text.color = "red"
            page.update()
            return

        progress_bar.visible = True
        progress_details.visible = True
        download_btn.disabled = True
        page.update()

        try:
            async with websockets.connect(
                "ws://127.0.0.1:8000/ws/download"
            ) as websocket:
                await websocket.send(
                    json.dumps({"url": url_input.value, "output_path": output_path})
                )

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

    download_btn = ft.Button(
        "Descargar MP3", icon="download", on_click=download_clicked
    )

    page.add(
        ft.Column(
            [
                ft.Text("YT Downloader", size=32, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                theme_btn,
                status_text,
                ft.Divider(),
                url_input,
                select_folder_btn,
                output_dir_input,
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
    await start_server(None)
    page.update()


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP)
