import requests
from bs4 import BeautifulSoup
import os

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
URL_BCV = "https://www.bcv.org.ve/"

def obtener_tasas():
    try:
        # El BCV a veces bloquea conexiones que no parecen navegadores
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        response = requests.get(URL_BCV, headers=headers, verify=False) # verify=False porque a veces falla su SSL
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscamos los valores en los IDs específicos de la web del BCV
        dolar = soup.find(id="dolar").get_text().strip()
        euro = soup.find(id="euro").get_text().strip()
        fecha = soup.find(class_="date-display-single").get_text().strip()

        enviar_a_discord(dolar, euro, fecha)

    except Exception as e:
        print(f"Error al extraer datos: {e}")

def enviar_a_discord(dolar, euro, fecha):
    payload = {
        "embeds": [{
            "title": "🏦 Tasas Oficiales BCV",
            "description": f"Fecha valor: **{fecha}**",
            "color": 3066993, # Color verde
            "fields": [
                {"name": "💵 Dólar (USD)", "value": f"{dolar} Bs.", "inline": True},
                {"name": "💶 Euro (EUR)", "value": f"{euro} Bs.", "inline": True}
            ],
            "footer": {"text": "Datos extraídos de bcv.org.ve"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    obtener_tasas()
    
