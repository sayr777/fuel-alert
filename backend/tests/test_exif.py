from datetime import datetime, timedelta, timezone
from io import BytesIO

from PIL import Image

from app.services.exif import extract_exif
from app.services.validation import check_exif_consistency

_BASE_TIME = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_LON, _LAT = 37.62, 55.75


def _plain_jpeg() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (10, 10)).save(buf, format="JPEG")
    return buf.getvalue()


# --- extract_exif ---

def test_extract_invalid_bytes():
    assert extract_exif(b"not an image") == (None, None)


def test_extract_jpeg_without_exif():
    taken_at, gps = extract_exif(_plain_jpeg())
    assert taken_at is None
    assert gps is None


def test_extract_empty_bytes():
    assert extract_exif(b"") == (None, None)


# --- check_exif_consistency ---

def test_no_exif_no_flags():
    assert check_exif_consistency(None, None, _BASE_TIME, _LON, _LAT) == []


def test_time_within_3h_no_flag():
    taken_at = _BASE_TIME - timedelta(hours=2, minutes=59)
    flags = check_exif_consistency(taken_at, None, _BASE_TIME, _LON, _LAT)
    assert "exif_time_mismatch" not in flags


def test_time_over_3h_flagged():
    taken_at = _BASE_TIME - timedelta(hours=3, seconds=1)
    flags = check_exif_consistency(taken_at, None, _BASE_TIME, _LON, _LAT)
    assert "exif_time_mismatch" in flags


def test_time_naive_treated_as_utc():
    # naive datetime должен приниматься без падения
    taken_at = _BASE_TIME.replace(tzinfo=None) - timedelta(hours=4)
    flags = check_exif_consistency(taken_at, None, _BASE_TIME, _LON, _LAT)
    assert "exif_time_mismatch" in flags


def test_gps_close_no_flag():
    # ~63 м — в пределах порога 5 км
    flags = check_exif_consistency(None, (37.621, 55.75), _BASE_TIME, _LON, _LAT)
    assert "exif_gps_mismatch" not in flags


def test_gps_far_flagged():
    # 1° по долготе на 55° ш ≈ 63 км — превышает порог 5 км
    flags = check_exif_consistency(None, (38.62, 55.75), _BASE_TIME, _LON, _LAT)
    assert "exif_gps_mismatch" in flags


def test_both_flags_independent():
    taken_at = _BASE_TIME - timedelta(hours=5)
    flags = check_exif_consistency(taken_at, (38.62, 55.75), _BASE_TIME, _LON, _LAT)
    assert "exif_time_mismatch" in flags
    assert "exif_gps_mismatch" in flags
