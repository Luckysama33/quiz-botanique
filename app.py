import streamlit as st
import pandas as pd
import os
import random

# --- CONFIGURATION ---
FILE_CSV = "plantes.csv"
IMG_FOLDER = "images"

# Créer le dossier images s'il n'existe pas
if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

# --- FONCTIONS UTILES ---

def charger_donnees():
    """Charge le fichier CSV ou crée un tableau vide si inexistant"""
    if os.path.exists(FILE_CSV):
        return pd.read_csv(FILE_CSV)
    else:
        return pd.DataFrame(columns=["Vernaculaire", "Genre", "Espece", "Famille", "Image"])

def sauvegarder_donnees(df):
    """Sauvegarde le tableau dans le fichier CSV"""
    df.to_csv(FILE_CSV, index=False)

# --- INTERFACE PRINCIPALE ---

st.title("🌿 Mon Quiz Botanique")

# Barre latérale pour la navigation
menu = st.sidebar.radio("Menu", ["Ajouter une plante", "Mode Quiz", "Ma Collection"])
df = charger_donnees()

# --- PAGE 1 : AJOUTER UNE PLANTE ---
if menu == "Ajouter une plante":
    st.header("Ajouter une nouvelle fiche")
    
    with st.form("ajout_plante"):
        nom = st.text_input("Nom Vernaculaire (ex: Chêne rouvre)")
        genre = st.text_input("Genre (ex: Quercus)")
        espece = st.text_input("Espèce (ex: robur)")
        famille = st.text_input("Famille (ex: Fagaceae)")
        photo = st.file_uploader("Photo de la plante", type=["jpg", "png", "jpeg"])
        
        submit = st.form_submit_button("Enregistrer la plante")
        
        if submit:
            if nom and genre and photo:
                # 1. Sauvegarder l'image
                photo_path = os.path.join(IMG_FOLDER, photo.name)
                with open(photo_path, "wb") as f:
                    f.write(photo.getbuffer())
                
                # 2. Ajouter au tableau
                new_data = pd.DataFrame({
                    "Vernaculaire": [nom],
                    "Genre": [genre],
                    "Espece": [espece],
                    "Famille": [famille],
                    "Image": [photo_path]
                })
                df = pd.concat([df, new_data], ignore_index=True)
                sauvegarder_donnees(df)
                st.success(f"La plante {nom} a été ajoutée !")
            else:
                st.error("Il manque des infos (Nom, Genre ou Photo) !")

# --- PAGE 2 : MODE QUIZ ---
elif menu == "Mode Quiz":
    st.header("🔎 Reconnaissance")
    
    if len(df) < 4:
        st.warning("Il faut au moins 4 plantes dans la base pour lancer un Quiz QCM !")
    else:
        # Initialiser une question si elle n'existe pas encore dans la session
        if 'bon_reponse' not in st.session_state:
            # Choisir une plante au hasard
            ligne_plante = df.sample(1).iloc[0]
            st.session_state['bon_reponse'] = ligne_plante
            # Choisir 3 mauvaises réponses
            distracteurs = df[df.index != ligne_plante.name].sample(3)
            # Mélanger les choix
            choix = [ligne_plante] + [d for _, d in distracteurs.iterrows()]
            random.shuffle(choix)
            st.session_state['choix'] = choix
            st.session_state['repondu'] = False

        # Afficher la question
        plante_mystere = st.session_state['bon_reponse']
        
        # Afficher l'image
        try:
            st.image(plante_mystere["Image"], width=400)
        except:
            st.error("Image introuvable.")

        st.write("### Quel est le nom latin de cette plante ?")

        # Afficher les boutons de réponse
        col1, col2 = st.columns(2)
        for i, choix in enumerate(st.session_state['choix']):
            nom_complet = f"{choix['Genre']} {choix['Espece']}"
            bouton = col1.button(nom_complet, key=i) if i % 2 == 0 else col2.button(nom_complet, key=i)
            
            if bouton:
                st.session_state['repondu'] = True
                if choix['Vernaculaire'] == plante_mystere['Vernaculaire']:
                    st.success(f"BRAVO ! C'est bien {plante_mystere['Genre']} {plante_mystere['Espece']} ({plante_mystere['Vernaculaire']})")
                else:
                    st.error(f"Raté... C'était {plante_mystere['Genre']} {plante_mystere['Espece']}")
        
        if st.session_state['repondu']:
            if st.button("Question Suivante"):
                del st.session_state['bon_reponse']
                st.rerun()

# --- PAGE 3 : MA COLLECTION ---
elif menu == "Ma Collection":
    st.header("Mon Herbier Numérique")
    st.dataframe(df)