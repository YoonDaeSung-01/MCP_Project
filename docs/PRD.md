# PRD

개정일: 2026-10-04
상태: 제품 요구사항 확정. 아래 완료 조건은 아직 실행 검증 결과가 아니다.

이 문서는 기능, 사용자 제어, 제한과 완료 조건을 관리한다.
Release 범위는 [Project Plan](./PROJECT_PLAN.md)에서만 관리한다.
저장, API와 실행 계약은 [Architecture](./ARCHITECTURE.md)를 따른다.
사용 순서는 [User Flow](./USER_FLOWS.md)에 있다.
작성 규칙은 [DOCUMENTATION_STYLE](./DOCUMENTATION_STYLE.md)를 따른다.

## 1. 사용자와 사용 상황

주 사용자는 기술 Stack을 공부하고 취업을 준비하는 개인 사용자다.
사용자는 Markdown Wiki를 이미 보유한다.
사용자는 Browser에서 학습, 메모와 Task를 직접 관리한다.
실전 Coding Test는 Programmers에서 진행한다.

| 사용 상황 | 필요한 결과 |
|---|---|
| 개념을 읽어도 이해가 부족하다 | 선택한 수준의 설명과 근거 |
| 공부할 분야와 난이도를 선택한다 | 해당 Study Unit과 관련 Wiki |
| Algorithm의 동작을 이해한다 | 검토한 Wiki 개념 구간과 작은 사례 |
| Coding Test에서 특정 부분이 막힌다 | 정답 없는 힌트, 문법과 다음 점검 |
| 내용을 직접 정리한다 | Block 기반 Page와 원문 참조 |
| 공부할 작업과 시간을 관리한다 | 직접 수정하는 Task와 Calendar |
| 채용공고를 보고 준비 방향을 정한다 | 공고 근거와 사용자가 명시한 경험의 비교 |

## 2. 제품 원칙

AI 답변은 사용자가 직접 이해하고 적용하도록 돕는다.
일반 질문마다 Quiz, 기록 작성과 진도 등록을 강제하지 않는다.
자료 조회와 AI 설명, 실제 실행 결과를 구분한다.
명확한 변경 요청은 검증 후 실행한다.
AI가 제안한 여러 변경은 미리보기에서 선택해 적용한다.
일반적인 단일 변경에 반복 승인을 요구하지 않는다.

기본 화면 언어는 한국어다.
문서의 English Technical Name 규칙을 UI 언어 변경 지시로 사용하지 않는다.
MCP는 AI Backend의 연결 구성이다.
독립 MCP 학습 Track을 서비스의 중심으로 만들지 않는다.
MCP 설명 Study Unit은 실제 연결을 이해하는 작은 검증 예제로 사용한다.

## 3. 사용자 공간

| 공간 | 표시할 내용 | 사용자 조작 |
|---|---|---|
| Wiki | 읽기 전용 원문과 Source Reference | 검색, Section 선택, 참조 열기 |
| Study | 분야, 난이도와 Study Unit | 단원 선택, 수준 변경, 활동 실행 |
| Page | 사용자가 작성하는 Block 문서 | 작성, 직접 수정, 내부 Block 이동 |
| Practice | Python Code와 실제 실행 결과 | 실행, Test Case 실행, 중단, Code 수정 |
| Chat | Session, 활성 Context와 처리 결과 | 질문, Context 해제, 취소, Session 관리 |
| Task | 작업과 선택적 마감 및 자료 연결 | 생성, 수정, 완료 취소, 보관, 복원 |
| Calendar 및 Planner | 시간 배치와 공부 가능 시간 | Event와 설정의 직접 수정 |
| Job | 공고 근거, 준비 후보와 수동 지원 상태 | 검색 요청, 보관, 분석, 상태 수정 |

현재 제공 시점은 Project Plan을 따른다.
제공 전 기능을 사용 가능 기능으로 표시하지 않는다.
처음부터 Layout 설정을 완료해야 공부할 수 있게 만들지 않는다.

