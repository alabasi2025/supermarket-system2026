"""
سكربت تحميل خريطة صنعاء للعمل أوفلاين
Sanaa Map Tiles Downloader
"""

import os
import math
import time
import sys

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import ssl

# إعدادات صنعاء
SANAA_CENTER = (15.3694, 44.1910)
SANAA_BOUNDS = {
    'north': 15.42,
    'south': 15.30,
    'east': 44.25,
    'west': 44.12
}

# مستويات التكبير - تقليل للسرعة
ZOOM_LEVELS = [13, 14, 15, 16]

# مجلد حفظ البلاطات
TILES_DIR = 'static/map_tiles'

# مصادر البلاطات المتعددة - جرب مصادر مختلفة
TILE_SERVERS = [
    'https://tile.openstreetmap.de/{z}/{x}/{y}.png',
    'https://tiles.wmflabs.org/osm/{z}/{x}/{y}.png',
    'https://a.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def lat_lng_to_tile(lat, lng, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lng + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

def get_tiles_for_bounds(bounds, zoom):
    min_x, max_y = lat_lng_to_tile(bounds['south'], bounds['west'], zoom)
    max_x, min_y = lat_lng_to_tile(bounds['north'], bounds['east'], zoom)
    
    tiles = []
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            tiles.append((zoom, x, y))
    return tiles

def download_tile(z, x, y, server_idx=0):
    url = TILE_SERVERS[server_idx % len(TILE_SERVERS)].format(z=z, x=x, y=y)
    save_path = os.path.join(TILES_DIR, str(z), str(x))
    file_path = os.path.join(save_path, f'{y}.png')
    
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return True
    
    os.makedirs(save_path, exist_ok=True)
    
    try:
        if HAS_REQUESTS:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return True
        else:
            req = urllib.request.Request(url, headers=HEADERS)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                with open(file_path, 'wb') as f:
                    f.write(response.read())
            return True
    except Exception as e:
        return False
    return False

def main():
    print('=' * 50, flush=True)
    print('  تحميل خريطة صنعاء أوفلاين', flush=True)
    print('=' * 50, flush=True)
    
    os.makedirs(TILES_DIR, exist_ok=True)
    
    total_tiles = 0
    for zoom in ZOOM_LEVELS:
        tiles = get_tiles_for_bounds(SANAA_BOUNDS, zoom)
        total_tiles += len(tiles)
    
    print(f'اجمالي البلاطات: {total_tiles}', flush=True)
    
    downloaded = 0
    failed = 0
    current = 0
    
    for zoom in ZOOM_LEVELS:
        tiles = get_tiles_for_bounds(SANAA_BOUNDS, zoom)
        print(f'\nمستوى {zoom}: {len(tiles)} بلاطة', flush=True)
        
        for i, (z, x, y) in enumerate(tiles):
            current += 1
            
            if download_tile(z, x, y, i):
                downloaded += 1
                print(f'  [{current}/{total_tiles}] OK: {z}/{x}/{y}', flush=True)
            else:
                failed += 1
                print(f'  [{current}/{total_tiles}] FAIL: {z}/{x}/{y}', flush=True)
            
            time.sleep(0.2)
    
    print('\n' + '=' * 50, flush=True)
    print(f'تم: {downloaded} | فشل: {failed}', flush=True)
    print('=' * 50, flush=True)

if __name__ == '__main__':
    main()
