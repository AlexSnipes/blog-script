#!/usr/bin/env python3
"""
Scraper de Screencaps de TrekCore.com - SERIES LEGACY (TOS, TNG, DS9, VOY, ENT)
Se ejecuta UNA SOLA VEZ para poblar __screencaps.json con series finalizadas.
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import re
import traceback
import sys

# Configuración
EPISODES_JSON_PATH = '/home/alex/Projects/startrekar/old/src/data/jsons/__episodes.json'
SCREENCAPS_JSON_PATH = '/home/alex/Projects/startrekar/old/src/data/jsons/__screencaps.json'
LOG_FILE = '/home/alex/Projects/startrekar/scripts/trekcore_scraper_legacy.log'

# Headers para simular navegador real (ROBUSTOS)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}

def load_existing_screencaps():
    """Carga los datos actuales para verificar qué ya existe"""
    if os.path.exists(SCREENCAPS_JSON_PATH):
        try:
            with open(SCREENCAPS_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'screencaps': []}
    return {'screencaps': []}

def episode_exists(data, series_slug, episode_number):
    """Verifica si un episodio ya tiene screencaps"""
    for ep in data.get('screencaps', []):
        if ep.get('series_slug') == series_slug and ep.get('episode_number') == episode_number:
            # Verificar que tenga screencaps
            if ep.get('screencaps') and len(ep['screencaps']) > 0:
                return True
    return False

# Series Legacy en TrekCore
TREKCORE_LEGACY_SERIES = {
    'star-trek-the-original-series': {
        'base_url': 'https://tos.trekcore.com',
        'episodes_url': 'https://tos.trekcore.com/episodes/',
        'name': 'Star Trek: The Original Series'
    },
    'star-trek-the-next-generation': {
        'base_url': 'https://tng.trekcore.com',
        'episodes_url': 'https://tng.trekcore.com/episodes/',
        'name': 'Star Trek: The Next Generation'
    },
    'star-trek-deep-space-nine': {
        'base_url': 'https://ds9.trekcore.com',
        'episodes_url': 'https://ds9.trekcore.com/episodes/',
        'name': 'Star Trek: Deep Space Nine'
    },
    'star-trek-voyager': {
        'base_url': 'https://voy.trekcore.com',
        'episodes_url': 'https://voy.trekcore.com/episodes/',
        'name': 'Star Trek: Voyager'
    },
    'star-trek-enterprise': {
        'base_url': 'https://ent.trekcore.com',
        'episodes_url': 'https://ent.trekcore.com/episodes/',
        'name': 'Star Trek: Enterprise'
    }
}

def log(message):
    """Registra mensaje en log y consola"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')

def load_json(filepath):
    """Carga archivo JSON"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def save_json(filepath, data):
    """Guarda archivo JSON"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_episode_number_from_text(text):
    """Extrae número de episodio del texto (1x03, Episode 103, Season 1 Episode 3, etc.)"""
    # Formato 1x03
    match = re.search(r'(\d+)x(\d+)', text)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return f"S{season}E{episode:02d}"
    
    # Formato Episode 103
    match = re.search(r'[Ee]pisode\s*(\d{3})', text)
    if match:
        ep_num = match.group(1)
        # Para legacy, a veces 103 es S1E03
        if len(ep_num) == 3:
            season = int(ep_num[0])
            episode = int(ep_num[1:])
            # Ajuste para DS9/VOY/TNG donde temp +2 tiene eps > 20
            # Mejor verificación: buscar en JSON de episodios si existe
            return f"S{season}E{episode:02d}"
    
    return None

import random

