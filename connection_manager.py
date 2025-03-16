# connection_manager.py
from typing import Dict, List

from starlette.websockets import WebSocket


class ConnectionManager:
    def __init__(self):
        # Each room is stored as a dictionary with:
        # - "language": target language for translation (set by the first user)
        # - "connections": list of WebSocket connections in that room.
        self.rooms: Dict[str, Dict] = {}

    async def connect(self, room_id: str, model_id: str, user_id: str, username: str, websocket: WebSocket,
                      language: str = None):
        await websocket.accept()
        if room_id not in self.rooms:
            # For the first connection, record the room’s language
            self.rooms[room_id] = {"language": language, "connections": []}
        self.rooms[room_id]["connections"].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            self.rooms[room_id]["connections"].remove(websocket)
            if not self.rooms[room_id]["connections"]:
                # Clean up the room when empty
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: str):
        if room_id in self.rooms:
            for connection in self.rooms[room_id]["connections"]:
                await connection.send_text(message)

    def get_room_language(self, room_id: str):
        if room_id in self.rooms:
            return self.rooms[room_id]["language"]
        return None