## 4. 기능 요구사항

각 FR의 완료 조건은 해당 기능을 구현할 때 검증한다.
전체 기능이 첫 Release의 완료 조건은 아니다.

### FR-01. Wiki 검색

사용자는 Collection과 검색어로 기존 Markdown을 찾는다.
제목, Alias, Tag와 본문을 검색한다.
제목과 Alias의 일치를 본문 일치보다 우선한다.
기본 검색은 Keyword Search다.
검색 Index의 Refresh 상태와 Collection 오류를 구분한다.

완료 조건:

- 제목, Alias, 한국어 표현과 빈 결과를 실제 자료로 확인한다.
- 읽기 실패를 정상적인 검색 결과 없음으로 표시하지 않는다.
- 일부 Collection이 실패하면 검색 범위의 누락을 표시한다.
- 제한된 검색에서 찾지 못한 내용을 Wiki 전체에 없다고 단정하지 않는다.

### FR-02. Wiki Viewer와 Source Reference

Wiki 원문은 Page Editor와 별도 Viewer에서 읽는다.
선택한 Heading과 Section을 질문에 연결할 수 있다.
답변의 Source Reference는 실제 읽은 자료를 연다.
File Version이 바뀌면 변경 상태를 표시한다.
지원하지 않는 Obsidian 표현은 원문을 보존한다.

완료 조건:

- Frontmatter, Code Block과 같은 이름의 Heading을 구분한다.
- Wiki Link를 허용 Note ID로 해결하거나 연결 실패를 표시한다.
- Source Reference의 원문 구간과 실제 답변 근거가 맞는다.
- Raw HTML과 외부 Script를 실행하지 않는다.
- App은 원래 Wiki File을 수정하지 않는다.

### FR-03. Track과 Study Unit

Track은 분야와 난이도로 묶은 Study Unit의 탐색 공간이다.
처음에는 별도 사용자 Track Database를 만들지 않는다.
사용자는 기초, 응용, 심화 수준을 선택한다.
상위 수준을 잠그지 않는다.
Study Unit은 목표, 선행 개념, 자료, 활동과 확인 기준을 가진다.

완료 조건:

- 작성한 Study Unit과 일반 Wiki Note를 구분해서 표시한다.
- 선택한 분야와 난이도로 단원을 연다.
- Wiki의 learning_level과 Programmers 난이도를 자동 대응시키지 않는다.
- 설명, 예측, 실행, 수정과 새 사례 적용 중 필요한 활동을 제공한다.
- 자료를 열었다는 이유로 학습 완료나 숙련도를 판정하지 않는다.
- 질문만으로 새 Track과 진도 기록을 생성하지 않는다.

### FR-04. Learning Agent

Learning Agent는 AI, Data, Backend와 일반 CS 개념을 설명한다.
사용자가 선택한 수준과 질문 목적에 맞춘다.
설명은 핵심 개념, 작은 사례와 사용 조건을 포함한다.
이해 확인을 요청하면 짧은 확인 질문을 제공한다.

완료 조건:

- 필요한 Wiki Section을 실제로 읽고 Source Reference를 연결한다.
- Wiki 내용, Model의 추가 설명과 Web Search 근거를 구분한다.
- 없는 근거와 자료 사이의 차이를 알린다.
- 일반 질문에 Quiz와 선행 학습 절차를 강제하지 않는다.
- 피드백은 맞는 부분, 수정할 부분과 필요한 선행 개념을 구분한다.
- 답변 길이와 Task 완료로 이해 수준을 추정하지 않는다.

### FR-05. Coding Agent의 Algorithm 학습

사용자가 정리한 Markdown Wiki를 기본 자료로 사용한다.
외부 문제 Dataset과 학습 API를 가져오지 않는다.
개념, 선행 개념, 작은 입력의 상태와 Complexity의 이유를 설명한다.
질문에 필요한 검토된 Concept Reference만 사용한다.

완료 조건:

