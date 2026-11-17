"""Build a real architecture-specific macOS app/helper/pkg on a macOS runner."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from macclient import read_config,profile_bytes,MODELS,VERSION,BUNDLE_ID

ROOT=Path(__file__).resolve().parent

def run(*args):subprocess.run([str(a) for a in args],check=True)

def main():
    if sys.platform!='darwin':raise SystemExit('A real macOS build runner is required.')
    arch=platform.machine().lower()
    if arch not in ('arm64','x86_64'):raise SystemExit('Unsupported architecture: '+arch)
    if os.environ.get('EXPECTED_ARCH',arch)!=arch:raise SystemExit('Runner/Python architecture mismatch')
    config=dict(issuer=os.environ['GATEWAY_ISSUER'],client_id=os.environ['GATEWAY_CLIENT_ID'],
        gateway_url=os.environ['GATEWAY_URL'],admin_api_url=os.environ['GATEWAY_ADMIN_API_URL'],models=MODELS)
    work=ROOT/'build';work.mkdir(exist_ok=True)
    (work/'site-config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    read_config(work)
    for script,name,gui in [('helper.py','api-key-helper',False),('login.py','AWSome Gateway Login',True)]:
        args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir',
            '--name',name,'--distpath',str(work/'frozen'),'--workpath',str(work/'pyinstaller'/name),
            '--specpath',str(work/'spec'),'--paths',str(ROOT),'--paths',str(ROOT.parent/'windows-client'),
            '--collect-submodules','gateway_cli_oidc','--collect-submodules','api_key_helper',
            '--collect-submodules','cli','--collect-data','certifi','--copy-metadata','gateway-cli']
        if gui:args+=['--windowed','--osx-bundle-identifier',BUNDLE_ID]
        run(*args,ROOT/script)
    payload=work/'payload';apps=payload/'Applications';apps.mkdir(parents=True,exist_ok=True)
    support=payload/'Library'/'Application Support'/'AWSomeGateway';support.mkdir(parents=True,exist_ok=True)
    shutil.copytree(work/'frozen/AWSome Gateway Login.app',apps/'AWSome Gateway Login.app',symlinks=True,dirs_exist_ok=True)
    shutil.copytree(work/'frozen/api-key-helper',support/'helper',symlinks=True,dirs_exist_ok=True)
    shutil.copy2(work/'site-config.json',support/'site-config.json')
    (support/'ClaudeGateway.mobileconfig').write_bytes(profile_bytes(config))
    shutil.copy2(ROOT/'uninstall.sh',support/'uninstall.sh')
    (support/'uninstall.sh').chmod(0o755)
    # Disable automatic bundle relocation: the helper/profile paths must remain deterministic.
    component_plist=work/'components.plist'
    run('pkgbuild','--analyze','--root',payload,component_plist)
    import plistlib
    components=plistlib.loads(component_plist.read_bytes())
    for c in components:c['BundleIsRelocatable']=False;c['BundleOverwriteAction']='upgrade'
    component_plist.write_bytes(plistlib.dumps(components))
    component=work/'component.pkg'
    run('pkgbuild','--root',payload,'--component-plist',component_plist,
        '--identifier','com.awsome.gateway.client','--version',VERSION,
        '--install-location','/','--ownership','recommended',component)
    distribution=work/'distribution.xml'
    distribution.write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
<title>AWSome Gateway</title>
<options customize="never" rootVolumeOnly="true" hostArchitectures="{arch}"/>
<domains enable_localSystem="true" enable_currentUserHome="false" enable_anywhere="false"/>
<welcome file="welcome.html" mime-type="text/html"/>
<conclusion file="conclusion.html" mime-type="text/html"/>
<choices-outline><line choice="client"/></choices-outline>
<choice id="client" visible="false"><pkg-ref id="com.awsome.gateway.client"/></choice>
<pkg-ref id="com.awsome.gateway.client" version="{VERSION}">component.pkg</pkg-ref>
</installer-gui-script>''')
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    package=out/f'AWSomeGatewaySetup-macOS-{arch}-v{VERSION}.pkg'
    run('productbuild','--distribution',distribution,'--resources',ROOT/'resources','--package-path',work,package)
    package.with_suffix('.pkg.sha256').write_text(hashlib.sha256(package.read_bytes()).hexdigest()+'  '+package.name+'\n')
    print('CREATED:',package)

if __name__=='__main__':main()
