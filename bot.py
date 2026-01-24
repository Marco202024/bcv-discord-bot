import instaloader
import requests
import os

# Configuraciones desde los Secretos de GitHub
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
USUARIO_IG = 'bcv.org.ve'

def descargar_y_enviar():
    L = instaloader.Instaloader()
    try:
        print(f"Buscando publicación de {USUARIO_IG}...")
        profile = instaloader.Profile.from_username(L.context, USUARIO_IG)
        post = next(profile.get_posts()) # El post más reciente
        
        # Si es un carrusel (varias fotos), seleccionamos la primera
        if post.typename == 'GraphSidecar':
            # Obtenemos la URL de la primera imagen del carrusel
            nodos = list(post.get_sidecar_nodes())
            imagen_url = nodos[0].display_url
        else:
            # Si es una sola imagen, la tomamos directamente
            imagen_url = post.url
        
        payload = {
            "embeds": [
                {
                    "title": "📊 Tasa Oficial del Banco Central de Venezuela",
                    "description": f"Fecha de publicación: {post.date_local.strftime('%d/%m/%Y')}",
                    "color": 16766720, # Color dorado/amarillo
                    "image": {
                        "url": imagen_url
                    },
                    "footer": {
                        "text": "Actualización diaria automática"
                    }
                }
            ]
        }
        
        response = requests.post(WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            print("Enviado con éxito a Discord.")
        else:
            print(f"Error en Discord: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    descargar_y_enviar()
