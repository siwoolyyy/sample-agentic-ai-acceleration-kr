import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import contextlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import clientlib

class Key:
    def __enter__(self):return self
    def __exit__(self,*args):pass

class FakeRegistry:
    HKEY_LOCAL_MACHINE=0
    KEY_READ=1;KEY_WOW64_64KEY=2;KEY_SET_VALUE=4
    REG_SZ=1;REG_DWORD=4
    def __init__(self,values=None,fail=None):self.values=copy.deepcopy(values or {});self.fail=fail
    def OpenKey(self,*args):
        if not self.values:raise FileNotFoundError()
        return Key()
    def CreateKeyEx(self,*args):return Key()
    def QueryInfoKey(self,key):return (0,len(self.values),0)
    def QueryValueEx(self,key,name):
        if name not in self.values:raise FileNotFoundError()
        return self.values[name]
    def SetValueEx(self,key,name,reserved,kind,value):
        if name==self.fail:self.fail=None;raise PermissionError('test registry failure')
        self.values[name]=[value,kind]
    def DeleteValue(self,key,name):
        if name not in self.values:raise FileNotFoundError()
        del self.values[name]

class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'Program Files/Gateway';self.root.mkdir(parents=True)
        self.config=dict(issuer='https://cognito.example.com/pool',client_id='test-client',gateway_url='https://gateway.example.com',admin_api_url='https://gateway.example.com',models=['haiku-test'])
        (self.root/'site-config.json').write_text(json.dumps(self.config))
    def tearDown(self):self.temp.cleanup()
    def test_config_rejects_secrets_and_insecure_addresses(self):
        for key,value in [('password','secret'),('gateway_url','http://insecure.example.com'),('gateway_url','https://user:pass@example.com'),('models',[])]:
            data=dict(self.config);data[key]=value;(self.root/'site-config.json').write_text(json.dumps(data))
            with self.subTest(key=key),self.assertRaises(ValueError):clientlib.read_config(self.root)
    def test_existing_policy_is_not_overwritten(self):
        w=FakeRegistry({'bootstrapUrl':['https://organization.example.com',1]});before=copy.deepcopy(w.values)
        with patch.dict(sys.modules,{'winreg':w}),self.assertRaises(ValueError):clientlib.install_policy(self.root)
        self.assertEqual(w.values,before);self.assertFalse((self.root/'desktop-policy-state.json').exists())
    def test_install_upgrade_restore_preserves_newer_admin_changes(self):
        w=FakeRegistry()
        with patch.dict(sys.modules,{'winreg':w}):
            clientlib.install_policy(self.root);clientlib.install_policy(self.root)
            self.assertEqual(w.values['inferenceCredentialHelperTtlSec'],[1800,4])
            self.assertEqual(json.loads(w.values['inferenceModels'][0]),['haiku-test'])
            self.assertIn('Program Files',w.values['inferenceCredentialHelper'][0])
            w.values['inferenceGatewayBaseUrl']=['https://new-admin.example.com',1]
            with self.assertRaises(ValueError):clientlib.install_policy(self.root)
            clientlib.remove_policy(self.root)
        self.assertEqual(w.values,{'inferenceGatewayBaseUrl':['https://new-admin.example.com',1]})
    def test_failed_install_rolls_back(self):
        w=FakeRegistry(fail='inferenceCredentialHelper')
        with patch.dict(sys.modules,{'winreg':w}),self.assertRaises(PermissionError):clientlib.install_policy(self.root)
        self.assertEqual(w.values,{});self.assertFalse((self.root/'desktop-policy-state.json').exists())
    def test_environment_is_specific_to_company(self):
        env=clientlib.environment(self.config)
        self.assertEqual(env['OIDC_AUDIENCE'],'test-client')
        self.assertEqual(env['OIDC_SCOPES'],'openid profile email')
        self.assertNotIn('AWS_ACCESS_KEY_ID',env)
    def test_helper_has_token_only_stdout(self):
        spec=importlib.util.spec_from_file_location('client_helper',ROOT/'helper.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        def issue_key(**kwargs):
            self.assertEqual(kwargs,dict(args=[],standalone_mode=False));print('test-token-not-real')
        stub=types.ModuleType('api_key_helper.main');stub.main=issue_key
        with patch.dict(sys.modules,{'api_key_helper':types.ModuleType('api_key_helper'),'api_key_helper.main':stub}),patch('sys.argv',['helper']),patch.object(module,'read_config',return_value=self.config),patch.dict('os.environ',{},clear=True):
            out=io.StringIO()
            with contextlib.redirect_stdout(out):module.main()
            self.assertEqual(out.getvalue(),'test-token-not-real\n')

if __name__=='__main__':unittest.main()
