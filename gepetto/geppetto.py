import json
import google.generativeai as genai
import os
from gtts import gTTS
import playsound
import streamlit as st
import requests
import pandas as pd
import folium 


# Classe pour gérer l'API Google Places
class GooglePlacesAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        self.photo_url = "https://maps.googleapis.com/maps/api/place/photo"

    def search_places(self, query):
        search_params = {
            "query": query,
            "key": self.api_key
        }
        place_data = []

        while True:
            try:
                response = requests.get(self.search_url, params=search_params)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Erreur lors de la requête de recherche: {e}")
                break

            search_data = response.json()
            places = search_data.get('results', [])

            for place in places:
                place_info = {
                    'name': place.get('name'),
                    'address': place.get('formatted_address'),
                    'latitude': place.get('geometry', {}).get('location', {}).get('lat'),
                    'longitude': place.get('geometry', {}).get('location', {}).get('lng'),
                    'ratings': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total'),
                    'place_id': place.get('place_id')
                }
                place_data.append(place_info)

            next_page_token = search_data.get('next_page_token')
            if next_page_token:
                search_params['pagetoken'] = next_page_token
            else:
                break

        return place_data

    def get_place_details(self, place_id):
        details_params = {
            "place_id": place_id,
            "key": self.api_key
        }

        try:
            response = requests.get(self.details_url, params=details_params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête de détails: {e}")
            return {}

        return response.json().get('result', {})

    def generate_map(self, place_data):
        if not place_data:
            print("Aucun lieu à afficher sur la carte.")
            return None

        df = pd.DataFrame(place_data)
        m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=13)

        for _, row in df.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(f"<b>{row['name']}</b><br>{row['address']}<br>Ratings: {row['ratings']}", max_width=300),
                icon=folium.Icon(color='blue')
            ).add_to(m)

        return m

# Classe Geppetto enrichie
class Geppetto:
    def __init__(self, api_key=api_key, name_model="gemini-1.5-flash", temperature=1):
        self.api_key = api_key
        self.model = None
        self.name_model = name_model
        self.temperature = temperature
        self.places_api = GooglePlacesAPI(api_key=self.api_key)  # Intégration de Google Places
        self.preprompt('admin_preprompt')

    def _configure(self):
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.name_model).start_chat()
        self.talk(self.admin_preprompt)

    def _load_preprompt(self, cle_dico: str):
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir, 'preprompt.json')
        try:
            with open(file_path, 'r') as file:
                prompts = json.load(file)
                if cle_dico in prompts:
                    self.admin_preprompt = prompts[cle_dico]
                else:
                    raise ValueError("Clé introuvable dans le préprompt")
        except FileNotFoundError:
            raise FileNotFoundError(f"Le fichier {file_path} est introuvable.")
        except json.JSONDecodeError:
            raise ValueError("Erreur lors du décodage du fichier JSON.")

    def preprompt(self, cle_dico):
        self._load_preprompt(cle_dico)
        self._configure()

    def talk(self, message: str) -> str:
        try:
            response = self.model.send_message(message)
            assistant_response = response.text.strip().replace('\\', '')
            return assistant_response
        except Exception as e:
            print(f"Une erreur est survenue lors de l'envoi du message: {e}")
            return "Une erreur est survenue."

    def voice_talk(self, message: str):
        response = self.talk(message)
        if response != "Une erreur est survenue.":
            tts = gTTS(response, lang='fr')
            tts.save('response.mp3')
            playsound.playsound('response.mp3')
            return 'response.mp3'
        else:
            print("Erreur lors de la génération de la réponse audio.")
            return None

    def search_places(self, query):
        places = self.places_api.search_places(query)
        if not places:
            return "Aucun lieu trouvé pour la requête."

        for place in places[:5]:  # Limiter à 5 résultats pour une réponse concise
            details = self.places_api.get_place_details(place['place_id'])
            place['details'] = {
                'phone_number': details.get('formatted_phone_number', 'Non disponible'),
                'website': details.get('website', 'Non disponible'),
                'opening_hours': details.get('opening_hours', {}).get('weekday_text', 'Non disponible')
            }

        map_object = self.places_api.generate_map(places)
        return places, map_object


# nb total de restau likés, visités, 
# repartitions geographique des restau
# duree mpyenne entre les visites des restau
# distribution des gammes de prix
# repartition des types de cuisines
# wordCloud des commentaires des restau


# voir le placesearch, en plus de texrsearch pour avoir plus d'infos sur les restaurants
# il faurt que Geppetto(), au lieu de donner uniquement une liste de restaurant, donne par exemple ses trois recommandations dans le dataframe en fonction de ce qu'il a compris de la demande utilisateur
