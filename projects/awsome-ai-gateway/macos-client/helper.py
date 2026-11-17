"""No credentials in the package. Default stdout contains only the short-lived Gateway key."""
import os
import sys
from macclient import read_config,environment


def main():
    if sys.argv[1:]==['--self-test']:
        read_config()
        from api_key_helper.main import main as bundled_helper
        from gateway_cli_oidc.oidc_client import OIDCConfig
        print('Configuration and bundled dependencies: OK');return
    if sys.argv[1:]:raise ValueError('지원하지 않는 옵션입니다.')
    if os.geteuid()==0:raise ValueError('본인 Mac 사용자 계정으로 실행하세요. sudo/root 로그인은 지원하지 않습니다.')
    os.environ.update(environment(read_config()))
    from api_key_helper.main import main as issue_key
    issue_key(args=[],standalone_mode=False)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Gateway 도우미: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
