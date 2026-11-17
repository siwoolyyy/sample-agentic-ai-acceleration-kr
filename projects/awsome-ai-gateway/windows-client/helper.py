import sys
from clientlib import read_config, environment


def main():
    import os
    if sys.argv[1:] == ['--install-desktop']:
        from clientlib import install_policy
        install_policy();return
    if sys.argv[1:] == ['--remove-desktop']:
        from clientlib import remove_policy
        remove_policy();return
    if sys.argv[1:] == ['--self-test']:
        read_config()
        from api_key_helper.main import main as bundled_helper
        from gateway_cli_oidc.oidc_client import OIDCConfig
        print('Configuration and bundled dependencies: OK');return
    if sys.argv[1:]:raise ValueError('지원하지 않는 옵션입니다.')
    os.environ.update(environment(read_config()))
    from api_key_helper.main import main as issue_key
    issue_key(args=[],standalone_mode=False)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Gateway 도우미: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
