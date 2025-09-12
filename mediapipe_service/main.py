from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from mediapipe_processor import MediaPipeProcessor
import logging
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MediaPipe Detection Service", version="1.0.0")
processor = MediaPipeProcessor()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MediaPipe Detection",
        "mediapipe_available": processor.is_available()
    }

@app.post("/detect_pose")
async def detect_pose(file: UploadFile = File(...)):
    """Detect human pose in uploaded image"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        result = processor.process_pose(frame)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Pose detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_hands")
async def detect_hands(file: UploadFile = File(...)):
    """Detect hands in uploaded image"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        result = processor.process_hands(frame)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Hand detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_combined")
async def detect_combined(file: UploadFile = File(...)):
    """Detect both pose and hands in uploaded image"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        pose_result = processor.process_pose(frame)
        hands_result = processor.process_hands(frame)

        combined_result = {
            "pose": pose_result,
            "hands": hands_result,
            "timestamp": processor.get_timestamp()
        }

        return JSONResponse(content=combined_result)

    except Exception as e:
        logger.error(f"Combined detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)