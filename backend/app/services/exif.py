"""Best-effort EXIF extraction for uploaded photos.

Used by the validation pipeline to flag reports where the photo's metadata
disagrees with what the driver claims (see docs/moderation.md, "review_flags").
Telegram strips EXIF from photos sent as compressed "photo" attachments but
keeps it when sent as an uncompressed "file" — the bot should prefer asking
for files where possible; either way this must degrade gracefully to None.
"""

from datetime import datetime
from io import BytesIO

from PIL import ExifTags, Image


def extract_exif(data: bytes) -> tuple[datetime | None, tuple[float, float] | None]:
    """Returns (taken_at, (lon, lat)) — either element may be None."""
    try:
        image = Image.open(BytesIO(data))
        raw_exif = image.getexif()
    except Exception:
        return None, None

    if not raw_exif:
        return None, None

    tags = {ExifTags.TAGS.get(k, k): v for k, v in raw_exif.items()}

    taken_at = None
    for key in ("DateTimeOriginal", "DateTime"):
        value = tags.get(key)
        if value:
            try:
                taken_at = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                break
            except ValueError:
                continue

    gps_info = raw_exif.get_ifd(ExifTags.IFD.GPSInfo) if hasattr(raw_exif, "get_ifd") else None
    lon_lat = None
    if gps_info:
        lon_lat = _parse_gps(gps_info)

    return taken_at, lon_lat


def _to_degrees(value) -> float:
    d, m, s = value
    return float(d) + float(m) / 60.0 + float(s) / 3600.0


def _parse_gps(gps_info: dict) -> tuple[float, float] | None:
    try:
        lat = _to_degrees(gps_info[2])
        if gps_info[1] == "S":
            lat = -lat
        lon = _to_degrees(gps_info[4])
        if gps_info[3] == "W":
            lon = -lon
        return lon, lat
    except (KeyError, ZeroDivisionError, TypeError):
        return None
