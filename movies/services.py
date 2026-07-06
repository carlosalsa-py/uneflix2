# services.py
import requests
import time
import re
from django.conf import settings

# --- CONFIGURACIÓN DE FILTROS ---
KEYWORDS_LATINO = ['latino', 'lat', 'español', 'espanol', 'dual', 'multi', 'audio latino']
KEYWORDS_AVOID = ['castellano', 'cast', 'spain', 'es-es']
KEYWORDS_BLOCK_PACK = ['pack', 'collection', 'season', 'series', 'complete', 'archive', 'temporada', 'coleccion']
KEYWORDS_VIDEO_EXT = ('.mp4', '.mkv', '.avi', '.mov')

def clean_search_title(title):
    """Limpia el título para mejorar la búsqueda (Ej: 'Click: Perdiendo el control' -> 'click')"""
    t = title.lower()
    t = t.split(':')[0] # Quita subtítulos después de ":"
    t = t.split('(')[0] # Quita años o info en paréntesis
    t = re.sub(r'[^a-z0-9 ]+', '', t) # Quita símbolos raros
    return t.strip()

def get_stream_score(title, seeders):
    """Calcula la puntuación para elegir el mejor Torrent de la lista."""
    score = 0
    title_lower = title.lower()
    
    if any(k in title_lower for k in KEYWORDS_LATINO): score += 100
    if any(k in title_lower for k in KEYWORDS_AVOID): score -= 200
    if any(k in title_lower for k in KEYWORDS_BLOCK_PACK): score -= 500 # Evitar packs desde el origen
    
    if '1080p' in title_lower: score += 30
    elif '720p' in title_lower: score += 15
    
    if seeders < 2: score -= 100
    else: score += min(seeders, 50)
    
    if any(bad in title_lower for bad in ['cam', 'ts', 'telesync']): score -= 300
        
    return score

def get_direct_link(magnet_link, movie_title):
    api_key = settings.ALLDEBRID_API_KEY
    base_url = "https://api.alldebrid.com/v4.1"
    headers = {'Authorization': f'Bearer {api_key}'}
    
    clean_name = clean_search_title(movie_title)
    print(f"\n[DEBUG] === BUSCANDO: '{clean_name}' (Original: {movie_title}) ===")

    try:
        # 1. Subir Magnet
        upload_res = requests.post(f"{base_url}/magnet/upload", headers=headers, data={"magnets[]": magnet_link}).json()
        if upload_res.get('status') == 'success':
            magnet_id = upload_res['data']['magnets'][0]['id']
        elif upload_res.get('error', {}).get('code') == 'MAGNET_ALREADY_IN_HISTORY':
            magnet_id = upload_res['error']['data']['id']
        else:
            return None

        # 2. Esperar y Procesar
        for i in range(10): # Reducido a 10 intentos (50 segs)
            status_res = requests.get(f"{base_url}/magnet/status", headers=headers, params={'id': magnet_id}).json()
            
            if status_res.get('status') == 'success':
                data = status_res['data']['magnets']
                estado = data.get('status')
                
                if estado == 'Ready':
                    files = []
                    # Aplanar la lista de archivos de todas las carpetas
                    for folder in data.get('files', []):
                        for item in folder.get('e', []):
                            files.append(item)
                    
                    # --- FILTRO ANTI-PACKS ---
                    # Si hay más de 10 archivos de video, probablemente es un pack/colección pesada
                    video_files = [f for f in files if f.get('n', '').lower().endswith(KEYWORDS_VIDEO_EXT)]
                    if len(video_files) > 10:
                        print(f"[DEBUG] Torrent descartado: Es un PACK ({len(video_files)} videos).")
                        break

                    # --- SELECCIÓN INTELIGENTE ---
                    best_file = None
                    
                    # Prioridad 1: Que contenga el nombre limpio Y sea latino
                    for f in video_files:
                        fname = f.get('n', '').lower()
                        if clean_name in fname and any(k in fname for k in KEYWORDS_LATINO):
                            best_file = f
                            break
                    
                    # Prioridad 2: Que al menos contenga el nombre limpio
                    if not best_file:
                        for f in video_files:
                            if clean_name in f.get('n', '').lower():
                                best_file = f
                                break
                    
                    # Prioridad 3: Si solo hay UN video (muy común en pelis sueltas), usar ese
                    if not best_file and len(video_files) == 1:
                        best_file = video_files[0]

                    if best_file:
                        print(f"[DEBUG] Seleccionado: {best_file['n']}")
                        unlock = requests.get(f"{base_url}/link/unlock", headers=headers, params={'link': best_file['l']}).json()
                        return unlock['data']['link'] if unlock.get('status') == 'success' else None
                    else:
                        print(f"[DEBUG] No se halló archivo de video válido para '{clean_name}'.")
                        break # No seguir esperando si ya está Ready y no hay match
                
                elif estado in ['Error', 'Canceled', 'Deadline Reached']:
                    break
                
            time.sleep(5)
            
        # Limpieza: Si no funcionó, borrar de la lista para no saturar Alldebrid
        requests.get(f"{base_url}/magnet/delete", headers=headers, params={'id': magnet_id})
        return None

    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")
        return None