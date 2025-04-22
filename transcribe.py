from vosk import Model, KaldiRecognizer
import wave
import json
from datetime import timedelta
import os

def format_srt_time(seconds):
    td = timedelta(seconds=seconds)
    return str(td)[:-3].replace('.', ',').zfill(11)

def transcribe_to_youtube_shorts_srt_notebook(wav_path, srt_filename="shorts_style.srt"):
    try:
        model = Model("vosk-model-small-hi-0.22")
        wf = wave.open(wav_path, "rb")

        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Audio file must be WAV format with 16KHz, mono, 16-bit")

        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        srt_lines = []
        caption_index = 1

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if "result" in result:
                    for word_info in result["result"]:
                        word = word_info["word"].upper()
                        start_time = word_info["start"]
                        end_time = word_info["end"]
                        srt_lines.append(f"{caption_index}")
                        srt_lines.append(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}")
                        srt_lines.append(f"{word}\n")
                        caption_index += 1

        # Handle final result
        final_result = json.loads(rec.FinalResult())
        if "result" in final_result:
            for word_info in final_result["result"]:
                word = word_info["word"].upper()
                start_time = word_info["start"]
                end_time = word_info["end"]
                srt_lines.append(f"{caption_index}")
                srt_lines.append(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}")
                srt_lines.append(f"{word}\n")
                caption_index += 1

        print("Transcription completed")
        return srt_lines

    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        return None
    finally:
        wf.close()