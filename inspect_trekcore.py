#!/usr/bin/env python3
"""
Script de prueba para inspeccionar la estructura de TrekCore
Ayuda a identificar los selectores CSS correctos
"""

import requests
from bs4 import BeautifulSoup

# Headers para simular navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def inspect_page(url):
    """Inspecciona la estructura de una página"""
    print(f"\n🔍 Inspeccionando: {url}")
    print("=" * 70)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Guardar HTML para inspección manual
        with open('/home/alex/Projects/startrekar/scripts/trekcore_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        print("✅ HTML guardado en: trekcore_page.html")
        print()
        
        # Buscar enlaces a episodios
        print("📺 Enlaces encontrados:")
        links = soup.find_all('a', href=True)
        episode_links = [link for link in links if 'episode' in link.get('href', '').lower()]
        
        for i, link in enumerate(episode_links[:10], 1):  # Primeros 10
            print(f"  {i}. {link.text.strip()[:50]} -> {link['href']}")
        
        print(f"\n  Total de enlaces con 'episode': {len(episode_links)}")
        print()
        
        # Buscar imágenes
        print("🖼️  Imágenes encontradas:")
        images = soup.find_all('img')
        print(f"  Total de imágenes: {len(images)}")
        
        for i, img in enumerate(images[:10], 1):  # Primeras 10
            src = img.get('src', '') or img.get('data-src', '')
            alt = img.get('alt', '')
            print(f"  {i}. {alt[:30]:30} -> {src[:60]}")
        
        print()
        
        # Buscar clases comunes
        print("📋 Clases CSS más comunes:")
        all_classes = []
        for tag in soup.find_all(class_=True):
            all_classes.extend(tag.get('class', []))
        
        from collections import Counter
        common_classes = Counter(all_classes).most_common(15)
        
        for cls, count in common_classes:
            print(f"  {cls:30} ({count} veces)")
        
        print()
        print("=" * 70)
        print("✅ Inspección completada")
        print("📝 Revisa trekcore_page.html para más detalles")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Función principal"""
    print("🚀 TrekCore Inspector")
    print("=" * 70)
    
    # Probar con Starfleet Academy
    inspect_page("https://academy.trekcore.com/episodes/")
    
    # Si quieres probar una página de episodio específica, descomenta:
    # inspect_page("https://academy.trekcore.com/episodes/107/")

if __name__ == "__main__":
    main()
