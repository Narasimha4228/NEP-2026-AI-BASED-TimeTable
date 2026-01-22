import json
from urllib import request, error
url='http://127.0.0.1:8000/api/v1/auth/register'
data=json.dumps({'email':'chilamkurinarasimhareddy2@gmail.com','name':'NARASIMHA REDDY CHILAMKURI','password':'Reddy@1234'}).encode('utf-8')
req=request.Request(url,data=data,headers={'Content-Type':'application/json'})
try:
    resp=request.urlopen(req)
    print('STATUS',resp.status)
    print(resp.read().decode())
except error.HTTPError as e:
    print('STATUS', e.code)
    print(e.read().decode())
except Exception as e:
    print('ERR',e)
