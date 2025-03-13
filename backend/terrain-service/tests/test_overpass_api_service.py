import pytest
import logging
import logging_setup
from app.overpass_api_service import fetch_overpass_data, build_overpass_query


# Test per build_overpass_query
def test_build_overpass_query():
    """Test the function generates a valid Overpass query."""
    min_lat, min_lng, max_lat, max_lng = 46.110155, 8.287771,46.115901,8.291248
    query = build_overpass_query(min_lat, min_lng, max_lat, max_lng)

    print("Generated Overpass Query:\n" + query)

    # Check that the query contains the right elements
    assert "[out:json]" in query, "La query dovrebbe essere in formato JSON."
    assert f'way["highway"]({min_lat},{min_lng},{max_lat},{max_lng})' in query, "La query dovrebbe contenere i limiti geografici corretti."
    assert "out body;" in query, "La query dovrebbe contenere 'out body;' per l'output."
    
# Test for fetch_overpass_data with a real query
def test_fetch_overpass_data():
    """Test the Overpass API call to verify it returns valid data."""
    min_lat, min_lng, max_lat, max_lng = 46.110155, 8.287771,46.115901,8.291248
    query = build_overpass_query(min_lat, min_lng, max_lat, max_lng)

    print("Testing Overpass API call...")
    response = fetch_overpass_data(query)

    if response:
        print("Overpass API returned data successfully.")
        assert "elements" in response, "The response should contain 'elements'."
        assert isinstance(response["elements"], list), "The elements should be a list."
    else:
        print("Overpass API did not return any data. Check the connection of the geographical limits.")
