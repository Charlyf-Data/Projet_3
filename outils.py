import requests
import json
import requests
import json
import pandas as pd
from typing import Optional
import base64
import streamlit as st 

def find(query: str) -> Optional[pd.DataFrame]:
    """
    Finds places based on the query string using the Google Places API.

    Args:
        query (str): The search query to find places.

    Returns:
        Optional[pd.DataFrame]: A DataFrame containing the places data, or None if an error occurs.
    """
    with open('api.txt') as file:
        api_key = file.read().strip()  # Remove extra whitespace or newlines

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.currentOpeningHours,places.reviews,places.internationalPhoneNumber,places.websiteUri,places.photos,places.location,places.priceLevel"
    }

    data = {
        "textQuery": query
    }

    try:

        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

        response_json = response.json()
        places = response_json.get('places', [])  
        if places:
            df = pd.json_normalize(places)
            return df
        else:
            print("No places found in the response.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        return None
    

def add_background(image_path):
    """
    Ajoute une image de fond en utilisant un encodage base64.
    """
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;  
        }}
        </style>
        """,
        unsafe_allow_html=True
    )