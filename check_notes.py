import sys
sys.path.insert(0, 'H:/Codex/.codex/skills/Auto-Redbook-Skills-main/vendor/xhs_publish_runtime')
from dotenv import load_dotenv
load_dotenv('H:/Codex/.codex/skills/Auto-Redbook-Skills-main/.env')
import os
from apis.xhs_creator_apis import XHS_Creator_Apis
from xhs_utils.xhs_creator import XHSCreatorAuth
ck = os.getenv('XHS_CREATOR_COOKIE')
au = XHSCreatorAuth.from_cookie(ck)
api = XHS_Creator_Apis(au).bootstrap()
ok, msg, res = api.get_posted_notes_page(page=0, tab=0)
print('OK', ok, msg)
ns = res.get('data').get('notes')
print('count', len(ns))
for n in ns[:3]:
    print(n.get('display_title'), n.get('id'), n.get('time'))
au.close()
