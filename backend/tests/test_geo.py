import pytest

from app.services.geo import haversine_m, point_in_region


def test_haversine_same_point():
    assert haversine_m(37.6, 55.75, 37.6, 55.75) == pytest.approx(0.0)


def test_haversine_moscow_spb():
    # Москва (37.62, 55.75) → Санкт-Петербург (30.32, 59.93) ≈ 634 км
    dist = haversine_m(37.62, 55.75, 30.32, 59.93)
    assert 630_000 < dist < 640_000


def test_haversine_100m_latitude():
    # 0.001° по широте ≈ 111 м
    dist = haversine_m(37.6, 55.700, 37.6, 55.701)
    assert 100 < dist < 120


def test_haversine_symmetry():
    d1 = haversine_m(37.6, 55.75, 30.32, 59.93)
    d2 = haversine_m(30.32, 59.93, 37.6, 55.75)
    assert d1 == pytest.approx(d2, rel=1e-9)


# region_bbox по умолчанию: min_lon=27, min_lat=41, max_lon=60, max_lat=70 (Европейская Россия)

def test_region_moscow():
    assert point_in_region(37.62, 55.75) is True


def test_region_spb():
    assert point_in_region(30.32, 59.93) is True


def test_region_south_border():
    assert point_in_region(44.0, 41.0) is True   # граница включена
    assert point_in_region(44.0, 40.9) is False


def test_region_west_border():
    assert point_in_region(27.0, 55.0) is True
    assert point_in_region(26.9, 55.0) is False


def test_region_east_border():
    assert point_in_region(60.0, 55.0) is True
    assert point_in_region(60.1, 55.0) is False


def test_region_kamchatka_outside():
    # Петропавловск-Камчатский — вне bbox по долготе
    assert point_in_region(158.65, 53.01) is False


def test_region_london_outside():
    assert point_in_region(-0.12, 51.5) is False
