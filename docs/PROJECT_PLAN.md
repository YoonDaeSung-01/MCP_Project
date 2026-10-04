# Project Plan

개정일: 2026-10-05
상태: R0 순서 1(환경, Package, Lock File, Health Check 및 Build 검증) 완료. 순서 2(Wiki MCP 연결) 대기.

이 문서는 Project의 목적, 우선순위, Release 범위와 구현 순서를 관리한다.
기능 계약은 [PRD](./PRD.md)를 따른다.
기술과 Module 계약은 [Architecture](./ARCHITECTURE.md)를 따른다.
실제 사용 순서는 [User Flow](./USER_FLOWS.md)를 따른다.
작성 규칙은 [DOCUMENTATION_STYLE](./DOCUMENTATION_STYLE.md)에 있다.

## 1. 목적

기존 Markdown Wiki를 읽고 개념을 이해하는 개인 학습 App을 만든다.
사용자는 Windows의 Browser에서 App을 사용한다.
App은 AI, Data, Backend, CS와 Algorithm 학습을 지원한다.
사용자는 Python 기초를 App에서 실습한다.
실전 Coding Test 문제 풀이와 공식 채점은 Programmers에서 진행한다.

하나의 Multi-turn Chat에서 학습, 메모, Task와 일정 관리를 요청한다.
사용자는 같은 기능을 UI에서 직접 조작할 수 있다.
채용준비에서는 공고의 요구사항과 공부할 내용을 연결한다.
개발 과정에서는 MCP, Agent, Skill, Memory, Rules, Hook, Tool과 Harness를 익힌다.

이 Project의 목표는 사용자의 실제 공부 흐름을 완성하는 것이다.
회원, 결제와 여러 사용자의 동시 편집은 현재 목표에 포함하지 않는다.
기본 시간대는 Asia/Seoul이다.

## 2. 해결할 문제와 성공 기준

| 현재 문제 | App이 제공할 결과 | 확인 방법 |
|---|---|---|
| Wiki 자료와 질문이 떨어져 있다 | 읽은 Section을 근거로 설명하고 원문을 연다 | 답변의 Source Reference에서 실제 근거를 확인한다 |
| 정의를 읽어도 적용 이유가 불분명하다 | 개념, 작은 사례와 사용 조건을 연결한다 | 사용자가 자신의 말로 설명하거나 결과를 예측한다 |
| Coding Test에서 막히면 완성 답안을 보기 쉽다 | 힌트와 관련 문법으로 직접 해결을 돕는다 | 사용자가 다음 점검과 구현을 직접 진행한다 |
| 메모와 공부할 작업을 따로 관리한다 | Page와 Task를 학습 대상에 연결한다 | Task에서 해당 자료와 메모를 다시 연다 |
| 작성 내용과 질문 Context를 잃을 수 있다 | 저장 상태와 이어서 하기를 제공한다 | App을 다시 열고 같은 내용을 사용한다 |
| MCP를 이론으로만 이해한다 | 실제 Tool, Resource와 Prompt를 사용한다 | 호출 결과와 Trace로 연결 경계를 설명한다 |

답변 수, Agent 수와 화면 수를 성공 기준으로 사용하지 않는다.
공부 시간과 Task 완료를 숙련도 점수로 바꾸지 않는다.
자료가 있다는 이유로 완성된 강의라고 표시하지 않는다.
측정하지 않은 학습 효과와 검색 개선률을 확정하지 않는다.

## 3. 확정한 방향

