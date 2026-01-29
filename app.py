import streamlit as st
import pandas as pd
import os
import random
import time  

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

# --- GESTION DE LA NAVIGATION (SESSION STATE) ---

# 1. On initialise la page par défaut si elle n'existe pas
if 'navigation' not in st.session_state:
    st.session_state['navigation'] = 'Accueil'

# 2. Fonctions pour changer de page via les boutons de l'accueil
def aller_au_quiz():
    st.session_state['navigation'] = 'Mode Quiz'

def aller_a_ajout():
    st.session_state['navigation'] = 'Ajouter une plante'

# --- INTERFACE PRINCIPALE ---

# Le menu latéral est connecté à la variable 'navigation'
menu = st.sidebar.radio(
    "Menu", 
    ["Accueil", "Ajouter une plante", "Mode Quiz", "Ma Collection"],
    key='navigation'
)

df = charger_donnees()

# ==========================================
# PAGE 0 : ACCUEIL
# ==========================================
if menu == "Accueil":
    st.title("🌿 Mon Quiz Botanique")
    st.write("### Bienvenue dans ton outil de révision !")
    st.write("C'est l'heure de pratiquer. Que veux-tu faire ?")
    
    st.divider()
    
    # On crée deux colonnes pour aligner les boutons
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("🎓 **S'entraîner**")
        st.write("Teste tes connaissances sur les plantes enregistrées.")
        # Le bouton déclenche la fonction 'aller_au_quiz'
        st.button("Lancer le Quiz ➡️", on_click=aller_au_quiz, use_container_width=True)

    with col2:
        st.success("🌱 **Enrichir**")
        st.write("Ajoute une nouvelle plante avec ses photos.")
        # Le bouton déclenche la fonction 'aller_a_ajout'
        st.button("Ajouter une fiche ➕", on_click=aller_a_ajout, use_container_width=True)

    st.divider()
    # Petit résumé en bas
    st.metric(label="Plantes dans ta collection", value=len(df))


# ==========================================
# PAGE 1 : AJOUTER UNE PLANTE
# ==========================================
elif menu == "Ajouter une plante":
    st.header("Ajouter une nouvelle fiche")
    
    with st.form("ajout_plante"):
        col_a, col_b = st.columns(2)
        with col_a:
            nom = st.text_input("Nom Vernaculaire (ex: Chêne rouvre)")
            famille = st.text_input("Famille (ex: Fagaceae)")
        with col_b:
            genre = st.text_input("Genre (ex: Quercus)")
            espece = st.text_input("Espèce (ex: robur)")
        
        # Upload multiple
        photos = st.file_uploader("Photos (Feuille, Port, Ecorce...)", 
                                  type=["jpg", "png", "jpeg"], 
                                  accept_multiple_files=True)
        
        submit = st.form_submit_button("Enregistrer la plante")
        
        if submit:
            if nom and genre and photos:
                liste_chemins = []
                
                # On boucle sur toutes les photos envoyées
                for i, photo in enumerate(photos):
                    # 1. Récupérer l'extension (.jpg)
                    extension = os.path.splitext(photo.name)[1]
                    
                    # 2. Créer un nom propre : Genre_Espece_Index_Timestamp.jpg
                    # Le timestamp évite les doublons si tu ajoutes la même plante plus tard
                    nom_fichier_propre = f"{genre}_{espece}_{i}_{int(time.time())}{extension}"
                    
                    # 3. Nettoyage (pas d'espaces)
                    nom_fichier_propre = nom_fichier_propre.replace(" ", "_")
                    
                    # 4. Chemin final (avec slash / pour compatibilité)
                    photo_path = f"{IMG_FOLDER}/{nom_fichier_propre}"
                    
                    # Sauvegarde physique
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())
                    
                    liste_chemins.append(photo_path)
                
                # On joint les chemins avec un point-virgule pour le CSV
                images_string = ";".join(liste_chemins)
                
                # Ajouter au tableau
                new_data = pd.DataFrame({
                    "Vernaculaire": [nom],
                    "Genre": [genre],
                    "Espece": [espece],
                    "Famille": [famille],
                    "Image": [images_string]
                })
                df = pd.concat([df, new_data], ignore_index=True)
                sauvegarder_donnees(df)
                st.success(f"✅ La plante {nom} a été ajoutée avec {len(photos)} photos !")
            else:
                st.error("⚠️ Il manque des infos (Nom, Genre ou Photos) !")


