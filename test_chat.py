import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()

# login
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True)

# chat page
r=s.get(base+'/chat', verify=False)
print('Chat page:', r.status_code)

# get csrf from chat page
csrf2=re.search(r'id="csrfToken" value="([^"]+)"', r.text).group(1)

# send message
from requests_toolbelt import MultipartEncoder
fd={'room':'general', 'message':'مرحبا، هذا اختبار للدردشة!'}
r=s.post(base+'/api/chat/send', data=fd, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Send:', r.status_code, r.json())

# get messages
r=s.get(base+'/api/chat/messages?room=general&after=0', headers={'X-CSRF-Token': csrf2}, verify=False)
print('Messages:', r.status_code)
data=r.json()
for m in data.get('messages', []):
    print(f"  [{m['created_at']}] {m['sender_name']}: {m['message']}")
