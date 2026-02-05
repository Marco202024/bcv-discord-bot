import requests
from bs4 import BeautifulSoup
import os

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
URL_BCV = "https://www.bcv.org.ve/"

def limpiar_valor(texto_sucio):
    try:
        # Quitamos espacios y dejamos solo lo que parece número
        limpio = texto_sucio.strip().replace('.', '').replace(',', '.')
        # Convertimos a número, redondeamos a 2 y volvemos a poner la coma
        valor_fin = round(float(limpio), 2)
        return f"{valor_fin:.2f}".replace('.', ',')
    except:
        # Si algo falla (ej. hay letras), devolvemos el texto original sin romper el bot
        return texto_sucio

def obtener_tasas():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        # verify=False ayuda si la web del BCV tiene problemas de certificado
        response = requests.get(URL_BCV, headers=headers, verify=False)
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer los textos
        d_raw = soup.find(id="dolar").get_text()
        e_raw = soup.find(id="euro").get_text()
        fecha = soup.find(class_="date-display-single").get_text().strip()

        # Limpiar y redondear
        dolar = limpiar_valor(d_raw)
        euro = limpiar_valor(e_raw)

        enviar_a_discord(dolar, euro, fecha)

    except Exception as e:
        print(f"Error en el proceso: {e}")

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
            "footer": {"text": "Actualización automática • Redondeado a 2 decimales"}
        }]
    }
    r = requests.post(WEBHOOK_URL, json=payload)
    print(f"Status de Discord: {r.status_code}")

if __name__ == "__main__":
    obtener_tasas()
