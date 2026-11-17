"""Windows client configuration; no passwords, VKs or refresh tokens in the package."""
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlparse

POLICY_KEY = r'SOFTWARE\Policies\Claude'


def root_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent


def read_config(root=None):
    data = json.loads(((root or root_dir())/'site-config.json').read_text(encoding='utf-8-sig'))
    required = {'issuer', 'client_id', 'gateway_url', 'admin_api_url', 'models'}
    if set(data) != required:
        raise ValueError('설치 연결 설정이 올바르지 않습니다. IT 담당자에게 문의하세요.')
    for k in ('issuer','gateway_url','admin_api_url'):
        u = urlparse(data[k])
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('HTTPS 회사 연결 주소가 필요합니다: '+k)
        data[k] = data[k].rstrip('/')
    if not isinstance(data['client_id'],str) or not data['client_id'].strip():
        raise ValueError('Cognito Client ID가 필요합니다.')
    if not isinstance(data['models'],list) or not data['models'] or any(not isinstance(m,str) or not m.strip() for m in data['models']):
        raise ValueError('등록된 모델 이름이 필요합니다.')
    return data


def environment(config):
    return dict(OIDC_ISSUER_URL=config['issuer'], OIDC_CLIENT_ID=config['client_id'],
        OIDC_AUDIENCE=config['client_id'], OIDC_REDIRECT_PORT='8090',
        OIDC_SCOPES='openid profile email', ADMIN_API_URL=config['admin_api_url'])


def policy(config, root=None):
    return dict(deploymentMode='3p', inferenceProvider='gateway',
        inferenceCredentialKind='helper-script', inferenceGatewayBaseUrl=config['gateway_url'],
        inferenceGatewayAuthScheme='bearer',
        inferenceCredentialHelper=str((root or root_dir())/'helper/api-key-helper.exe'),
        inferenceCredentialHelperTtlSec=1800, inferenceModels=json.dumps(config['models']))


def registry_read(w, name):
    try:
        with w.OpenKey(w.HKEY_LOCAL_MACHINE,POLICY_KEY,0,w.KEY_READ|w.KEY_WOW64_64KEY) as key:
            v,t = w.QueryValueEx(key,name); return [v,t]
    except FileNotFoundError:
        return None


def registry_write(w, name, value):
    with w.CreateKeyEx(w.HKEY_LOCAL_MACHINE,POLICY_KEY,0,w.KEY_SET_VALUE|w.KEY_WOW64_64KEY) as key:
        if value is None:
            try:w.DeleteValue(key,name)
            except FileNotFoundError:pass
        else:w.SetValueEx(key,name,0,value[1],value[0])


def save_state(path, state):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(path)


def install_policy(root=None):
    import winreg as w
    root=root or root_dir(); state_file=root/'desktop-policy-state.json'
    values={k:[v,w.REG_DWORD if isinstance(v,int) else w.REG_SZ] for k,v in policy(read_config(root),root).items()}
    state=json.loads(state_file.read_text()) if state_file.exists() else None
    if state:
        for k,v in state['applied'].items():
            if registry_read(w,k)!=v:
                raise ValueError('다른 관리자가 변경한 Claude 정책은 덮어쓰지 않습니다.')
        before=state['before']
    else:
        try:
            with w.OpenKey(w.HKEY_LOCAL_MACHINE,POLICY_KEY,0,w.KEY_READ|w.KEY_WOW64_64KEY) as key:
                if w.QueryInfoKey(key)[1]:raise ValueError('기존 Claude 관리형 정책이 있습니다. IT 담당자에게 문의하세요.')
        except FileNotFoundError:pass
        before={k:None for k in values}
    rollback={k:registry_read(w,k) for k in values}
    previous=state_file.read_bytes() if state_file.exists() else None
    save_state(state_file,dict(before=before,applied=values))
    try:
        for k,v in values.items():registry_write(w,k,v)
    except Exception:
        for k,v in rollback.items():registry_write(w,k,v)
        if previous is None:state_file.unlink(missing_ok=True)
        else:state_file.write_bytes(previous)
        raise


def remove_policy(root=None):
    import winreg as w
    state_file=(root or root_dir())/'desktop-policy-state.json'
    if not state_file.exists():return
    state=json.loads(state_file.read_text())
    for k,v in state['applied'].items():
        # Do not erase later policy changes made by another administrator.
        if registry_read(w,k)==v:registry_write(w,k,state['before'].get(k))
    state_file.unlink()
