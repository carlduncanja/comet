```markdown
# Comet API

## Overview

The Comet API provides functionalities for adding voices and real-time chat via WebSocket. It includes endpoints for uploading voice files, establishing chat connections, and translating audio.

## Features

- **Add Voice**: Upload a file to add a new voice.
- **WebSocket Chat**: Establish a chat connection with real-time translation and text-to-speech (TTS) capabilities.
- **WebSocket Audio**: Receive an audio stream, convert it to text, and process it similarly to the chat endpoint.
- **Audio Translation**: Convert audio to text, translate it to a target language, and generate TTS audio from the translated text.

## Endpoints

### POST /v1/voices/add

Upload a file to add a new voice.

#### Parameters

- `name` (str): The display name for the new voice.
- `file` (UploadFile): The file containing the voice data.

#### Response

- JSON response containing the result of the voice addition.

### WebSocket /ws/chat/{room_id}/{model_id}/{user_id}/{username}

Establish a chat connection.

#### Parameters

- `room_id` (str): The room ID.
- `model_id` (str): The model ID.
- `user_id` (str): The user ID.
- `username` (str): The username.

### WebSocket /ws/audio/{room_id}/{model_id}/{user_id}/{username}

Receive an audio stream, convert it to text, and process it similarly to the chat endpoint.

#### Parameters

- `room_id` (str): The room ID.
- `model_id` (str): The model ID.
- `user_id` (str): The user ID.
- `username` (str): The username.

### POST /v1/audio/translate

Convert audio to text, translate it to a target language, and generate TTS audio from the translated text.

#### Parameters

- `audio` (UploadFile): The audio file (WAV).
- `model_id` (str): The model ID.
- `target_language` (str): The target language for translation.

#### Response

- JSON response containing the original text, translated text, and base64-encoded TTS audio.

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/carlduncanja/comet-api.git
   cd comet-api
   ```

2. Build the Docker image:
   ```sh
   docker build -t comet-api .
   ```

3. Run the Docker container:
   ```sh
   docker run -p 5000:5000 comet-api
   ```

## Dependencies

- Python 3.13
- FastAPI
- Uvicorn
- Requests
- Other dependencies listed in `requirements.txt`

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
```