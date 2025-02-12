from dotenv import dotenv_values
from sqlalchemy import create_engine, text
import pandas as pd
from typing import Optional
import streamlit as st
from streamlit_authenticator import Authenticate
from sqlalchemy import text


class Sql_manager:
    def __init__(self, env_path=".env"):
        config = dotenv_values(env_path)
        DB_HOST = config["DB_HOST"]
        DB_NAME = config["DB_NAME"]
        DB_USER = config["DB_USER"]
        DB_PASSWORD = config["DB_PASSWORD"]
        self.engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')
        try:
            self.engine.connect()
            print("✅ Connexion à PostgreSQL réussie !")
        except Exception as e:
            print(f"❌ Erreur de connexion : {e}")


    def insert_lieu(self, lieu: pd.Series) -> Optional[dict]:
        query = text("""
            INSERT INTO lieux (country, city, nom, adresse, longitude, latitude, type)
            VALUES (:country, :city, :nom, :adresse, :longitude, :latitude, :type)
        """)
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    conn.execute(query, {
                        "country": lieu.get("country"),
                        "city": lieu.get("city"),
                        "nom": lieu.get("displayName.text"),
                        "adresse": lieu.get("formattedAddress"),
                        "longitude": lieu.get("location.longitude"),
                        "latitude": lieu.get("location.latitude"),
                        "type": lieu.get("primaryType"),
                    })
            print("✅ Première ligne insérée avec succès !")
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion en base de données : {e}")


    def find_all_data_df(self, table: str):
        with self.engine.connect() as conn:
            query = text(f"SELECT * FROM {table}")
            result = self.engine.execute(query)
            rows = result.fetchall()
            return pd.DataFrame(rows, columns=result.keys())
    
    def find_id_user(self, username, password):
        with self.engine.connect() as conn:
            query = text("SELECT id, usernames, role FROM users WHERE usernames = :username AND password = :password")
            result = conn.execute(query, {"username": username, "password": password})
            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=result.keys())
            id_user = df["id"].iloc[0]  
            username = df["usernames"].iloc[0]
            role_user = df["role"].iloc[0]
            return id_user, username, role_user
        
        
    def inscrire_utilisateur(self, name: str, username: str, email: str, password: str, role: str):
        insert_query = text("""
            INSERT INTO users (date_de_creation, password, usernames, name, email, failed_login_attempts, logged_in, role)
            VALUES (CURRENT_TIMESTAMP, :password, :username, :name, :email, 0, false, :role)
            ON CONFLICT (usernames) DO NOTHING
        """)

        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(insert_query, {
                        "password": password,  # Stocke le mot de passe en clair (temporairement)
                        "username": username,
                        "name": name,
                        "email": email,
                        "role": role
                    })
                    
                    if result.rowcount > 0:  # Vérifie si une ligne a été insérée
                        return True  
                    else:
                        return False 

        except Exception:
            return False  
        
    def find_place(self, city, adresse):
         with self.engine.connect() as conn:
            query = text("SELECT country, city, adresse, nom   FROM lieux WHERE adresse = :adresse AND city = :city")
            result = conn.execute(query, {"adresse": adresse, "city": city})
            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=result.keys())
            city = df["city"].iloc[0]  
            adresse = df["adresse"].iloc[0]
            country = df["country"].iloc[0]
            nom = df["nom"].iloc[0]
            return country, city, adresse, nom
        