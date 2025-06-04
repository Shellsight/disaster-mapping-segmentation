from pydantic import BaseModel

class SegmentRequest(BaseModel):
    image_path: str
    output_path: str

class SegmentResponse(BaseModel):
    status: str
    message: str