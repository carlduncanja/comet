import asyncio

import requests
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import io
import speech_recognition as sr

from constants import ELEVENLABS_API_KEY, SUPABASE_JWT_PUBLIC_KEY

bearer_scheme = HTTPBearer()


def generate_tts(voice_id: str, text: str) -> bytes:
    """
    Synchronously calls the ElevenLabs TTS API and returns MP3 audio content.
    """
    target_url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        "?output_format=mp3_44100_128"
    )
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }
    response = requests.post(target_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.content


def translate_text(text: str, target_language: str) -> str:
    try:
        from googletrans import Translator
        translator = Translator()
        result = asyncio.run(translator.translate(text, dest=target_language))

        return result.text
    except Exception:
        # If translation fails, fallback to the original text.
        return text


def verify_token(token: str):
    """
    Verify the Supabase JWT token using HS256 algorithm.
    """
    try:
        payload = jwt.decode(token, SUPABASE_JWT_PUBLIC_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Dependency that extracts and verifies the Bearer token.
    The token is automatically pulled from the 'Authorization' header.
    """
    token = credentials.credentials
    return verify_token(token)


def transcribe_audio(audio_data: bytes) -> str:
    """
    Transcribe binary audio data to text using the Google Web Speech API.

    Parameters:
        audio_data (bytes): The binary audio data.

    Returns:
        str: The transcribed text. If transcription fails or the speech is unclear,
             an empty string is returned.
    """
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_data)

    # Use AudioFile to process the binary data from a file-like object.
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)

    try:
        # Attempt transcription using Google's speech recognition.
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        # Speech was unintelligible.
        return ""
    except sr.RequestError as e:
        # Could not request results from the service.
        raise Exception(f"Error with the speech recognition service: {e}")
