from pydantic import BaseModel

class AudioRequest(BaseModel):
    id: str
    texto: str

class AudioResponse(BaseModel):
    status: str
    file: str
    node: str
