from typing import Dict, List
from starlette.websockets import WebSocket
from starlette.concurrency import run_in_threadpool
import base64
import json
from utils import generate_tts, translate_text


class ConnectionManager:
    def __init__(self):
        # Rooms now map to a list of connection dicts.
        # Each dict contains:
        #  - "websocket": the connection instance,
        #  - "model_id", "user_id", "username",
        #  - "language": the user’s preferred language.
        self.rooms: Dict[str, List[dict]] = {}

    async def connect(self, room_id: str, model_id: str, user_id: str, username: str, websocket: WebSocket,
                      language: str = None):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        # Enforce a maximum of 2 users per room.
        if len(self.rooms[room_id]) >= 2:
            await websocket.close(code=1000)
            return
        self.rooms[room_id].append({
            "websocket": websocket,
            "model_id": model_id,
            "user_id": user_id,
            "username": username,
            "language": language
        })

    def is_connected(self, room_id: str, websocket: WebSocket) -> bool:
        """Helper to check if a websocket is still in the room."""
        if room_id in self.rooms:
            return any(conn["websocket"] == websocket for conn in self.rooms[room_id])
        return False

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            self.rooms[room_id] = [conn for conn in self.rooms[room_id] if conn["websocket"] != websocket]
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast_message(self, room_id: str, sender_language: str, sender_model_id: str, sender_user_id: str,
                                sender_username: str, original_text: str):
        """
        Broadcast a message in room 'room_id' by translating the original text into each receiver's language if needed.
        This helper is provided in case you wish to offload the per-connection logic from the route handler.
        """
        if room_id in self.rooms:
            for connection in self.rooms[room_id]:
                receiver_language = connection["language"]
                if receiver_language and receiver_language != sender_language:
                    translated_text = await run_in_threadpool(translate_text, original_text, receiver_language)
                else:
                    translated_text = original_text
                audio_content = await run_in_threadpool(generate_tts, sender_model_id, translated_text)
                audio_base64 = base64.b64encode(audio_content).decode("utf-8")
                message_data = {
                    "model_id": sender_model_id,
                    "user_id": sender_user_id,
                    "username": sender_username,
                    "text": translated_text,
                    "audio": audio_base64
                }
                json_message = json.dumps(message_data)
                await connection["websocket"].send_text(json_message)
