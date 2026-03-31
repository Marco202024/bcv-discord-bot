import requests
from bs4 import BeautifulSoup
import os
import re

# ==========================================
# 1. MODELO (Lógica de Datos y Memoria)
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
        except Exception as e:
            print(f"Error al procesar: {e}")
            return 0.0

    @staticmethod
    def leer_memoria():
        """Lee el último precio guardado en el archivo."""
        try:
            with open('ultimo_precio.txt', 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            return "" # Si el archivo no existe aún, devuelve vacío

    @staticmethod
    def guardar_memoria(nuevo_registro):
        """Guarda el nuevo precio para el día siguiente."""
        with open('ultimo_precio.txt', 'w') as file:
            file.write(nuevo_registro)

# ==========================================
# 2. VISTA (Lógica de Formato y Apariencia)
# ==========================================
class DiscordView:
    @staticmethod
    def formatear_moneda(numero):
        return "{:,.2f}".format(numero).replace('.', 'X').replace(',', '.').replace('X', ',')

    @classmethod
    def crear_mensaje_embed(cls, dolar, euro, fecha, color):
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
# 3. CONTROLADOR (Lógica de Condición)
# ==========================================
class BotController:
    def __init__(self):
        # colores para mostrar en los servidores, Morado: 10181046 | Azul: 3447003 | Verde: 3066993 | Dorado: 15844367
        self.servidores = [
            {"url": os.getenv('DISCORD_WEBHOOK'), "color": 10181046},
            {"url": os.getenv('DISCORD_WEBHOOK_2'), "color": 3447003}
        ]

    def ejecutar(self):
        try:
            # 1. Obtener datos actuales
            soup = BCVModel.obtener_html()
            d_raw = soup.find(id="dolar").get_text()
            e_raw = soup.find(id="euro").get_text()
            fecha = soup.find(class_="date-display-single").get_text().strip()

            dolar_valor = BCVModel.procesar_precio(d_raw)
            euro_valor = BCVModel.procesar_precio(e_raw)

            # 2. Crear una "huella" del precio actual para comparar
            registro_actual = f"{dolar_valor}-{euro_valor}-{fecha}"
            registro_anterior = BCVModel.leer_memoria()

            # 3. La Condición Mágica: ¿Son iguales?
            if registro_actual == registro_anterior:
                print("Los precios no han cambiado desde la última publicación. Abortando envío.")
                return # Detiene la ejecución aquí mismo

            # 4. Si son distintos, publicamos
            print("Nuevos precios detectados. Iniciando envíos...")
            for s in self.servidores:
                if s["url"]:
                    payload = DiscordView.crear_mensaje_embed(dolar_valor, euro_valor, fecha, s["color"])
                    requests.post(s["url"], json=payload)
                    print(f"Enviado a servidor color {s['color']}")

            # 5. Guardar la nueva huella para mañana
            BCVModel.guardar_memoria(registro_actual)
            print("Memoria actualizada exitosamente.")

        except Exception as e:
            print(f"Falla crítica: {e}")

if __name__ == "__main__":
    bot = BotController()
    bot.ejecutar()
    
