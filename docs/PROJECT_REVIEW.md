# 개인 Project 검토와 개선 기록

작성일: 2026-10-04
검토 대상: 구현 전 계획, 기술 선택, 학습 흐름, 기존 Wiki의 대표 구간.
결과: 목적은 유지한다. Algorithm 학습과 정답 없는 학습 도움에 집중한다.

현재 Project에는 계획 문서와 구현 전 Directory 구조가 있다.
따라서 아래 내용은 Code Bug 목록이 아니다.
계획의 구현 부담, 실패 가능성, 빠진 계약을 검토한 결과다.
실제 성능과 API 호환성을 측정한 결과도 아니다.

## 1. 핵심 판단

이 Project는 기존 Wiki를 다시 찾고 실습하기 위한 수단이다.
MCP를 직접 사용하는 경험도 핵심 목적이다.
기능을 모두 완성하기 전까지 공부를 시작하지 못하는 계획은 이 목적과 맞지 않는다.

이전 계획의 첫 Release에는 11개 기능 묶음이 있었다.
Study Unit 8개와 Practice Problem 6개도 조건이었다.
Calendar, Job Agent, 외부 Drag and Drop까지 같은 완료 조건에 포함했다.
이 수량과 연결 범위는 사용자 수가 한 명이어도 개발과 검토 부담을 만든다.

R1은 MCP와 Hash 학습 흐름으로 줄였다.
Study Unit은 2개, Practice Problem은 2개다.
다른 분야의 Wiki 탐색과 질문은 R1에도 제공한다.
Calendar, 채용준비, 세 종류의 Drag and Drop 목표는 유지한다.
연결 시점을 R2와 R3으로 옮겼다.

이후 사용자는 실전 문제를 Programmers에서 풀기로 정했다.
Coding Agent는 Markdown Wiki의 Algorithm 학습과 정답 없는 Coding Test 학습 도움만 담당한다.
Coding Record는 선택적으로 사용하는 보조 Page다.
외부 문제 수집과 실전 채점 환경의 구현 부담을 제거한다.
현재 범위의 기준은 [Project Plan](./PROJECT_PLAN.md)이다.

## 2. 항목별 판단과 반영

| 항목 | 우선순위 | 확인한 문제 또는 예상 부담 | 반영한 개선 |
|---|---|---|---|
| 첫 Release 범위 | 높음 | 여러 기능의 완성이 실제 사용을 지연시킨다 | 작은 R1과 후속 Release로 분리했다 |
| 학습 내용 작성 | 높음 | 8개 단원의 설명과 활동 검토가 선행 작업이 된다 | 2개 검증 단원으로 시작한다 |
| 학습 품질 | 높음 | 답변과 자료를 모아도 이해가 늘었다고 보장할 수 없다 | 설명, 예측, 실행, 수정의 관찰 기준을 둔다 |
| 실전 문제 풀이 | 높음 | 외부 문제 수집과 채점 구현이 목표 공부를 늦춘다 | Programmers에서 풀고 App에서 힌트와 문법을 확인한다 |
| 문제 기록 | 중간 | 기록이 학습 Chat의 선행 조건이 될 수 있다 | 기존 Page의 보조 기능으로 제공한다 |
| Agent 책임 | 높음 | 학습 안내와 기록 및 일정 변경이 한 Role에 섞일 수 있다 | Coding Agent는 두 학습 역할과 읽기 Tool만 사용한다 |
| 정답 제공 | 높음 | 완성 Code와 Pseudocode가 직접 풀이를 대신할 수 있다 | 공개 단계를 제거하고 Rules와 출력 검증을 적용한다 |
| 결과의 신뢰성 | 높음 | AI 검토와 작은 Test Case 통과를 외부 판정으로 혼동할 수 있다 | 외부 결과는 사용자 입력으로 유지한다 |
| Agent 구성 | 중간 | 분류와 답변 재작성의 추가 호출이 생길 수 있다 | Role 설정과 공통 Harness를 사용한다 |
| Multi-turn | 높음 | 대화 저장과 Model Context 전달의 계약이 불명확했다 | 공통 Session, Message, 최신 값 조회를 명시했다 |
| Drag and Drop | 높음 | Editor, Widget, Calendar의 입력 처리가 충돌할 수 있다 | 내부 Block 순서 변경을 먼저 제공한다 |
| Markdown 복원 | 높음 | 변환 중 Block과 연결 정보가 손실될 수 있다 | Backup과 Export를 분리했다 |
| Python 실행 | 높음 | Worker가 접근 경계 전체를 만들지 않는다 | 다른 Origin과 최소 접근 검사를 유지한다 |
| 힌트 Context | 높음 | 기존 Hash 자료에 완성 풀이가 있다 | 검토한 개념 구간만 기본 Context로 사용한다 |
| 저장 구조 | 중간 | Page와 Note, 범용 Undo가 중복 설계를 만든다 | Page로 통합하고 필요한 복구만 구현한다 |
| Web Search | 중간 | 외부 공고 접근과 Provider Metadata가 불안정할 수 있다 | 요청 기반 검색과 실패 표시를 둔다 |
| Local 시작 | 중간 | 여러 Runtime 준비가 일상 사용의 부담이 될 수 있다 | 한 개의 실행 진입점과 오류 분리를 계획했다 |
| 문서 일관성 | 중간 | 여러 문서의 첫 Release 조건이 다를 수 있다 | 현행 기준을 하나로 정했다 |