# ==========================================
# PAGE 2 : MODE QUIZ
# ==========================================
elif menu == "Mode Quiz":
    st.header("🔎 Reconnaissance")
    
    if len(df) < 4:
        st.warning("⚠️ Il faut au moins 4 plantes dans la base pour lancer un Quiz QCM !")
        st.info("Va dans l'onglet 'Ajouter une plante' pour commencer ta collection.")
    else:
        # Initialiser une question si elle n'existe pas encore
        if 'bon_reponse' not in st.session_state:
            # Choisir une plante au hasard
            ligne_plante = df.sample(1).iloc[0]
            st.session_state['bon_reponse'] = ligne_plante
            
            # Choisir 3 mauvaises réponses (distracteurs)
            distracteurs = df[df.index != ligne_plante.name].sample(3)
            
            # Mélanger les choix
            choix = [ligne_plante] + [d for _, d in distracteurs.iterrows()]
            random.shuffle(choix)
            st.session_state['choix'] = choix
            st.session_state['repondu'] = False

        # Afficher la question
        plante_mystere = st.session_state['bon_reponse']
        
        # --- GESTION DE L'IMAGE HASARDEUSE ---
        raw_images = str(plante_mystere["Image"])
        # On sépare les images s'il y en a plusieurs (séparateur ;)
        if ";" in raw_images:
            liste_images = raw_images.split(";")
        else:
            liste_images = [raw_images]
            
        # On choisit UNE image au hasard parmi celles de la plante pour ce tour
        # On utilise une "clé" dans session_state pour que l'image ne change pas quand on clique sur un bouton
        if 'image_courante' not in st.session_state:
             st.session_state['image_courante'] = random.choice(liste_images)
        
        # Affichage
        try:
            st.image(st.session_state['image_courante'], width=400)
        except:
            st.error(f"Image introuvable : {st.session_state['image_courante']}")

        st.write("### Quel est le nom latin de cette plante ?")

        # Afficher les boutons de réponse en grille (2x2)
        col1, col2 = st.columns(2)
        for i, choix in enumerate(st.session_state['choix']):
            nom_complet = f"{choix['Genre']} {choix['Espece']}"
            
            # On place les boutons : pairs à gauche, impairs à droite
            zone = col1 if i % 2 == 0 else col2
            
            # Si on clique sur un bouton...
            if zone.button(nom_complet, key=i, use_container_width=True):
                st.session_state['repondu'] = True
                
                # Vérification
                if choix['Vernaculaire'] == plante_mystere['Vernaculaire']:
                    st.balloons() # Petite animation sympa
                    st.success(f"✅ BRAVO ! C'est bien *{plante_mystere['Genre']} {plante_mystere['Espece']}* ({plante_mystere['Vernaculaire']})")
                    st.info(f"Famille : {plante_mystere['Famille']}")
                else:
                    st.error(f"❌ Raté... C'était *{plante_mystere['Genre']} {plante_mystere['Espece']}*")
        
        # Bouton Suivant (n'apparaît que si on a répondu)
        if st.session_state['repondu']:
            st.write("---")
            if st.button("Question Suivante ➡️"):
                # On efface les variables de session pour forcer une nouvelle question
                del st.session_state['bon_reponse']
                del st.session_state['image_courante']
                st.rerun() # On recharge la page


# ==========================================
# PAGE 3 : MA COLLECTION
# ==========================================
elif menu == "Ma Collection":
    st.header("Mon Herbier Numérique")
    st.write(f"Tu as **{len(df)}** plantes enregistrées.")
    st.dataframe(df)
