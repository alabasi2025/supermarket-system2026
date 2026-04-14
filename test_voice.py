import requests, urllib3
urllib3.disable_warnings()
r=requests.get('https://localhost:5555/stocktake', verify=False, timeout=15)
print('Status:', r.status_code)
print('Voice recording UI:', 'existingRecordBtn' in r.text)
print('toggleRecording function:', 'toggleRecording' in r.text)
