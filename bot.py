import requests
from bs4 import BeautifulSoup
import os

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
URL_BCV = "https://www.bcv.org.ve/"

def limpiar_y_redondear(texto_valor):
    # Cambiamos la coma por punto para que Python lo entienda como número
    valor_limpio = texto_valor.replace(',', '.')
    # Convertimos a número flotante, redondeamos a 2 y volvemos a poner la coma para el mensaje
    valor_numero = float(valor_limpio)
    return f"{round(valor_numero, 2)}".replace('.', ',')

def obtener_tasas():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        response = requests.get(URL_BCV, headers=headers, verify=False)
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraemos el texto crudo
        dolar_raw = soup.find(id="dolar").get_text().strip()
        euro_raw = soup.find(id="euro").get_text().strip()
        fecha = soup.find(class_="date-display-single").get_text().strip()

        # Procesamos los decimales
        dolar = limpiar_y_redondear(dolar_raw)
        euro = limpiar_y_redondear(euro_raw)

        enviar_a_discord(dolar, euro, fecha)

    except Exception as e:
        print(f"Error al extraer datos: {e}")

def enviar_a_discord(dolar, euro, fecha):
    payload = {
        "embeds": [{
            "title": "🏦 Tasas Oficiales BCV (Redondeado)",
            "description": f"Fecha valor: **{fecha}**",
            "color": 3066993,
            "fields": [
                {"name": "💵 Dólar (USD)", "value": f"{dolar} Bs.", "inline": True},
                {"name": "💶 Euro (EUR)", "value": f"{euro} Bs.", "inline": True}
            ],
            "footer": {"text": "Automatización con redondeo a 2 decimales"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    obtener_tasas()