- Algorithm 설명이 실제 Markdown 근거와 연결된다.
- 자료가 없는 주제를 있는 것처럼 설명하지 않는다.
- 현재 Coding Test의 답안이 되지 않는 독립된 작은 사례를 사용한다.
- 완성 풀이와 정답이 있는 확인 항목을 기본 Context에 넣지 않는다.
- Coding Agent의 Tool은 Wiki 읽기와 검색으로 제한된다.
- Coding Agent가 Python 실행, Page 저장과 일정 변경을 직접 수행하지 않는다.

### FR-06. Coding Agent의 Coding Test 학습 도움

사용자가 막힌 부분이나 문법을 질문할 때 도움을 제공한다.
문제 요약과 Code는 선택 입력이다.
자료가 부족한 경우에만 필요한 조건이나 막힌 지점을 짧게 묻는다.
사용자가 직접 판단하고 구현할 다음 점검을 안내한다.

완료 조건:

- 문법 질문은 다른 작은 상황의 예제로 직접 설명한다.
- 오류는 확인한 오류와 원인 후보로 구분한다.
- 실행하지 않은 반례를 실제 실행 결과로 표시하지 않는다.
- 현재 문제의 정답, 완성 제출 Code, 전체 풀이 순서와 완성 Pseudocode를 제공하지 않는다.
- 사용자 Code 전체를 수정 답안으로 다시 작성하지 않는다.
- 정답 요청, 반복 압박과 Role 전환에도 같은 제한을 유지한다.
- 앞선 힌트와 후속 안내를 합쳐 전체 답안을 제공하지 않는다.
- Hint Level에 정답 공개 단계를 두지 않는다.
- 문법 예제의 Code Block을 일괄 금지하지 않는다.
- Prompt와 Hook만으로 의미상의 정답 유출을 완벽하게 차단했다고 표시하지 않는다.

### FR-07. Page 편집과 저장

사용자 문서는 Block JSON을 원본으로 저장한다.
제목, 기본 Block, Code, 체크 항목과 자료 참조를 지원한다.
사용자는 내부 Block의 순서를 바꿀 수 있다.
저장 상태는 편집 내용의 실제 저장 결과를 표시한다.

완료 조건:

- 한글 입력과 Block 이동 후 저장 및 다시 열기가 동작한다.
- 저장 실패 시 작성 내용을 유지한다.
- 오래된 Revision의 저장으로 최신 내용을 덮어쓰지 않는다.
- Editor Undo와 저장본 복원을 구분한다.
- Markdown Export를 원형 복원용 Backup으로 표시하지 않는다.

### FR-08. 보조 Coding Record

Coding Record는 오답이나 배운 내용을 남기는 Page의 종류다.
처음에는 제목과 문제 URL만으로 저장한다.
접근, 내 Code, 실패 입력, 원인, 직접 수정한 Code와 배운 점은 선택 항목이다.
질문과 Algorithm 학습에 기록 작성을 요구하지 않는다.

완료 조건:

- 일반 Page와 같은 저장 및 복원 기능을 사용한다.
- 같은 URL을 등록하면 기존 기록을 먼저 보여주고 자동 병합하지 않는다.
- 외부 판정과 복습 상태는 사용자가 직접 입력한다.
- AI 설명과 App Test Case 결과가 외부 판정을 덮어쓰지 않는다.
- 문제 전문을 대량 수집하지 않는다.
- 기록 반영과 복습 Task 생성은 사용자의 명확한 요청으로 처리한다.

### FR-09. 기초 Python Practice

App은 작은 Python Function의 기초 실습을 제공한다.
Code Draft를 저장한 뒤 Browser의 Python Runtime에서 실행한다.
사용자는 실행, Test Case 실행과 중단을 선택한다.
Test Case는 실제 Program이 비교한다.

완료 조건:

