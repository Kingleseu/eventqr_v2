import os
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger
from django.core.files import File

import os
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger
from django.core.files import File
import os, uuid
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger
from django.core.files import File
from django.conf import settings

from PIL import Image, ImageDraw, ImageFont
import uuid, os
from PyPDF2 import PdfMerger
from django.core.files import File
from PIL import Image, ImageDraw, ImageFont
import uuid, os
from PyPDF2 import PdfMerger
from django.core.files import File

def generer_billet_pdf(participant, files):
    # 1. Charger fond
    bg = os.path.join(settings.BASE_DIR, 'retreat/static/retreat/badges/billetJCMP 2.jpg')
    img = Image.open(bg).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 2. Polices
    font_path = os.path.join(settings.BASE_DIR, 'retreat/static/retreat/fonts/DejaVuSans-Bold.ttf')
    font_big = ImageFont.truetype(font_path, 38)
    font_serial = ImageFont.truetype(font_path, 20)  # taille réduite

    # 3. Génération du numéro de série
    serial = uuid.uuid4().hex[:8].upper()
    if hasattr(participant, 'num_serie'):
        participant.num_serie = serial
        participant.save(update_fields=['num_serie'])

    # 4. QR Code (petit) et position
    qr_size = 135
    qr_x = 1307
    qr_y = 129
    if participant.qr_code and os.path.exists(participant.qr_code.path):
        qr_img = (Image.open(participant.qr_code.path)
                       .convert("RGBA")
                       .resize((qr_size, qr_size)))
        img.paste(qr_img, (qr_x, qr_y), qr_img)

    # 5. Numéro de série uniquement (pas de label)
    serie_num_x = qr_x + 10
    serie_num_y = qr_y + qr_size + 147  # ajustable
    draw.text((serie_num_x, serie_num_y), serial, font=font_serial, fill="black")

    # 6. Nom vertical à droite (inchangé)
        # 6. Nom vertical à droite (ajustements)
    full_name = f"{participant.prenom} {participant.nom}".upper()

    # Agrandis légèrement la police si besoin :
    font_big = ImageFont.truetype(font_path, 42)

    # Mesure du texte
    bbox = draw.textbbox((0, 0), full_name, font=font_big)
    txt_w, txt_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Crée une image transparente pour le texte
    txt_img = Image.new("RGBA", (txt_w, txt_h), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    txt_draw.text((0, 0), full_name, font=font_big, fill="black")

    # Tire-bouchon (rotation 90°)
    txt_r = txt_img.rotate(90, expand=True)

    # Coordonnées ajustées :
    x_vert = img.width - txt_r.width - 10  # décale un peu vers le centre
    y_vert = (img.height - txt_r.height) // 2  # centre verticalement

    # Colle le texte
    img.paste(txt_r, (x_vert, y_vert), txt_r)


    # 7. Sauvegarde / fusion PDF
    temp = os.path.join(settings.MEDIA_ROOT, 'temp')
    os.makedirs(temp, exist_ok=True)
    img_png = os.path.join(temp, f'billet_{participant.id}.png')
    img_pdf = os.path.join(temp, f'billet_{participant.id}.pdf')
    final_pdf = os.path.join(temp, f'billet_{participant.id}_final.pdf')

    img.convert("RGB").save(img_png, "PNG")
    Image.open(img_png).convert("RGB").save(img_pdf, "PDF", resolution=150)

    merger = PdfMerger()
    merger.append(img_pdf)
    for f in files or []:
        if f and os.path.exists(f):
            merger.append(f)
    merger.write(final_pdf)
    merger.close()

    with open(final_pdf, 'rb') as fp:
        participant.billet_pdf.save(f"billet_{participant.id}.pdf", File(fp), save=True)

    for p in (img_png, img_pdf, final_pdf):
        if os.path.exists(p): os.remove(p)

    return participant.billet_pdf.path








from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings
import uuid

def generer_billet_image(participant):
    # 1. Ouvre l’image de fond
    bg_path = os.path.join(
        settings.BASE_DIR, 'retreat', 'static', 'retreat', 'badges', 'billetJCMP2.jpg'
    )
    image = Image.open(bg_path).convert("RGBA")
    draw = ImageDraw.Draw(image)

    # 2. Prépare les polices
    font_path = os.path.join(
        settings.BASE_DIR, 'retreat', 'static', 'retreat', 'fonts', 'DejaVuSans-Bold.ttf'
    )
    font_name = ImageFont.truetype(font_path, 48)
    font_serial = ImageFont.truetype(font_path, 36)

    # 3. Génère un numéro de série unique (24h + ID choisi ici)
    serial = participant.id * 100000 + int(uuid.uuid4().int % 100000)

    # 4. Place le QR code dans le petit carré à droite
    if getattr(participant, "qr_code", None) and participant.qr_code and os.path.exists(participant.qr_code.path):
        qr_img = Image.open(participant.qr_code.path).convert("RGBA")
        qr_img = qr_img.resize((260, 260))
        qr_x, qr_y = 1700, 180  # ajuster pour le positionnement
        image.paste(qr_img, (qr_x, qr_y), qr_img)

    # 5. Place le nom verticalement dans sa zone
    full_name = f"{participant.prenom} {participant.nom}".upper()
    # Zone réservée
    x0, y0, area_w, area_h = 1450, 200, 200, 600
    # Calcule la taille maximale et ajuste la taille de police si besoin
    w, h = draw.textsize(full_name, font=font_name)
    if h > area_h:
        font_name = ImageFont.truetype(font_path, int(48 * area_h / h))
        w, h = draw.textsize(full_name, font=font_name)
    # Dessine une rotation de 90° (sur la gauche)
    txt_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(txt_img).text((0, 0), full_name, font=font_name, fill="black")
    txt_img = txt_img.rotate(90, expand=1)
    nx = x0
    ny = y0 + (area_h - txt_img.height) // 2
    image.paste(txt_img, (nx, ny), txt_img)

    # 6. Place le numéro de série sous le QR dans la zone blanche
    serial_text = f"N° {serial}"
    sx = qr_x
    sy = qr_y + 280
    draw.text((sx, sy), serial_text, font=font_serial, fill="black")

    # 7. Sauvegarde dans /media/temp
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    path = os.path.join(temp_dir, f'billet_{participant.id}_serial.png')
    image.convert("RGB").save(path, "PNG")

    return path


from cryptography.fernet import Fernet
from django.conf import settings

def encrypt_qr_data(plain_text: str) -> str:
    f = Fernet(settings.FERNET_SECRET_KEY.encode())
    token = f.encrypt(plain_text.encode())
    return token.decode()

def decrypt_qr_data(token_str: str) -> str:
    f = Fernet(settings.FERNET_SECRET_KEY.encode())
    return f.decrypt(token_str.encode()).decode()