| ID | 결정 | 적용 이유 |
|---|---|---|
| D-01 | 기존 Wiki는 원래 Directory에서 읽기 전용으로 사용한다 | 기존 자료 관리 방식을 유지한다 |
| D-02 | Markdown을 다른 원본 형식으로 일괄 변환하지 않는다 | 별도 자료 복제와 수정 부담을 줄인다 |
| D-03 | 분야와 난이도로 Study Unit을 묶어 탐색한다 | 다음 학습 자동 추천보다 명시한 학습 공간을 제공한다 |
| D-04 | 사용자 문서는 Page로 통합한다 | 메모와 오답노트의 중복 저장 구조를 없앤다 |
| D-05 | Coding Agent는 Algorithm 학습과 정답 없는 Coding Test 도움만 담당한다 | 사용자의 직접 풀이를 유지한다 |
| D-06 | Learning, Coding, Job의 세 Role과 공통 Harness를 사용한다 | 책임을 구분하고 실행 구성을 공유한다 |
| D-07 | Supervisor는 현재 목적의 Role 또는 App 관리 경로를 선택한다 | 같은 Chat에서 학습과 명확한 변경 요청을 처리한다 |
| D-08 | UI와 Chat의 변경은 같은 Service를 사용한다 | 저장 결과와 검증 규칙을 일치시킨다 |
| D-09 | 기본 검색은 Keyword Search와 필요한 Section 읽기다 | 작은 Baseline을 먼저 실제로 사용한다 |
| D-10 | Embedding 및 Hybrid Search는 후속 비교 실험으로 진행한다 | 핵심 기능 구현을 늦추지 않고 RAG를 익힌다 |
| D-11 | 내부 Block 이동부터 구현하고 외부 Drop과 Widget Layout은 뒤에 구현한다 | 편집과 저장을 먼저 안정화한다 |
| D-12 | 선택 기술과 설치 및 실행 검증을 구분한다 | 문서 작성만으로 사용 가능 상태를 주장하지 않는다 |

검색한 자료를 답변 Context에 넣는 Baseline도 넓은 의미의 RAG다.
이 문서의 후속 RAG 실험은 Embedding과 Hybrid Search의 추가 효과를 비교하는 작업이다.
RAG Study Unit과 App의 검색 기능 실험은 별도 작업이다.

## 4. 우선순위 원칙

1. 작성 내용 보존과 실제 자료 조회를 먼저 완성한다.
2. 개념 학습, Python 기초 실습과 정답 없는 질문 흐름을 연결한다.
3. 실제 사용에서 필요한 Calendar, Planner와 채용준비를 추가한다.
4. 외부 Drag and Drop과 Layout 조작을 추가한다.
5. 안정된 Baseline을 기준으로 후속 RAG 실험을 수행한다.

E1은 R1 이후의 별도 실험이다.
R2와 R3의 완료 조건에 E1을 넣지 않는다.
실험 실행 시점은 Baseline의 사용 기록과 현재 기능의 불편을 기준으로 정한다.
실험 때문에 저장 오류와 Context 혼동의 수정을 미루지 않는다.

## 5. Release 범위

Release는 개인 사용 가능 범위의 구현 단계다.
상용 배포를 뜻하지 않는다.
아래 표에서만 현행 Release 범위를 관리한다.
FR ID의 세부 동작과 완료 조건은 PRD에 있다.

| 단계 | 구현 범위 | 완료 기준 |
|---|---|---|
| R0: 기술 경계 검증 | Windows MCP 연결, SQLite 저장, BlockNote 복원, Pyodide 실행, Gemini Tool Calling과 Multi-turn 계약 | 경계별 실제 실행 결과와 설치 Version을 기록한다 |
| R1: 학습 MVP | Wiki, Track 탐색, Page, Learning 및 Coding Chat, 기초 Python 실습, 기본 Task, 요청한 Web Search, 저장 및 복원 | 아래 R1 사용 흐름과 해당 PRD 완료 조건을 검증한다 |
| R2: 개인 학습 관리 | Calendar, Planner, Job Agent, 공고 보관, 하위 Page와 목적별 Template, 필요한 추가 Study Unit | 사용자가 직접 관리하고 Chat에서 명확히 요청할 수 있다 |
| R3: 작업 공간 조작 | 메뉴의 외부 Block Drop, Widget 이동 및 크기 변경, 저장 Layout, 통합 검색 | 세 종류의 Drag and Drop과 다시 열기를 함께 검증한다 |
| E1: 후속 RAG 실험 | 같은 Wiki와 질문으로 Keyword, Embedding, Hybrid Search 비교 | 결과와 실패 사례를 기록하고 실제 적용 여부를 결정한다 |

### R1의 구체적인 범위

