#!/usr/bin/env python3
"""Script rápido para inspeccionar la galería (TODAS las imágenes)"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

url = "https://academy.trekcore.com/gallery/thumbnails.php?album=4"
response = requests.get(url, headers=HEADERS)
soup = BeautifulSoup(response.content, 'html.parser')

images = soup.find_all('img')
print(f"Total de imágenes: {len(images)}")

print("\nListado de imágenes no-diseño (filtrando 'design', 'spacer', 'arrow'):")
for i, img in enumerate(images, 1):
    src = img.get('src', '')
    if any(x in src for x in ['design_', 'spacer.gif', 'arrow']):
        continue
    
    # Buscar el padre <a> para ver a dónde enlaza
    parent = img.find_parent('a')
    href = parent.get('href') if parent else "No link"
    
    print(f"{i}. src={src}")
    print(f"   link={href}")
    print("-" * 40)