높음은 첫 공부 흐름이나 저장 Data에 영향을 줄 수 있다는 뜻이다.
중간은 개발 부담이나 사용 불편을 만들 수 있다는 뜻이다.
점수와 예상 개발 기간은 계산하지 않았다.

## 3. 실제 자료에서 확인한 내용

### Hash 자료의 풀이 공개

[기존 Hash Wiki Note](C:/Users/yds67/OneDrive/Desktop/workspace/Cowork-HQ/20_Vault/알고리즘/02_해시_dict_set.md:26)에는 count_items의 완성 Code가 있다.
같은 문서에는 직접 확인 활동의 답도 있다.
문서 전체를 Coding Agent에 보내면 Hint Level의 목적과 충돌할 수 있다.

R1은 허용 Note ID와 Section ID를 직접 지정한다.
Coding Agent의 기본 Context에서는 기준 풀이를 제외한다.
풀이 공개 단계는 제공하지 않는다.
정답을 요청해도 개념, 문법과 확인 방법을 안내한다.
Prompt만으로 정답 공개를 완벽하게 막는다고 설명하지 않는다.

### Wiki 형식과 난이도

[MCP Wiki Note](C:/Users/yds67/OneDrive/Desktop/workspace/Cowork-HQ/20_Vault/AI-IT용어/wiki/03_응용/MCP.md)에는 Frontmatter, Callout, Wiki Link가 있다.
RAG 자료에서도 Wiki Link를 확인했다.
일반 Markdown과 모든 Obsidian 표현의 동작이 같다고 가정할 수 없다.

read_note가 전달한 원문은 별도 Wiki Viewer에 표시한다.
사용자 Page Editor로 자동 변환하지 않는다.
지원하지 않는 형식은 원문을 보존한다.
필요한 Wiki Link의 대상만 Note ID로 해결한다.

MCP와 Data Leakage 자료의 learning_level은 8-9다.
이 값을 App의 기초, 응용, 심화로 자동 대응시키지 않는다.
새 Study Unit의 목표와 활동으로 난이도를 정한다.

### SDK와 Protocol

MCP Wiki Note는 SDK Version과 Protocol Revision의 차이를 설명한다.
구현 계획도 두 값을 구분해야 한다.
SDK의 major version만 보고 연결 절차를 직접 작성하지 않는다.
선택 SDK가 실제 지원하는 연결을 R0에서 확인한다.

이 검토는 모든 Wiki Note를 읽은 결과가 아니다.
대표 문서의 구간과 형식을 확인한 결과다.
Wiki 전체의 사실 정확성과 검색 품질은 아직 검증하지 않았다.

## 4. 기술 선택의 판단

React, FastAPI, SQLite 조합은 현재 요구에 맞는다.
다른 Framework로 교체할 근거는 없다.
선택한 기능을 검증할 수 있는 작은 예제를 먼저 만든다.

