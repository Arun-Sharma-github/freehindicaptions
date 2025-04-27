from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
import os
import logging
import tempfile
from datetime import datetime
from convert_mp3_to_wav import convert_mp3_to_wav
from transcribe import transcribe_to_youtube_shorts_srt_notebook
from convert_to_hinglish import convert_to_hinglish
from fastapi.middleware.cors import CORSMiddleware
from werkzeug.utils import secure_filename


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Rate limiter
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Security headers
from starlette.middleware.base import BaseHTTPMiddleware


app = FastAPI(title="Free Hindi Captions Generator")



# Middleware: Security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

# app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://freehindicaptions.com","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



# Temporary directories
UPLOAD_DIR = "uploads"
SRT_DIR = "srt_for_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SRT_DIR, exist_ok=True)

@app.post("/generate-captions", response_class=FileResponse)
@limiter.limit("2/minute")  # ⏱️ 5 requests per minute per IP
async def generate_captions(request: Request, file: UploadFile = File(...)):
    try:
        logger.info(f"Received file upload request: {file.filename}")
        # Validate MIME type and file extension
        if file.content_type != "audio/mpeg" or not file.filename.lower().endswith(".mp3"):
            logger.warning("Invalid file format or MIME type")
            raise HTTPException(status_code=400, detail="Only MP3 files are allowed")

        # Secure filename to prevent path traversal
        secure_name = secure_filename(file.filename)

        # Limit file size manually (5MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            logger.warning("File size exceeds limit")
            raise HTTPException(status_code=400, detail="File size exceeds 5 MB")
        
        # Save MP3
        temp_mp3_path = os.path.join(UPLOAD_DIR, secure_name)
        with open(temp_mp3_path, "wb") as buffer:
            buffer.write(contents)
        logger.info(f"Saved MP3 file: {temp_mp3_path}")

        # Convert to WAV
        temp_wav_path = convert_mp3_to_wav(temp_mp3_path, os.path.join(tempfile.gettempdir(), "temp.wav"))
        logger.info(f"Converted MP3 to WAV: {temp_wav_path}")

        # Prepare filename
        today = datetime.now().strftime("%Y-%m-%d")
        base_filename = os.path.splitext(secure_name)[0]
        srt_filename = f"{base_filename}_{today}_yt.srt"

        # Transcribe
        srt_lines = transcribe_to_youtube_shorts_srt_notebook(temp_wav_path, srt_filename)
        if not srt_lines:
            logger.error("Transcription failed")
            raise HTTPException(status_code=500, detail="Transcription failed")

        # Hinglish
        final_srt_path = convert_to_hinglish(srt_lines)
        if not final_srt_path or not os.path.exists(final_srt_path):
            logger.error("Hinglish conversion failed")
            raise HTTPException(status_code=500, detail="Hinglish conversion failed")
        
        logger.info(f"Returning SRT file: {final_srt_path}")
        return FileResponse(final_srt_path, filename=srt_filename, media_type="application/x-subrip")

    except HTTPException as http_ex:
        logger.warning(f"HTTPException: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        logger.exception("Unexpected error occurred")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:    
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

@app.on_event("startup")
async def startup_event():
    # Verify Vosk model exists
    if not os.path.exists("vosk-model-small-hi-0.22"):
        logger.critical("Vosk model not found")
        raise RuntimeError("Vosk model not found at 'vosk-model-small-hi-0.22'")

    # Clean up old SRT files
    if os.path.exists(SRT_DIR):
        for file in os.listdir(SRT_DIR):
            logger.info(f"Removed existing SRT file: {file}")
            os.remove(os.path.join(SRT_DIR, file))
    else:
        os.makedirs(SRT_DIR, exist_ok=True)
        logger.info("Created missing SRT_DIR")
        
        
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)