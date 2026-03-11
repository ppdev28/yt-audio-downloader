from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from downloader import YouTubeAudioDownloader
import uvicorn
import os
import asyncio

app = FastAPI(title="Motor Local de Descargas")
downloader = YouTubeAudioDownloader(output_path="./downloads")

# Asegurarse de que el directorio de descargas existe
os.makedirs("./downloads", exist_ok=True)


@app.websocket("/ws/download")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_event_loop()

    def progress_hook(d):
        if d["status"] == "downloading":
            progress_data = {
                "status": "downloading",
                "progress": d.get("_percent_str", "0%"),
                "eta": d.get("eta", 0),
                "speed": d.get("_speed_str", "N/A"),
                "total_bytes": d.get("total_bytes"),
                "downloaded_bytes": d.get("downloaded_bytes"),
            }
            asyncio.run_coroutine_threadsafe(websocket.send_json(progress_data), loop)
        elif d["status"] == "finished":
            progress_data = {"status": "finished"}
            asyncio.run_coroutine_threadsafe(websocket.send_json(progress_data), loop)

    try:
        while True:
            data = await websocket.receive_json()
            url = data.get("url")
            if not url:
                await websocket.send_json(
                    {"status": "error", "message": "URL no proporcionada"}
                )
                continue

            file_path = await loop.run_in_executor(
                None,
                lambda: downloader.download_audio(url, progress_hook=progress_hook),
            )

            if file_path and os.path.exists(file_path):
                await websocket.send_json({"status": "success", "file_path": file_path})
            else:
                await websocket.send_json(
                    {"status": "error", "message": "Error en la extracción del audio."}
                )
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except:
            pass  # Ignore if we can't send
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
