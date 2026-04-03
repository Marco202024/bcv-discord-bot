import requests
from bs4 import BeautifulSoup
import os
import re

# ==========================================
# 1. MODELO (Gestión de Datos y Fecha)
# ==========================================
class BCVModel:
    @staticmethod
    def obtener_html():
        url = "https://www.bcv.org.ve/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, verify=False)
        return BeautifulSoup(response.content, 'html.parser')

    @staticmethod
    def procesar_precio(texto_sucio):
        try:
            limpio = re.sub(r'[^0-9,.]', '', texto_sucio)
            if ',' in limpio and '.' in limpio:
                limpio = limpio.replace('.', '')
            valor_punto = limpio.replace(',', '.')
            return float(valor_punto)
        except:
            return 0.0

    @staticmethod
    def leer_ultima_fecha():
        """Lee la fecha de la última publicación exitosa."""
        try:
            with open('ultima_fecha.txt', 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            return ""

    @staticmethod
    def guardar_fecha(nueva_fecha):
        """Guarda la fecha actual como la última procesada."""
        with open('ultima_fecha.txt', 'w') as file:
            file.write(nueva_fecha)

# ==========================================
# 2. VISTA (Formato de Mensaje)
# ==========================================
class DiscordView:
    @staticmethod
    def formatear_moneda(numero):
        return "{:,.2f}".format(numero).replace('.', 'X').replace(',', '.').replace('X', ',')

    @classmethod
    def crear_mensaje_embed(cls, dolar, euro, fecha, color):
        return {
            "embeds": [{
                "title": "🏦 Reporte Oficial BCV",
                "description": f"📅 **Fecha Valor:** {fecha}",
                "color": color,
                "fields": [
                    {"name": "💵 Dólar (USD)", "value": f"**{cls.formatear_moneda(dolar)} Bs.**", "inline": True},
                    {"name": "💶 Euro (EUR)", "value": f"**{cls.formatear_moneda(euro)} Bs.**", "inline": True}
                ],
                "footer": {"text": "Validación por fecha detectada"}
            }]
        }

# ==========================================
# 3. CONTROLADOR (Lógica de Decisión)
# ==========================================
class BotController:
    def __init__(self):
        self.servidores = [
            {"url": os.getenv('DISCORD_WEBHOOK'), "color": 10181046},
            {"url": os.getenv('DISCORD_WEBHOOK_2'), "color": 3447003}
        ]

    def ejecutar(self):
        try:
            # 1. El Modelo obtiene los datos actuales del sitio
            soup = BCVModel.obtener_html()
            fecha_bcv = soup.find(class_="date-display-single").get_text().strip()
            
            # 2. Comparamos la fecha del sitio con nuestra "memoria"
            fecha_anterior = BCVModel.leer_ultima_fecha()

            if fecha_bcv == fecha_anterior:
                print(f"La fecha '{fecha_bcv}' ya fue publicada. No hay cambios.")
                return # Detenemos todo

            # 3. Si la fecha es nueva, procesamos los precios
            print(f"¡Nueva fecha detectada!: {fecha_bcv}. Publicando...")
            d_raw = soup.find(id="dolar").get_text()
            e_raw = soup.find(id="euro").get_text()
            
            dolar_valor = BCVModel.procesar_precio(d_raw)
            euro_valor = BCVModel.procesar_precio(e_raw)

            # 4. Enviamos a los servidores
            for s in self.servidores:
                if s["url"]:
                    payload = DiscordView.crear_mensaje_embed(dolar_valor, euro_valor, fecha_bcv, s["color"])
                    requests.post(s["url"], json=payload)

            # 5. El Modelo actualiza la memoria con la nueva fecha
            BCVModel.guardar_fecha(fecha_bcv)
            print("Memoria de fecha actualizada.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    bot = BotController()
    bot.ejecutar()
    
