import instaloader
import requests
import os

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
USUARIO_IG = 'bcv.org.ve'

def descargar_y_enviar():
    # Creamos el cargador con un "disfraz" de navegador real
    L = instaloader.Instaloader(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    try:
        print(f"Buscando publicación de {USUARIO_IG}...")
        profile = instaloader.Profile.from_username(L.context, USUARIO_IG)
        post = next(profile.get_posts())
        
        # Seleccionamos la primera imagen si es carrusel
        if post.typename == 'GraphSidecar':
            nodos = list(post.get_sidecar_nodes())
            imagen_url = nodos[0].display_url
        else:
            imagen_url = post.url
        
        payload = {
            "embeds": [{
                "title": "📊 Tasa Oficial BCV",
                "description": f"Fecha: {post.date_local.strftime('%d/%m/%Y')}",
                "color": 16766720,
                "image": {"url": imagen_url},
                "footer": {"text": "Bot Automatizado"}
            }]
        }
        
        requests.post(WEBHOOK_URL, json=payload)
        print("¡Enviado con éxito!")

    except Exception as e:
        print(f"Error detectado: {e}")
        # Si sigue fallando, intentamos enviar solo el link de Instagram como respaldo
        if "429" in str(e):
             requests.post(WEBHOOK_URL, json={"content": f"⚠️ Instagram nos bloqueó temporalmente, pero aquí está el link directo: https://www.instagram.com/{USUARIO_IG}/"})

if __name__ == "__main__":
    descargar_y_enviar()
