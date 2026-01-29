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

# --- NAVIGATION ET ETATS ---

# 1. On initialise la page par défaut si elle n'existe pas
if 'navigation' not in st.session_state:
    st.session_state['navigation'] = 'Accueil'

# 2. Fonctions pour changer de page via les boutons
def aller_au_quiz():
    st.session_state['navigation'] = 'Mode Quiz'

def aller_a_ajout():
    st.session_state['navigation'] = 'Ajouter une plante'

# 3. Le Menu Latéral (Connecté à la mémoire 'navigation')
# Le paramètre 'key' lie ce menu à la variable st.session_state['navigation']
menu = st.sidebar.radio(
    "Menu", 
    ["Accueil", "Ajouter une plante", "Mode Quiz", "Ma Collection"],
    key='navigation'
)

df = charger_donnees()

# --- PAGE 0 : ACCUEIL ---
if menu == "Accueil":
    st.write("### 🌱PlantQuiz🌱")
    st.write("Que veux-tu faire aujourd'hui ?")
    
    # On crée deux colonnes pour aligner les boutons
    col1, col2 = st.columns(2)
    
    with col1:
        # Un grand bouton pour le Quiz
        st.info("🎓 **S'entraîner**")
        st.write("Teste tes connaissances")
        # Le bouton déclenche la fonction 'aller_au_quiz'
        st.button("Lancer le Quiz ➡️", on_click=aller_au_quiz, use_container_width=True)

    with col2:
        # Un grand bouton pour l'Ajout
        st.success("🌱 **Enrichir**")
        st.write("Ajoute une nouvelle plante avec ses photos.")
        # Le bouton déclenche la fonction 'aller_a_ajout'
        st.button("Ajouter une fiche ➕", on_click=aller_a_ajout, use_container_width=True)

    # Petit résumé en bas
    st.divider()
    st.metric(label="Plantes dans ta collection", value=len(df))

# --- PAGE 1 : AJOUTER UNE PLANTE ---
elif menu == "Ajouter une plante":

    st.header("Ajouter une nouvelle fiche")
    
    with st.form("ajout_plante"):
        nom = st.text_input("Nom Vernaculaire (ex: Chêne rouvre)")
        genre = st.text_input("Genre (ex: Quercus)")
        espece = st.text_input("Espèce (ex: robur)")
        famille = st.text_input("Famille (ex: Fagaceae)")
        
        # MODIFICATION ICI : On accepte plusieurs fichiers
        photos = st.file_uploader("Photos (Feuille, Port, Ecorce...)", 
                                  type=["jpg", "png", "jpeg"], 
                                  accept_multiple_files=True)
        
        submit = st.form_submit_button("Enregistrer la plante")
        
        if submit:
            if nom and genre and photos:
                liste_chemins = []
                
                # On boucle sur toutes les photos envoyées
                for photo in photos:
                    # On force le slash / pour la compatibilité Windows/Web
                    photo_path = f"{IMG_FOLDER}/{photo.name}"
                    
                    # Sauvegarde physique
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())
                    
                    liste_chemins.append(photo_path)
                
                # On joint les chemins avec un point-virgule
                images_string = ";".join(liste_chemins)
                
                # Ajouter au tableau
                new_data = pd.DataFrame({
                    "Vernaculaire": [nom],
                    "Genre": [genre],
                    "Espece": [espece],
                    "Famille": [famille],
                    "Image": [images_string] # On stocke la liste sous forme de texte
                })
                df = pd.concat([df, new_data], ignore_index=True)
                sauvegarder_donnees(df)
                st.success(f"La plante {nom} a été ajoutée avec {len(photos)} photos !")
            else:
                st.error("Il manque des infos ou des photos !")

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
        
        # Récupérer la chaîne des images (ex: "img1.jpg;img2.jpg")
        raw_images = str(plante_mystere["Image"])
        
        # On coupe la chaîne au niveau des points-virgules pour faire une liste
        if ";" in raw_images:
            liste_images = raw_images.split(";")
        else:
            liste_images = [raw_images] # Cas où il n'y a qu'une seule image
            
        # On choisit UNE image au hasard parmi celles de la plante
        image_a_afficher = random.choice(liste_images)

        # Afficher l'image
        try:
            st.image(image_a_afficher, width=400)
        except:
            st.error(f"Image introuvable : {image_a_afficher}")

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



