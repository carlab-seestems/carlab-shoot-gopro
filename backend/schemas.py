from pydantic import BaseModel
from datetime import datetime


class FileInfo(BaseModel):
    path: str
    size: int
    creation_time: float
    modification_time: float
    camera_serial_number: str

    class Config:
        schema_extra = {
            "example": {
                "path": "/path/to/file.txt",
                "size": 123456,
                "creation_time": datetime.timestamp(datetime.now()),
                "modification_time": datetime.timestamp(datetime.now()),
                "camera_serial_number": "1234567890"
            }
        }
