#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

url = "https://tos.trekcore.com/gallery/thumbnails.php?album=193"
print(f"Inspeccionando paginación en: {url}")

resp = requests.get(url, headers=HEADERS)
soup = BeautifulSoup(resp.content, 'html.parser')

# Buscar enlaces de paginación
# Usualmente están en una clase 'navmenu' o similar, o simplemente números
links = soup.find_all('a', href=True)
print("\nEnlaces encontrados que podrían ser paginación:")
for link in links:
    if 'page=' in link['href']:
        print(f" - {link.text.strip()} -> {link['href']}")