- 제공한 입력과 Return Value의 비교 규칙을 명시한다.
- 준비 실패, 실행 오류, Test Case 실패와 시간 초과를 구분한다.
- 중단 후 Code Draft가 남고 다음 실행을 준비할 수 있다.
- Attempt에 Code Snapshot, Problem Version과 Runtime Version을 남긴다.
- 표시는 제공 Test Case의 통과 또는 실패로 제한한다.
- AI 설명과 실제 실행 결과를 구분한다.
- 별도 Origin과 Message 검증이 App Data 접근을 제한한다.
- 사용자 Code를 Backend에서 exec하지 않는다.
- 공식 채점, 숨겨진 Test Case와 통과 보장을 제공하지 않는다.

### FR-10. 공통 Multi-turn Chat

같은 Session은 필요한 앞선 대화와 활성 Context를 사용한다.
Role 전환은 같은 Session을 유지한다.
현재 자료, Study Unit, Page와 Code의 참조 대상을 입력 영역에 표시한다.
사용자는 참조 대상을 해제할 수 있다.

완료 조건:

- 새 Session, 이전 Session 열기와 Session 삭제가 동작한다.
- Role별 별도 대화 기록을 만들지 않는다.
- 같은 Session에서 필요한 후속 질문의 대상을 유지한다.
- 새 Session에 다른 Session의 활성 Context를 전달하지 않는다.
- Page와 Task는 다음 요청에서 최신 저장값을 조회한다.
- Code 질문은 해당 Turn의 Code Snapshot을 사용한다.
- 다른 문제로 이동하면 이전 문제의 Code와 조건을 섞지 않는다.
- 오래된 대화를 확인하지 못하면 기억하는 것처럼 답하지 않는다.
- Session 삭제로 연결 Page와 Task를 삭제하지 않는다.

### FR-11. Supervisor와 Harness

Supervisor는 현재 요청의 명시한 목적을 우선한다.
UI와 Session Context는 생략한 대상을 보완한다.
학습은 필요한 Role로 연결한다.
명확한 Page, Task와 일정 변경은 App 관리 경로로 연결한다.
Harness는 모든 AI 실행의 제한과 검증을 관리한다.

완료 조건:

- 명확한 요청마다 별도 분류 Model을 먼저 호출하지 않는다.
- 모호한 목적이나 대상만 짧게 확인한다.
- Supervisor가 Agent의 최종 답변을 다시 작성하지 않는다.
- 복합 요청은 필요한 경우에만 최대 두 Role을 순서대로 연결한다.
- Role별 Tool 허용 목록을 실행 전에 검사한다.
- 명백히 무관한 질문에는 지원 범위를 안내한다.
- 선행 수학, 통계, 설치와 오류 해결은 학습 관련 요청으로 처리한다.
- 인사와 App 사용법을 허용한다.
- 수동 Page 및 Task 조작에 Scope Check Model을 호출하지 않는다.
- 제한 초과와 취소를 정상 완료로 표시하지 않는다.

### FR-12. 요청 기반 Web Search

기본 자료 모드는 Wiki다.
사용자가 검색을 요청하거나 웹 포함 모드를 선택하면 공개 자료를 검색한다.
기술 자료는 공식 문서와 논문을 우선한다.
채용 자료는 회사의 공식 공고를 우선한다.
Coding Agent에는 Web Search Tool을 직접 제공하지 않는다.

완료 조건:

- 이미 요청한 검색에 같은 승인을 다시 요구하지 않는다.
- 실제 URL과 확인한 자료를 답변에 연결한다.
- 읽기 실패와 확인하지 못한 내용을 표시한다.
- 저장한 URL을 자동으로 분석하지 않는다.
- 비공개 Code와 개인 정보 전체를 Search Query에 넣지 않는다.
- 검색 실패가 Page 편집과 Task 관리를 막지 않는다.

### FR-13. Task 관리

사용자는 해야 할 작업과 선택적 마감을 직접 관리한다.
자료, Study Unit과 Page를 Task에 연결할 수 있다.
UI와 명확한 Chat 요청은 같은 저장 기능을 사용한다.

완료 조건:

