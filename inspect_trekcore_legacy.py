#!/usr/bin/env python3
"""
Script de prueba para inspeccionar la estructura de TrekCore LEGACY (TOS)
"""

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

def inspect_page(url):
    print(f"\n🔍 Inspeccionando: {url}")
    print("=" * 70)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Guardar HTML
        with open('trekcore_legacy_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
            
        print("✅ HTML guardado en: trekcore_legacy_page.html")
        
        print("\n📺 Enlaces encontrados:")
        links = soup.find_all('a', href=True)
        
        # Mostrar los primeros 50 enlaces para ver patrones
        for i, link in enumerate(links[:50], 1):
            print(f"  {i}. {link.text.strip()[:30]} -> {link['href']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    inspect_page("https://tos.trekcore.com/episodes/")
