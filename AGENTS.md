# Project 작업 규칙

이 Project는 개인 학습 App이다.
기능 검토는 개인 사용과 실제 공부 흐름을 기준으로 한다.

## 1. 현재 단계

현재 단계는 R0(기술 경계 검증)의 순서 2(Wiki MCP의 Tool, Resource, Prompt와 Client 연결)를 마친 상태다.
Wiki MCP Server(stdio Child Process), Client, Service, FastAPI 엔드포인트 및 관련 검증(76개 pytest 통과)을 완료했다.
다음 작업은 docs/PROJECT_PLAN.md §6의 구현 순서 3(Page 및 Task 저장, Revision, Session 저장과 Backup을 연결한다)을 따른다.
R0의 경계 검증 없이 R1 기능을 먼저 구현하지 않는다.
단계가 바뀌면 이 절과 README.md의 상태를 함께 수정한다.

## 2. 기준 문서

| 판단 대상 | 기준 문서 |
|---|---|
| 목적, 우선순위, Release 범위, 구현 순서 | docs/PROJECT_PLAN.md |
| 기능, 사용자 제어, 완료 조건 | docs/PRD.md |
| 기술 선택, Directory, Module, 저장 및 실행 계약 | docs/ARCHITECTURE.md |
| 사용자 조작 순서 | docs/USER_FLOWS.md |
| 문서 및 답변 작성 규칙, Technical Name 정의 | docs/DOCUMENTATION_STYLE.md |
| 판단 근거 | docs/PROJECT_REVIEW.md, docs/research |

전략과 계획을 수정할 때 docs/PROJECT_PLAN.md를 먼저 확인한다.
같은 기준을 여러 문서에서 따로 관리하지 않는다.
다른 문서는 기준 문서를 참조한다.
문서의 책임 범위가 충돌하면 해당 기준을 함께 수정한다.
검토와 Research 문서는 판단 근거이며 추가 구현 약속이 아니다.
과거 문서의 Release 수량을 현재 완료 조건으로 사용하지 않는다.
일반 Project 문서는 docs에서 관리한다.
Root의 README.md와 AGENTS.md는 진입 문서와 개발 규칙이다.

## 3. 문서 및 답변 작성

전략, 구현 계획, 검토 기록, README, 사용자 답변을 작성할 때 docs/DOCUMENTATION_STYLE.md를 따른다.
설명은 한국어로 쓴다.
기술 용어와 English에서 온 표현은 English로 쓴다.
Project Technical Name은 docs/DOCUMENTATION_STYLE.md §5의 정의에 맞춘다.
ASD-STE100의 짧은 문장과 일관된 용어 원칙을 적용한다.
혼합 언어 문서를 ASD-STE100 전체 준수 문서라고 표시하지 않는다.

File Path, Code Identifier, 원래 Wiki 제목을 임의로 번역하지 않는다.
문서 작성 규칙을 App의 UI 언어 변경 지시로 해석하지 않는다.
App의 사용자 화면은 한국어를 기본으로 한다.

Project 안의 문서 Link는 상대 경로로 쓴다.
Project 밖의 원래 Wiki를 가리키는 근거 Link는 예외다.
Mermaid Source를 수정하면 같은 작업에서 SVG와 manifest.json을 다시 생성한다.

## 4. 불변 규칙

아래 규칙의 세부 내용은 괄호 안의 기준 문서를 따른다.

- 기존 Wiki는 읽기 전용으로 연결한다. Markdown 원본을 일괄 변환하거나 복제하지 않는다. (ARCHITECTURE §7)
- 기본 검색은 Keyword Search와 필요한 Section 읽기다. Embedding 및 Hybrid Search는 E1 실험이며 R1 완료 조건과 초기 Vector Database 도입으로 바꾸지 않는다. (PROJECT_PLAN §4)
- Wiki MCP는 Backend의 learning_app Package 안에 두고 별도 Process로 실행한다. (ARCHITECTURE §4, §7)
- Coding Agent는 현재 문제의 정답, 완성 제출 Code와 완성 Pseudocode를 제공하지 않는다. (PRD FR-06)
- 사용자 Python Code를 Backend에서 실행하지 않는다. (PRD FR-09)
- API Key는 Backend에서만 사용한다. (PRD NF-02)
- UI와 Chat의 변경은 같은 Service를 호출한다. (PROJECT_PLAN D-08)
- 설치물과 사용자 Database를 Project Source에 넣지 않는다. (ARCHITECTURE §13)
- 새 Framework와 Agent는 실제 필요가 있을 때 추가한다.

## 5. 작업 환경

개발 환경은 Windows와 PowerShell이다.
모든 Text File은 BOM 없는 UTF-8로 저장한다.
한글을 출력하는 명령은 UTF-8 출력 설정을 먼저 확인한다.
Project는 OneDrive 동기화 경로 안에 있다.
.venv, node_modules와 실행 중 SQLite는 동기화 충돌을 고려해서 배치한다.
실행 명령은 실제로 정한 뒤 6절에 기록한다.
기록하지 않은 명령을 추측해서 문서화하지 않는다.

## 6. 명령

| 목적 | 명령 | 상태 |
|---|---|---|
| 문서 Diagram 생성 | `node scripts/render_docs.mjs <renderer-package-directory>` | 사용 중 |
| Backend 설치 | `uv sync` (backend 디렉터리) | 사용 중 |
| Backend Test | `uv run pytest` (backend 디렉터리) | 사용 중 |
| Frontend 설치 | `npm install` (frontend 디렉터리) | 사용 중 |
| Frontend Build | `npm run build` (frontend 디렉터리) | 사용 중 |
| Backend 서버 실행 | `uv run uvicorn learning_app.api.main:app --host 127.0.0.1 --port 8000` | 사용 중 |
| Frontend 개발 서버 실행 | `npm run dev` (frontend 디렉터리) | 사용 중 |