BlockNote와 React-Grid-Layout은 책임이 다르다.
둘을 함께 선택해도 입력 충돌과 저장 계약은 App이 해결해야 한다.
R1은 고정 Layout과 기본 Block 편집으로 시작한다.

BlockNote는 Markdown 변환의 정보 손실을 설명한다.
JSON은 편집 내용 보존에 사용한다.
SQLite Backup은 App의 연결 상태 보존에 사용한다.
Markdown Export는 복원용 Backup으로 표시하지 않는다.
[BlockNote Markdown 문서](https://www.blocknotejs.org/docs/features/import/markdown)

Pyodide는 Browser에서 Python을 실행할 수 있다.
JavaScript와 연결할 수도 있다.
따라서 Worker 선택만으로 App 접근이 차단됐다고 판단하지 않는다.
[Pyodide 환경 문서](https://pyodide.org/en/stable/usage/faq.html)

개인 사용의 주된 실패는 무한 실행, 큰 출력, 준비 실패, 작성 내용 손실이다.
실행 시간과 출력 크기를 제한하고 Code Draft를 먼저 저장한다.
API Key와 Wiki File은 실행 영역에 주지 않는다.
별도 Server Judge와 Container Pool은 만들지 않는다.

Wiki Viewer에는 react-markdown과 remark-gfm을 추가한다.
기존 Markdown을 읽는 기능에 필요하다.
이는 문서 편집 기능을 새로 만드는 선택이 아니다.
Raw HTML을 활성화하지 않는다.
[react-markdown 공식 저장소](https://github.com/remarkjs/react-markdown)

## 5. Multi-turn 변경

사용자는 같은 Session에서 앞선 대화를 기억하기를 요청했다.
이 요구는 R1의 필수 기능으로 반영했다.
상세 계약은 [Architecture](./ARCHITECTURE.md)의 Multi-turn 절에 있다.

- SQLite는 Session과 Message를 보존한다.
- Harness는 필요한 대화와 Session Context를 Model에 전달한다.
- Agent 전환은 같은 Session을 사용한다.
- 새 Session은 이전 대화의 활성 Context를 사용하지 않는다.
- Task와 Event는 실제 최신 저장값을 다시 읽는다.
- Code 질문은 해당 Turn의 Code Snapshot을 참조한다.

Model API는 Interactions API로 정했다.
store=false를 사용하고 App이 대화를 관리한다.
SDK의 임시 Chat 객체나 Provider의 대화 ID만으로 복원을 처리하지 않는다.
Provider가 요구하는 Tool Call 연결 정보는 보존한다.
[Gemini Interactions API 문서](https://ai.google.dev/gemini-api/docs/interactions-overview)

대화 저장과 무제한 Context 전송은 다르다.
오래된 내용은 해당 Session에서 다시 읽을 수 있게 한다.
자동 Summary와 Vector Memory는 초기 구현에 추가하지 않는다.
문서만으로 Multi-turn 동작을 검증했다고 보고하지 않는다.

## 6. 개인 Project에서 유지하는 최소 조건

다음 항목은 사용자 수가 한 명이어도 필요하다.

- 저장 실패와 복원 실패를 확인한다.
- API Key를 Browser에 보내지 않는다.
- App에서 사용자 Python을 직접 exec하지 않는다.
- 실제 실행 결과와 AI 설명을 구분한다.
- 사용자 입력의 외부 채점 결과와 AI의 검토 결과를 구분한다.
- 기존 Wiki는 읽기 전용으로 사용한다.
- Chat 변경과 UI 변경이 같은 Service를 사용한다.
- 같은 요청의 반복으로 Task를 중복 생성하지 않는다.

다음 항목은 현재 필요하지 않다.

- 여러 사용자의 Auth와 권한 Model
- 결제와 회원 관리
- 분산 Lock과 Event Sourcing
- 상시 공고 Monitoring
- Agent별 Server와 Model Deployment
- 범용 Plugin과 Hook 등록 Framework
- 강의 자동 생성과 숙련도 자동 평가
- 실전 문제은행, 대량 문제 수집과 외부 채점 환경 복제
- Programmers 계정 연결, 자동 제출과 결과 자동 수집

## 7. Coding Practice 전략 변경

Programmers를 실제 문제 풀이 공간으로 사용한다.
App은 Python 기초 실행과 학습 도움을 제공한다.
한 App에서 모든 문제를 풀어야 한다는 조건을 제거한다.
이 판단은 개인 Project의 공부 목적과 사용자가 선택한 흐름에 근거한다.

Coding Agent는 두 학습 역할로 한정한다.
Algorithm 학습은 사용자가 정리한 Markdown Wiki를 MCP로 읽어 설명한다.
외부 개념 Dataset과 문제 API를 추가하지 않는다.
Coding Test 학습 도움은 막힌 부분의 질문에 힌트와 관련 문법을 제공한다.
사용자가 현재 문제의 판단과 구현을 직접 진행한다.

완성 답안, 전체 풀이 순서와 완성 Pseudocode는 제공하지 않는다.
다른 Role과 반복 질문을 통해 같은 답안을 제공하지 않도록 검토한다.
일반 개념과 문법은 별도의 작은 예제로 설명할 수 있다.
Prompt만으로 정답 유출을 완벽하게 막았다고 보고하지 않는다.

Coding Record는 기존 Page의 종류다.
새 문서 저장소와 기록 담당 Agent를 추가하지 않는다.
오답노트가 없어도 학습 질문을 할 수 있다.
사용자는 문제 Link부터 저장하고 필요한 항목을 나중에 채운다.
내 접근, Code와 배운 내용을 직접 수정할 수 있다.
실패 입력을 모르면 원인 후보와 추가 확인 질문을 남긴다.

Code가 포함된 질문은 해당 Turn의 Code Snapshot으로 검토한다.
문제 원문을 읽지 못하면 그 사실을 알린다.
확인하지 않은 제약과 채점 결과를 만들어 내지 않는다.
복습 완료를 외부 문제 통과로 바꾸지 않는다.
Coding Agent에 기록 쓰기, 실행과 일정 변경 Tool을 제공하지 않는다.
사용자가 요청한 기록과 일정 변경은 같은 App Service의 관리 경로로 처리한다.

기초 Python Runtime은 유지한다.
작은 예제로 개념을 적용하고 결과를 확인하는 데 필요하다.
stdin과 stdout의 지원은 후속 Release의 필수 조건에서 뺐다.
Exercism, MBPP와 외부 문제 API의 조사 결과는 참고 기록으로 남긴다.
현재 Release에는 해당 자료의 Import를 요구하지 않는다.

기록을 많이 남기는 것 자체를 학습 목표로 삼지 않는다.
힌트와 문법을 이해한 뒤 사용자가 직접 문제에 적용하는지 확인한다.
자동 복습 일정과 학습 점수 System도 초기 구조에 추가하지 않는다.

## 8. 학습 사용 후의 검토 기준

R1을 사용한 뒤 다음 내용을 확인한다.

1. Markdown의 Algorithm 설명과 질문의 학습 안내를 실제 공부에 적용했는가.
2. 사용자가 답변의 근거를 열어 확인했는가.
3. 기초 Test Case나 외부 문제의 확인한 실패 원인을 설명할 수 있는가.
4. 후속 질문에서 같은 대상과 Hint Level을 유지했는가.
5. 다시 시작했을 때 작성 내용과 학습 대상을 복원했는가.
6. 반복한 수동 작업 중 실제로 줄여야 할 것이 무엇인가.
7. 복습한 Algorithm을 Programmers 재도전에 적용할 수 있는가.
8. 정답을 대신 받지 않고 사용자가 다음 확인과 구현을 진행했는가.

별도 Analytics System을 설치하지 않는다.
사용자가 남긴 Page와 오류 기록으로 먼저 확인한다.
개발 기간과 기능 수만으로 학습 효과를 판정하지 않는다.

## 9. Agent 역할 검토와 개선

검토 대상은 세 Agent의 책임, 답변 기준, Context와 Tool 권한이다.
Coding Agent의 역할은 Algorithm 학습과 Coding Test 학습 도움으로 유지했다.
Agent 수와 기술 Stack을 늘리지 않았다.
현재 Release 범위는 Project Plan에서만 관리한다.

| 대상 | 현재 계획의 빈틈 또는 예상 문제 | 반영한 개선 | 판단 이유 |
|---|---|---|---|
| Learning Agent | 일반 학습과 Algorithm 학습의 경계가 불분명하다 | 일반 기술 개념을 담당하고 Algorithm 질문은 Coding Agent로 연결한다 | 역할 중복과 일관되지 않은 설명을 줄인다 |
| Learning Agent | 설명과 학습 피드백의 형식이 넓게만 정의됐다 | 난이도에 맞춘 개념, 작은 사례와 구체적 피드백을 제공한다 | 자료 요약만으로 학습 도움을 끝내지 않는다 |
| Learning Agent | 확인 질문이 모든 답변의 선행 조건이 될 수 있다 | 일반 질문은 바로 설명하고 이해 확인은 요청할 때 제공한다 | 사용자가 원하는 설명을 먼저 받는다 |
| Learning Agent | Wiki와 최신 사실의 검증을 혼동할 수 있다 | 읽은 근거와 추가 설명을 구분하고 자료 부족과 불일치를 표시한다 | 작성 상태와 사실 검증을 구분한다 |
| Coding Agent | Algorithm 설명과 문제 풀이 도움의 안내 방식이 같다 | 같은 Role에서 algorithm과 coding_test 목적을 구분한다 | 개념 설명은 충분히 하고 현재 답안은 완성하지 않는다 |
| Coding Agent | 완성 Code를 숨겨도 문서의 다른 구간에서 풀이가 드러날 수 있다 | 확인 항목의 답과 문제별 풀이도 Context에서 제외한다 | Section 제목만으로 내용을 판단하지 않는다 |
| Coding Agent | 후속 힌트를 모으면 전체 풀이가 될 수 있다 | 앞선 힌트를 확인하고 다른 개념 설명과 사용자 적용으로 이어 간다 | Multi-turn에서도 직접 해결하는 목적을 유지한다 |
| Job Agent | 공고 요약과 실제 준비 내용의 연결 기준이 부족하다 | 필수, 우대와 미확인 항목을 구분하고 중요한 준비 후보를 좁힌다 | 준비할 이유와 근거가 있는 항목만 제시한다 |
| Job Agent | 사용자 Wiki를 보유 기술의 근거로 오해할 수 있다 | 사용자가 제공한 경험만 비교하고 나머지는 미확인으로 둔다 | 공부 자료의 존재를 숙련도와 경력으로 바꾸지 않는다 |
| Job Agent | 본문 분석 시각을 모집 상태 확인 시각으로 오해할 수 있다 | 제공 본문 분석과 실제 원문 조회를 구분한다 | 미확인 모집 상태와 마감을 만들어 내지 않는다 |
| Supervisor | 이전 UI 모드가 새 질문의 목적보다 우선할 수 있다 | 현재 요청의 명시한 목적을 우선한다 | 한 Session에서 학습 주제를 바꿀 수 있다 |
| Harness | 형식 검사만으로 정답 제공을 완전히 감지한다고 가정할 수 있다 | 권한과 출처는 Code로 검사하고 답변 의미는 실제 사례로 검토한다 | 확인 가능한 계약과 의미 검토를 구분한다 |

### 기존 자료에 대한 판단

Algorithm Directory에는 Python 문법, Hash, Sorting, Stack, Queue, DFS와 BFS 자료가 있다.
파일 목록을 확인했으며 모든 본문의 정확성을 검증한 것은 아니다.
[기존 과정 README](C:/Users/yds67/OneDrive/Desktop/workspace/Cowork-HQ/20_Vault/알고리즘/README.md)는 일부 주제를 범위에서 제외한다.
따라서 모든 Algorithm에 자료가 있다고 가정하지 않는다.

[Hash Wiki Note](C:/Users/yds67/OneDrive/Desktop/workspace/Cowork-HQ/20_Vault/알고리즘/02_해시_dict_set.md:26)에는 완성 Code와 직접 확인의 답이 함께 있다.
개념 설명, 작은 입력 추적과 풀이 구간을 구분해야 한다.
기존 File을 수정하기보다 App이 읽을 Concept Reference를 지정한다.
Coding Test 도움은 필요한 구간만 사용한다.

### 개인 사용 기준의 선택

세 Agent는 자료 조회와 안내를 맡는다.
기록 저장과 일정 변경은 사용자의 명확한 요청을 받은 App 관리 경로가 맡는다.
같은 Session에서 역할이 바뀌어도 질문 목적과 필요한 조건을 유지한다.
Agent마다 별도 Profile과 대화 Memory를 만들지 않는다.

학습 도움은 작은 실제 질문으로 먼저 검토한다.
새 평가 Agent, 자동 적합도 점수와 추가 Framework는 만들지 않는다.
Source Reference, Hint Level과 공고 근거의 동작은 구현 뒤 검증한다.
이번 수정은 설계 개선이며 실제 Agent의 답변을 시험한 결과가 아니다.

## 10. 문서 변경 범위

이전 정리에서는 FINAL_PROJECT_STRATEGY.md와 README.md를 수정했다.
현재 기준은 아래 12절에서 정한 네 문서로 통합했다.
이 문서에는 검토 근거를 모았다.
DOCUMENTATION_STYLE.md와 AGENTS.md에는 앞으로의 작성 규칙을 남겼다.

필요한 Research는 docs/research에서 보존한다.
중복 계획의 필요한 판단 이유는 이 문서에 남긴다.
오래된 수량과 Release 조건은 현재 완료 조건이 아니다.

원래 Wiki는 수정하지 않았다.
App Code, Package 설치, 실제 Model API 호출은 수행하지 않았다.
실행 검증은 R0와 이후 구현 단계에 남아 있다.

## 11. 구현 전 Directory 정리

일반 문서를 docs로 옮겼다.
Root에는 README.md와 개발 규칙인 AGENTS.md를 남겼다.
Source, 학습 정의와 실행 Script의 Directory를 생성했다.
현재 세부 배치는 [Architecture](./ARCHITECTURE.md)에 있다.

이전 PROJECT_PLAN.md, STUDY_PLATFORM_PLAN.md와 LEARNING_WORKSPACE_STRATEGY.md는 중복 계획으로 제거했다.
현재 PROJECT_PLAN.md는 네 핵심 문서의 역할 분리에 맞춰 새로 작성한 문서다.
필요한 Wiki 조회 계약은 현재 Architecture의 MCP 절에 있다.
CODING_DATA_RESEARCH.md는 외부 문제 수집 방향을 사용하지 않으므로 제거했다.
Drag and Drop 및 서비스 UX 조사는 선택 근거와 출처가 있어 유지했다.

Wiki MCP는 Backend의 Python Package 안에 둔다.
별도 Process는 유지하되 별도 Python 환경과 의존성 목록을 추가하지 않는다.
원래 Wiki를 복사하거나 수정하지 않았다.
App Code, Package 설정, 비밀값과 실행 Script는 아직 작성하지 않았다.

## 12. 네 핵심 문서와 후속 RAG 실험

사용자는 지금까지의 결정을 네 문서로 정리하도록 요청했다.
문서의 목적과 기준을 다음과 같이 나눴다.

| 문서 | 관리할 기준 |
|---|---|
| PROJECT_PLAN.md | 목적, 우선순위, Release 범위와 구현 순서 |
| PRD.md | 기능, 사용자 제어와 완료 조건 |
| ARCHITECTURE.md | 기술 Stack, Module, 저장과 실행 계약 |
| USER_FLOWS.md | 실제 사용 순서와 결과 및 실패 확인 |

이전 FINAL_PROJECT_STRATEGY.md와 PROJECT_STRUCTURE.md의 필요한 내용을 통합했다.
두 문서를 별도 현행 기준으로 유지하지 않는다.
README, AGENTS와 DOCUMENTATION_STYLE의 문서 참조도 같은 기준으로 바꾼다.
Research는 후보와 선택 근거로 유지한다.

사용자는 RAG의 우선순위를 뒤로 두고 Baseline과 실험적으로 비교하도록 정했다.
기본 검색은 Keyword Search와 필요한 Wiki Section 읽기다.
Embedding과 Hybrid Search는 E1의 후속 비교 실험으로 둔다.
E1은 R1, R2와 R3의 완료 조건이 아니다.
검색이 개선됐는지는 같은 질문, 문서 Version과 Model 조건으로 확인한다.
검색 실패와 답변 해석 실패를 구분한다.

Markdown 원본의 일괄 변환과 정제를 요구하지 않는다.
기본 검색에도 제목, Metadata와 Heading의 가벼운 Parsing은 필요하다.
실험에서는 원본을 수정하지 않고 Section, Embedding과 파생 Index를 생성한다.
Coding Agent의 Concept Reference 제한은 실험에서도 유지한다.

문서 작성은 DOCUMENTATION_STYLE의 한국어 설명과 English Technical Name을 따른다.
혼합 언어 문서를 ASD-STE100 전체 준수 문서로 표시하지 않는다.
Architecture Diagram은 표준 Mermaid Source와 문서용 SVG로 관리한다.
문서 Renderer 설치와 Diagram 생성은 App 구현 검증과 별개다.
문서 Renderer는 임시 Tool Directory에 설치했다.
App의 Frontend와 Backend 의존성에는 추가하지 않았다.
Mermaid Source는 Architecture와 User Flow에 남겼다.
같은 Source에서 생성한 SVG와 생성 정보는 docs/diagrams에 둔다.

이번 문서 검증에서는 Local Link 45개와 UTF-8 본문을 확인했다.
FR 21개, NF 8개와 UF 15개의 정의 및 참조를 확인했다.
네 Diagram의 Source Hash, SVG Hash와 SVG 구조를 확인했다.
Browser에서 한국어 글자, 연결선과 그림 범위 밖의 글자를 확인했다.
이 검증은 문서와 Diagram에 대한 검증이다.
App의 기능 Test, Model API 호출과 R0 실행 검증은 수행하지 않았다.

## 13. 공개 GitHub Project 학습과 면접 준비

검토일: 2026-10-05.
사용자는 GitHub URL로 Project를 이해하고 공부 및 면접 준비를 하는 기능을 요청했다.
연결의 첫 범위는 공개 Repository로 정했다.

단순 README 요약보다 구조, 실행 진입점과 핵심 Code를 연결하는 학습 흐름이 필요하다.
면접 연습은 사용자 답변 뒤 근거와 비교하고 필요한 공부로 돌아갈 수 있어야 한다.
현행 기능 계약은 [PRD의 FR-22 및 FR-23](./PRD.md#fr-22-공개-github-project-연결과-이해)에 추가했다.
제공 시점과 우선순위는 [Project Plan](./PROJECT_PLAN.md)에서 관리한다.
사용 순서는 [UF-16 및 UF-17](./USER_FLOWS.md#18-uf-16-github-project를-연결하고-공부하기)에 있다.

Learning Agent는 Project 이해, 개념 학습과 기술 면접 피드백을 담당한다.
Job Agent는 공고별 준비를 요청했을 때 요구사항과 확인한 경험을 연결한다.
기존 Role, Session, Page와 Task Service를 사용하므로 별도 Agent와 면접 Database는 추가하지 않는다.
자동 Track 및 Study Unit 생성은 요구하지 않는다.
Code의 존재와 사용자의 개인 기여 및 성과를 구분한다.

GitHub Adapter는 필요한 File을 읽고 Commit을 고정한 Source Reference를 남긴다.
이 방식은 같은 학습과 면접 연습의 근거가 다른 Version으로 바뀌는 문제를 줄인다.
일부 File만 읽은 분석을 전체 Project 검토로 표시하지 않는다.
원문 조회와 AI 설명, 정적 추론과 실제 실행 검증을 구분한다.
Code 실행, 의존성 설치와 원격 변경은 요구하지 않는다.

GitHub의 Tree 누락, Blob 조회와 Rate Limit 계약을 공식 문서로 확인했다.
HTTPX의 AsyncClient, Streaming과 Timeout 계약도 공식 문서로 확인했다.
근거 Link와 초기 읽기 제한은 [Architecture 17절](./ARCHITECTURE.md#17-공개-github-repository-계약)에 남겼다.
httpx는 기존 Backend 의존성이며 이번 작업에서 새 Package를 설치하지 않았다.
이번 변경은 요구사항과 설계 반영이다.
실제 GitHub 연결, Model 설명과 Browser 학습 흐름의 검증은 해당 기능 구현 단계에 남아 있다.
