from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import shutil
import tempfile
from datetime import datetime
from convert_mp3_to_wav import convert_mp3_to_wav
from transcribe import transcribe_to_youtube_shorts_srt_notebook
from convert_to_hinglish import convert_to_hinglish

app = FastAPI(title="Free Hindi Captions Generator")

# Temporary directories
UPLOAD_DIR = "uploads"
SRT_DIR = "srt_for_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SRT_DIR, exist_ok=True)

@app.post("/generate-captions", response_class=FileResponse)
async def generate_captions(file: UploadFile = File(...)):
    try:
        # Validate file
        if not file.filename.lower().endswith(".mp3"):
            raise HTTPException(status_code=400, detail="Only MP3 files are allowed")
        
        # Save uploaded MP3 temporarily
        temp_mp3_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(temp_mp3_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Generate WAV
        temp_wav_path = convert_mp3_to_wav(temp_mp3_path, os.path.join(tempfile.gettempdir(), "temp.wav"))
        
        # Generate SRT filename with date
        today = datetime.now().strftime("%Y-%m-%d")
        base_filename = os.path.splitext(file.filename)[0]
        srt_filename = f"{base_filename}_{today}_yt.srt"
        srt_path = os.path.join(SRT_DIR, srt_filename)
        
        # Transcribe to SRT
        srt_lines = transcribe_to_youtube_shorts_srt_notebook(temp_wav_path, srt_filename)
        if not srt_lines:
            raise HTTPException(status_code=500, detail="Transcription failed")
        
        # Convert to Hinglish
        final_srt_path = convert_to_hinglish(srt_lines)
        if not final_srt_path or not os.path.exists(final_srt_path):
            raise HTTPException(status_code=500, detail="Hinglish conversion failed")
        
        # Return SRT file
        return FileResponse(final_srt_path, filename=srt_filename, media_type="application/x-subrip")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

@app.on_event("startup")
async def startup_event():
    # Verify Vosk model exists
    if not os.path.exists("vosk-model-small-hi-0.22"):
        raise RuntimeError("Vosk model not found at 'vosk-model-small-hi-0.22'")
    for file in os.listdir(SRT_DIR):
        os.remove(os.path.join(SRT_DIR, file))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)