## 7. 구현 규칙

### 7.1 Hardcoding 금지

변경 가능한 환경별 값과 사용자 Data를 Code에 직접 고정하지 않는다.
File Path, API Endpoint, Model 선택, 실행 제한과 사용자 설정은 명시한 설정으로 관리한다.
비밀값은 Environment Variable 등 지정한 비밀 설정에서 읽는다.
학습 내용과 문제 정의는 content의 File에서 읽는다.
사용자 기록은 실제 저장소에서 조회한다.
같은 설정과 업무 규칙을 여러 Module에 복사하지 않는다.
불변의 Protocol 식별자와 상태값은 의미가 분명한 Constant 또는 Enum으로 정의한다.
실제 조회와 실행 결과를 고정 응답으로 대체하지 않는다.

### 7.2 구현의 모호함 제거

구현 전에 입력, 출력, 상태 변화, 원본 Data와 책임 Module을 명확히 정한다.
검증 조건, 권한, 실패 처리와 기능의 완료 조건도 정한다.
모호한 계약을 임의의 가정, 조용한 Fallback 또는 미완성 TODO로 남기지 않는다.
기존 요구와 문서로 판단할 수 있는 부분은 결정하고 필요한 근거를 기록한다.
사용자 의도에 영향을 주며 근거로 결정할 수 없는 부분만 구체적으로 확인한다.
확인이 필요한 부분과 무관한 작업은 계속 진행한다.
외부 API와 Model의 한계는 명시하고 실제 확인한 동작과 미검증 상태를 구분한다.
모호한 부분을 숨긴 채 구현 완료로 보고하지 않는다.

### 7.3 실제 사용 가능한 Service 구현

개인 Project의 범위와 Release 순서를 지키며 실제 사용할 수 있는 흐름을 완성한다.
UI, API, Service와 저장소를 연결하고 필요한 MCP와 Model 호출을 실제로 처리한다.
Mock 화면과 고정 Data만으로 기능 완료를 판단하지 않는다.
개발용 Fixture와 예제는 실제 사용자 Data 및 실행 결과와 구분한다.
저장 성공, 실행 성공과 AI의 설명을 실제 처리 결과에 맞춰 표시한다.
오류, 취소와 연결 실패를 정상 완료로 바꾸지 않는다.
핵심 흐름은 실제 사용, 다시 열기와 필요한 실패 사례로 검증한다.
설정, 설치, 시작과 종료 절차를 실제 동작에 맞게 문서화한다.

### 7.4 의존성

새 Package는 docs/ARCHITECTURE.md §3의 선택 안에서 추가한다.
선택 밖의 Package가 필요하면 이유를 기록하고 Architecture를 먼저 수정한다.
설치 Version은 package-lock.json과 uv.lock으로 고정한다.
새 Package 기능과 API 계약은 공식 문서로 확인하고 확인 날짜를 기록한다.

### 7.5 Test

Backend의 저장, Revision, request_id, Source Version과 Tool 권한을 바꾸면 pytest를 함께 작성한다.
Browser 흐름을 바꾸면 해당 Playwright 흐름을 함께 작성하거나 갱신한다.
Test 위치는 backend/tests와 frontend/tests다.
실행하지 않은 Test를 통과했다고 보고하지 않는다.

## 8. 완료 보고

기술 선택과 실제 구현, 실행 검증을 구분해서 보고한다.
완료 보고는 다음 순서로 구분한다.

1. 구현 범위: 변경한 File과 연결한 FR ID.
2. 수행한 검증: 실제로 실행한 명령과 결과.
3. 미검증 항목: 실행하지 못한 경계와 이유.
4. 남은 제한과 다음 작업.

## 9. Commit 기록

Commit Message는 docs/DOCUMENTATION_STYLE.md를 따른다.
설명은 한국어로 쓰고 기술 용어는 English로 쓴다.
File Path와 Code Identifier는 원래 표기를 유지한다.

Commit Message는 다음 구조로 쓴다.

1. 첫 줄에 변경의 핵심을 짧은 소제목 하나로 쓴다.
2. 소제목 다음에 빈 줄 하나를 둔다.
3. 본문에 변경 내용을 자세히 쓴다.

소제목은 50자 이내로 쓴다.
소제목 끝에 마침표를 쓰지 않는다.
한 Commit에는 한 목적의 변경만 넣는다.

본문은 아래 항목을 순서대로 쓴다.
해당하지 않는 항목은 생략한다.

- 변경: 바꾼 File과 바꾼 내용.
- 이유: 변경이 필요한 근거와 연결한 FR ID 또는 기준 문서.
- 검증: 실제로 실행한 명령과 결과.
- 미검증: 실행하지 못한 경계와 이유.

본문의 한 문장은 한 판단이나 동작을 설명한다.
실행하지 않은 검증을 본문에 완료로 쓰지 않는다.

예:

```text
문서 Link를 상대 경로로 변경

변경:
- README.md와 docs의 문서 7개에서 Project 안의 절대 경로 Link 41개를 상대 경로로 바꿨다.
- Project 밖 원래 Wiki의 근거 Link 4개는 유지했다.

이유:
- AGENTS.md §3은 Project 안의 문서 Link를 상대 경로로 쓰도록 정한다.

검증:
- 상대 Link 41개가 실제 File로 연결되는 것을 Node Script로 확인했다.

미검증:
- GitHub 화면에서 Link 동작을 확인하지 않았다.
```