- 생성, 수정, 완료, 완료 취소, 보관과 복원이 동작한다.
- 마감이 없어도 저장할 수 있다.
- 연결 대상에서 해당 자료나 Page를 다시 연다.
- 재시도한 같은 변경으로 Task가 중복 생성되지 않는다.
- 복습 Task는 사용자의 요청으로만 생성한다.
- Task 완료를 개념 숙련이나 외부 문제 통과로 바꾸지 않는다.

### FR-14. Calendar

Event는 실제 배치한 시작과 종료 시간을 가진다.
사용자는 Event를 생성, 수정, 이동하고 삭제한다.
Task를 시간에 배치해도 Task의 마감은 유지한다.

완료 조건:

- 시작보다 늦은 종료 시간과 시간대를 검증한다.
- 시간 겹침을 표시하고 사용자가 배치를 판단한다.
- Event 이동과 길이 변경 후 실제 저장값을 보여준다.
- Event 삭제로 연결 Task를 삭제하지 않는다.
- 외부 Calendar 동기화와 App 종료 후 알림을 구현 완료로 표시하지 않는다.

### FR-15. Planner

사용자는 목표, 공부 가능 시간과 선택한 Task의 예상 시간을 설정한다.
Planner는 선택한 작업의 시간 배치를 돕는다.
시간 정보가 없는 작업을 AI가 임의의 시간으로 채우지 않는다.

완료 조건:

- 총 배치 시간, 가능 시간과 겹침을 비교한다.
- AI 제안은 생성 전 미리보기에서 선택해 적용한다.
- 새 Study Unit과 반복 일정을 자동 생성하지 않는다.
- 미완료 작업은 사용자가 재배치한다.
- 날짜와 시간을 직접 바꿀 수 있다.

### FR-16. Job Agent와 채용준비

사용자는 공고 URL 또는 본문으로 분석을 시작한다.
검색 요청에는 직무, 경력 조건과 지역을 사용한다.
Job Agent는 필수, 우대, 경력과 확인한 마감을 구분한다.
사용자의 경험은 직접 제공한 설명과 선택한 자료만 사용한다.

완료 조건:

- 요구사항에 원문 URL 또는 제공 본문 근거를 연결한다.
- 본문 분석 시각과 실제 모집 상태 확인 시각을 구분한다.
- 미확인 마감과 모집 상태를 만들어 내지 않는다.
- Wiki 보유와 Task 완료를 숙련이나 경력으로 추정하지 않는다.
- 확인한 경험, 준비 후보와 추가 확인 사항을 구분한다.
- 준비 후보는 처음에 중요한 항목 최대 세 개로 좁힌다.
- 학습 연결은 실제 존재하는 Wiki와 Study Unit을 사용한다.
- 관심, 준비, 지원, 면접, 결과의 상태를 사용자가 직접 관리한다.
- 자동 적합도 점수, 합격 예측과 자동 지원을 제공하지 않는다.

### FR-17. 하위 Page와 Template

사용자는 Page를 계층으로 정리한다.
개념 정리, Coding Record와 공고 준비의 Template을 선택할 수 있다.
Template은 같은 Page 저장 구조를 사용한다.

완료 조건:

- 하위 Page 이동과 다시 열기가 동작한다.
- 순환하는 부모 관계를 저장하지 않는다.
- Template 선택이 기존 Page 내용을 조용히 덮어쓰지 않는다.
- 범용 Database, Formula와 Plugin 구조를 만들지 않는다.

### FR-18. 세 종류의 Drag and Drop

조작은 내부 Block 이동, 메뉴에서 Page로 Block 추가, Widget Layout 이동으로 구분한다.
Widget은 기존 Page, Task와 Calendar를 참조한다.
Layout은 문서 내용과 별도로 저장한다.

완료 조건:

- Editor Handle과 Widget Handle의 조작이 충돌하지 않는다.
- 메뉴 Drop은 지정한 Block을 한 번만 추가한다.
- Widget 이동, 크기 변경과 Layout 복원이 동작한다.
- Widget을 닫아도 원본 Page, Task와 Event를 삭제하지 않는다.
- 기본 Layout으로 돌아갈 수 있다.
- 이동 메뉴와 직접 추가 등 Drag를 쓰지 않는 대체 조작을 제공한다.
- Calendar 시간 이동과 다른 Drag 조작의 충돌을 검증한다.

