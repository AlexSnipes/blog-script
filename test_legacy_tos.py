#!/usr/bin/env python3
"""Test rápido para verificar detección de episodios TOS Legacy"""
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

url = "https://tos.trekcore.com/episodes/"
print(f"Probando {url}...")

try:
    response = requests.get(url, headers=HEADERS, timeout=10)
    print(f"Status: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    links_found = 0
    print("\nPrimeros 5 episodios detectados:")
    
    # Lógica copiada de scrape_series en legacy
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Lógica de detección
        if ('season' in href.lower() and '.html' in href.lower() and 'index' not in href.lower()) or re.search(r'\d{3}\.html', href):
            print(f" - {link.text.strip()} -> {href}")
            links_found += 1
            if links_found >= 5:
                break
                
    print(f"\nTotal enlaces potenciales encontrados: {len(soup.find_all('a', href=True))}")
    
except Exception as e:
    print(f"Error: {e}")
