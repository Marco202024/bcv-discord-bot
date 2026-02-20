#  Bot de Tasas BCV para Discord

Este bot extrae automáticamente las tasas oficiales del **Banco Central de Venezuela** directamente desde su sitio web y las publica en múltiples servidores de Discord.

##  Características
* **Precisión:** Redondeo estricto a 2 decimales.
* **Multiservidor:** Envío simultáneo a varios servidores con colores personalizados (Morado, Azul, etc.).
* **Automatización:** Envía una publicación de Marte a viernes a las 5:45 AM GMT-4:00 mediante GitHub Actions.
* **Seguridad:** Uso de Secrets para proteger los Webhooks de Discord.

##  Cómo funciona
1. El script entra a la web del BCV usando `BeautifulSoup4`.
2. Limpia los datos y les da formato profesional.
3. Envía un "Embed" elegante a Discord usando Webhooks.

---
*Desarrollado como proyecto de automatización con Python.*

![Seguridad](https://img.shields.io/github/actions/workflow/status/Marco202024/bcv-discord-bot/main.yml?label=Seguridad&style=for-the-badge)
