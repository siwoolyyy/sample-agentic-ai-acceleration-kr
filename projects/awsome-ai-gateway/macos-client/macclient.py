"""macOS paths and consent-based Claude configuration; shared authentication with Windows."""
from pathlib import Path, PurePosixPath
import plistlib
import sys
import uuid

# Both clients use the same validation and OIDC environment contract.
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parent/'windows-client'))
from clientlib import read_config as shared_read_config, environment

SUPPORT=Path('/Library/Application Support/AWSomeGateway')
PROFILE_ID='com.awsome.gateway.desktop'
BUNDLE_ID='com.awsome.gateway.login'
VERSION='0.1.1'
MODELS=['claude-haiku-5-5','claude-sonnet-5-5','claude-opus-5-5','claude-sonnet-5','claude-opus-5']


def root_dir():
    return SUPPORT if getattr(sys,'frozen',False) else SOURCE


def read_config(root=None):
    return shared_read_config(root or root_dir())


def helper_path(root=None):
    return (root or root_dir())/'helper/api-key-helper'


def profile_bytes(config):
    # Use an explicitly POSIX path even when the profile generator is unit-tested elsewhere.
    helper=PurePosixPath('/Library/Application Support/AWSomeGateway/helper/api-key-helper')
    inner=dict(PayloadType='com.anthropic.claudefordesktop',
        PayloadIdentifier=PROFILE_ID+'.settings',
        PayloadUUID=str(uuid.uuid5(uuid.NAMESPACE_DNS,PROFILE_ID+'.settings')).upper(),
        PayloadVersion=1,PayloadDisplayName='AWSome Gateway — Claude 연결',
        deploymentMode='3p',inferenceProvider='gateway',inferenceCredentialKind='helper-script',
        inferenceGatewayBaseUrl=config['gateway_url'],inferenceGatewayAuthScheme='bearer',
        inferenceCredentialHelper=str(helper),inferenceCredentialHelperTtlSec=1800,
        inferenceModels=list(config['models']))
    return plistlib.dumps(dict(PayloadType='Configuration',PayloadVersion=1,
        PayloadIdentifier=PROFILE_ID,
        PayloadUUID=str(uuid.uuid5(uuid.NAMESPACE_DNS,PROFILE_ID)).upper(),
        PayloadDisplayName='AWSome Gateway — Claude 연결',
        PayloadDescription='Claude 모델 요청을 회사 Gateway로 보냅니다. 비밀번호나 개인 키는 포함하지 않습니다.',
        PayloadScope='System',PayloadRemovalDisallowed=False,PayloadContent=[inner]))
