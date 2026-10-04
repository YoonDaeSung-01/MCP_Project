# 문서 작성 규칙

작성일: 2026-10-04
적용 대상: 앞으로 작성하거나 수정하는 Project 전략, 구현 계획, 검토 기록, README, 사용자 답변.

## 1. ASD-STE100 적용 범위

ASD-STE100은 English의 문장 규칙과 제한된 어휘를 정한다.
Project별 Technical Name도 정해진 조건으로 사용할 수 있다.
[ASD-STE100 공식 설명](https://www.asd-ste100.org/about.html)

이 Project는 사용자의 요청에 따라 한국어 설명과 English Technical Name을 함께 쓴다.
한국어 문장에 English 문법 규칙을 그대로 적용하지 않는다.
이 혼합 문서를 ASD-STE100 전체 준수 문서라고 표시하지 않는다.

English 문장을 작성할 때는 ASD-STE100의 어휘, 문법, 문장 길이를 따른다.
Technical Name은 아래 용어 정의와 공식 표기를 사용한다.
고유 제품명, Package Name, API Field, Code Identifier, File Path는 원래 표기를 유지한다.

공식 규칙은 [ASD-STE100 Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)를 기준으로 확인한다.
작성 Tool의 자동 검사만으로 준수를 확정하지 않는다.
[공식 Tool 안내](https://asd-ste100.org/STEsoftware.html)

## 2. 언어와 용어

- 목적, 이유, 판단, 절차 설명은 한국어로 쓴다.
- 기술 용어와 English에서 온 표현은 English로 쓴다.
- 같은 개념에는 같은 용어를 사용한다.
- 처음 사용하는 Project Technical Name의 의미를 설명한다.
- 뜻이 다른 개념은 같은 용어로 묶지 않는다.
- Machine-readable 값과 원래 File Name을 번역하지 않는다.
- 원문 인용과 과거 기록의 표기를 임의로 바꾸지 않는다.

문서에서는 Backend, Browser, Session, Calendar, Layout, Token을 사용한다.
해당 용어를 한글로 음역해서 함께 사용하지 않는다.
사용자가 작성한 Wiki의 실제 제목과 Directory Name은 예외다.

문서 작성 규칙과 App의 UI 표시 언어는 별개다.
App의 사용자 화면은 한국어를 기본으로 유지한다.

## 3. 문장과 절차

한 문장은 한 판단이나 동작을 설명한다.
문장의 주체와 대상이 분명해야 한다.
가능한 경우 능동형을 사용한다.
동작, 조건, 결과를 구체적으로 쓴다.

English 절차 문장은 최대 20단어로 쓴다.
English 설명 문장은 최대 25단어로 쓴다.
한 문단에는 관련 내용만 둔다.
English 문단은 최대 여섯 문장으로 쓴다.
한국어 문단도 짧게 나눈다.

이 Word Count를 한국어의 띄어쓰기 수에 그대로 적용하지 않는다.
English 문장과 혼합 문장의 검토 범위를 구분한다.
계약에 필요한 주체나 조건을 삭제해서 문장을 줄이지 않는다.

절차는 실행 순서대로 번호를 붙인다.
선택지가 있는 절차는 해당 조건을 먼저 쓴다.
기능을 나열할 때는 기능과 완료 조건을 연결한다.
표는 비교, 정의, 변경 전후를 보여줄 때 사용한다.

## 4. 상태와 근거

선택한 기술과 검증한 기술을 구분한다.
제안, 확정, 구현, 검증 완료를 같은 상태로 쓰지 않는다.
측정하지 않은 성능과 요금을 확정하지 않는다.
자료에서 확인한 사실과 설계 판단을 구분한다.

새로운 Package 기능과 API 계약은 공식 문서로 확인한다.
확인 날짜를 적는다.
실패한 조회와 미검증 상태도 정확히 적는다.
문서 검토를 실제 실행 Test 결과로 보고하지 않는다.

현행 Release 범위는 docs/PROJECT_PLAN.md에서만 관리한다.
기능과 완료 조건은 docs/PRD.md에서 관리한다.
기술 선택, Directory와 Module 계약은 docs/ARCHITECTURE.md에서 관리한다.
사용자의 실제 조작 순서는 docs/USER_FLOWS.md에서 관리한다.
각 문서는 다른 기준을 참조하며 같은 표를 별도로 갱신하지 않는다.
과거 문서는 참고 기록임을 표시한다.
같은 범위 표를 여러 문서에서 따로 갱신하지 않는다.
Root의 진입 문서와 개발 규칙 외의 Project Markdown은 docs에 둔다.
App Agent의 Skill과 자체 학습 Markdown은 Source와 content의 정의된 위치에 둔다.

## 5. Project 용어 정의

다음은 Project의 Technical Name 정의다.
ASD-STE100 일반 사전의 승인 어휘 목록을 복제한 표가 아니다.
일반 기술명과 제품명은 공식 표기를 유지한다.

| Technical Name | 이 Project에서의 의미 |
|---|---|
| App | 사용자가 사용하는 전체 개인 학습 Program |
| Frontend | Browser의 UI와 표시 로직 |
| Backend | API와 업무 로직을 실행하는 Python 구성 |
| Service | 실제 조회와 저장을 처리하는 업무 Function 묶음 |
| Data | 저장하거나 처리하는 정보 |
| Data Entity | 별도 식별자로 저장하는 정보 단위 |
| Page | 사용자가 작성하는 Block 문서 |
| Web Page | 공개 URL로 읽는 외부 문서 |
| Wiki Note | 기존 Directory의 읽기 전용 Markdown 문서 |
| Block | Page를 구성하는 편집 단위 |
| Widget | 특정 내용을 표시하는 이동 가능한 화면 영역 |
| Layout | Widget의 위치와 크기 |
| Drag and Drop | 대상을 끌어서 지정한 위치에 놓는 조작 |
| Study Unit | 목표, 자료, 활동, 확인 기준을 가진 학습 단원 |
| Track | 분야와 난이도로 묶은 Study Unit의 탐색 공간 |
| Practice Problem | 입력, 결과, 제약, Test Case를 가진 App의 기초 실습 문제 |
| Coding Test | 문제의 조건에 맞게 Code를 직접 구현하고 외부 판정을 확인하는 시험 |
| Coding Record | 필요할 때 외부 문제의 Link, 내 Code와 배운 내용을 남기는 보조 Page |
| Concept Reference | 설명에 사용할 검토된 개념 구간 |
| Source Reference | 원문의 ID, Version, 구간 또는 URL을 가진 참조 |
| Code | 실행하거나 검토하는 Source Code |
| Code Draft | 사용자가 현재 편집하는 Code |
| Code Snapshot | 한 Turn 또는 실행에 연결한 Code 사본 |
| Attempt | App 기초 실습의 Code, Problem Version, 실제 실행 결과 기록 |
| Test Case | 입력과 판정 규칙을 가진 연습 검증 항목 |
| Task | 해야 할 작업과 선택적 마감 |
| Event | 시작과 종료 시간이 있는 일정 |
| Planner | 목표와 공부 가능 시간으로 작업 배치를 돕는 기능 |
| Calendar | Event를 날짜와 시간으로 표시하는 화면 |
| Chat | 사용자가 AI와 대화하는 공통 화면 |
| Session | 같은 대화 기록과 활성 Context를 공유하는 단위 |
| Multi-turn | 앞선 대화 내용을 다음 요청에 사용하는 대화 구조 |
| Turn | 한 사용자 요청과 해당 처리 결과의 단위 |
| Message | Session에 저장한 발화 또는 필요한 실행 결과 |
| Context | 현재 요청에 전달할 대화와 선택 자료 |
| Session Context | 같은 Session의 활성 대상과 요청 설정 |
| Settings | 사용자가 명시한 공통 설정 |
| Memory | Session 기록과 확인한 Settings를 사용하는 구성 |
| Role | Agent의 책임, 지침, 허용 Tool 설정 |
| Agent | Role을 사용해서 요청을 처리하는 실행 담당 |
| Learning Agent | AI, Data, Backend와 일반 CS 개념 설명 및 학습 피드백을 처리하는 Role |
| Coding Agent | Markdown Wiki의 Algorithm 학습과 정답 없는 Coding Test 학습 도움만 담당하는 Role |
| Job Agent | 공고의 근거를 추출하고 사용자가 명시한 경험과 준비 내용을 연결하는 Role |
| Supervisor | 현재 요청의 목적에 따라 Role 또는 App 관리 경로를 선택하는 구성 |
| Harness | Context, Model, Tool, 제한, 취소, 검증의 실행 구성 |
| Skill | 특정 작업의 절차와 출력 기준 |
| Rules | 지원 범위와 실행 조건 |
| Hook | 실행 시점에 App이 호출하는 Code Function |
| Tool | Program이 실제 수행하는 기능 |
| Function Tool | App의 Function를 Model 호출에 연결하는 Tool |
| Tool Call | 요청한 Tool의 이름과 Argument |
| Tool Result | Tool 실행 결과 |
| MCP | Model Context Protocol |
| Host | MCP 기능을 사용하는 AI App |
| MCP Client | Host에서 MCP 연결을 관리하는 구성 |
| MCP Server | MCP의 Tool, Resource, Prompt를 제공하는 구성 |
| Resource | MCP가 식별자로 제공하는 자료 |
| Prompt | MCP가 제공하는 재사용 지침 |
| Protocol Revision | 연결 규약의 개정 식별자 |
| SDK Version | 설치한 SDK Package의 Version |
| Trace | Tool 동작과 출처를 확인하는 실행 기록 |
| Provider Metadata | 선택 API의 실행 연결에 필요한 부가 정보 |
| Origin | scheme, host, port로 정한 Browser 접근 기준 |
| CSRF Token | 다른 Origin의 변경 요청을 제한하는 검증값 |
| API Key | Provider API 호출에 쓰는 비밀값 |
| Python Runtime | Browser에서 Python을 실행하는 환경 |
| Namespace | 실행에서 이름과 값을 보관하는 범위 |
| Hint Level | 정답을 제외한 확인 질문, 개념 설명, 문법 예제와 부분 점검의 안내 수준 |
| Backup | 원래 App 상태를 복원하기 위한 저장물 |
| Restore | 검증한 Backup으로 App 상태를 되돌리는 작업 |
| Export | 다른 곳에서 읽거나 사용할 수 있는 형식으로 출력하는 작업 |
| Revision | 저장 내용의 수정 순서를 확인하는 값 |
| MVP | 실제 사용 흐름을 제공하는 최소 구현 범위 |
| Release | 개인 사용 가능 범위의 구현 단계 |
| Web Search | 요청에 필요한 공개 웹 자료 검색 |
| Project Plan | 목적, 우선순위, Release 범위와 구현 순서의 기준 문서 |
| PRD | 기능, 사용자 제어와 완료 조건의 기준 문서 |
| Architecture | 기술, Module, 저장과 실행 계약의 기준 문서 |
| User Flow | 사용자의 조작 순서와 결과 확인의 기준 문서 |
| Baseline | 다른 방식과 비교하는 기본 구현 |
| RAG | 검색한 자료를 Context로 사용해서 답변하는 흐름 |
| Keyword Search | 입력한 용어와 문서의 표현을 비교하는 검색 |
| Embedding | 검색 비교에 사용할 의미 표현의 수치값 |
| Hybrid Search | Keyword Search와 Embedding Search를 결합하는 검색 |
| Index | 검색을 위해 원본에서 생성한 구조 |
| Section | Heading과 원문 위치로 식별하는 문서 구간 |
| File Version | 특정 원문 내용의 Version 식별자 |
| Diagram | 구성, 연결 또는 실행 순서를 표시하는 그림 |

새 Project Technical Name이 필요하면 이 표에 정의를 추가한다.
같은 개념에 새로운 동의어를 만들지 않는다.
일반 기술명과 Package Name을 모두 이 표에 반복해서 적을 필요는 없다.

## 6. 작성 예

Backend는 Task를 저장한다.
Harness는 허용 목록의 Tool만 실행한다.
같은 Session은 필요한 Message를 다음 Turn에 전달한다.
Calendar는 Event를 옮겨도 Task의 마감일을 바꾸지 않는다.
Markdown Export로 사용자 정의 Block의 복원을 보장하지 않는다.

English 절차를 쓸 때는 짧은 동작 문장을 사용한다.

- Read the source.
- Save the page.
- Stop the worker.

API Field와 Code Identifier는 정확히 표시한다.
예: session_id, turn_id, request_id, source_mode, hint_level.

## 7. Diagram 작성

Diagram의 Label은 본문과 같은 Technical Name을 사용한다.
관계와 동작 설명은 짧은 한국어로 쓴다.
구성 관계와 실제 실행 순서를 같은 그림에서 혼동하지 않는다.
하나의 Diagram에는 한 목적의 경계만 표시한다.

표준 Mermaid Source를 핵심 문서에 남긴다.
Source와 같은 내용의 SVG를 docs/diagrams에 생성한다.
Source를 수정하면 SVG와 생성 정보를 함께 갱신한다.
Theme, Font와 간격은 공통 설정에서 관리한다.
Mermaid Renderer를 App 기능의 추가 의존성으로 사용하지 않는다.
색상만으로 읽기, 변경과 실행의 의미를 구분하지 않는다.
