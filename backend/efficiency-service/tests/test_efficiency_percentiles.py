import pytest
from utils.percentiles import map_percentile_to_zone


@pytest.mark.parametrize("score, population, expected_zone", [
    (0.1, [0.1, 0.2, 0.3, 0.4, 0.5], "very_low"),
    (0.2, [0.1, 0.2, 0.3, 0.4, 0.5], "low"),
    (0.3, [0.1, 0.2, 0.3, 0.4, 0.5], "medium"),
    (0.4, [0.1, 0.2, 0.3, 0.4, 0.5], "high"),
    (0.5, [0.1, 0.2, 0.3, 0.4, 0.5], "very_high"),
    (0.75, [0.5, 0.6, 0.7, 0.8, 0.9], "medium"),
    (0.6, [0.5, 0.6, 0.7, 0.8, 0.9], "low"),
    (0.3, [0.3], "very_high"),  # unique element
])
def test_map_percentile_to_zone(score, population, expected_zone):
    assert map_percentile_to_zone(score, population) == expected_zone


def test_map_percentile_to_zone_empty_population():
    with pytest.raises(ValueError, match="Population for percentile zone is empty"):
        map_percentile_to_zone(0.5, [])
