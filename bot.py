import requests
from bs4 import BeautifulSoup
import os
import re

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
URL_BCV = "https://www.bcv.org.ve/"

def limpiar_y_formatear(texto):
    try:
        # 1. Extraer solo números, comas y puntos usando expresiones regulares
        solo_numeros = re.sub(r'[^0-9,.]', '', texto)
        
        # 2. Manejar el formato venezolano (Punto para miles, coma para decimales)
        # Primero quitamos el punto de miles si existe
        if ',' in solo_numeros and '.' in solo_numeros:
            solo_numeros = solo_numeros.replace('.', '')
            
        # 3. Cambiamos la coma decimal por punto para que Python pueda calcular
        valor_punto = solo_numeros.replace(',', '.')
        
        # 4. Convertimos a número y forzamos 2 decimales exactos
        valor_final = float(valor_punto)
        
        # 5. Formateamos de vuelta al estilo local: "36,50"
        return "{:,.2f}".format(valor_final).replace('.', 'X').replace(',', '.').replace('X', ',')
    except Exception as e:
        print(f"Error procesando {texto}: {e}")
        return texto

def obtener_tasas():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        response = requests.get(URL_BCV, headers=headers, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscamos los contenedores de los valores
        d_raw = soup.find(id="dolar").get_text()
        e_raw = soup.find(id="euro").get_text()
        fecha = soup.find(class_="date-display-single").get_text().strip()

        # Aplicamos la limpieza estricta
        dolar = limpiar_y_formatear(d_raw)
        euro = limpiar_y_formatear(e_raw)

        enviar_a_discord(dolar, euro, fecha)
    except Exception as e:
        print(f"Error general: {e}")

def enviar_a_discord(dolar, euro, fecha):
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
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    obtener_tasas()
