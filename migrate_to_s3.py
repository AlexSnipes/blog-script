#!/usr/bin/env python3
"""
Script para migrar screencaps de TrekCore a AWS S3
ESTE SCRIPT ES UNA PLANTILLA - Requiere configurar credenciales AWS
"""

import json
import requests
import boto3
import os
import time
from botocore.exceptions import NoCredentialsError

# Configuración AWS
AWS_ACCESS_KEY = 'TU_ACCESS_KEY'
AWS_SECRET_KEY = 'TU_SECRET_KEY'
AWS_BUCKET_NAME = 'startrekar-screencaps'
AWS_REGION = 'us-east-1'

# Archivos
SCREENCAPS_JSON_PATH = '/home/alex/Projects/startrekar/old/src/data/jsons/__screencaps.json'

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def migrate_images():
    # Inicializar cliente S3
    s3 = boto3.client('s3', 
                      aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY,
                      region_name=AWS_REGION)

    data = load_json(SCREENCAPS_JSON_PATH)
    total_migrated = 0
    
    print(f"🚀 Iniciando migración de {data['total_episodes']} episodios...")

    for episode in data['screencaps']:
        new_urls = []
        changed = False
        
        print(f"Procesando {episode['series_slug']} - {episode['episode_number']}...")
        
        for url in episode['screencaps']:
            # Solo migrar si es URL de TrekCore
            if 'trekcore.com' in url:
                try:
                    # Nombre de archivo único para S3
                    # Estructura: series/episodio/filename.jpg
                    filename = url.split('/')[-1]
                    s3_key = f"{episode['series_slug']}/{episode['episode_number']}/{filename}"
                    
                    # Descargar imagen
                    print(f"  ⬇️ Descargando {filename}...")
                    response = requests.get(url, stream=True)
                    
                    if response.status_code == 200:
                        # Subir a S3
                        print(f"  ⬆️ Subiendo a S3...")
                        s3.upload_fileobj(response.raw, AWS_BUCKET_NAME, s3_key, ExtraArgs={'ACL': 'public-read'})
                        
                        # Generar nueva URL
                        new_url = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
                        new_urls.append(new_url)
                        changed = True
                        total_migrated += 1
                    else:
                        print(f"  ❌ Error descargando {url}: {response.status_code}")
                        new_urls.append(url) # Mantener original si falla
                except Exception as e:
                    print(f"  ❌ Error migrando {url}: {str(e)}")
                    new_urls.append(url)
            else:
                new_urls.append(url)
        
        if changed:
            episode['screencaps'] = new_urls
            episode['source'] = 'aws_s3'
            
            # Guardar progreso parcial cada 5 episodios
            save_json(SCREENCAPS_JSON_PATH, data)

    print("=" * 50)
    print(f"✅ Migración completada. {total_migrated} imágenes movidas a S3.")

if __name__ == "__main__":
    if AWS_ACCESS_KEY == 'TU_ACCESS_KEY':
        print("❌ Error: Debes configurar las credenciales de AWS en el script.")
    else:
        migrate_images()
