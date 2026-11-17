import contextlib
import importlib.util
import io
import json
from pathlib import Path
import plistlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import macclient

class MacClientTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.config=dict(issuer='https://cognito.example.com/pool',client_id='test-client',gateway_url='https://gateway.example.com',admin_api_url='https://gateway.example.com',models=list(macclient.MODELS))
        (self.root/'site-config.json').write_text(json.dumps(self.config))
    def tearDown(self):self.temp.cleanup()
    def test_validation_and_auth_contract_match_windows(self):
        from clientlib import environment as windows_environment
        self.assertEqual(macclient.read_config(self.root),self.config)
        self.assertEqual(macclient.environment(self.config),windows_environment(self.config))
        self.assertEqual(macclient.environment(self.config)['OIDC_REDIRECT_PORT'],'8090')
    def test_profile_is_system_scoped_but_user_removable(self):
        p=plistlib.loads(macclient.profile_bytes(self.config))
        self.assertEqual(p['PayloadScope'],'System')
        self.assertFalse(p['PayloadRemovalDisallowed'])
        inner=p['PayloadContent'][0]
        self.assertEqual(inner['PayloadType'],'com.anthropic.claudefordesktop')
        self.assertEqual(inner['inferenceModels'],self.config['models'])
        self.assertIsInstance(inner['inferenceModels'],list)
        self.assertEqual(inner['inferenceCredentialKind'],'helper-script')
        self.assertEqual(inner['inferenceCredentialHelper'],'/Library/Application Support/AWSomeGateway/helper/api-key-helper')
        self.assertEqual(inner['inferenceModels'][0],'claude-haiku-5-5')
        self.assertNotIn('inferenceGatewayApiKey',inner)
    def test_profile_uuid_is_stable_for_upgrades(self):
        one=plistlib.loads(macclient.profile_bytes(self.config));two=plistlib.loads(macclient.profile_bytes(self.config))
        self.assertEqual(one['PayloadUUID'],two['PayloadUUID'])
        self.assertEqual(one['PayloadContent'][0]['PayloadUUID'],two['PayloadContent'][0]['PayloadUUID'])
    def test_config_rejects_bundled_secrets(self):
        self.config['password']='do-not-bundle'
        (self.root/'site-config.json').write_text(json.dumps(self.config))
        with self.assertRaises(ValueError):macclient.read_config(self.root)
    def test_frozen_app_uses_support_folder_not_root_user_home(self):
        with patch.object(sys,'frozen',True,create=True):
            self.assertEqual(macclient.root_dir(),Path('/Library/Application Support/AWSomeGateway'))
    def test_helper_reuses_cli_with_token_only_stdout(self):
        spec=importlib.util.spec_from_file_location('mac_helper',ROOT/'helper.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        def issue(**kwargs):
            self.assertEqual(kwargs,dict(args=[],standalone_mode=False));print('test-token-only')
        stub=types.ModuleType('api_key_helper.main');stub.main=issue
        with patch.dict(sys.modules,{'api_key_helper':types.ModuleType('api_key_helper'),'api_key_helper.main':stub}),patch('sys.argv',['helper']),patch.object(module,'read_config',return_value=self.config),patch('os.geteuid',return_value=501),patch.dict('os.environ',{},clear=True):
            out=io.StringIO()
            with contextlib.redirect_stdout(out):module.main()
            self.assertEqual(out.getvalue(),'test-token-only\n')
    def test_root_helper_cannot_create_personal_login(self):
        spec=importlib.util.spec_from_file_location('mac_helper_root',ROOT/'helper.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with patch('sys.argv',['helper']),patch('os.geteuid',return_value=0),self.assertRaises(ValueError):module.main()
    def test_reject_linux_cross_compilation(self):
        spec=importlib.util.spec_from_file_location('mac_build',ROOT/'build.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with patch('sys.platform','linux'),self.assertRaises(SystemExit):module.main()

if __name__=='__main__':unittest.main()
