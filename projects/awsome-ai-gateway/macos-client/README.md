# macOS 사용자 설치 프로그램

Windows와 동일한 Cognito 브라우저 로그인 → 개인 Gateway 키 자동 발급·갱신 로직이다. 사용자의 Mac에는 Git·Python이 필요 없다. Claude Desktop은 별도 설치 제품이다.

## 설치

1. Apple 메뉴 → 이 Mac에 관하여에서 칩/프로세서를 확인한다. Apple M 시리즈는 `arm64.pkg`, Intel은 `x86_64.pkg`를 받는다.
2. `AWSomeGatewaySetup-macOS-...-v0.1.1.pkg`를 실행해 설치한다.
3. 응용 프로그램의 **AWSome Gateway Login**을 연다.
4. **Claude 연결 설정 승인**을 누르고 시스템 설정의 일반 → 기기 관리(또는 프로파일)에서 **AWSome Gateway — Claude 연결**을 검토·승인한다. 최초 한 번 필요하다.
5. 로그인 앱에서 **회사 계정 로그인**을 누르고 브라우저에서 본인 Cognito 이메일·비밀번호로 로그인한다.
6. Claude를 완전히 종료했다가 다시 열고 Haiku 5.5로 새 대화를 테스트한다.

개발자 메뉴에서 도우미 경로·Gateway 주소·모델 목록을 직접 입력하지 않는다. 연결 프로파일은 시스템 범위이며 회사 Gateway를 사용하도록 Claude를 설정한다. 기존 회사 관리 프로파일이 있는 Mac은 IT 담당자와 먼저 조율한다. 설치 프로그램은 기존 프로파일을 삭제하거나 승인 절차를 우회하지 않는다.

## 구성

| 대상 | 경로 |
|---|---|
| 로그인 앱 | `/Applications/AWSome Gateway Login.app` |
| 실행 도우미 | `/Library/Application Support/AWSomeGateway/helper/api-key-helper` |
| 공개 연결값 | `/Library/Application Support/AWSomeGateway/site-config.json` |
| 승인할 프로파일 | `/Library/Application Support/AWSomeGateway/ClaudeGateway.mobileconfig` |
| 사용자 로그인 토큰/키 캐시 | 기존 CLI와 같은 본인 `~/.gateway-cli/` |

비밀번호·개인 키는 패키지와 프로파일에 넣지 않는다. 로그인은 root가 아닌 본인 사용자 계정으로 진행한다. 지원 모델은 Windows v0.1.1과 같은 Haiku 5.5, Sonnet 5·5.5, Opus 5·5.5다. 실제 사용은 서버의 사용자/팀 권한·예산을 따른다.

## 빌드·검증

본인 포크의 `build/macos-client-*` 브랜치에 push하면 GitHub Actions가 실제 `macos-15`(arm64), `macos-15-intel`(x86_64)에서 각각 빌드한다. 아키텍처가 맞지 않으면 실패한다.

프로파일·인증 계약 테스트 → PyInstaller 앱/도우미 빌드 → pkg 생성 → 실제 설치 → 설치된 도우미와 Tcl/Tk 의존성 검사 → 제거를 확인한다. CI에서는 사용자 브라우저 로그인이나 프로파일 승인을 자동 실행하지 않는다.

현재 빌드는 Developer ID 서명·공증 자격증명이 없는 테스트 패키지다. 정식 배포는 IT가 서명·공증을 적용하고 실제 Mac의 로그인·프로파일 적용·대화를 검증해야 한다. Gatekeeper나 조직 보안 정책을 끄지 않는다. 차단되면 IT 담당자에게 승인/서명된 배포본을 요청한다.

## 제거

1. 시스템 설정에서 이 패키지의 AWSome Gateway Claude 프로파일을 제거한다. 다른 프로파일은 건드리지 않는다.
2. 로그인 앱에서 로그아웃하고 Claude를 종료한다.
3. IT 담당자가 다음을 실행하고 확인 문구에 `REMOVE`를 입력한다.

```bash
sudo '/Library/Application Support/AWSomeGateway/uninstall.sh'
```

이 패키지의 앱·도우미·설정 파일만 삭제한다. 개인 Claude 데이터와 다른 사용자 토큰은 삭제하지 않는다. 서버 키를 즉시 폐기하려면 Gateway 관리자에게 별도로 요청한다.
