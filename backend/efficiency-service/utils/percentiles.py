def map_percentile_to_zone(score: float, population: list[float]) -> str:
    """
    Returns a quality zone ('very_low' ... 'very_high') based on 
    the percentile of the efficiency score compared to the reference population.
    """
    if not population:
        raise ValueError("Population for percentile zone is empty")

    sorted_vals = sorted(population)
    count = sum(1 for val in sorted_vals if val <= score)
    percentile = count / len(sorted_vals)

    if percentile <= 0.2:
        return "very_low"
    elif percentile <= 0.4:
        return "low"
    elif percentile <= 0.6:
        return "medium"
    elif percentile <= 0.8:
        return "high"
    else:
        return "very_high"
