import requests
import json
import os

ig_id_user = os.environ["IG_USER_ID"]
horoscope_token_ll = os.environ["IG_TOKEN_LL"]

def get_description(sign):
    descritpions = f"""🔮✨ Horoscope du jour pour le signe {sign} ✨🔮

Que penses-tu de ton horoscope du jour ? Dis le nous en commentaire ! 💬

Découvre ce que les étoiles ont à te révéler aujourd'hui, {sign} ! 🌟 Plonge dans l'univers mystérieux de l'astrologie et laisse toi guider par les prédictions célestes.

✨ Quelles aventures passionnantes te réservent les astres dans les domaines de l'amour, de l'argent et du travail, de la santé et de l'humeur ? Laisse la magie de l'horoscope illuminer ta journée et t'inspirer vers de nouveaux horizons !
•
•
•
•
•
•
•
•
•
•
•
#Horoscope #HoroscopeDuJour #DailyHoroscope #{sign} #Astrologie #Signe #Signes #Destinée #Zodiaque #Etoiles #Spiritualité #Constellations #AstrologieQuotidienne #Cosmos #Harmonie #Amour #Argent #Travail #Santé #Humeur #Soleil #Lune #Cosmos #Energie #Avenir #InfluenceLunaire #Constellation #Guidance #Prediction
"""
    
    return descritpions

def elements_creation(sign):
    url = "https://graph.facebook.com/v19.0/" + ig_id_user + "/media"
    id_element = []

    
    files = os.listdir(os.path.join("posts_api", sign))

    for file in files:
        image_url = "http://194.164.63.3/sunaloom?post=" + os.path.join("posts_api", sign, file)
        
        params = {
            "is_carousel_item": "true",
            "image_url": image_url,
            "access_token": horoscope_token_ll
        }

        res = requests.post(url, params=params)

        if res.status_code == 200:
            print("[INFO] Element {} created".format(sign))
            id_element.append(res.json()["id"])
        else:
            print('[ERROR] Element not created')
            return []

    return id_element

def conteneur_creation(id_element : list, description : str):

    url = "https://graph.facebook.com/v19.0/" + ig_id_user + "/media"
    params = {
        "caption": description,
        "media_type": "CAROUSEL",
        "children": json.dumps(id_element),
        "access_token": horoscope_token_ll
    }

    id_conteneur = ""

    res = requests.post(url, params=params)

    if res.status_code == 200:
        print("[INFO] -- Conteneur created")
        id_conteneur = res.json()["id"]
    else:
        print("[ERROR] -- Conteneur error")

    return id_conteneur

def publish_id(id_conteneur : str):

    url = "https://graph.facebook.com/v19.0/" + ig_id_user + "/media_publish"
    params = {
        "creation_id": id_conteneur,
        "access_token": horoscope_token_ll
    }

    id_post = ""

    res = requests.post(url, params=params)

    if res.status_code == 200:
        print("[INFO ]---- Published")
        id_post = res.json()["id"]
    else:
        print("[ERROR] ---- Not published")

    return id_post

def publish():

    signs = ["belier", "taureau", "gemeaux", "cancer", "lion", "vierge", "balance", "scorpion", "sagittaire", "capricorne", "verseau", "poissons"]

    
    for sign in signs:
        
        description = get_description(sign)
        
        ids_element  = elements_creation(signs)

        if not ids_element:
            return

        id_conteneur = conteneur_creation(ids_element, description)

        if id_conteneur == 0:
            return

        publish_id(id_conteneur)