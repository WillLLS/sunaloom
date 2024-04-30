from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from textwrap import wrap 
from bs4 import BeautifulSoup

import os
from tqdm import tqdm
import json
import requests
import shutil

def is_in_the_box(res, box=(160, 220, 920, 900)):
    if res[0] >= box[0] and res[1] >= box[1] and res[2] <= box[2] and res[3] <= box[3]:
        return True
    return False

def is_more_than_limit_horizontal(res, box=(160, 220, 920, 900)):
    if res[2] > box[2] or res[0] < box[0]:
        return True
    return False

def is_more_than_limit_vertical(res, box=(160, 220, 920, 900)):
    if res[3] > box[3] or res[1] < box[1]:
        return True
    return False

def is_in_horizontal_limit(res, box_min, box_max):
    condition_0 = box_max[0] >= res[0] >= box_min[0]
    condition_1 = box_max[2] >= res[2] >= box_min[2]
    
    if condition_0 and condition_1:
        return True
    return False

def process_text(background, content, anchor_y_init=200, box_coord = (130, 200, 950, 950), bbox_horizontal = (230, 200, 850, 950), anchor_type="ms", width_wrap=10, font_size=150):
    
    width = background.width

    
    draw = ImageDraw.Draw(background)
    
    #draw.rectangle(box_coord, outline="red", width=5)
    #draw.rectangle(bbox_horizontal, outline="red", fill="blue", width=5)
    
    content = content.replace(" ", " ")
    res3 = wrap(content, width=width_wrap)
    mutli_line = "\n".join(res3)
    
    font = ImageFont.truetype("SimplyMono-Bold.ttf", font_size)

    current_box = draw.multiline_textbbox((width/ 2,anchor_y_init), mutli_line, font=font, anchor=anchor_type, align="center")
    height_box = box_coord[3] - box_coord[1]
    height_current_box = current_box[3] - current_box[1]
    
    while (not is_in_the_box(current_box, box_coord)):
    
        if not is_in_the_box(current_box, box_coord):
            #print("Updating font_size")
            font_size -= 1
            font = ImageFont.truetype("SimplyMono-Bold.ttf", font_size)
            height_current_box = current_box[3] - current_box[1]
        
            anchor_y = anchor_y_init + ((height_box - height_current_box) / 2)
            current_box = draw.multiline_textbbox((width/ 2,anchor_y), mutli_line, font=font, anchor=anchor_type, align="center")
        
        if not is_in_horizontal_limit(current_box, bbox_horizontal, box_coord) and not is_more_than_limit_horizontal(current_box, box_coord):
            #print("Updating width_wrap")
            width_wrap += 1
            res3 = wrap(content, width=width_wrap)
            mutli_line = "\n".join(res3)
            font = ImageFont.truetype("SimplyMono-Bold.ttf", font_size)
            
            height_current_box = current_box[3] - current_box[1]
        
            anchor_y = anchor_y_init + ((height_box - height_current_box) / 2)
            current_box = draw.multiline_textbbox((width/ 2,anchor_y), mutli_line, font=font, anchor=anchor_type, align="center")
        
    anchor_y = anchor_y_init + ((height_box - height_current_box) / 2)
    
    current_box = draw.multiline_textbbox((width/ 2, anchor_y), mutli_line, font=font, anchor=anchor_type, align="center")
    
    return background, current_box, mutli_line, font_size, anchor_y

def add_delta(bbox, delta):
    box =  (bbox[0] - delta, bbox[1] - delta, bbox[2] + delta, bbox[3] + delta)
        
    return tuple(map(lambda x: int(x), box))
    
def draw_rectangle(background, text_box, delta = 50, color="white", fill=(18, 9, 22)):
    
    bbox = add_delta(text_box, delta)
    
    draw = ImageDraw.Draw(background)
    
    draw.rounded_rectangle(bbox, radius=40, width=5, outline=color, fill=fill)
    
    return background

def blur_rectangle(background, text_bbox, template,  delta = 50):
    import numpy as np
    
    
    def remove_high_pixel(image, threshold=50):
        
        image = np.asarray(image).copy()
                
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                if image[i, j] > threshold:
                    image[i, j] = threshold
        
        return Image.fromarray(image)
    
    def slice_histogram(image):
        
        def get_min(hist):
    
            for i in range(len(hist)):
                if hist[i] != 0:
                    return i
                
        delta = get_min(image.histogram())
        image = np.asarray(image).copy()
        
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                image[i, j] = image[i, j] - delta
                
        return Image.fromarray(image)
            
        
    # Update the bbox with a delta
    bbox = add_delta(text_bbox)
    
    # Cropping
    back_cropped = template.crop(bbox)
    back_blur = back_cropped.filter(ImageFilter.GaussianBlur(radius=150))

    back_blur = back_blur.convert("L")
    #back_blur = slice_histogram(back_blur)
    
    # Conversion for pasting
    back_blur = back_blur.convert("RGBA")
    background = background.convert("RGBA")
     
    # Pasting
    #background.paste(back_blur, (bbox[0], bbox[1]), back_blur)
    
    draw = ImageDraw.Draw(background, "RGBA")
    
    #draw.rounded_rectangle(bbox, fill=(255, 255, 255, 150))

    
    draw.rounded_rectangle(bbox, radius=40, width=5, outline="white", fill=(18, 9, 22))
    
    
    return background, bbox