- FR-01, FR-02: 제목, Alias, Tag, 본문 검색과 Wiki Viewer, Source Reference.
- FR-03, FR-04: 분야와 난이도 탐색, MCP 역할과 Hash 적용의 Study Unit 두 개.
- FR-05, FR-06: Markdown 기반 Algorithm 설명과 정답 없는 Coding Test 학습 도움.
- FR-07: 기본 Block, Code, 체크 항목, 자료 참조와 내부 Block 순서 변경.
- FR-08: 같은 Page 구조의 보조 Coding Record.
- FR-09: Hash 개수 계산과 중복 구분의 기초 Practice Problem 두 개.
- FR-10, FR-11: 공통 Session, Multi-turn, 활성 Context, Supervisor, Harness와 취소.
- FR-12: 사용자가 요청한 Web Search와 URL 읽기.
- FR-13: Task 생성, 수정, 완료 취소, 보관 및 복원과 학습 대상 연결.
- FR-20: 저장 상태, 최근 대상 복원, Backup과 Restore.

Coding Record 작성은 Chat 사용의 선행 조건이 아니다.
전용 오답 통계, 기록 자동 생성과 별도 문제 저장소는 요구하지 않는다.
초기 화면은 자료, Page, Chat의 고정된 세 영역이다.
기초 실습에서는 Code와 실제 실행 결과를 중심에 둔다.
영역 접기와 전환을 제공한다.
React-Grid-Layout을 R1 완료 조건으로 사용하지 않는다.

### 후속 범위의 기준

R2는 FR-14, FR-15, FR-16, FR-17을 연결한다.
추가 Study Unit은 실제 공부할 주제로 작성한다.
RAG와 Data Leakage는 후속 Study Unit의 후보로 유지한다.
기존 Wiki 탐색과 질문은 R1부터 여러 분야에서 사용할 수 있다.

R3는 FR-18의 외부 Drop과 Widget Layout, FR-19를 연결한다.
Page 내부 Block 이동은 FR-07로 먼저 제공한다.
추가 Library는 기존 선택으로 입력 계약을 충족하지 못할 때만 검토한다.

E1의 실험 계약은 FR-21과 Architecture의 RAG 절에 있다.
Embedding 검색을 기본값으로 바꾸는 결정은 실험 결과 이후에 한다.

## 6. 구현 순서

| 순서 | 작업 | 남길 결과 |
|---|---|---|
| 1 | 설정, Python 및 Node.js 환경, Package와 Lock File을 준비한다 | 설치 Version과 실제 시작 및 종료 절차 |
| 2 | Wiki MCP의 Tool, Resource, Prompt와 Client를 연결한다 | 실제 자료 읽기, 오류 구분과 Source Reference |
| 3 | Page 및 Task 저장, Revision, Session 저장과 Backup을 연결한다 | 저장 후 다시 열기와 충돌 및 복원 결과 |
| 4 | Pyodide의 별도 Origin 실행 영역을 검증한다 | 실행, 중단, 실패와 접근 경계의 결과 |
| 5 | Gemini Adapter와 공통 Harness를 연결한다 | Tool Call 연결, Multi-turn, 제한과 취소 결과 |
| 6 | R1 화면과 두 Study Unit 및 두 Practice Problem을 연결한다 | 자료 읽기부터 질문과 사용자 적용까지의 사용 흐름 |
| 7 | 실제 공부에 사용하고 필요한 불편을 수정한다 | 저장 손실, 잘못된 Context와 반복 조작의 사례 |
| 8 | 필요한 R2와 R3 기능을 순서대로 연결한다 | PRD와 User Flow에서 정한 동작 |
| 9 | E1의 검색 비교 실험을 수행한다 | 검색 품질, 답변 근거, 시간, 비용과 적용 판단 |

Model API를 실제로 사용할 수 없으면 그 검증은 미완료로 남긴다.
Fixture로 확인한 동작을 실제 Provider 호출 성공으로 표시하지 않는다.
R0에서 확인한 계약 없이 큰 Framework를 추가하지 않는다.

## 7. R1 사용 가능 판단

다음 흐름을 실제로 확인한다.

1. API Key가 없어도 Page, Task, Wiki 탐색과 준비된 Python Runtime을 사용한다.
2. Wiki 근거를 열고 개념을 질문한 뒤 자신의 설명을 Page에 남긴다.
3. Python 기초 문제를 실행하고 실패한 Test Case의 원인을 직접 수정한다.
4. Algorithm 질문이 실제 Markdown 근거를 사용한다.
5. Coding Test 질문이 정답 없이 개념, 문법과 다음 점검으로 이어진다.
6. 같은 Session의 후속 질문이 해당 문제와 Code Snapshot을 유지한다.
7. Role 전환과 새 Session에서 자료와 대화가 잘못 섞이지 않는다.
8. UI에서 수정한 Page와 Task를 다음 Chat이 최신 값으로 읽는다.
9. 취소, 읽기 실패, 저장 실패와 재시도의 중복 처리를 구분한다.
10. App 재시작과 검증한 Backup Restore 후 기록을 다시 연다.

