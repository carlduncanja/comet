import base64
import json

import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, WebSocket
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect

from connection_manager import ConnectionManager
from constants import ELEVENLABS_API_KEY, ELEVENLABS_VOICES_ADD_URL
from utils import generate_tts, translate_text, get_current_user, verify_token

app = FastAPI(
    title="Comet API",
    description="""
    # Comet API Documentation

    The Comet API provides functionalities for adding voices and real-time chat via WebSocket.

    ## Endpoints
    - **POST /v1/voices/add:** Upload a file to add a new voice.
    - **WebSocket /ws/chat/{room_id}/{model_id}/{user_id}/{username}:** Establish a chat connection.

    Refer to the endpoint-specific docs for more details.
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

manager = ConnectionManager()


@app.post("/v1/voices/add")
async def add_voice(
        name: str = Form(...),
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
):
    """
    **Add Voice Endpoint**

    Add a new voice by uploading a file and providing a name.
    - **name**: The display name for the new voice.
    - **file**: The file containing the voice data.

    This endpoint requires authentication.
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
    """
    WebSocket chat endpoint.
    For authentication, the JWT token is expected either in the 'Authorization'
    header or as a query parameter 'token'. The token is verified before establishing
    the connection.
    """
    # Try to extract token from headers first; if not available, fall back to query parameter.
    token = websocket.headers.get("Authorization") or websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]
    try:
        user_payload = verify_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    # Retrieve the language (if provided)
    language = websocket.query_params.get("language")
    await manager.connect(room_id, model_id, user_id, username, websocket, language)

    # Exit early if connection failed (e.g., room capacity exceeded)
    if not manager.is_connected(room_id, websocket):
        return

    try:
        while True:
            original_text = await websocket.receive_text()
            # Translate text if receiver's language differs
            if room_id in manager.rooms:
                for conn in manager.rooms[room_id]:
                    receiver_language = conn["language"]
                    if receiver_language and receiver_language != language:
                        translated_text = await run_in_threadpool(translate_text, original_text, receiver_language)
                    else:
                        translated_text = original_text

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
                    await conn["websocket"].send_text(json_message)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        disconnect_message = json.dumps({
            "model_id": model_id,
            "user_id": user_id,
            "username": username,
            "text": f"{username} has disconnected from room {room_id}.",
            "audio": ""
        })
        if room_id in manager.rooms:
            for conn in manager.rooms[room_id]:
                await conn["websocket"].send_text(disconnect_message)
