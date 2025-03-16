import base64
import json
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.websockets import WebSocket, WebSocketDisconnect

from connection_manager import ConnectionManager
from constants import ELEVENLABS_API_KEY, ELEVENLABS_VOICES_ADD_URL
from utils import generate_tts, translate_text

app = FastAPI()
manager = ConnectionManager()


@app.post("/v1/voices/add")
async def add_voice(name: str = Form(...), file: UploadFile = File(...)):
    """
    Add a new voice by uploading a file and providing a name.
    """
    try:
        file_content = await file.read()
        files = {"files": (file.filename, file_content, file.content_type)}
        data = {"name": name}
        headers = {"xi-api-key": ELEVENLABS_API_KEY}

        response = requests.post(
            ELEVENLABS_VOICES_ADD_URL,
            headers=headers,
            data=data,
            files=files
        )
        response.raise_for_status()
        return JSONResponse(content=response.json())

    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=response.status_code, detail=str(http_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.websocket("/ws/chat/{room_id}/{model_id}/{user_id}/{username}")
async def websocket_chat(websocket: WebSocket, room_id: str, model_id: str, user_id: str, username: str):
    # For the first connection to a room, the creator should include ?language=<target_lang> in the URL.
    language =  websocket.query_params.get("language")
    await manager.connect(room_id, model_id, user_id, username, websocket, language)
    try:
        while True:
            original_text = await websocket.receive_text()

            # Retrieve the room's target language set by the first user.
            target_language = manager.get_room_language(room_id)
            if target_language:
                # Translate the received text to the target language.
                translated_text = await run_in_threadpool(translate_text, original_text, target_language)
            else:
                translated_text = original_text

            # Generate TTS audio using the sender's model_id on the translated text.
            audio_content = await run_in_threadpool(generate_tts, model_id, translated_text)
            audio_base64 = base64.b64encode(audio_content).decode("utf-8")

            message_data = {
                "model_id": model_id,
                "user_id": user_id,
                "username": username,
                "text": translated_text,
                "audio": audio_base64
            }
            json_message = json.dumps(message_data)
            await manager.broadcast(room_id, json_message)

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        disconnect_message = json.dumps({
            "model_id": model_id,
            "user_id": user_id,
            "username": username,
            "text": f"{username} has disconnected from room {room_id}.",
            "audio": ""
        })
        await manager.broadcast(room_id, disconnect_message)
