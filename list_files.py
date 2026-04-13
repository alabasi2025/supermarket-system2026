# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

for folder in ['data', 'data_clean']:
    path = rf"D:\supermarket-system\{folder}"
    if not os.path.exists(path):
        continue
    print(f"\n=== {folder}/ ===")
    for f in sorted(os.listdir(path)):
        fp = os.path.join(path, f)
        if os.path.isfile(fp):
            size = os.path.getsize(fp) // 1024
            print(f"  {f} ({size} KB)")