def draw_text(background, content, text_bbox, font_size, anchor_y, anchor_type="ms", color="white"):
    
    
    font = ImageFont.truetype("SimplyMono-Bold.ttf", font_size)
     
    draw = ImageDraw.Draw(background)
    
    width = background.width
    
    draw.multiline_text((width/2,anchor_y), content, fill=color, font=font, anchor=anchor_type, align="center")
    
    return background

def generate_posts():

    sections = os.listdir("templates")

    for section in tqdm(sections, desc="Sections", unit="section", position=0):
        # Load horoscope
        with open(os.path.join("horoscopes", f"{section}.json"), "r", encoding="utf-8") as f:
            horoscope = json.load(f)
            
        signs = list(horoscope.keys())

        # Pour chaque signe on récupère le template, on le charge, on écrit le texte, on blur et encadre et on sauvegarde
        for sign in tqdm(signs, desc="Signs", unit="sign", position=1, leave=False):

            path_template = os.path.join("templates", section, f"{sign}.png")
            template = Image.open(path_template)
            
            anchor_y_init = 200
            box_coord = (100, anchor_y_init, 924, 924)
            bbox_horizontal = (box_coord[0]+100, anchor_y_init, box_coord[2]-100, box_coord[3]) # Bbox min
            
            anchor_type = "ma" #"ma"
            
            width_wrap  = 10
            font_size   = 150
    

            background, text_bbox, content, font_size, anchor_y = process_text(template, horoscope[sign], anchor_y_init, box_coord, bbox_horizontal, anchor_type, width_wrap, font_size)

            background = draw_rectangle(background, text_bbox, 50)
            background = draw_text(background, content, text_bbox, font_size, anchor_y, anchor_type=anchor_type)

            path_save = os.path.join("posts", section)

            if not os.path.exists(path_save):
                os.mkdir(path_save)

            path_save_post = os.path.join(path_save, f"{sign}.jpg")
            background = background.convert("RGB")
            background.save(path_save_post)

def generate_stories():
    
    signs = os.listdir("templates_story")
    
    for sign in tqdm(signs, desc="Signs", unit="sign", position=1, leave=False):
        
        sign = sign.split(".")[0]
    
        with open(os.path.join("horoscopes", "conseil.json"), "r", encoding="utf-8") as f:
            horoscope = json.load(f)

        path_template = os.path.join("templates_story", sign + ".png")
        template = Image.open(path_template)

        content = horoscope[sign]
        content = content.replace(" ", " ")
        
        anchor_y_init = 650
        box_coord = (100, 650, 980, 1500)
        bbox_horizontal = (200, 650, 880, 1500) # Bbox min
        
        anchor_type = "ma" #"ma"
        
        width_wrap  = 10
        font_size   = 150
        background, text_bbox, content, font_size, anchor_y = process_text(template, content, anchor_y_init=anchor_y_init, box_coord=box_coord, bbox_horizontal=bbox_horizontal, anchor_type=anchor_type, width_wrap=width_wrap, font_size=font_size)
        background = draw_rectangle(background, text_bbox, 50, "black", "white")
        
        background = draw_text(background, content, text_bbox, font_size, anchor_y, anchor_type=anchor_type, color="black")

        path_save = os.path.join("stories")
    
        if not os.path.exists(path_save):
            os.mkdir(path_save)

        path_save_post = os.path.join(path_save, sign + ".jpg")
        background = background.convert("RGB")
        background.save(path_save_post)

def scrapp_horoscopes():
    
    def write_horoscope(sign, section, content):
    
        try:
            with open(f"horoscopes/{section}.json", "r", encoding="utf-8") as f:
                horoscopes = json.load(f)
        except:
            horoscopes = {}
        
        horoscopes[sign] = content
        
        with open(f"horoscopes/{section}.json", "w", encoding="utf-8") as f:
            json.dump(horoscopes, f, indent=4)
            
    with open("cookies_20minutes_fr.json", "r", encoding="utf-8") as f: 
        cookies = json.load(f)
        
    session = requests.Session()
    session.cookies.update(cookies)
    
    signs = ["belier", "taureau", "gemeaux", "cancer", "lion", "vierge", "balance", "scorpion", "sagittaire", "capricorne", "verseau", "poissons"]
    
    
    for sign in signs:
        url = f"https://www.20minutes.fr/horoscope/horoscope-{sign}"

        response = session.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Sélectionner tous les éléments correspondant au sélecteur CSS
        amour, argent_et_travail, sante, humeur = soup.select('div[layout="desktop"] > ul > li')
        
        write_horoscope(sign, "amour", amour.select_one("p").text)
        write_horoscope(sign, "argent_et_travail", argent_et_travail.select_one("p").text)
        write_horoscope(sign, "sante", sante.select_one("p").text)
        write_horoscope(sign, "humeur", humeur.select_one("p").text)
        
        conseil = soup.select_one("div[layout='desktop'] > div > div > div > p")
        write_horoscope(sign, "conseil", conseil.text)

def move_post_api():
    
    sections = os.listdir("posts")
    
    
    for section in tqdm(sections):
        posts = os.listdir(os.path.join("posts", section))
        
        for post in tqdm(posts):
            path_post = os.path.join("posts", section, post)
            
            
            path_src = os.path.join("posts", section, post)
            path_dst = os.path.join("posts_api", post.split(".")[0])
            
            if not os.path.exists(path_dst):
                os.mkdir(path_dst)
                
            path_dst = os.path.join(path_dst, section + "-" + post)
            
            shutil.copy(path_src, path_dst)   
    
    

if __name__ == "__main__":
    #scrapp_horoscopes()
    #generate_posts()
    move_post_api()