import requests
import pandas as pd
import json
from typing import Optional

def find(query: str) -> Optional[pd.DataFrame]:
    """
    Finds places based on the query string using the Google Places API.

    Args:
        query (str): The search query to find places.

    Returns:
        Optional[pd.DataFrame]: A DataFrame containing the places data, or None if an error occurs.
    """
    with open('api.txt') as file:
        api_key = file.read().strip()  # Read API key

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.primaryType"
    }

    data = {
        "textQuery": query
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Check for HTTP errors

        response_json = response.json()
        places = response_json.get('places', [])
        if not places:
            print("No places found in the response.")
            return None

        # Convert JSON to DataFrame
        df = pd.json_normalize(places)

        # Extract city & country
        df[['city', 'country']] = df['formattedAddress'].str.rsplit(',', n=2, expand=True)[[1, 2]]

        return df[['displayName.text', 'formattedAddress', 'city', 'country', 'location.latitude', 'location.longitude', 'rating', 'userRatingCount', 'primaryType']]

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        return None



def findV2(query: str) -> Optional[pd.DataFrame]:
    """
    Finds places based on the query string using the Google Places API.

    Args:
        query (str): The search query to find places.

    Returns:
        Optional[pd.DataFrame]: A DataFrame containing the places data, or None if an error occurs.
    """
     # Read API key

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": "AIzaSyA7qPLy7k6Gnl50R-dYBxODXm8muIRtKGE",
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.primaryType"
    }

    data = {
        "textQuery": query
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Check for HTTP errors

        response_json = response.json()
        places = response_json.get('places', [])
        if not places:
            print("No places found in the response.")
            return None

        # Convert JSON to DataFrame
        df = pd.json_normalize(places)

        # Extract city & country
        df[['city', 'country']] = df['formattedAddress'].str.rsplit(',', n=2, expand=True)[[1, 2]]

        return df[['displayName.text', 'formattedAddress', 'city', 'country', 'location.latitude', 'location.longitude', 'rating', 'userRatingCount', 'primaryType']]

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        return None