def scrape_episode_page(episode_url, base_url):
    """Extrae screencaps de una página de episodio buscando el enlace de galería"""
    try:
        log(f"    Scraping página: {episode_url}")
        response = requests.get(episode_url, headers=HEADERS, timeout=30)
        # Algunos sitios legacy pueden dar 404 si el link está mal construido, lo manejamos fuera
        if response.status_code != 200:
            log(f"    ⚠️ Error HTTP {response.status_code} al acceder a {episode_url}")
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        screencaps = []
        
        # Buscar el enlace de "SCREENCAPS", "HD SCREENCAPS"
        # En sitios legacy suele ser "HD Screencaps" o similar apuntando a gallery/thumbnails.php
        gallery_link = None
        
        # Prioridad 1: Buscar por texto explícito "Screencaps" o "HD Screencaps"
        for link in soup.find_all('a', href=True):
            text = link.text.lower()
            if 'screencap' in text and 'gallery/thumbnails.php' in link['href']:
                gallery_link = link['href']
                log(f"    ✅ Encontrado enlace de galería (Screencaps): {gallery_link}")
                break
                
        # Prioridad 2: Si no hay específico, buscar cualquier thumbnails.php 
        # (pero tratando de evitar behind the scenes si es posible, aunque thumbnails.php suele ser el main)
        if not gallery_link:
            for link in soup.find_all('a', href=True):
                if 'gallery/thumbnails.php' in link['href']:
                    gallery_link = link['href']
                    log(f"    ✅ Encontrado enlace de galería (Genérico): {gallery_link}")
                    break
        
        if gallery_link:
            # Construir URL completa de la galería
            if not gallery_link.startswith('http'):
                gallery_url = f"{base_url}/{gallery_link.lstrip('/')}"
            else:
                gallery_url = gallery_link
            
            log(f"    Accediendo a galería: {gallery_url}")
            
            # Helper para extraer imágenes de una sopa
            def extract_images_from_soup(soup, base_url_gallery):
                imgs = []
                for img in soup.find_all('img'):
                    parent = img.find_parent('a')
                    if parent and parent.get('href'):
                        full_res_url = parent.get('href')
                        if not full_res_url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')): continue
                        if 'displayimage.php' in full_res_url or 'thumbnails.php' in full_res_url: continue
                        
                        # Asegurar URL absoluta
                        gallery_base_dir = base_url_gallery.rsplit('/', 1)[0]
                        if not full_res_url.startswith('http'):
                            full_res_url = f"{gallery_base_dir}/{full_res_url}"
                        
                        imgs.append(full_res_url)
                return imgs

            try:
                # 1. Scrap página 1
                gallery_response = requests.get(gallery_url, headers=HEADERS, timeout=30)
                gallery_response.raise_for_status()
                gallery_soup = BeautifulSoup(gallery_response.content, 'html.parser')
                
                potential_screencaps = extract_images_from_soup(gallery_soup, gallery_url)
                
                # 2. Detectar total de páginas para mayor variedad
                # Buscamos texto como: "738 files on 31 page(s)"
                total_pages = 1
                # Buscar en la tabla que contiene esa info (clase tableh1 a veces)
                page_info_match = re.search(r'(\d+) files on (\d+) page', gallery_soup.text)
                if page_info_match:
                    total_pages = int(page_info_match.group(2))
                    log(f"    📄 Galería tiene {total_pages} páginas. Realizando muestreo aleatorio...")

                # 3. Si hay más páginas, seleccionar hasta 5 aleatorias adicionales
                if total_pages > 1:
                    # Seleccionar hasta 5 páginas random del resto
                    pages_pool = list(range(2, total_pages + 1))
                    random_pages = random.sample(pages_pool, min(5, len(pages_pool)))
                    random_pages.sort()
                    
                    log(f"    Explorando páginas adicionales: {random_pages}")
                    
                    for page_num in random_pages:
                        # Construir URL paginada: thumbnails.php?album=193&page=X
                        if '?' in gallery_url:
                            page_url = f"{gallery_url}&page={page_num}"
                        else:
                            page_url = f"{gallery_url}?page={page_num}"
                            
                        try:
                            # Pequeña pausa
                            time.sleep(0.5) 
                            p_resp = requests.get(page_url, headers=HEADERS, timeout=15)
                            if p_resp.status_code == 200:
                                p_soup = BeautifulSoup(p_resp.content, 'html.parser')
                                new_imgs = extract_images_from_soup(p_soup, gallery_url)
                                potential_screencaps.extend(new_imgs)
                        except Exception as e:
                            log(f"    ⚠️ Error en página {page_num}: {e}")

                # Eliminar duplicados
                potential_screencaps = list(set(potential_screencaps))
                
                total_found = len(potential_screencaps)
                log(f"    Encontrados {total_found} screencaps potenciales en total")
                
                # SELECCIÓN ALEATORIA DE 20 SCREENCAPS
                if total_found > 20:
                    screencaps = random.sample(potential_screencaps, 20)
                    log(f"    🎲 Seleccionados 20 screencaps aleatorios de {total_found}")
                else:
                    screencaps = potential_screencaps
                    log(f"    📥 Seleccionados todos los {total_found} screencaps (menos de 20)")
                
            except Exception as e:
                log(f"    ❌ Error scraping galería {gallery_url}: {str(e)}")

        else:
            log(f"    ⚠️  No se encontró enlace de galería en la página")
        
        return screencaps
        
    except Exception as e:
        log(f"    ❌ Error scraping {episode_url}: {str(e)}")
        return []

