import requests
from bs4 import BeautifulSoup
import os
import re

# Cargamos ambas URLs desde los secretos de GitHub
WEBHOOKS = [
    os.getenv('DISCORD_WEBHOOK'),
    os.getenv('DISCORD_WEBHOOK_2')
]

URL_BCV = "https://www.bcv.org.ve/"

def limpiar_y_formatear(texto):
    try:
        solo_numeros = re.sub(r'[^0-9,.]', '', texto)
        if ',' in solo_numeros and '.' in solo_numeros:
            solo_numeros = solo_numeros.replace('.', '')
        valor_punto = solo_numeros.replace(',', '.')
        valor_final = float(valor_punto)
        # Formato estricto de 2 decimales
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

        # Enviamos a cada webhook en la lista
        for url in WEBHOOKS:
            if url: # Solo intentamos si la URL existe
                enviar_a_discord(url, dolar, euro, fecha)
                
    except Exception as e:
        print(f"Error general: {e}")

def enviar_a_discord(url, dolar, euro, fecha):
    payload = {
        "embeds": [{
            "title": "🏦 Tasas Oficiales BCV",
            "description": f"📅 Fecha valor: **{fecha}**",
            "color": 3066993,
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
