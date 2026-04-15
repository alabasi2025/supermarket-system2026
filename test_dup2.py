# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)
r = s.get(base+'/stocktake/requests', verify=False)
# Check if orange badge appears
print('Orange badge:', 'bg-orange-100' in r.text)
print('مكرر text:', r.text.count('مكرر'))
# Find duplicate count badge
import re as re2
dup_count = re2.findall(r'مكررة.*?(\d+)', r.text)
print('Dup count found:', dup_count[:5])
