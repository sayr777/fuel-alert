from pydantic import BaseModel


class StationOut(BaseModel):
    id: int
    name: str
    brand: str | None
    address: str | None
    lat: float
    lon: float
