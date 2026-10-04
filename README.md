# 개인 학습 App

기존 Markdown Wiki로 개념을 익히고 Python 기초를 실습하는 개인 App이다.
실전 Coding Test 문제 풀이와 채점은 Programmers에서 진행한다.
하나의 Multi-turn Chat에서 학습과 관리 기능을 요청한다.

Learning Agent는 AI, Data, Backend와 일반 CS 개념을 설명한다.
Coding Agent는 Markdown 기반 Algorithm 학습과 정답 없는 Coding Test 학습 도움만 담당한다.
Job Agent는 공고의 근거와 사용자가 명시한 경험을 연결한다.
오답노트는 직접 작성하는 보조 Page다.
후속 기능으로 공개 GitHub URL을 연결하는 Project 학습과 모의 면접을 계획했다.
구조 설명, 핵심 Code 공부와 면접 피드백은 읽은 File과 고정한 Commit을 근거로 사용한다.
해당 기능은 설계 상태이며 아직 App에서 사용할 수 없다.
세부 동작은 [PRD의 FR-22 및 FR-23](./docs/PRD.md#fr-22-공개-github-project-연결과-이해)을 따른다.

상태: 2026-10-05 R0의 순서 4(Pyodide의 별도 Origin 실행 영역 검증)를 완료했다.
별도 Origin(127.0.0.1:5174)의 iframe과 Pyodide Web Worker 격리, 3초 타임아웃 강제 중단 및 복구, 64 KiB 출력 제한, 사용자 출력/Test Case 분리 및 Cross-Origin 접근 차단을 구현하고 Playwright 6개 E2E 테스트를 통과했다.
다음 작업은 R0 순서 5인 Gemini Adapter와 공통 Harness 연결이다.
문서 Diagram의 생성은 App 구현과 별도로 관리한다.

## 문서 진입점

| 문서 | 목적 |
|---|---|
| [Project Plan](./docs/PROJECT_PLAN.md) | 목적, 우선순위, Release 범위와 구현 순서 |
| [PRD](./docs/PRD.md) | 기능, 사용자 제어와 완료 조건 |
| [Architecture](./docs/ARCHITECTURE.md) | 기술 Stack, Module, 저장, 실행 계약과 Diagram |
| [User Flow](./docs/USER_FLOWS.md) | 학습, 기록, 관리와 실패 처리의 사용 순서 |
| [검토 기록](./docs/PROJECT_REVIEW.md) | 변경 이유와 판단 근거 |
| [문서 작성 규칙](./docs/DOCUMENTATION_STYLE.md) | 한국어 설명과 English Technical Name |
| [Drag and Drop 조사](./docs/research/DRAG_AND_DROP_RESEARCH.md) | Library 비교와 출처 |
| [서비스 UX 조사](./docs/research/SERVICE_UX_RESEARCH.md) | 서비스 사례와 기능 후보 |

일반 Project 문서는 docs에서 관리한다.
Root의 [AGENTS.md](./AGENTS.md)는 개발 Agent의 규칙이다.
Release 범위는 Project Plan에서만 관리한다.
기능과 완료 조건은 PRD를 따른다.
기술과 구조는 Architecture를 따른다.

RAG의 Embedding 및 Hybrid Search는 Baseline 이후의 E1 비교 실험이다.
기본 검색은 Keyword Search와 필요한 Wiki Section 읽기다.
기존 Markdown 원본을 일괄 변환하거나 복제하지 않는다.

## Directory 개요

```text
MCP_project/
├── AGENTS.md
├── README.md
├── .gitignore
├── docs/        # 네 핵심 문서, Diagram, 작성 규칙과 검토 자료
├── frontend/    # Browser UI와 별도 Origin의 Python Runtime Source
├── backend/     # API, Service, Agent, Harness와 Wiki MCP
├── content/     # 자체 Study Unit과 기초 문제 정의
└── scripts/     # 문서 Diagram 생성; App 시작과 Backup 진입점은 구현 단계에서 추가
```

Frontend는 React, TypeScript와 Vite를 사용한다.
Backend는 FastAPI, Python과 SQLite를 사용한다.
Agent는 공통 Model 연결과 Harness를 사용한다.
Wiki MCP는 Backend와 같은 Python 환경에서 별도 Process로 실행한다.

기존 Wiki는 원래 Directory에서 읽기 전용으로 연결한다.
사용자 Data와 활성 SQLite의 기본 경로는 %LOCALAPPDATA%/MCP_project다.
API Key는 Backend에서만 사용한다.
사용자 Database Directory는 아직 만들지 않았다.
