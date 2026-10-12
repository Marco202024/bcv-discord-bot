import os
import re
import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks

# ==========================================
# CONSTANTES Y CONFIGURACIÓN GLOBALES
# ==========================================
BCV_URL = "https://www.bcv.org.ve/"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Configuramos los intents del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# 1. ENTIDADES Y MODELO (Gestión de Datos)
# ==========================================
class BCVModel:
    @staticmethod
    def obtener_datos():
        try:
            response = requests.get(BCV_URL, headers=HEADERS, verify=False, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            fecha = soup.find(class_="date-display-single").get_text().strip()
            d_raw = soup.find(id="dolar").get_text()
            e_raw = soup.find(id="euro").get_text()
            
            return {
                "fecha": fecha,
                "dolar": BCVModel.__limpiar_precio(d_raw),
                "euro": BCVModel.__limpiar_precio(e_raw)
            }
        except Exception as e:
            print(f"Error obteniendo datos del BCV: {e}")
            return None

    @staticmethod
    def __limpiar_precio(texto_sucio: str) -> float:
        try:
            limpio = re.sub(r'[^0-9,.]', '', texto_sucio)
            if ',' in limpio and '.' in limpio:
                limpio = limpio.replace('.', '')
            return float(limpio.replace(',', '.'))
        except:
            return 0.0

# ==========================================
# 2. VISTA (Formato de Interfaz)
# ==========================================

class ModalCalculadora(discord.ui.Modal):
    def __init__(self, tasa_usd: float, tasa_eur: float, tipo: str):
        super().__init__(title=f"Calculadora BCV ({tipo})")
        self.tasa_usd = tasa_usd
        self.tasa_eur = tasa_eur
        self.tipo = tipo

        self.monto_input = discord.ui.inputText(
            label=f"Ingrese la cantidad en {tipo}",
            placeholder="Ej. 50 o 1500.50",
            min_length=1,
            max_length=15
        )
        self.add_item(self.monto_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            valor = float(self.monto_input.value.replace(',', '.'))
            if self.tipo == "USD":
                bs_dolar = valor * self.tasa_usd
                bs_euro = valor * self.tasa_eur
                mensaje = (
                    f"🧮 **Resultado del Cálculo:**\n"
                    f"💵 **{valor:,.2f} USD** = `{bs_dolar:,.2f} Bs.`\n"
                    f"💶 **{valor:,.2f} EUR** = `{bs_euro:,.2f} Bs.`"
                ).replace('.', 'X').replace(',', '.').replace('X', ',')
            else:
                usd = valor / self.tasa_usd if self.tasa_usd > 0 else 0
                eur = valor / self.tasa_eur if self.tasa_eur > 0 else 0
                mensaje = (
                    f"🧮 **Resultado del Cálculo:**\n"
                    f"🇻🇪 **{valor:,.2f} Bs.**\n"
                    f"💵 Equivale a: `__{usd:,.2f} USD__`\n"
                    f"💶 Equivale a: `__{eur:,.2f} EUR__`"
                ).replace('.', 'X').replace(',', '.').replace('X', ',')

            await interaction.response.send_message(mensaje, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Por favor, ingresa un número válido.", ephemeral=True)

class VistaCalculadora(discord.ui.View):
    def __init__(self, tasa_usd: float, tasa_eur: float):
        super().__init__(timeout=None)
        self.tasa_usd = tasa_usd
        self.tasa_eur = tasa_eur

    @discord.ui.button(label="🧮 Calcular desde USD", style=discord.ButtonStyle.green, custom_id="calc_usd")
    async def boton_usd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalCalculadora(self.tasa_usd, self.tasa_eur, "USD"))

    @discord.ui.button(label="🧮 Calcular desde Bolívares", style=discord.ButtonStyle.blurple, custom_id="calc_bs")
    async def boton_bs(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalCalculadora(self.tasa_usd, self.tasa_eur, "Bolívares"))

# ==========================================
# 3. CONTROLADOR (Orquestador)
# ==========================================

@bot.event
async def on_ready():
    print(f'¡Bot conectado exitosamente como {bot.user}!')
    verificar_tasas_bcv.start()

@bot.tree.command(name="tasa", description="Muestra la tasa actual del BCV con calculadora interactiva")
async def tasa_cmd(interaction: discord.Interaction):
    datos = BCVModel.obtener_datos()
    if not datos:
        await interaction.response.send_message("❌ No se pudo conectar con el BCV en este momento.", ephemeral=True)
        return

    d_fmt = f"{datos['dolar']:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')
    e_fmt = f"{datos['euro']:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')

    embed = discord.Embed(
        title="🏦 Tasas Oficiales BCV",
        description=f"📅 **Fecha Valor:** {datos['fecha']}",
        color=10181046
    )
    embed.add_field(name="💵 Dólar (USD)", value=f"**{d_fmt} Bs.**", inline=True)
    embed.add_field(name="💶 Euro (EUR)", value=f"**{e_fmt} Bs.**", inline=True)
    embed.set_footer(text="Usa los botones de abajo para calcular conversiones al instante")

    view = VistaCalculadora(datos['dolar'], datos['euro'])
    await interaction.response.send_message(embed=embed, view=view)

# Tarea automática opcional (Ejecuta una verificación periódica)
@tasks.loop(hours=2)
async def verificar_tasas_bcv():
    # Aquí puedes programar la lógica si deseas que el bot anuncie automáticamente en un canal específico
    pass

# ==========================================
# EJECUCIÓN DEL PROGRAMA
# ==========================================
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        print("Error: No se encontró la variable de entorno DISCORD_BOT_TOKEN.")
    else:
        bot.run(TOKEN)
