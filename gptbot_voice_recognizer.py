import os
import subprocess

import speech_recognition as sr

recognizer = sr.Recognizer()


def recognize_voice(file_oga):
    file_wav = file_oga + ".wav"

    subprocess.run(['ffmpeg', '-v', 'quiet', '-i', file_oga, file_wav])

    with open(file_wav, "rb") as wav:
        user_audio_file = sr.AudioFile(wav)
        with user_audio_file as source:
            user_audio = recognizer.record(source)
    text = recognizer.recognize_google(user_audio, language='ru-RU')
    os.remove(file_wav)
    return text