### FR-19. 통합 검색

Wiki, Page, Task와 보관한 공고를 종류별로 찾는다.
같은 Data를 새 저장소에 복제하지 않는다.

완료 조건:

- 결과 종류와 실제 대상을 구분해서 연다.
- 읽기 실패를 숨기지 않는다.
- 검색 결과를 여는 동작으로 기록과 완료 상태를 바꾸지 않는다.

### FR-20. 저장 상태, 이어서 하기와 Backup

사용자는 최근 학습 대상과 저장한 내용을 다시 연다.
Backup은 App의 저장 Data와 연결 관계를 보존한다.
Markdown Export는 자료 이동용 형식이다.

완료 조건:

- Page, Code Draft, Task와 Session을 재시작 후 다시 연다.
- 저장 중, 저장 완료와 저장 실패를 구분한다.
- 검증한 Backup을 App 종료 상태에서 Restore한다.
- Schema가 맞지 않거나 손상된 Backup을 적용하지 않는다.
- 실패한 Restore로 기존 Database를 덮어쓰지 않는다.
- 기존 Wiki와 API Key는 App Backup에 포함하지 않는다.
- Restore 후 Wiki 설정과 Source Reference 상태를 확인한다.

### FR-21. 후속 RAG 비교 실험

이 기능은 기본 Release의 필수 조건이 아니다.
Baseline이 안정된 뒤 Embedding과 Hybrid Search를 비교한다.
Markdown 원본은 수정하지 않는다.
추가 Index는 다시 만들 수 있는 파생 Data다.

실험 완료 조건:

- 실제 학습 질문 15~20개와 기대하는 Note 및 Section을 정한다.
- 문서 집합, Model, Prompt와 Context 예산을 같게 유지한다.
- 검색 성공, 답변 근거, 없는 자료의 처리, 시간과 확인 가능한 비용을 비교한다.
- 생성, 수정, 삭제한 Wiki에 대한 Index 갱신을 확인한다.
- Coding Agent의 Concept Reference 제한을 검색 이전부터 유지한다.
- 검색 실패, 잘못된 근거 선택과 답변 해석 오류를 구분한다.
- 결과에 따라 기본 검색 적용, 제한 적용 또는 실험 유지로 결정한다.
- 측정하지 않은 개선률을 문서에 적지 않는다.

## 5. 공통 품질 요구사항

| ID | 요구사항 | 완료 조건 |
|---|---|---|
| NF-01 | Data 보존과 변경 일관성 | Revision, Transaction과 request_id로 충돌 및 중복을 구분한다 |
| NF-02 | Local 접근 경계 | API Key를 Backend에만 두고 Runtime과 Wiki 접근 범위를 검증한다 |
| NF-03 | 결과의 근거 | 출처, AI 설명, 실제 실행과 사용자 입력 판정을 구분한다 |
| NF-04 | 실패와 취소 표시 | 오류 종류와 이미 완료한 변경을 실제 결과로 표시한다 |
| NF-05 | 사용자 제어 | 직접 수정, Context 해제, 취소와 필요한 대체 조작을 제공한다 |
| NF-06 | 설정과 실제 실행 | 변경 가능한 값을 설정에서 읽고 Mock을 실제 완료로 사용하지 않는다 |
| NF-07 | 비용과 실행 제한 | 설정한 제한을 적용하고 Provider가 반환한 사용량만 표시한다 |
| NF-08 | 기능 간 독립성 | Model과 MCP 오류가 Page 및 Task의 수동 조작을 막지 않는다 |

응답 시간과 학습 효과의 목표 수치는 아직 측정하지 않았다.
Architecture의 초기 제한은 조정 가능한 실행 설정이다.
기술 선택의 성공 여부는 해당 Release에서 실제로 검증한다.
