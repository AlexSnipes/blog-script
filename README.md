# 📸 Sistema de Screencaps TrekCore

Dos scripts para poblar la base de datos de imágenes de Start Trek.

## 1. Scraper Continuo (`trekcore_scraper.py`)

Diseñado para ejecutarse periódicamente (cron) y monitorear series nuevas/activas.

- **Objetivo**: Series en emisión (Starfleet Academy, Strange New Worlds, etc.)
- **Ejecución**: Cronjob cada 6 horas.
- **Acción**: Busca nuevos episodios y actualiza JSONs.

```bash
python3 trekcore_scraper.py
```

## 2. Scraper Legacy (`trekcore_scraper_legacy.py`)

Diseñado para ejecutarse **UNA SOLA VEZ** para importar todo el histórico.

- **Objetivo**: Series finalizadas (TOS, TNG, DS9, VOY, ENT).
- **Ejecución**: Manual (una vez).
- **Acción**: Escanea cientos de episodios antiguos e importa sus galerías de screencaps.

```bash
python3 trekcore_scraper_legacy.py
```

## 📁 Archivos de Datos

Ambos scripts alimentan el mismo archivo de datos:

- `src/data/jsons/__screencaps.json`: Base de datos de URLs de imágenes.
- `src/data/jsons/__episodes.json`: Se actualiza agregando IDs al campo `gallery[]`.

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## ⚠️ Migración a AWS S3

Cuando el bucket S3 esté listo:
1. Las URLs en `__screencaps.json` apuntan actualmente a `trekcore.com`.
2. Se necesitará un script de migración para:
   - Descargar cada imagen.
   - Subirla a S3.
   - Actualizar la URL en el JSON.
