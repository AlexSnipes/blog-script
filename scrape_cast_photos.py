import requests
import json
import re
from bs4 import BeautifulSoup
import os
import sys

# Mapeo de slugs internos a slugs de startrek.com
SERIES_MAPPING = {
    "star-trek-deep-space-nine": "deep-space-nine",
    "star-trek-voyager": "star-trek-voyager",
    "star-trek-the-next-generation": "star-trek-the-next-generation",
    "star-trek-the-original-series": "star-trek-the-original-series",
    "star-trek-enterprise": "star-trek-enterprise",
    "star-trek-discovery": "star-trek-discovery",
    "star-trek-picard": "star-trek-picard",
    "star-trek-strange-new-worlds": "star-trek-strange-new-worlds",
    "star-trek-lower-decks": "star-trek-lower-decks",
    "star-trek-prodigy": "star-trek-prodigy",
    "star-trek-starfleet-academy": "star-trek-starfleet-academy"
}

# Alias para personajes con nombres distintos entre la web y nuestra DB
CHARACTER_ALIASES = {
    "dr. m'benga": ["joseph m'benga", "m'benga"],
    "m'benga": ["joseph m'benga", "dr. m'benga"],
    "william riker": ["william t. riker", "will riker", "william t riker"],
    "uhura": ["nyota uhura"],
    "una “número uno” – una chin-riley": ["una chin-riley", "number one", "una"],
    "katherine pulaski": ["dr. katherine pulaski", "dr. pulaski"],
    "beverly crusher": ["dr. beverly crusher", "beverly crusher"],
    "julian bashir": ["dr. julian bashir", "julian bashir"],
    "the doctor": ["the holo-doc", "doctor", "the doctor"],
    "seven of nine": ["seven of nine", "7 of 9"],
}

BASE_URL = "https://www.startrek.com/series/"
JSON_PATH = "/home/alex/Projects/startrekar/old/src/data/jsons/__series.json"

def clean_name(name):
    """Limpia el nombre para facilitar la comparación"""
    if not name: return ""
    # Quitar títulos comunes y puntuación
    name = name.lower()
    name = name.replace("dr. ", "").replace("doctor ", "").replace("captain ", "")
    # Reemplazar caracteres especiales y puntuación
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip()

def is_match(internal_role, internal_actor, scraped_name):
    internal_role_clean = clean_name(internal_role)
    scraped_name_clean = clean_name(scraped_name)
    
    # Check exact clean match
    if internal_role_clean == scraped_name_clean:
        return True
        
    # Check if one is contained in the other
    if internal_role_clean in scraped_name_clean or scraped_name_clean in internal_role_clean:
        if len(internal_role_clean) > 3: # Evitar coincidencias de una letra
            return True

    # Check aliases
    role_lower = internal_role.lower()
    if role_lower in CHARACTER_ALIASES:
        for alias in CHARACTER_ALIASES[role_lower]:
            alias_clean = clean_name(alias)
            if alias_clean == scraped_name_clean or alias_clean in scraped_name_clean:
                return True
                
    return False

def scrape_series_cast(external_slug):
    url = f"{BASE_URL}{external_slug}"
    print(f"\n--- Scraping {url} ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Error: status code {response.status_code}")
            return []
    except Exception as e:
        print(f"Request failed: {e}")
        return []

    html = response.text
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    
    items = soup.find_all(class_=re.compile("Characters_character"))
    
    if not items:
        # Búsqueda por patrones en el HTML si no hay clases directas
        char_blocks = re.split(r'Characters_character', html)
        for block in char_blocks[1:]:
            name_match = re.search(r'heading-6.*?children\\":\[\\"([^"]+)\\"\]', block)
            img_match = re.search(r'src\\":\\"([^"]+prismic\.io/[^"]+)\\"', block)
            if name_match and img_match:
                name = name_match.group(1)
                img = img_match.group(1).replace("\\u0026", "&")
                results.append({"character": name, "image": img})
    else:
        for item in items:
            name_el = item.find(class_=re.compile("heading-6"))
            img_el = item.find("img")
            if name_el and img_el:
                name = name_el.get_text().strip()
                src = img_el.get("src") or img_el.get("srcset", "").split(" ")[0]
                if src:
                    results.append({"character": name, "image": src})

    print(f"Total personajes encontrados en la web: {len(results)}")
    return results

def update_all_series():
    if not os.path.exists(JSON_PATH):
        print(f"Error: No se encuentra {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        series_list = json.load(f)
    
    total_updated = 0
    
    for series in series_list:
        internal_slug = series.get('slug')
        if internal_slug in SERIES_MAPPING:
            external_slug = SERIES_MAPPING[internal_slug]
            scraped_cast = scrape_series_cast(external_slug)
            
            if not scraped_cast:
                continue
                
            cast_list = series.get('production', {}).get('cast', [])
            if not cast_list:
                print(f"La serie {series.get('title')} no tiene lista de cast definida.")
                continue
            
            updated_in_series = 0
            for cast_member in cast_list:
                role = cast_member.get('role', '')
                full_name = cast_member.get('fullName', '')
                
                # Buscar mejor coincidencia
                match = None
                for s_item in scraped_cast:
                    if is_match(role, full_name, s_item['character']):
                        match = s_item
                        break
                
                if match:
                    cast_member['image'] = match['image']
                    updated_in_series += 1
                    total_updated += 1
            
            print(f"Actualizados {updated_in_series}/{len(cast_list)} miembros del cast para {series.get('title')}")

    if total_updated > 0:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(series_list, f, indent=2, ensure_ascii=False)
        print(f"\nProceso finalizado. Se actualizaron {total_updated} fotos en total.")
    else:
        print("\nNo se realizaron actualizaciones.")

if __name__ == "__main__":
    update_all_series()
