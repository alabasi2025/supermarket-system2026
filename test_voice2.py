import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()

# login
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True)

# stocktake page
r=s.get(base+'/stocktake', verify=False)
print('Status:', r.status_code)
print('Voice recording UI:', 'existingRecordBtn' in r.text)
print('toggleRecording function:', 'toggleRecording' in r.text)
print('Voice note input:', 'existingVoiceNote' in r.text)
