# main.py
import streamlit as st
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import spacy

from C_belaud.config import DEFAULT_LOCATION, COLOR_SCHEME
from C_belaud.services import LocationService, RestaurantService
from C_belaud.ui import RestaurantUI
from C_belaud.api_utils import find_restaurants, create_restaurant, get_route, generate_wordcloud

# Charger le modèle spaCy pour le français
nlp = spacy.load("fr_core_news_sm")
all_stopwords = nlp.Defaults.stop_words.union()

def clean_text_spacy(text):
    """
    Nettoie le texte avec spaCy :
      - Conversion en minuscules
      - Tokenisation et lemmatisation
      - Suppression des stopwords, de la ponctuation et des nombres
    """
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc 
              if token.text not in all_stopwords and not token.is_punct and not token.like_num]
    return " ".join(tokens)

# Utilisation de la colormap "Reds" pour tous les graphiques Plotly
PLOTLY_COLOR_SCHEME = "Reds"

def main1():
    # Initialisation de st.session_state
    for key in ['restaurants', 'df', 'favorites', 'search_history', 'reviews', 'selected_route']:
        if key not in st.session_state:
            st.session_state[key] = [] if key != 'df' else pd.DataFrame()
    if "user_reviews" not in st.session_state:
        st.session_state.user_reviews = {}
    if "go_to_itinerary" not in st.session_state:
        st.session_state.go_to_itinerary = False

    loc_service = LocationService()
    st.set_page_config(layout="wide")
    tab = st.radio("Navigation", ["🔍 Recherche", "👤 Profil"], horizontal=True, index=1)

    # ------------------------- Section Recherche -------------------------
    if tab == "🔍 Recherche":
        st.title("🔍 Recherche de Restaurants et Géolocalisation")
        loc = loc_service.get_user_location()
        if loc:
            loc_service.display_location_info()
        else:
            st.warning("Activez la géolocalisation dans votre navigateur")
        
        with st.form("search_form"):
            query = st.text_input("Rechercher des restaurants")
            if st.form_submit_button("🔍 Lancer la recherche"):
                with st.spinner("Recherche en cours..."):
                    df = find_restaurants(query, st.session_state.location)
                    if df is not None and not df.empty:
                        st.session_state.df = df
                        st.session_state.restaurants = [r for r in [create_restaurant(row) for _, row in df.iterrows()] if r is not None]
                        st.session_state.search_history.append(time.time())
                        st.success(f"{len(st.session_state.restaurants)} résultats trouvés!")
                    else:
                        st.session_state.restaurants = []
                        st.warning("Aucun résultat trouvé")
                        
        if st.session_state.restaurants:
            cols = st.columns([1, 2])
            with cols[0]:
                st.subheader("Liste des résultats")
                types_valides = {r.primary_type for r in st.session_state.restaurants if r.primary_type}
                selected_type = st.selectbox("Filtrer par type", ["Tous"] + sorted(types_valides))
                sort_option = st.selectbox("Trier par", ["Note décroissante", "Note croissante", "Nombre d'avis"])
                filtered = [r for r in st.session_state.restaurants if selected_type == "Tous" or r.primary_type == selected_type]
                reverse = (sort_option == "Note décroissante")
                if "Note" in sort_option:
                    filtered.sort(key=lambda x: x.rating or 0, reverse=reverse)
                else:
                    filtered.sort(key=lambda x: x.user_ratings_total or 0, reverse=True)
                for restaurant in filtered:
                    with st.expander(f"🏠 {restaurant.name}"):
                        st.write(f"⭐ **Note Google Maps:** {restaurant.rating}/5" if restaurant.rating else "⭐ Aucune note Google Maps")
                        st.write(f"📍 {restaurant.address}")
                        st.write(f"📌 Type: {restaurant.primary_type}")
                        if restaurant.latest_review:
                            st.write(f"💬 Dernier avis: _{restaurant.latest_review}_")
                        
                        col_actions = st.columns(2)
                        with col_actions[0]:
                            if st.button("🗺️ Itinéraire", key=f"route_{restaurant.place_id}"):
                                st.session_state.selected_route = restaurant
                                st.session_state.go_to_itinerary = True
                                st.rerun()
                        with col_actions[1]:
                            if st.button("❤️ Ajouter aux favoris", key=f"fav_{restaurant.place_id}"):
                                if restaurant not in st.session_state.favorites:
                                    st.session_state.favorites.append(restaurant)
                                    st.success("Ajouté aux favoris!")
                        
                        st.markdown("---")
                        col_slider, col_text = st.columns([1, 3])
                        rating_value = col_slider.slider("Votre note", 0.0, 5.0, 0.0, step=0.1, key=f"slider_{restaurant.place_id}")
                        user_review = col_text.text_area("Votre avis", key=f"review_input_{restaurant.place_id}", height=100)
                        if st.button("Ajouter votre avis", key=f"add_review_{restaurant.place_id}"):
                            if user_review.strip():
                                st.session_state.reviews.append({
                                    "restaurant": restaurant.name,
                                    "type": restaurant.primary_type,
                                    "review": user_review,
                                    "rating": rating_value,
                                    "date": datetime.now().strftime("%d/%m/%Y %H:%M")
                                })
                                st.success("Votre avis a été ajouté !")
                        
                        if restaurant.place_id in st.session_state.user_reviews:
                            st.markdown("**Avis des utilisateurs :**")
                            for ur in st.session_state.user_reviews[restaurant.place_id]:
                                st.write(ur)
     
            with cols[1]:
                if st.session_state.get("go_to_itinerary", False) and st.session_state.selected_route:
                    st.subheader("Itinéraire détaillé")
                    # Vérifier si selected_route est une liste et extraire le premier élément si nécessaire
                    selected = st.session_state.selected_route[0] if isinstance(st.session_state.selected_route, list) else st.session_state.selected_route
                    user_loc = (st.session_state.location.latitude, st.session_state.location.longitude)
                    resto_loc = (selected.latitude, selected.longitude)
                    geometry, distance, duration = get_route(user_loc, resto_loc)
                    if geometry:
                        m_route = folium.Map(
                            location=[(user_loc[0] + resto_loc[0]) / 2, (user_loc[1] + resto_loc[1]) / 2],
                            zoom_start=13
                        )
                        folium.Marker(user_loc, popup="Vous", icon=folium.Icon(color="blue")).add_to(m_route)
                        folium.Marker(resto_loc, popup=selected.name, icon=folium.Icon(color="red")).add_to(m_route)
                        folium.GeoJson(geometry, style_function=lambda x: {'color': 'green'}).add_to(m_route)
                        st_folium(m_route, width=700)
                        if distance and duration:
                            st.write(f"**Distance:** {distance/1000:.2f} km | **Durée:** {duration/60:.1f} min")
                    else:
                        st.info("Aucun itinéraire trouvé.")
                    if st.button("Retour aux visualisations"):
                        st.session_state.go_to_itinerary = False
                        st.rerun()
                else:
                    m = folium.Map(
                        location=(st.session_state.location.latitude, st.session_state.location.longitude)
                        if st.session_state.location else DEFAULT_LOCATION,
                        zoom_start=14
                    )
                    if st.session_state.location:
                        folium.Marker(
                            [st.session_state.location.latitude, st.session_state.location.longitude],
                            tooltip="Votre position",
                            icon=folium.Icon(color="red", icon="user")
                        ).add_to(m)
                    cluster = MarkerCluster().add_to(m)
                    for r in filtered:
                        folium.Marker(
                            [r.latitude, r.longitude],
                            popup=f"<b>{r.name}</b><br>Note: {r.rating}/5",
                            icon=folium.Icon(color="blue", icon="glyphicon glyphicon-cutlery")
                        ).add_to(cluster)
                    st_folium(m, width=700)
                    
                    tabs_right = st.tabs(["Visualisations", "Itinéraire"])
                    with tabs_right[0]:
                        st.subheader("📈 Statistiques")
                        cols_stats = st.columns(3)
                        if not st.session_state.df.empty:
                            cols_stats[0].metric("Note moyenne Google Maps", f"{st.session_state.df['rating'].mean():.1f}/5")
                            cols_stats[1].metric("Total établissements", len(st.session_state.df))
                            cols_stats[2].metric("Avis total", st.session_state.df['userRatingCount'].sum())
                        
                        tabs_viz = st.tabs([
                            "Distribution des notes Google Maps", 
                            "Répartition par type", 
                            "Notes vs Avis", 
                            "WordCloud Avis par Restaurants",
                            "WordCloud Avis Global"
                        ])
                        
                        with tabs_viz[0]:
                            df_sorted = st.session_state.df.sort_values(by="rating", ascending=True)
                            fig_hist = px.bar(
                                df_sorted, 
                                y='rating',
                                title='Distribution des notes',
                                color='rating',
                                color_continuous_scale="Reds",
                                orientation='h'
                            )
                            fig_hist.update_layout(
                                plot_bgcolor="white",
                                paper_bgcolor="white",
                                font=dict(color="black"),
                                xaxis_title="Nombre d'établissements",
                                yaxis_title="Note moyenne"
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)
                        
                        with tabs_viz[1]:
                            if 'primaryType' in st.session_state.df.columns:
                                type_counts = st.session_state.df['primaryType'].value_counts().reset_index()
                                type_counts.columns = ['Type', 'Count']
                                type_counts = type_counts.sort_values(by="Count", ascending=True)
                                fig_pie = px.pie(
                                    type_counts, 
                                    values="Count", 
                                    names="Type",
                                    title="Répartition par type de restaurant",
                                    color="Type",
                                    color_discrete_sequence=px.colors.sequential.Reds
                                )
                                fig_pie.update_layout(
                                    plot_bgcolor="white",
                                    paper_bgcolor="white",
                                    font=dict(color="black")
                                )
                                st.plotly_chart(fig_pie, use_container_width=True)
                        
                        with tabs_viz[2]:
                            fig_scatter = px.scatter(
                                st.session_state.df, x='rating', y='userRatingCount',
                                color='displayName.text', title="Relation entre note et nombre d'avis",
                                size='rating',
                                labels={'rating': "Note", 'userRatingCount': "Nombre d'avis"},
                                color_discrete_sequence=px.colors.sequential.Reds
                            )
                            fig_scatter.update_layout(
                                plot_bgcolor="white",
                                paper_bgcolor="white",
                                font=dict(color="black")
                            )
                            st.plotly_chart(fig_scatter, use_container_width=True)
                        
                        with tabs_viz[3]:
                            restaurants_avec_avis = [r for r in st.session_state.restaurants 
                                                     if (r.all_reviews and len(r.all_reviews) > 0) or 
                                                        (r.place_id in st.session_state.user_reviews and st.session_state.user_reviews[r.place_id])]
                            if restaurants_avec_avis:
                                restaurant_names = [r.name for r in restaurants_avec_avis]
                                selected_restaurant_name = st.selectbox("Choisissez un restaurant pour afficher le WordCloud de ses avis", restaurant_names, key="wc_select")
                                selected_restaurant = next((r for r in restaurants_avec_avis if r.name == selected_restaurant_name), None)
                                if selected_restaurant:
                                    all_reviews = list(selected_restaurant.all_reviews) if selected_restaurant.all_reviews else []
                                    if selected_restaurant.place_id in st.session_state.user_reviews:
                                        all_reviews.extend(st.session_state.user_reviews[selected_restaurant.place_id])
                                    if all_reviews:
                                        all_reviews = [clean_text_spacy(review) for review in all_reviews]
                                        all_reviews_text = " ".join(all_reviews)
                                        wordcloud = WordCloud(
                                            width=800, height=400,
                                            background_color="white",
                                            colormap="Reds",
                                            max_words=200,
                                            contour_color="black",
                                            contour_width=2,
                                            stopwords=all_stopwords
                                        ).generate(all_reviews_text)
                                        fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
                                        ax_wc.imshow(wordcloud, interpolation="bilinear")
                                        ax_wc.axis("off")
                                        ax_wc.set_title(f"WordCloud des Avis - {selected_restaurant_name}", fontsize=14, color="black")
                                        fig_wc.patch.set_facecolor("white")
                                        st.pyplot(fig_wc)
                                    else:
                                        st.info("Aucun avis disponible pour ce restaurant.")
                            else:
                                st.info("Aucun avis disponible pour générer un WordCloud.")
                        
                        with tabs_viz[4]:
                            all_reviews_global = []
                            for r in st.session_state.restaurants:
                                if r.all_reviews and len(r.all_reviews) > 0:
                                    all_reviews_global.extend([clean_text_spacy(review) for review in r.all_reviews])
                                if r.place_id in st.session_state.user_reviews:
                                    all_reviews_global.extend([clean_text_spacy(review) for review in st.session_state.user_reviews[r.place_id]])
                            if all_reviews_global:
                                all_reviews_text_global = " ".join(all_reviews_global)
                                wordcloud_global = WordCloud(
                                    width=800, height=400,
                                    background_color="white",
                                    colormap="Reds",
                                    max_words=200,
                                    contour_color="black",
                                    contour_width=2,
                                    stopwords=all_stopwords
                                ).generate(all_reviews_text_global)
                                fig_global, ax_global = plt.subplots(figsize=(10, 5))
                                ax_global.imshow(wordcloud_global, interpolation="bilinear")
                                ax_global.axis("off")
                                ax_global.set_title("WordCloud des Avis Global", fontsize=14, color="black")
                                fig_global.patch.set_facecolor("white")
                                st.pyplot(fig_global)
                            else:
                                st.info("Aucun avis global disponible pour générer un WordCloud.")
                    
                        with tabs_right[1]:
                            st.subheader("Itinéraire détaillé")
                            user_loc = (st.session_state.location.latitude, st.session_state.location.longitude)
                            # Vérifier si selected_route est une liste, et en extraire le premier élément si nécessaire
                            selected = st.session_state.selected_route[0] if isinstance(st.session_state.selected_route, list) else st.session_state.selected_route
                            resto_loc = (selected.latitude, selected.longitude)
                            geometry, distance, duration = get_route(user_loc, resto_loc)
                            if geometry:
                                m_route = folium.Map(
                                    location=[(user_loc[0] + resto_loc[0]) / 2, (user_loc[1] + resto_loc[1]) / 2],
                                    zoom_start=13
                                )
                                folium.Marker(user_loc, popup="Vous", icon=folium.Icon(color="blue")).add_to(m_route)
                                folium.Marker(resto_loc, popup=selected.name, icon=folium.Icon(color="red")).add_to(m_route)
                                folium.GeoJson(geometry, style_function=lambda x: {'color': 'green'}).add_to(m_route)
                                st_folium(m_route, width=700)
                                if distance and duration:
                                    st.write(f"**Distance:** {distance/1000:.2f} km | **Durée:** {duration/60:.1f} min")
                            else:
                                st.info("Aucun itinéraire trouvé.")
                    
            # Fin des onglets Visualisations
        # Fin de la section Recherche

    # ------------------------- Section Profil -------------------------
    elif tab == "👤 Profil":
        st.title("👤 Votre Profil")
        st.markdown("## Tableau de Bord Personnel")
        
        profile_tabs = st.tabs(["Métriques", "Avis & Statistiques", "Favoris"])
        
        with profile_tabs[0]:
            st.subheader("📊 Métriques")
            reviews_count = len(st.session_state.reviews)
            favorites_count = len(st.session_state.favorites)
            rated_reviews = [rev for rev in st.session_state.reviews if rev.get("rating") is not None]
            avg_rating = sum([rev["rating"] for rev in rated_reviews]) / len(rated_reviews) if rated_reviews else 0
            cols_stats = st.columns(3)
            cols_stats[0].metric("Total Avis", reviews_count)
            cols_stats[1].metric("Favoris", favorites_count)
            cols_stats[2].metric("Note Moyenne", f"{avg_rating:.1f}" if rated_reviews else "N/A")
        
        with profile_tabs[1]:
            st.subheader("📈 Avis & Statistiques")
            sub_tabs = st.tabs(["Avis Récents", "Distribution des Notes", "Word Cloud"])
            with sub_tabs[0]:
                st.subheader("Vos Avis Récents")
                if st.session_state.reviews:
                    recent_reviews = st.session_state.reviews[-5:]
                    for rev in reversed(recent_reviews):
                        st.markdown(f"**{rev['restaurant']}** – *{rev['date']}*")
                        st.info(f"> {rev['review']}")
                        if rev.get("rating") is not None:
                            st.write(f"**Note :** {rev['rating']}/5")
                        st.markdown("---")
                else:
                    st.info("Aucun avis n'a été laissé.")
            with sub_tabs[1]:
                st.subheader("Distribution des Notes")
                if st.session_state.reviews:
                    df_reviews = pd.DataFrame(st.session_state.reviews)
                    if not df_reviews.empty and "rating" in df_reviews.columns:
                        df_reviews["rating"] = pd.to_numeric(df_reviews["rating"], errors='coerce').fillna(0)
                    fig_hist = px.histogram(df_reviews, x="rating", nbins=10, title="Distribution des Notes",
                                            color_discrete_sequence="Reds")
                    fig_hist.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                           font=dict(color="black"), xaxis_title="Note", yaxis_title="Nombre d'avis")
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("Pas d'avis pour afficher la distribution.")
            with sub_tabs[2]:
                st.subheader("Word Cloud de Vos Avis")
                if st.session_state.reviews:
                    df_reviews = pd.DataFrame(st.session_state.reviews)
                    reviews_text = " ".join([clean_text_spacy(review) for review in df_reviews["review"].astype(str).tolist()])
                    if reviews_text.strip():
                        wordcloud = WordCloud(width=800, height=400, background_color="white", colormap="Reds",
                                              max_words=200, contour_color="black", contour_width=2,
                                              stopwords=all_stopwords).generate(reviews_text)
                        fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
                        ax_wc.imshow(wordcloud, interpolation="bilinear")
                        ax_wc.axis("off")
                        ax_wc.set_title("Word Cloud de Vos Avis", fontsize=14, color="black")
                        fig_wc.patch.set_facecolor("white")
                        st.pyplot(fig_wc)
                    else:
                        st.info("Aucun texte disponible pour le Word Cloud.")
                else:
                    st.info("Aucun avis n'a été laissé.")
        
        with profile_tabs[2]:
            st.subheader("⭐ Favoris")
            if st.session_state.favorites:
                for fav in st.session_state.favorites:
                    st.markdown(f"- **{fav.name}**")
                st.markdown("### Carte de vos restaurants favoris")
                map_center = (st.session_state.location.latitude, st.session_state.location.longitude) if st.session_state.location else DEFAULT_LOCATION
                m_fav = folium.Map(location=map_center, zoom_start=13)
                for fav in st.session_state.favorites:
                    folium.Marker([fav.latitude, fav.longitude], popup=fav.name,
                                  icon=folium.Icon(color='green', icon='star')).add_to(m_fav)
                st_folium(m_fav, width=700)
            else:
                st.info("Vous n'avez aucun favori pour le moment.")
        
        st.markdown("---")
        st.markdown("<h3 style='text-align: center; color: #FF5733;'>Continuez à explorer et à partager vos expériences culinaires !</h3>", unsafe_allow_html=True)

if __name__ == "__main__":
    main1()
