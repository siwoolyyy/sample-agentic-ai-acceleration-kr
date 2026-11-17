# Windows 사용자 설치 프로그램

사용자에게 전달할 파일: **`AWSomeGatewaySetup-Windows-x64.exe`**. 빌드 키트가 아니다.

## 사용자 설치

1. Claude Desktop을 먼저 설치한다.
2. `AWSomeGatewaySetup-Windows-x64.exe`를 일반 사용자 계정에서 더블클릭하고 UAC 요청을 승인한다.
3. Claude Desktop 연결 항목은 이 PC의 모든 사용자에게 회사 Gateway를 적용한다. 내용을 확인한 뒤 설치한다.
4. 완료 후 **AWSome Gateway Login**을 열고 **회사 계정 로그인**을 누른다.
5. 브라우저에서 본인 Cognito 이메일/비밀번호로 로그인한다. 비밀번호는 설치 파일에 들어 있지 않다.
6. 연결 완료 후 Claude를 완전히 종료했다가 다시 실행한다. Haiku 모델로 짧은 대화를 테스트한다.

Git·Python·터미널 명령은 사용자 PC에 필요 없다. 기존 회사 관리형 Claude 정책이 있으면 설치 프로그램은 덮어쓰기를 거부한다. 이 경우 IT 담당자가 기존 정책과 통합해야 한다.

로그인 앱은 관리자 권한으로 실행하지 않는다. 설치만 관리자 승인을 받고, 로그인/키는 본인 OS 계정에 저장한다. 시작 메뉴에서 로그인 앱을 다시 열 수 있다.

## 빌드 및 검증

별도 `build/windows-client-*` 브랜치를 push하면 Windows GitHub Actions가 실행된다. `main`이나 AWS 서버는 변경하지 않는다.

1. Windows x64 runner에서 Python과 CLI 의존성을 묶는다.
2. 레지스트리 보존·복원 등 테스트를 실행한다.
3. Inno Setup으로 설치 EXE를 생성한다.
4. 설치 마법사를 무인 실행하되 CI에서는 Desktop 정책/브라우저 로그인을 선택하지 않는다.
5. 설치된 helper/GUI의 의존성을 확인하고 제거를 검증한다.
6. 성공한 EXE와 SHA256을 `Windows-user-installer` artifact로 올린다.

현재 빌드는 코드 서명 인증서가 없는 **미서명 파일**이다. 임원 배포 전에 사내 PC의 보안 정책을 확인하고 Authenticode 서명·실제 사용자 PC 테스트를 완료한다. Windows 보안 정책을 우회하거나 백신을 끄지 않는다.

CI가 확인하는 것은 실행파일 생성·설치·의존성·제거다. 실제 사용자 브라우저 로그인, 회사 계정의 모델 호출, 사내 보안 제품과의 호환성은 사용자 PC에서 별도로 확인한다.

## 변경 범위와 제거

- 프로그램: `C:\Program Files\AWSomeGateway`
- Desktop 정책: `HKLM\SOFTWARE\Policies\Claude`
- 본인 로그인 토큰/키 캐시: 기존 CLI와 같은 `~/.gateway-cli/`
- Claude Desktop/Claude Code 자체와 사용자 파일은 설치하거나 삭제하지 않는다.

로그인 앱에서 로그아웃하고 Claude를 종료한 뒤 Windows 설정의 앱 목록에서 제거한다. 이 설치 프로그램이 넣은 정책만 복원하며, 이후 다른 관리자가 바꾼 값은 유지한다. 서버의 발급 키를 즉시 폐기하려면 관리자에게 요청한다.