세 번의 실제 사용에서 불편과 실패 사례를 남긴다.
이 횟수는 학습 효과를 통계적으로 증명하는 기준이 아니다.
오답노트 수량과 전용 통계는 완료 조건이 아니다.
세부 기능 검증은 PRD의 완료 조건을 사용한다.

## 8. 현재 제외 범위

| 제외 항목 | 이유 |
|---|---|
| 실전 문제은행, 외부 Dataset Import와 공식 채점 Server | Programmers에서 실제 문제를 푼다 |
| Programmers 계정 연결, 자동 제출과 판정 자동 수집 | 학습 도움의 목적에 필요하지 않다 |
| 정답 공개, 완성 제출 Code와 완성 Pseudocode | Coding Agent의 역할과 충돌한다 |
| Wiki 원본 편집, 일괄 Import와 전처리 변환 | 원본 Markdown을 읽기 전용으로 사용한다 |
| 자동 학습 Track, 자동 진도 및 숙련도 판정 | 사용자 선택과 실제 학습 활동을 우선한다 |
| 자동 Task와 반복 복습 일정 생성 | 사용자가 직접 요청하고 관리한다 |
| 자동 지원, Mail 전송과 상시 공고 Monitoring | 요청한 공고 분석과 수동 준비를 제공한다 |
| 여러 사용자의 Auth, 결제, Cloud 배포와 동시 편집 | 개인 Local App 범위를 유지한다 |
| Agent별 Server, 별도 Memory Database와 범용 Plugin System | 공통 Harness와 명시한 Module로 구현한다 |
| 초기 Vector Database, File Watcher와 자동 Vector Memory | Baseline을 먼저 만들고 검색을 후속 실험한다 |

## 9. 위험과 처리 기준

| 위험 | 처리 기준 | 검증할 위치 |
|---|---|---|
| 기능 확대가 실제 공부 시작을 늦춘다 | Release 범위와 제외 항목을 유지한다 | Project Plan |
| Wiki에 완성 풀이가 포함돼 있다 | Coding Context를 검토한 Concept Reference로 제한한다 | FR-05, FR-06 |
| 힌트를 모으면 전체 정답이 된다 | 앞선 안내와 현재 문제를 함께 검토한다 | FR-06, FR-10 |
| 저장과 편집이 충돌한다 | 최신 Revision과 실제 저장 결과를 확인한다 | FR-07, FR-13, NF-01 |
| Provider와 SDK 계약이 바뀐다 | 공식 문서와 R0 실행으로 확인하고 Version을 고정한다 | Architecture |
| Python Worker만으로 격리됐다고 가정한다 | 별도 Origin과 Message 검증을 함께 확인한다 | FR-09, NF-02 |
| 검색 Index가 Wiki 수정과 달라진다 | File Version과 Refresh 상태를 표시한다 | FR-01, FR-02, FR-21 |
| RAG가 항상 더 좋다고 가정한다 | 같은 조건의 Baseline과 비교하고 실패도 기록한다 | FR-21 |

## 10. 현재 상태와 문서 관리

현재 Source Directory는 비어 있다.
App Package 설정, Lock File, 시작 Script와 실제 App 기능은 아직 없다.
문서 Diagram 생성 Script는 App 기능과 별도로 관리한다.
기존 Wiki는 수정하거나 복제하지 않았다.
선택 기술과 논리 계약은 구현 기준이며 실행 성공의 증거가 아니다.

핵심 문서는 Project Plan, PRD, Architecture, User Flow의 네 개다.
이전 FINAL_PROJECT_STRATEGY와 PROJECT_STRUCTURE의 필요한 내용을 네 문서에 통합한다.
같은 Release 표와 기술 선택 표를 여러 문서에서 따로 관리하지 않는다.
검토 근거는 [PROJECT_REVIEW](./PROJECT_REVIEW.md)에 남긴다.
비교 자료는 docs/research에서 관리한다.
Research의 후보 기능은 구현 약속이 아니다.
