import requests
from bs4 import BeautifulSoup
import os
import re

# ==========================================
# 1. MODELO (Lógica de Datos y Extracción)
# ==========================================
class BCVModel:
    """Se encarga exclusivamente de la fuente de datos."""
    
    @staticmethod
    def obtener_html():
        url = "https://www.bcv.org.ve/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        # Obtenemos el contenido crudo del sitio
        response = requests.get(url, headers=headers, verify=False)
        return BeautifulSoup(response.content, 'html.parser')

    @staticmethod
    def procesar_precio(texto_sucio):
        """Limpia el texto y lo convierte en un número puro (float)."""
        try:
            # Quitamos todo lo que no sea número, coma o punto
            limpio = re.sub(r'[^0-9,.]', '', texto_sucio)
            # Manejamos el formato de miles (punto) y decimales (coma)
            if ',' in limpio and '.' in limpio:
                limpio = limpio.replace('.', '')
            valor_punto = limpio.replace(',', '.')
            return float(valor_punto)
        except Exception as e:
            print(f"Error al procesar valor numérico: {e}")
            return 0.0

# ==========================================
# 2. VISTA (Lógica de Formato y Apariencia)
# ==========================================
class DiscordView:
    """Se encarga de cómo se presentan los datos al usuario."""
    
    @staticmethod
    def formatear_moneda(numero):
        """Convierte un número a formato venezolano estricto de 2 decimales."""
        return "{:,.2f}".format(numero).replace('.', 'X').replace(',', '.').replace('X', ',')

    @classmethod
    def crear_mensaje_embed(cls, dolar, euro, fecha, color):
        """Construye el objeto JSON que Discord entiende."""
        return {
            "embeds": [{
                "title": "🏦 Tasas Oficiales BCV",
                "description": f"📅 Fecha valor: **{fecha}**",
                "color": color,
                "fields": [
                    {"name": "💵 Dólar (USD)", "value": f"**{cls.formatear_moneda(dolar)} Bs.**", "inline": True},
                    {"name": "💶 Euro (EUR)", "value": f"**{cls.formatear_moneda(euro)} Bs.**", "inline": True}
                ],
                "footer": {"text": "Datos extraídos de bcv.org.ve"}
            }]
        }

# ==========================================
# 3. CONTROLADOR (Lógica de Negocio y Flujo)
# ==========================================
class BotController:
    """El cerebro que coordina al Modelo y a la Vista."""
    
    def __init__(self):
        # Aquí definimos los destinos y sus preferencias estéticas
        self.servidores = [
            {"url": os.getenv('DISCORD_WEBHOOK'), "color": 10181046},   # Server 1: Morado
            {"url": os.getenv('DISCORD_WEBHOOK_2'), "color": 3447003}   # Server 2: Azul
        ]

    def ejecutar(self):
        try:
            # 1. El Controlador pide datos al Modelo
            soup = BCVModel.obtener_html()
            
            # Extraemos los datos crudos
            d_raw = soup.find(id="dolar").get_text()
            e_raw = soup.find(id="euro").get_text()
            fecha = soup.find(class_="date-display-single").get_text().strip()

            # 2. El Controlador procesa los datos (limpieza lógica)
            dolar_valor = BCVModel.procesar_precio(d_raw)
            euro_valor = BCVModel.procesar_precio(e_raw)

            # 3. El Controlador envía a la Vista y reparte a los servidores
            for s in self.servidores:
                if s["url"]:
                    payload = DiscordView.crear_mensaje_embed(
                        dolar_valor, euro_valor, fecha, s["color"]
                    )
                    requests.post(s["url"], json=payload)
                    print(f"Envío exitoso a servidor con color {s['color']}")

        except Exception as e:
            print(f"Falla crítica en el controlador: {e}")

# Punto de entrada
if __name__ == "__main__":
    bot = BotController()
    bot.ejecutar()
