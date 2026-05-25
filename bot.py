import os
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any

# ==========================================
# CONSTANTES Y CONFIGURACIÓN GLOBALES
# ==========================================
BCV_URL = "https://www.bcv.org.ve/"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
ARCHIVO_FECHA = 'ultima_fecha.txt'
TIMEOUT_REQ = 10  # Evita que el script se quede colgado en RAM si el servidor no responde


# ==========================================
# 1. MODELO (Gestión de Datos y Fecha)
# ==========================================
class BCVModel:
    @staticmethod
    def obtener_html() -> Optional[BeautifulSoup]:
        """Realiza la petición HTTP y devuelve el objeto BeautifulSoup o None si falla."""
        try:
            response = requests.get(BCV_URL, headers=HEADERS, verify=False, timeout=TIMEOUT_REQ)
            response.raise_for_status()  # Lanza excepción si el status HTTP es de error (ej. 500, 404)
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error de conexión al BCV: {e}")
            return None

    @staticmethod
    def procesar_precio(texto_sucio: str) -> float:
        """Limpia la cadena del precio y la convierte a flotante."""
        try:
            limpio = re.sub(r'[^0-9,.]', '', texto_sucio)
            if ',' in limpio and '.' in limpio:
                limpio = limpio.replace('.', '')
            valor_punto = limpio.replace(',', '.')
            return float(valor_punto)
        except (ValueError, TypeError): 
            return 0.0

    @staticmethod
    def leer_ultima_fecha() -> str:
        """Lee la fecha de la última publicación exitosa."""
        try:
            with open(ARCHIVO_FECHA, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except FileNotFoundError:
            return ""

    @staticmethod
    def guardar_fecha(nueva_fecha: str) -> None:
        """Guarda la fecha actual como la última procesada."""
        with open(ARCHIVO_FECHA, 'w', encoding='utf-8') as file:
            file.write(nueva_fecha)


# ==========================================
# 2. VISTA (Formato de Mensaje)
# ==========================================
class DiscordView:
    @staticmethod
    def formatear_moneda(numero: float) -> str:
        return f"{numero:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')

    @classmethod
    def crear_mensaje_embed(cls, dolar: float, euro: float, fecha: str, color: int) -> Dict[str, Any]:
        return {
            "embeds": [{
                "title": "🏦 Reporte Oficial BCV",
                "description": f"📅 **Fecha Valor:** {fecha}",
                "color": color,
                "fields": [
                    {"name": "💵 Dólar (USD)", "value": f"**{cls.formatear_moneda(dolar)} Bs.**", "inline": True},
                    {"name": "💶 Euro (EUR)", "value": f"**{cls.formatear_moneda(euro)} Bs.**", "inline": True}
                ],
                "footer": {"text": "Datos extraídos de bcv.org.ve"}
            }]
        }


# ==========================================
# 3. CONTROLADOR (Lógica de Decisión)
# ==========================================
class BotController:
    def __init__(self) -> None:
        self.servidores: List[Dict[str, Any]] = [
            {"url": os.getenv('DISCORD_WEBHOOK'), "color": 10181046},
            {"url": os.getenv('DISCORD_WEBHOOK_2'), "color": 3447003}
        ]

    def ejecutar(self) -> None:
        # 1. El Modelo obtiene los datos actuales del sitio
        soup = BCVModel.obtener_html()

        if not soup:
            print("No se pudo procesar la página web del BCV.")
            return

        try:
            fecha_elemento = soup.find(class_="date-display-single")
            if not fecha_elemento:
                print("No se encontró la clase de la fecha. ¿Cambió el diseño web?")
                return

            fecha_bcv = fecha_elemento.get_text().strip()

            # 2. Comparamos la fecha del sitio con nuestra "memoria"
            fecha_anterior = BCVModel.leer_ultima_fecha()

            if fecha_bcv == fecha_anterior:
                print(f"La fecha '{fecha_bcv}' ya fue publicada. No hay cambios.")
                return

                # 3. Si la fecha es nueva, procesamos los precios
            print(f"¡Nueva fecha detectada!: {fecha_bcv}. Publicando...")

            d_raw = soup.find(id="dolar").get_text() if soup.find(id="dolar") else "0"
            e_raw = soup.find(id="euro").get_text() if soup.find(id="euro") else "0"

            dolar_valor = BCVModel.procesar_precio(d_raw)
            euro_valor = BCVModel.procesar_precio(e_raw)

            # 4. Enviamos a los servidores
            for s in self.servidores:
                if s["url"]:
                    try:
                        payload = DiscordView.crear_mensaje_embed(dolar_valor, euro_valor, fecha_bcv, s["color"])
                        requests.post(s["url"], json=payload, timeout=5)
                    except requests.RequestException as e:
                        print(f"Ocurrió un error enviando datos al webhook: {e}")

            # 5. El Modelo actualiza la memoria con la nueva fecha
            BCVModel.guardar_fecha(fecha_bcv)
            print("Memoria de fecha actualizada exitosamente.")

        except AttributeError as e:
            print(f"Error de estructura HTML (falta un atributo esperado): {e}")
        except Exception as e:
            print(f"Error inesperado en la ejecución del controlador: {e}")


if __name__ == "__main__":
    bot = BotController()
    bot.ejecutar()
