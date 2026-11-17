"""Run on a real Windows runner; compile offline user installer and SHA256."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from clientlib import read_config
ROOT=Path(__file__).resolve().parent

def run(*args):subprocess.run([str(a) for a in args],check=True)

def main():
    if sys.platform!='win32':raise SystemExit('A Windows build runner is required.')
    stage=ROOT/'build/stage';stage.mkdir(parents=True,exist_ok=True)
    config=dict(issuer=os.environ['GATEWAY_ISSUER'],client_id=os.environ['GATEWAY_CLIENT_ID'],
        gateway_url=os.environ['GATEWAY_URL'],admin_api_url=os.environ['GATEWAY_ADMIN_API_URL'],
        models=['claude-haiku-5-5','claude-sonnet-5-5','claude-opus-5-5','claude-sonnet-5','claude-opus-5'])
    (stage/'site-config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    read_config(stage)
    for script,name,folder,gui in [('helper.py','api-key-helper','helper',False),('login.py','GatewayLogin','login',True)]:
        args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir',
            '--name',name,'--distpath',str(ROOT/'build/frozen'),
            '--workpath',str(ROOT/'build/work'/name),'--specpath',str(ROOT/'build/spec'),
            '--paths',str(ROOT),'--collect-submodules','gateway_cli_oidc',
            '--collect-submodules','api_key_helper','--collect-submodules','cli',
            '--collect-data','certifi','--copy-metadata','gateway-cli']
        if gui:args+=['--windowed']
        run(*args,ROOT/script)
        shutil.copytree(ROOT/'build/frozen'/name,stage/folder,dirs_exist_ok=True)
    run(stage/'helper/api-key-helper.exe','--self-test')
    iscc=shutil.which('ISCC.exe')
    for p in [Path('C:/Program Files (x86)/Inno Setup 6/ISCC.exe'),Path('C:/Program Files/Inno Setup 6/ISCC.exe')]:
        if not iscc and p.is_file():iscc=str(p)
    if not iscc:raise SystemExit('Inno Setup compiler was not found')
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    run(iscc,'/DStage='+str(stage),'/DOut='+str(out),ROOT/'setup.iss')
    exe=out/'AWSomeGatewaySetup-Windows-x64-v0.1.1.exe'
    exe.with_suffix('.exe.sha256').write_text(hashlib.sha256(exe.read_bytes()).hexdigest()+'  '+exe.name+'\n')
    print('CREATED:',exe)

if __name__=='__main__':main()
