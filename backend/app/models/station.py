from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Station(Base):
    """Reference directory of fuel stations, seeded from OSM and manually verified."""

    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
