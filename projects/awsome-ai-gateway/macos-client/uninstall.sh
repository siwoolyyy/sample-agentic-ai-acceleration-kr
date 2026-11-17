#!/bin/sh
set -eu
if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' 'IT 담당자: sudo로 실행하세요.' >&2
  exit 1
fi
printf '%s\n' '먼저 시스템 설정에서 AWSome Gateway Claude 프로파일을 제거하세요.'
printf '%s\n' '본인 계정의 로그인 앱에서 로그아웃하고 Claude를 완전히 종료하세요.'
printf '%s' '위 절차를 완료했으면 REMOVE를 입력하세요: '
read -r answer
[ "$answer" = REMOVE ] || exit 1
# Exact installer-owned paths only. Personal Claude files and other profiles are untouched.
rm -rf '/Applications/AWSome Gateway Login.app' '/Library/Application Support/AWSomeGateway/helper'
rm -f '/Library/Application Support/AWSomeGateway/site-config.json' \
      '/Library/Application Support/AWSomeGateway/ClaudeGateway.mobileconfig' \
      '/Library/Application Support/AWSomeGateway/uninstall.sh'
rmdir '/Library/Application Support/AWSomeGateway' 2>/dev/null || true
pkgutil --forget com.awsome.gateway.client
