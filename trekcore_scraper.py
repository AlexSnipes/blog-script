#!/usr/bin/env python3
"""
Scraper de Screencaps de TrekCore.com - VERSIÓN ACTUALIZADA
Extrae fotos promocionales de episodios de Star Trek

NOTA: Este script ahora usa los selectores CSS correctos basados en la estructura real de TrekCore
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import re

# Configuración
EPISODES_JSON_PATH = '/home/alex/Projects/startrekar/old/src/data/jsons/__episodes.json'
SCREENCAPS_JSON_PATH = '/home/alex/Projects/startrekar/old/src/data/jsons/__screencaps.json'
LOG_FILE = '/home/alex/Projects/startrekar/scripts/trekcore_scraper.log'

# Headers para simular navegador real
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# Series activas en TrekCore
TREKCORE_SERIES = {
    'star-trek-starfleet-academy': {
        'base_url': 'https://academy.trekcore.com',
        'episodes_url': 'https://academy.trekcore.com/episodes/',
        'name': 'Star Trek: Starfleet Academy'
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
    """Extrae número de episodio del texto (1x03, Episode 103, etc.)"""
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
        season = int(ep_num[0])
        episode = int(ep_num[1:])
        return f"S{season}E{episode:02d}"
    
    return None

def scrape_episode_page(episode_url, base_url):
    """Extrae screencaps de una página de episodio buscando el enlace de galería"""
    try:
        log(f"    Scraping página: {episode_url}")
        response = requests.get(episode_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        screencaps = []
        
        # Buscar el enlace de "PROMOTIONAL PHOTOS" que apunta a gallery/thumbnails.php
        gallery_link = None
        for link in soup.find_all('a', href=True):
            if 'gallery/thumbnails.php' in link['href']:
                gallery_link = link['href']
                log(f"    ✅ Encontrado enlace de galería: {gallery_link}")
                break
        
        if not gallery_link:
            # Buscar también por texto del enlace
            for link in soup.find_all('a', href=True):
                if 'promotional' in link.text.lower() or 'photos' in link.text.lower():
                    gallery_link = link['href']
                    log(f"    ✅ Encontrado enlace de galería por texto: {gallery_link}")
                    break
        
        if gallery_link:
            # Construir URL completa de la galería
            if not gallery_link.startswith('http'):
                gallery_url = f"{base_url}/{gallery_link.lstrip('/')}"
            else:
                gallery_url = gallery_link
            
            log(f"    Accediendo a galería: {gallery_url}")
            
            # Scrape la galería
            gallery_response = requests.get(gallery_url, headers=HEADERS, timeout=30)
            gallery_response.raise_for_status()
            
            gallery_soup = BeautifulSoup(gallery_response.content, 'html.parser')
            
            # Buscar todas las imágenes en la galería
            all_images = gallery_soup.find_all('img')
            log(f"    Total de imágenes en galería: {len(all_images)}")
            
            for img in all_images:
                # Verificar si es una miniatura válida
                src = img.get('src', '')
                parent = img.find_parent('a')
                
                if parent and parent.get('href'):
                    full_res_url = parent.get('href')
                    
                    # Filtrar enlaces que no sean imágenes
                    if not full_res_url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        continue
                        
                    # Filtrar imágenes de navegación (next page, etc)
                    if 'thumbnails.php' in full_res_url:
                        continue

                    # Asegurar URL absoluta
                    # La base para la galería es https://academy.trekcore.com/gallery/
                    gallery_base = gallery_url.rsplit('/', 1)[0]
                    if not full_res_url.startswith('http'):
                        full_res_url = f"{gallery_base}/{full_res_url}"
                    
                    screencaps.append(full_res_url)
                    log(f"      Encontrada: {full_res_url}")
            
            log(f"    Total de screencaps válidos: {len(screencaps)}")
        else:
            log(f"    ⚠️  No se encontró enlace de galería en la página")
        
        return screencaps
        
    except Exception as e:
        log(f"    ❌ Error scraping {episode_url}: {str(e)}")
        import traceback
        log(f"       {traceback.format_exc()}")
        return []

def scrape_series(series_slug, series_info):
    """Escanea todos los episodios de una serie"""
    log(f"Scraping {series_info['name']}...")
    
    try:
        response = requests.get(series_info['episodes_url'], headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar todas las filas de la tabla con clase col2 (contienen los enlaces)
        episode_cells = soup.find_all('td', class_='col2')
        log(f"  Encontradas {len(episode_cells)} celdas de episodios")
        
        episodes_data = []
        
        for cell in episode_cells:
            link = cell.find('a')
            if link:
                episode_url = link.get('href')
                episode_title = link.text.strip()
                
                # Construir URL completa - los enlaces son relativos a /episodes/
                if not episode_url.startswith('http'):
                    # Si la URL es relativa (season1/sfa-ep101.html), agregarla a episodes_url
                    if not episode_url.startswith('/'):
                        # Obtener el directorio base de episodes_url
                        base_dir = series_info['episodes_url'].rsplit('/', 1)[0]
                        episode_url = f"{base_dir}/{episode_url}"
                    else:
                        episode_url = f"{series_info['base_url']}{episode_url}"
                
                # Buscar el número de episodio en la celda anterior (col1)
                parent_row = cell.find_parent('tr')
                if parent_row:
                    ep_num_cell = parent_row.find('td', class_='col1')
                    if ep_num_cell:
                        ep_text = ep_num_cell.text.strip()
                        episode_number = extract_episode_number_from_text(ep_text)
                        
                        if episode_number:
                            log(f"  Procesando {episode_number}: {episode_title}")
                            
                            # Actualizar título si es genérico
                            if episode_title.startswith('Episode'):
                                # Buscar título real en __episodes.json
                                episodes_json = load_json(EPISODES_JSON_PATH)
                                if episodes_json:
                                    for ep in episodes_json.get('episodes', []):
                                        if ep.get('seriesSlug') == series_slug and ep.get('number') == episode_number:
                                            real_title = ep.get('title', '')
                                            if real_title and not real_title.startswith('Episode'):
                                                log(f"    📝 Título actualizado: {episode_title} -> {real_title}")
                                                episode_title = real_title
                                            break
                            
                            # Scrape la página del episodio
                            screencaps = scrape_episode_page(episode_url, series_info['base_url'])
                            
                            if screencaps:
                                episodes_data.append({
                                    'series_slug': series_slug,
                                    'episode_number': episode_number,
                                    'episode_title': episode_title,
                                    'screencaps': screencaps,
                                    'source': 'trekcore',
                                    'scraped_at': datetime.now().isoformat()
                                })
                                log(f"    ✅ {len(screencaps)} screencaps encontrados")
                            else:
                                log(f"    ⚠️  No se encontraron screencaps")
                            
                            # Delay para no sobrecargar el servidor
                            time.sleep(3)
                        else:
                            log(f"  ⚠️  No se pudo extraer número de episodio de: {ep_text}")
        
        log(f"✅ Total procesado: {len(episodes_data)} episodios con screencaps")
        return episodes_data
        
    except Exception as e:
        log(f"❌ Error scraping series {series_slug}: {str(e)}")
        import traceback
        log(f"   Traceback: {traceback.format_exc()}")
        return []

def update_screencaps_json(new_data):
    """Actualiza __screencaps.json con nuevos datos"""
    existing_data = load_json(SCREENCAPS_JSON_PATH)
    if existing_data is None:
        existing_data = {'screencaps': [], 'last_updated': None}
    
    existing_index = {}
    for item in existing_data.get('screencaps', []):
        key = f"{item['series_slug']}_{item['episode_number']}"
        existing_index[key] = item
    
    for new_item in new_data:
        key = f"{new_item['series_slug']}_{new_item['episode_number']}"
        existing_index[key] = new_item
    
    updated_screencaps = list(existing_index.values())
    
    save_json(SCREENCAPS_JSON_PATH, {
        'screencaps': updated_screencaps,
        'last_updated': datetime.now().isoformat(),
        'total_episodes': len(updated_screencaps)
    })
    
    log(f"✅ Screencaps JSON actualizado: {len(updated_screencaps)} episodios")

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
            if screencap_id not in episode['gallery']:
                episode['gallery'].append(screencap_id)
                updated_count += 1
    
    save_json(EPISODES_JSON_PATH, episodes_data)
    log(f"✅ Episodes JSON actualizado: {updated_count} episodios con gallery")

def main():
    """Función principal"""
    log("=" * 70)
    log("🚀 Iniciando TrekCore Scraper")
    log("=" * 70)
    
    all_episodes_data = []
    
    for series_slug, series_info in TREKCORE_SERIES.items():
        episodes_data = scrape_series(series_slug, series_info)
        all_episodes_data.extend(episodes_data)
        time.sleep(5)
    
    if all_episodes_data:
        update_screencaps_json(all_episodes_data)
        update_episodes_json()
        log(f"✅ Scraping completado: {len(all_episodes_data)} episodios procesados")
    else:
        log("⚠️ No se encontraron screencaps")
    
    log("=" * 70)
    log("✅ TrekCore Scraper finalizado")
    log("=" * 70)

if __name__ == "__main__":
    main()
