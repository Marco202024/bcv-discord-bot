import os
import re
import pickle
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any

# ==========================================
# CONSTANTES Y CONFIGURACIÓN GLOBALES
# ==========================================
BCV_URL = "https://www.bcv.org.ve/"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
ARCHIVO_HISTORIAL = 'historial_tasas.dat'
TIMEOUT_REQ = 10  

# ==========================================
# 1. ENTIDADES Y MODELO (Gestión de Datos)
# ==========================================

class TasaCambio:
    """Objeto que representa la entidad de datos encapsulada."""
    def __init__(self, dolar: float, euro: float, fecha: str) -> None:
        self.__dolar = dolar
        self.__euro = euro
        self.__fecha = fecha

    @property
    def dolar(self) -> float:
        return self.__dolar

    @property
    def euro(self) -> float:
        return self.__euro

    @property
    def fecha(self) -> str:
        return self.__fecha

    def __str__(self) -> str:
        return f"[{self.fecha}] USD: {self.dolar} | EUR: {self.euro}"


class ManejadorHistorial:
    """Clase encargada exclusivamente de la serialización del historial en binario."""
    def __init__(self, ruta: str) -> None:
        self.__ruta = ruta

    def cargar_historial(self) -> List[TasaCambio]:
        """Carga la lista de objetos TasaCambio desde el archivo binario."""
        try:
            with open(self.__ruta, 'rb') as archivo:
                return pickle.load(archivo)
        except (OSError, EOFError):
            print("No se encontró el historial previo o está vacío. Iniciando historial nuevo.")
            return []

    def guardar_historial(self, historial: List[TasaCambio]) -> None:
        """Sobrescribe el archivo binario con la lista actualizada de objetos."""
        with open(self.__ruta, 'wb') as archivo:
            pickle.dump(historial, archivo)


class BCVModel:
    """Modelo principal que orquesta la lógica de negocio y los datos."""
    def __init__(self) -> None:
        self.__archivo = ManejadorHistorial(ARCHIVO_HISTORIAL)
        self.__historial_tasas: List[TasaCambio] = self.__archivo.cargar_historial()

    def obtener_html(self) -> Optional[BeautifulSoup]:
        try:
            response = requests.get(BCV_URL, headers=HEADERS, verify=False, timeout=TIMEOUT_REQ)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error de conexión al BCV: {e}")
            return None

    def procesar_precio(self, texto_sucio: str) -> float:
        try:
            limpio = re.sub(r'[^0-9,.]', '', texto_sucio)
            if ',' in limpio and '.' in limpio:
                limpio = limpio.replace('.', '')
            valor_punto = limpio.replace(',', '.')
            return float(valor_punto)
        except (ValueError, TypeError): 
            return 0.0

    def verificar_fecha_existe(self, fecha: str) -> bool:
        """Verifica en memoria si la fecha ya está en el historial de objetos."""
        for tasa in self.__historial_tasas:
            if tasa.fecha == fecha:
                return True
        return False

    def registrar_nueva_tasa(self, nueva_tasa: TasaCambio) -> None:
        """Agrega el nuevo objeto a la lista y manda a guardar el archivo serializado."""
        self.__historial_tasas.append(nueva_tasa)
        self.__archivo.guardar_historial(self.__historial_tasas)
        print(f"Registrado exitosamente en historial: {nueva_tasa}")


# ==========================================
# 2. VISTA (Formato de Interfaz)
# ==========================================
class DiscordView:
    """Encargada estrictamente de dar formato a los datos para el usuario/cliente."""
    def __formatear_moneda(self, numero: float) -> str:
        return f"{numero:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')

    def crear_mensaje_embed(self, tasa: TasaCambio, color: int) -> Dict[str, Any]:
        return {
            "embeds": [{
                "title": "🏦 Reporte Oficial BCV",
                "description": f"📅 **Fecha Valor:** {tasa.fecha}",
                "color": color,
                "fields": [
                    {"name": "💵 Dólar (USD)", "value": f"**{self.__formatear_moneda(tasa.dolar)} Bs.**", "inline": True},
                    {"name": "💶 Euro (EUR)", "value": f"**{self.__formatear_moneda(tasa.euro)} Bs.**", "inline": True}
                ],
                "footer": {"text": "Datos extraídos de bcv.org.ve"}
            }]
        }


# ==========================================
# 3. CONTROLADOR (Orquestador)
# ==========================================
class BotController:
    """Intermediario entre la Vista y el Modelo."""
    def __init__(self, modelo: BCVModel, vista: DiscordView) -> None:
        self.__modelo = modelo
        self.__vista = vista
        self.__servidores: List[Dict[str, Any]] = [
            {"url": os.getenv('DISCORD_WEBHOOK'), "color": 10181046},
            {"url": os.getenv('DISCORD_WEBHOOK_2'), "color": 3447003}
        ]

    def ejecutar(self) -> None:
        soup = self.__modelo.obtener_html()

        if not soup:
            print("No se pudo procesar la página web del BCV.")
            return

        try:
            fecha_elemento = soup.find(class_="date-display-single")
            if not fecha_elemento:
                print("No se encontró la clase de la fecha. ¿Cambió el diseño web?")
                return

            fecha_bcv = fecha_elemento.get_text().strip()

            if self.__modelo.verificar_fecha_existe(fecha_bcv):
                print(f"La fecha '{fecha_bcv}' ya se encuentra en el historial. No hay cambios.")
                return

            print(f"¡Nueva fecha detectada!: {fecha_bcv}. Publicando...")

            d_raw = soup.find(id="dolar").get_text() if soup.find(id="dolar") else "0"
            e_raw = soup.find(id="euro").get_text() if soup.find(id="euro") else "0"

            tasa_actual = TasaCambio(
                dolar=self.__modelo.procesar_precio(d_raw),
                euro=self.__modelo.procesar_precio(e_raw),
                fecha=fecha_bcv
            )

            for s in self.__servidores:
                if s.get("url"):
                    try:
                        payload = self.__vista.crear_mensaje_embed(tasa_actual, s["color"])
                        requests.post(s["url"], json=payload, timeout=5)
                    except requests.RequestException as e:
                        print(f"Ocurrió un error enviando datos al webhook: {e}")

            self.__modelo.registrar_nueva_tasa(tasa_actual)

        except AttributeError as e:
            print(f"Error de estructura HTML (falta un atributo esperado): {e}")
        except Exception as e:
            print(f"Error inesperado en la ejecución del controlador: {e}")


# ==========================================
# EJECUCIÓN DEL PROGRAMA
# ==========================================
if __name__ == "__main__":
    modelo_bcv = BCVModel()
    vista_discord = DiscordView()
    
    bot = BotController(modelo_bcv, vista_discord)
    bot.ejecutar()
