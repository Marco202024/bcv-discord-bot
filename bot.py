import requests
from bs4 import BeautifulSoup
import os
import re

# Morado: 10181046 | Azul: 3447003 | Verde: 3066993 | Dorado: 15844367
SERVIDORES = [
    {
        "url": os.getenv('DISCORD_WEBHOOK'),
        "color": 3066993  # verde para el primer server
    },
    {
        "url": os.getenv('DISCORD_WEBHOOK_2'),
        "color": 10181046   # morado para el segundo server (puedes cambiarlo)
    }
]

URL_BCV = "https://www.bcv.org.ve/"

def limpiar_y_formatear(texto):
    try:
        solo_numeros = re.sub(r'[^0-9,.]', '', texto)
        if ',' in solo_numeros and '.' in solo_numeros:
            solo_numeros = solo_numeros.replace('.', '')
        valor_punto = solo_numeros.replace(',', '.')
        valor_final = float(valor_punto)
        return "{:,.2f}".format(valor_final).replace('.', 'X').replace(',', '.').replace('X', ',')
    except:
        return texto

def obtener_tasas():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        response = requests.get(URL_BCV, headers=headers, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')

        d_raw = soup.find(id="dolar").get_text()
        e_raw = soup.find(id="euro").get_text()
        fecha = soup.find(class_="date-display-single").get_text().strip()

        dolar = limpiar_y_formatear(d_raw)
        euro = limpiar_y_formatear(e_raw)

        # Enviamos a cada servidor con su configuración propia
        for server in SERVIDORES:
            if server["url"]:
                enviar_a_discord(server["url"], server["color"], dolar, euro, fecha)
                
    except Exception as e:
        print(f"Error general: {e}")

def enviar_a_discord(url, color, dolar, euro, fecha):
    payload = {
        "embeds": [{
            "title": "🏦 Tasas Oficiales BCV",
            "description": f"📅 Fecha valor: **{fecha}**",
            "color": color,
            "fields": [
                {"name": "💵 Dólar (USD)", "value": f"**{dolar} Bs.**", "inline": True},
                {"name": "💶 Euro (EUR)", "value": f"**{euro} Bs.**", "inline": True}
            ],
            "footer": {"text": "Datos extraídos de bcv.org.ve"}
        }]
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    obtener_tasas()