def scrape_series(series_slug, series_info, force_update=False):
    """Scrapea una serie completa de TrekCore Legacy"""
    
    log(f"Scraping {series_info['name']}...")
    
    # Cargar datos existentes para verificar duplicados
    existing_data = load_existing_screencaps()
    
    try:
        series_url = series_info['episodes_url']
        log(f"  URL base serie: {series_url}")
        
        response = requests.get(series_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # En sitios Legacy, suelen usar tablas. Buscamos enlaces que parezcan episodios.
        # TOS: season1/1x01/
        # TNG/DS9/VOY suelen tener estructura similar
        
        episodes_data = []
        
        # Buscar todos los enlaces que contengan "season" en el href
        # Esto es un patrón común en TrekCore legacy
        episode_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Filtros para identificar enlaces a episodios
            
            # Caso 1: season1/1x01/ o season1/1x01.html
            if 'season' in href.lower() and ('x' in href.lower() or 'episode' in href.lower()):
                 # Verificar que tenga numeros (ej 1x01)
                 if re.search(r'\d+x\d+', href):
                     episode_links.append(link)
            
            # Caso 2: Archivos .html directos con números (ej 101.html)
            elif re.search(r'season\d+/\d{3}\.html', href):
                 episode_links.append(link)
            
            # Caso 3: Formato TOS directo (1x01/)
            elif re.search(r'season\d+/\d+x\d+/?$', href):
                 episode_links.append(link)

        log(f"  Encontrados {len(episode_links)} posibles enlaces de episodios")
        
        # Filtrar duplicados por URL
        seen_urls = set()
        unique_links = []
        for link in episode_links:
            href = link['href']
            # Normalizar URL (quitar slash final para comparar)
            norm_href = href.rstrip('/')
            if norm_href not in seen_urls:
                seen_urls.add(norm_href)
                unique_links.append(link)
        
        for link in unique_links:
            episode_url = link.get('href')
            link_text = link.text.strip()
            
            # Construir URL completa
            if not episode_url.startswith('http'):
                # Si es relativa compleja (season1/...)
                if not episode_url.startswith('/'):
                     # Obtener base de episodes_url
                    base_dir = series_info['episodes_url'].rstrip('/')
                    # A veces episodes_url termina en /episodes/ y el link es season1/1x01/ => /episodes/season1/1x01/
                    episode_url = f"{base_dir}/{episode_url}"
                else:
                    episode_url = f"{series_info['base_url']}{episode_url}"
            
            # Intentar deducir número de episodio de la URL
            # Ej: .../season1/102.html -> S1E02
            # Ej: .../season1/1x02/ -> S1E02
            
            # Buscar patrón 1x02
            match_sx = re.search(r'(\d+)x(\d+)', episode_url)
            
            # Buscar patrón 102.html
            match_num = re.search(r'/(\d{3})\.html', episode_url)
            
            episode_number = None
            
            if match_sx:
                season = int(match_sx.group(1))
                ep = int(match_sx.group(2))
                episode_number = f"S{season}E{ep:02d}"
            elif match_num:
                num = match_num.group(1)
                season = int(num[0])
                ep = int(num[1:])
                episode_number = f"S{season}E{ep:02d}"
            
            if episode_number:
                # CHECK IF EXISTS
                if not force_update and episode_exists(existing_data, series_slug, episode_number):
                    log(f"  ⏭️  Saltando {episode_number} (ya existe)")
                    continue

                log(f"  Procesando {episode_number} (Link: {link_text})")
                
                # Buscar título real en __episodes.json para referencia
                episode_title = link_text
                episodes_json = load_json(EPISODES_JSON_PATH)
                if episodes_json:
                    for ep in episodes_json.get('episodes', []):
                        if ep.get('seriesSlug') == series_slug and ep.get('number') == episode_number:
                            episode_title = ep.get('title', episode_title)
                            break
                
                screencaps = scrape_episode_page(episode_url, series_info['base_url'])
                
                if screencaps:
                    # Crear objeto episodio
                    new_episode_data = {
                        'series_slug': series_slug,
                        'episode_number': episode_number,
                        'episode_title': episode_title,
                        'screencaps': screencaps,
                        'source': 'trekcore_legacy',
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    episodes_data.append(new_episode_data)
                    log(f"    ✅ Procesado {episode_number}. Guardando...")
                    
                    # GUARDAR INMEDIATAMENTE
                    update_screencaps_json([new_episode_data])
                    update_episodes_json()
                    
                else:
                    log(f"    ⚠️  No se encontraron screencaps")
                
                # Pausa aleatoria para evitar ser detectado como bot agresivo
                sleep_time = random.uniform(2.0, 4.0)
                log(f"    💤 Esperando {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            
        return episodes_data
        
    except Exception as e:
        log(f"❌ Error scraping series {series_slug}: {str(e)}")
        log(f"   {traceback.format_exc()}")
        return []

def update_screencaps_json(new_data):
    """Actualiza __screencaps.json con nuevos datos (append update)"""
    existing_data = load_json(SCREENCAPS_JSON_PATH)
    if existing_data is None:
        existing_data = {'screencaps': [], 'last_updated': None}
    
    existing_index = {}
    for item in existing_data.get('screencaps', []):
        key = f"{item['series_slug']}_{item['episode_number']}"
        existing_index[key] = item
    
    for new_item in new_data:
        key = f"{new_item['series_slug']}_{new_item['episode_number']}"
        if key in existing_index:
             # Si ya existe, podemos optar por Sobreescribir o Ignorar.
             # Para Legacy, si ya tenemos algo, asumimos que es bueno, pero si estamos re-corriendo para completar, actualizamos.
             existing_index[key] = new_item
        else:
             existing_index[key] = new_item
    
    updated_screencaps = list(existing_index.values())
    
    # Ordenar por serie y episodio (opcional, pero util)
    
    save_json(SCREENCAPS_JSON_PATH, {
        'screencaps': updated_screencaps,
        'last_updated': datetime.now().isoformat(),
        'total_episodes': len(updated_screencaps)
    })
    
    log(f"✅ Screencaps JSON actualizado. Total: {len(updated_screencaps)} episodios.")

def update_episodes_json():
    """Actualiza __episodes.json con referencias a gallery"""
    episodes_data = load_json(EPISODES_JSON_PATH)
    screencaps_data = load_json(SCREENCAPS_JSON_PATH)
    
    if not episodes_data or not screencaps_data:
        log("⚠️ No se pudo cargar datos para actualizar episodes.json")
        return
    
    screencaps_index = {}
    for idx, item in enumerate(screencaps_data.get('screencaps', [])):
        key = f"{item['series_slug']}_{item['episode_number']}"
        screencaps_index[key] = idx
    
    updated_count = 0
    for episode in episodes_data.get('episodes', []):
        key = f"{episode.get('seriesSlug')}_{episode.get('number')}"
        if key in screencaps_index:
            if 'gallery' not in episode:
                episode['gallery'] = []
            
            screencap_id = screencaps_index[key]
            # Solo agregar si no está ya (evitar duplicados si corre varias veces)
            if screencap_id not in episode.get('gallery', []):
                # En realidad gallery debería ser solo una referencia al indice o al objeto
                # Si estamos reconstruyendo todo, podríamos limpiar gallery primero
                # Pero asumimos append seguro
                if not episode.get('gallery'):
                     episode['gallery'] = [screencap_id]
                elif screencap_id not in episode['gallery']:
                     episode['gallery'].append(screencap_id)
                
                updated_count += 1
    
    save_json(EPISODES_JSON_PATH, episodes_data)
    log(f"✅ Episodes JSON actualizado con referencias a galería. Episodios afectados: {updated_count}")


def main():
    """Función principal"""
    # Verificar flag --force
    force_update = '--force' in sys.argv
    
    log("=" * 70)
    log(f"🚀 Iniciando TrekCore LEGACY Scraper (Force: {force_update})")
    log("=" * 70)
    
    total_processed = 0
    
    # Iterar sobre las series legacy
    for series_slug, series_info in TREKCORE_LEGACY_SERIES.items():
        # scrape_series ya guarda episodio a episodio
        scrape_series(series_slug, series_info, force_update)
        time.sleep(2) # Pausa entre series
    
    log("=" * 70)
    log("✅ TrekCore Legacy Scraper finalizado")
    log("=" * 70)

if __name__ == "__main__":
    main()
