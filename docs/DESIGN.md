# UI/UX Design System & Specification

개정일: 2026-10-05  
상태: 디자인 시스템 및 UI 사양 확정. 글로벌 개발자/AI 서비스 10종 전수조사 및 Best Practice(BP) 벤치마킹 기반.

이 문서는 개인 학습 App의 디자인 철학, 글로벌 벤치마킹 전수조사 분석, 워크스페이스 레이아웃, 디자인 토큰(Design Tokens), 화면별 컴포넌트 사양, 마이크로 인터랙션 및 키보드 접근성을 정의한다.
요구사항은 [PRD](./PRD.md)를 따르고, 기술 아키텍처는 [Architecture](./ARCHITECTURE.md)를 따르며, 사용자 흐름은 [User Flow](./USER_FLOWS.md)를 따른다.

---

## 1. 디자인 비전 및 핵심 원칙 (Vision & Principles)

이 App은 개발자 및 기술 취업 준비생이 CS 이론과 AI 개념을 Markdown Wiki로 깊이 있게 탐구하고, 브라우저 격리 런타임에서 Python 코드를 직접 실행하며, AI 어시스턴트(Learning/Coding Agent)와 대화하는 **전문가용 AI-Native 스터디 워크스페이스**다.

화려한 시각 효과보다 엔지니어링 집중도(Focus)와 직관적인 정보 밀도를 최우선으로 삼는다.

1. **Achromatic Focus (무채색 기반 시각 노이즈 최소화)**
   - 과도한 원색 사용을 배제하고, 정교하게 조율된 무채색 계조(Achromatic Grayscale)로 시각적 계층을 구축한다.
   - 색상은 중요한 상태(Test 통과/실패)와 핵심 액션(Primary Indigo), AI 맥락 표시에만 목적 지향적(Purposeful)으로 사용한다.
2. **Hairline Structural Clarity (달빛 와이어프레임 구조미)**
   - 두껍고 둔탁한 테두리를 버리고, Linear 스타일의 초미세 반투명 테두리(`rgba(255, 255, 255, 0.07)`)를 사용해 화면을 깔끔하게 분할한다.
   - 정보가 빽빽하게 들어차도 답답하지 않고 가볍고 정돈된 느낌을 유지한다.
3. **Transparent Context & AI Cohesion (투명한 AI 맥락과 일체감)**
   - Cursor와 Windsurf처럼, AI가 참고하고 있는 데이터(Wiki 노트, 코드 스냅샷, 참조 Page)를 눈에 보이는 'Context Pill(캡슐 칩)'로 상시 노출한다.
   - AI 답변의 근거(Source Reference)는 Perplexity 스타일의 인용 카드로 투명하게 공개하여 환각(Hallucination)에 대한 불안을 제거한다.
4. **High-Density Engineering Ergonomics (높은 정보 밀도의 인체공학)**
   - 개발자는 스크롤을 끝없이 내리는 것보다 한 화면에서 코드, 실행 결과, AI 힌트를 한눈에 조망하는 것을 선호한다.
   - 기본 본문 13px, 코드 13.5px, 컴팩트한 패딩(4px 그리드)을 적용해 효율적인 작업 면적을 확보한다.
5. **Keyboard-First & Tactile Response (키보드 우선 조작과 촉각적 반응)**
   - 마우스 없이도 `Ctrl+Enter`(코드 실행), `Ctrl+K`(커맨드 검색), `Ctrl+B`(사이드바 토글), `Ctrl+L`(AI 패널 토글)로 모든 핵심 작업이 가능하다.
   - 버튼 클릭 및 호버 시 150ms 내외의 민첩하고 즉각적인 피드백을 제공한다.

---

## 2. 글로벌 벤치마킹 서비스 전수조사 분석 (Exhaustive BP Survey)

개발자 도구, AI 에이전트 인터페이스, 코딩 테스트 플랫폼, 지식 관리 도구 등 총 10개 대표 서비스의 UI/UX 패턴을 비교 분석하여 본 App에 최적화된 설계를 도출했다.

| 번호 | 서비스명 | 도메인 | 핵심 인터페이스 강점 (Best Practice) | 본 App 적용 방안 |
|:---:|---|---|---|---|
| **1** | **Cursor** | AI IDE | • 3-Pane 분할 레이아웃 (탐색기 + 에디터 + AI)<br>• `@file`, `@docs` 호출 시 나타나는 **Context Pill** 칩 인터랙션<br>• 코드 Diff 뷰 및 에디터-채팅 간 스냅샷 동기화 | • 우측 AI Chat 상단에 현재 활성 Wiki/Code Context Pill 배치<br>• 사용자가 X 버튼으로 참조 맥락을 직관적으로 해제 가능<br>• 문제 풀이 시점의 코드 스냅샷을 대화 턴에 보존 |
| **2** | **Windsurf (Cascade)** | Agentic IDE | • **Chat Mode**(질문/설명) vs **Write Mode**(코드 수정/실행) 구분<br>• Tool 실행(터미널 명령, 파일 분석) 과정의 실시간 상태 접기<br>• AI의 액션 제안과 사용자의 승인(Review) 분리 | • Learning Agent(개념 설명)와 Coding Agent(힌트 및 점검)의 모드 뱃지<br>• Wiki 검색, MCP 도구 호출 과정을 아코디언 컴포넌트로 접기/펼침<br>• 정답 코드를 강제 삽입하지 않고 힌트 중심 안내 |
| **3** | **Linear** | 이슈 & 프로젝트 관리 | • **Achromatic Zinc 다크 테마**와 시그니처 Indigo 액센트<br>• Hairline Border (`rgba(255, 255, 255, 0.07)`)로 선명한 구획 분할<br>• 키보드 단축키 뱃지(`⌘K`, `ESC`, `↵`) 및 150ms 샤프 트랜지션 | • **전체 테마 룩앤필의 표준 모델 채택**<br>• 미세 테두리와 서피스 계층(Surface 1, 2, 3) 시스템 구축<br>• Task 보드, 우선순위 태그, 단축키 가이드 디자인에 1:1 반영 |
| **4** | **LeetCode & NeetCode** | 코딩 테스트 & 저지 | • 문제 지문(좌) vs Monaco 에디터(우상) vs 콘솔 결과(우하) 3분할<br>• Test Cases(Pass/Fail)와 Stdout 탭 분리<br>• 오답 시 Input, Output, Expected를 나란히 비교하는 Diff 패널 | • **Practice 영역의 2분할 스플릿 러너 구조 채택**<br>• 사용자 print()와 Test Case 결과를 엄격히 탭 분리<br>• 테스트 실패 시 기대값 vs 실제값 비교 카드 제공 |
| **5** | **Perplexity** | AI 지식 검색 & 인용 | • 문장별 인용 뱃지(`[1]`, `[2]`) 부착<br>• 상단/하단 출처 카드 그리드 (파비콘, 도메인, 제목, 스니펫)<br>• 후속 추천 질문(Related Questions) 칩 | • AI Chat 답변 하단에 `SourceReferenceCard` 컴포넌트 부착<br>• Wiki 파일명, 줄 번호, 발췌문 표시 및 클릭 시 해당 원문 점프<br>• 사용자가 요청한 Web Search 결과의 출처 투명 노출 |
| **6** | **Claude Artifacts & Canvas** | AI 캔버스 인터페이스 | • 좌측 AI 대화 + 우측 독립 캔버스 작업 공간 분리<br>• 대화가 아무리 길어져도 본문(코드, 문서)이 가려지지 않는 불변성 | • 3-Pane 셸에서 메인 캔버스(Wiki/Page/Practice)와 우측 AI Chat을 병렬 유지하여 작업 맥락 유지 |
| **7** | **Notion & BlockNote** | 블록 문서 도구 | • 블록 기반(`:::`) 드래그 앤 드롭 재배치<br>• 슬래시(`/`) 커맨드 메뉴<br>• 군더더기 없는 타이포그래피와 체크리스트/콜아웃 박스 | • **Page 및 오답노트 영역**에 BlockNote 에디터 통합<br>• 제목, 코드 블록, 체크 항목, 원문 참조 블록의 모던 스타일링 |
| **8** | **Obsidian** | 로컬 마크다운 지식 베이스 | • 읽기 전용 문서 우측의 스티키 미니 목차(TOC) 아웃라인<br>• `[[WikiLink]]` 및 상호 참조 네비게이션<br>• 높은 정보 밀도와 로컬 파일 트리 브라우징 | • **Wiki Viewer 영역**에 우측 플로팅 TOC(Table of Contents) 배치<br>• 헤딩 클릭 시 스무스 스크롤 이동 및 현재 위치 하이라이트 |
| **9** | **Raycast** | 파워유저 커맨드 바 | • 중앙 플로팅 `Ctrl+K` 커맨드 팔레트<br>• 아이콘 + 단축키 캡슐 + 카테고리 그룹핑의 완벽한 가독성 | • 향후 글로벌 통합 검색 및 빠른 페이지/문제 전환 커맨드바로 적용 |
| **10** | **GitHub** | 소스 트리 & Diff | • Commit SHA 뱃지, Branch 태그, 파일 트리 구조<br>• 코드 블록 줄번호(Line Number) 및 구문 강조(Syntax Highlight) | • R2의 공개 GitHub 프로젝트 학습 화면(트리 및 파일 스냅샷 뷰)의 디자인 표준으로 채택 |

---

## 3. 워크스페이스 레이아웃 아키텍처 (Shell Layout)

화면은 헤더, 메인 3-Pane 캔버스, 하단 상태바의 3계층 수직 구조로 구성된다.

```text
+===================================================================================================+
|  Top Navigation Bar (Height: 44px)                                                                 |
|  [⬡ MCP Study] | [Wiki] [Study] [Page] [Practice] [Task]            [Pyodide: 127.0.0.1:5174 ●] [☀/☾] |
+-------------------+-----------------------------------------------------------+-------------------+
| Left Sidebar      | Center Main Workspace (Flex: 1)                           | Right AI Copilot  |
| Width: 260px      |                                                           | Width: 380px      |
| (Collapsible:     | [ Practice Mode Active ]                                  | (Collapsible:     |
|  Ctrl+B)          | +-------------------------------------------------------+ |  Ctrl+L)          |
|                   | | Editor Header Bar (File: solution.py | Python 3.12)   | |                   |
| 📂 Collections    | | [ ▶ 실행 (Ctrl+Enter) ] [ ■ 중단 ] [ ⏱ 3초 타임아웃 ] | | Active Context:   |
|  ├ 📄 CS Core     | +-------------------------------------------------------+ | [Wiki: Hash.md ×] |
|  ├ 📄 Backend     | | Monaco Editor (JetBrains Mono 13.5px)                 | | [Code: v1 Sol ×]|
|  └ 📄 Algorithm   | | def solution(arr):                                    | +-----------------+
|                   | |     # 사용자 코드 편집창 (VS Code Dark+)               | | AI Chat Stream: |
| 📑 Study Units    | |     table = {}                                        | | User: "해시 충돌|
|  • Hash Map       | +-------------------------------------------------------+ | 어떻게 처리해?" |
|  • Graph BFS      | | Split Runner (Tabs: Test Cases (2/2) | Stdout)        | |                 |
|                   | |  ✔ Test 1: PASS (args: [1,2,2], expected: {1:1,2:2})  | | AI Assistant:   |
| 📝 My Pages       | |  ✔ Test 2: PASS (args: [], expected: {})              | | "체이닝 방식과  |
|  • 오답노트 #1    | | Stdout: "계산 완료: 원소 2개"                         | | 개방주소법..."  |
|                   | +-------------------------------------------------------+ | 📎 [Source: Hash] |
| [ ⇱ 접기 ]        |                                                           | [Prompt...]   [↵] |
+-------------------+-----------------------------------------------------------+-------------------+
|  Bottom Status Bar (Height: 22px)                                                                 |
|  UTF-8 | LF | SQLite WAL: Synchronized | Origin: http://127.0.0.1:5174 (Isolated) | Ready        |
+===================================================================================================+
```

### 3.1 Top Navigation Bar (고정 44px)
- **로고 영역 (좌측 200px)**: 미니멀한 Hexagon 아이콘(`⬡`)과 `MCP Study` 타이틀.
- **모드 전환 세그먼트 (중앙)**:
  - 5개 탭: `Wiki (자료)`, `Study (학습)`, `Page (노트)`, `Practice (실습)`, `Task (작업)`.
  - 탭 클릭 시 120ms 슬라이딩 인디케이터 전환. 단축키 `Alt+1` ~ `Alt+5` 지원.
- **상태 및 유틸리티 (우측)**:
  - **Pyodide Runtime Indicator**: `127.0.0.1:5174 ●` (초록 점: 준비 완료, 회색 점: 준비 중, 빨간 점: 오류).
  - **Theme Toggle**: 썬/문 아이콘 원클릭 전환 (`Dark` / `Light`).
  - **Database Status**: 마지막 로컬 저장 시각 표기.

### 3.2 Left Sidebar (가변 240px ~ 280px, `Ctrl+B` 토글)
- 상단 탭 모드에 연동되어 콘텐츠 트리 동적 변경:
  - Wiki 모드: Collection별 디렉터리 및 Markdown 파일 목록.
  - Page 모드: 내가 작성한 Page 및 보조 Coding Record 목록 (최근 수정순).
  - Study 모드: 난이도별/분야별 Study Unit 리스트.
  - Task 모드: 할 일 필터 (오늘, 이번 주, 완료됨, 보관됨).
- 하단에 패널 접기 버튼 및 단축키 안내(`Ctrl+B`). 접혔을 때는 40px 미니 아이콘 레일(Rail)로 축소.

### 3.3 Center Main Workspace (유연한 너비, Flex: 1)
- 작업의 중심이 되는 공간. 모드별 최적 레이아웃:
  - **Wiki Mode**: 좌측 읽기 본문(최대 820px 최적 가독 너비, 라인 높이 1.7) + 우측 고정 플로팅 목차(TOC).
  - **Page Mode**: Notion 스타일 여백(최대 860px), BlockNote 블록 조작 핸들, 깔끔한 캔버스.
  - **Practice Mode**: 상단 Monaco Editor(60%) + 하단 Console/Test Result Runner(40%)의 수직 스플릿.
  - **Task Mode**: Linear 스타일의 상태별 컬럼 뷰(Board) 또는 컴팩트 리스트 뷰.

### 3.4 Right AI Copilot Panel (고정 380px, `Ctrl+L` 토글)
- **Active Context Bar (상단 고정)**:
  - 현재 대화에 연결된 소스를 캡슐 형태의 태그 칩으로 나열.
  - 예: `[Wiki: Hash.md ×]`, `[Code: solution.py (Snapshot) ×]`.
  - 사용자가 X를 누르면 다음 턴 질문에서 해당 컨텍스트가 깔끔히 제외됨.
- **Chat Stream Body (스크롤 영역)**:
  - 사용자 질문: 우측 정렬, 차분한 Surface-Raised 배경.
  - AI 답변: 좌측 정렬, 기술 블로그 아티클 형태의 가독성 높은 Markdown 렌더링.
  - Tool Execution Card: Wiki 검색 쿼리나 GitHub 파일 읽기 과정을 접이식 아코디언으로 표시.
  - Source Reference Card: 답변에서 인용한 Wiki 원문 경로, 라인 범위, 미리보기 스니펫 카드.
- **Prompt Input Box (하단 고정)**:
  - 텍스트 입력에 따라 최대 6줄까지 자동으로 늘어나는 Auto-growing textarea.
  - 슬래시(`/`) 입력 시 사용 가능한 명령어 팝오버.
  - 우측 하단에 `Shift+Enter 줄바꿈`, `Enter 전송` 단축키 힌트.

### 3.5 Bottom Status Bar (고정 22px)
- 정보 밀도와 신뢰성을 높여주는 VS Code 스타일의 초슬림 상태 표시줄.
- 파일 인코딩(`UTF-8`), 줄바꿈(`LF`), 로컬 SQLite WAL 상태, Runtime 격리 포트(`127.0.0.1:5174`), 단축키 치트시트 링크 제공.

---

## 4. 디자인 토큰 명세 (Design Tokens Specification)

Linear와 Cursor의 핵심 미학을 수치화하여 Vanilla CSS 토큰으로 정의한다.

### 4.1 Color System (Achromatic Zinc & Electric Indigo)

```css
:root {
  /* ================= 1. Background Surfaces (Dark Mode 기본) ================= */
  --bg-app: #08090a;             /* 앱 최하단 캔버스 배경 (Near Black) */
  --bg-surface: #101114;         /* 사이드바, 헤더, 기본 패널 서피스 */
  --bg-surface-raised: #18191d;  /* 카드, 입력창, 드롭다운 서피스 */
  --bg-surface-hover: #222329;   /* 리스트 아이템 호버, 액티브 서피스 */
  --bg-surface-active: #2a2b33;  /* 선택된 탭, 프레스 상태 */

  /* ================= 2. Hairline Borders (초미세 반투명 테두리) ================= */
  --border-hairline: rgba(255, 255, 255, 0.07);  /* 기본 1px 구획 분할선 */
  --border-subtle: rgba(255, 255, 255, 0.12);    /* 카드, 패널 기본 보더 */
  --border-strong: rgba(255, 255, 255, 0.20);    /* 입력창 호버, 구분 강조 */
  --border-focus: #5e6ad2;                       /* 포커스 링 (Linear Indigo) */

  /* ================= 3. Typography Inks (가독성 계층) ================= */
  --text-primary: #f2f3f5;       /* 핵심 헤딩, 본문 텍스트 (높은 명도) */
  --text-secondary: #9ea2aa;     /* 설명문, 부제목, 메타데이터 */
  --text-muted: #62656d;         /* 비활성 텍스트, 단축키 힌트, 플레이스홀더 */
  --text-inverse: #08090a;       /* 밝은 배경 위의 반전 텍스트 */

  /* ================= 4. Brand & AI Accents (Electric Indigo) ================= */
  --accent-primary: #5e6ad2;     /* Linear 시그니처 인디고-바이올렛 */
  --accent-primary-hover: #6e7be4;
  --accent-primary-subtle: rgba(94, 106, 210, 0.12);
  --accent-primary-glow: rgba(94, 106, 210, 0.25);

  /* ================= 5. Semantic Status Inks (피드백 컬러) ================= */
  --status-success: #10b981;     /* Test Case 통과 (Emerald) */
  --status-success-subtle: rgba(16, 185, 129, 0.12);
  --status-error: #f43f5e;       /* Test Case 실패, 실행 오류, 타임아웃 (Rose) */
  --status-error-subtle: rgba(244, 63, 94, 0.12);
  --status-warning: #f59e0b;     /* 변경 충돌, 출력 절삭 안내 (Amber) */
  --status-warning-subtle: rgba(245, 158, 11, 0.12);
  --status-info: #0ea5e9;        /* 소스 참조, 시스템 안내 (Sky) */
  --status-info-subtle: rgba(14, 165, 233, 0.12);
}

[data-theme="light"] {
  /* ================= Light Theme (1:1 대응) ================= */
  --bg-app: #f7f8f9;
  --bg-surface: #ffffff;
  --bg-surface-raised: #f0f2f5;
  --bg-surface-hover: #e5e8ec;
  --bg-surface-active: #d9dce2;

  --border-hairline: rgba(0, 0, 0, 0.06);
  --border-subtle: rgba(0, 0, 0, 0.10);
  --border-strong: rgba(0, 0, 0, 0.18);
  --border-focus: #5e6ad2;

  --text-primary: #121316;
  --text-secondary: #5a5d65;
  --text-muted: #8c9098;
  --text-inverse: #ffffff;

  --accent-primary: #5e6ad2;
  --accent-primary-hover: #4f5bc4;
  --accent-primary-subtle: rgba(94, 106, 210, 0.08);
  --accent-primary-glow: rgba(94, 106, 210, 0.18);

  --status-success: #059669;
  --status-success-subtle: rgba(5, 150, 105, 0.08);
  --status-error: #e11d48;
  --status-error-subtle: rgba(225, 29, 72, 0.08);
  --status-warning: #d97706;
  --status-warning-subtle: rgba(217, 119, 6, 0.08);
  --status-info: #0284c7;
  --status-info-subtle: rgba(2, 132, 199, 0.08);
}
```

### 4.2 Typography System

- **Font Family**:
  - UI Font: `'Pretendard', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif`
  - Code & Console Font: `'JetBrains Mono', 'Fira Code', Consolas, monospace`
- **Font Weight**:
  - `400` (Regular): 긴 본문 텍스트, 설명글
  - `510` (Medium+): Linear 특유의 가독성 높은 버튼 레이블, 메뉴 타이틀, 탭 텍스트
  - `600` (SemiBold): 헤딩, 모달 타이틀, 상태 뱃지
- **Letter Spacing**:
  - 본문: `-0.01em` (가독성을 살린 미세 조임)
  - 헤딩 (H1, H2): `-0.025em` ~ `-0.03em` (Linear 특유의 압축된 authoritative 느낌)
- **Type Scale**:
  - `11px` (Micro): 단축키 힌트, 태그 뱃지, 상태바
  - `12px` (Caption): 파일 경로, 작성 시각, 보조 레이블
  - `13px` (Base Dense): 사이드바 목록, 버튼, 입력창, 콘솔 출력 (표준 UI 밀도)
  - `14px` (Body): Wiki 본문, AI Chat 메시지 본문
  - `16px` (Subhead): 섹션 타이틀, 모달 헤더
  - `20px` (H3): 문서 H3 헤딩
  - `24px` (H2): 문서 H2 헤딩
  - `30px` (H1): 최상위 문서 H1 헤딩

### 4.3 Spatial Grid & Radii

- **Grid Unit**: 엄격한 `4px` 배수 스케일 (`4px`, `8px`, `12px`, `16px`, `20px`, `24px`, `32px`).
- **Corner Radius**:
  - `radius-xs` (3px): 단축키 캡슐(`Ctrl+K`), 인라인 코드 블록
  - `radius-sm` (5px): 기본 버튼, 텍스트 입력창, Context 칩
  - `radius-md` (8px): 카드, 패널 분할 영역, 콘솔 결과 박스
  - `radius-lg` (12px): 모달 창, 플로팅 팝오버
  - `radius-full` (9999px): 상태 인디케이터 Dot, 원형 아바타

---

## 5. 화면별 컴포넌트 상세 사양 (Feature Specifications)

### 5.1 Python Practice & Runner (LeetCode + Replit 모델)
- **Header Bar (38px)**:
  - 파일 라벨: `solution.py` (파이썬 로고 아이콘 포함).
  - 런타임 뱃지: `Pyodide v0.26.4 (Isolated Origin 5174) ●` (준비 완료 시 녹색 펄스).
  - 액션 버튼군:
    - `▶ 실행 (Ctrl+Enter)`: Primary Indigo 버튼 (`#5e6ad2`), 150ms 프레스 인터랙션.
    - `■ 중단`: 비상 취소 버튼 (실행 중에만 활성화).
    - `⏱ 3초 타임아웃 검증`: `while True` 무한루프 안전 차단 테스트 버튼.
- **Monaco Code Editor (상단 60%)**:
  - VS Code Dark+ 테마, 글꼴 `JetBrains Mono` 13.5px, 줄간격 1.55.
  - 접기(Code Folding), 미니맵(선택적), 자동 괄호 완성 지원.
- **Split Console Runner (하단 40%)**:
  - **Tabs**:
    - `Test Cases (2/2 통과)`: 개별 테스트 결과 카드 뷰.
    - `Stdout`: `print()` 출력 전용 터미널 화면.
  - **Test Case Result Card**:
    - 통과 상태: 좌측 3px 에메랄드 보더, `PASS` 뱃지, 소요 시간 (`3ms`).
    - 실패 상태: 좌측 3px 로즈 보더, `FAIL` 뱃지, `입력값(Input)`, `실제값(Actual)`, `기대값(Expected)`을 3열로 나란히 비교하는 Diff 그리드.
    - 타임아웃 상태: 로즈 배경 안내 배너 (`"실행 시간 제한(3초)을 초과하여 중단되었습니다. Worker가 자동으로 복구되었습니다."`).
  - **Stdout Panel**:
    - 검은 콘솔 배경 (`#08090a`), 녹색 프롬프트 기호 (`>`).
    - 64 KiB 초과 시 주황색 경고 뱃지와 함께 `[출력 제한(64 KiB)을 초과하여 이후 출력이 잘렸습니다]` 안내문 표시.

### 5.2 Wiki Explorer & Viewer (Obsidian + Perplexity 모델)
- **Explorer (좌측 사이드바)**:
  - 3개 Collection (`CS`, `Backend`, `Algorithm`) 폴더 아코디언.
  - 파일 클릭 시 중앙 뷰어 즉시 렌더링, 현재 파일 하이라이트.
- **Main Reader Canvas**:
  - 가독 너비: 최대 820px 중앙 정렬, 라인 높이 1.75.
  - 마크다운 스타일링:
    - Code Block: 언어 라벨, 원클릭 복사 버튼, 미세 테두리.
    - Blockquote: 좌측 인디고 세로선(`3px solid var(--accent-primary)`), 은은한 서피스 배경.
    - Tables: 1px 헤어라인 보더, 홀수 행 미세 배경 분할, 헤더 볼드.
- **Floating TOC (우측 스티키 목차)**:
  - 폭 180px, 문서 내 H1, H2, H3 제목을 트리 형태로 스티키 표시.
  - 본문 스크롤 위치에 맞춰 현재 읽고 있는 섹션에 인디고 바 인디케이터 부착.

### 5.3 Page & Coding Record (Notion + BlockNote 모델)
- **Document Canvas**:
  - 문서 타이틀: 30px 대형 타이포그래피, 엔터 입력 시 첫 블록 자동 생성.
  - 블록 인터랙션: 마우스 호버 시 블록 좌측에 6점 드래그 핸들(`:::`)과 추가 버튼(`+`) 노출.
- **Optimistic Revision Indicator**:
  - 우상단에 저장 상태 실시간 표기:
    - `저장 중...` (회색 회전 점)
    - `저장됨 (Rev 4)` (은은한 녹색 체크)
    - `충돌 발생(409): 새로고침 필요` (앰버 경고)

### 5.4 AI Multi-turn Chat & Copilot (Cursor + Windsurf 모델)
- **Active Context Pill Bar (채팅창 상단)**:
  - 캡슐 형태의 칩 태그 나열:
    - `[📄 Wiki: 해시 테이블 원리 ×]`
    - `[💻 Code: solution.py (v1) ×]`
    - `[📝 Page: 나의 오답노트 ×]`
  - 태그 클릭 시 해당 문서로 중앙 캔버스 전환, X 클릭 시 컨텍스트 제거.
- **AI Chat Message Feed**:
  - User Message: 우측 정렬 컴팩트 버블, 짙은 서피스 배경.
  - Assistant Message: 좌측 전폭, 기술 문서 스타일 렌더링.
  - **Tool Execution Accordion**:
    - `Wiki MCP 검색: "해시 충돌"` -> 접혀 있는 상태에서 성공 시 녹색 체크, 클릭 시 검색된 Note 3건 목록 확장.
  - **Source Reference Card (출처 카드)**:
    - 답변 하단에 인용된 Wiki 파일명, 라인 범위(`L42-L58`), 발췌문을 담은 카드 컴포넌트 노출.
    - 카드 클릭 시 좌측 Wiki 뷰어에서 해당 라인으로 스무스 스크롤 이동 및 2초간 하이라이트.
- **Prompt Input Box**:
  - 포커스 시 인디고 포커스 링(`0 0 0 1px var(--accent-primary)`).
  - 엔터 전송, Shift+Enter 줄바꿈, `/` 명령어 지원.

---

## 6. 마이크로 인터랙션 및 애니메이션 가이드 (Motion)

화려함보다는 즉각성과 부드러움을 주는 고성능 CSS 트랜지션을 적용한다.

1. **지속 시간 (Duration)**:
   - 미세 호버/포커스: `120ms`
   - 패널 접기/펼치기: `200ms`
   - 드롭다운/모달 페이드인: `150ms`
2. **이징 (Easing)**:
   - `cubic-bezier(0.16, 1, 0.3, 1)`: Linear가 사용하는 세련되고 날렵한 스프링 느낌의 감속 곡선.
3. **상태 피드백 인터랙션**:
   - 버튼 누름(Active): `transform: scale(0.98)` 미세 축소.
   - 복사 완료: '복사' 텍스트가 1.5초간 '복사됨!' 녹색 체크 아이콘으로 전환.
   - 런타임 실행 중: 실행 버튼 우측의 스피너 회전 및 상태 점 펄스(Pulse) 애니메이션.

---

## 7. 키보드 우선(Keyboard-First) 단축키 체계

| 단축키 | 동작 | 비고 |
|---|---|---|
| `Ctrl + Enter` | Python 코드 실행 및 Test Case 검증 | Practice 모드 |
| `Ctrl + B` | 좌측 탐색 사이드바 토글 (접기/펼치기) | 글로벌 |
| `Ctrl + L` | 우측 AI Chat 패널 토글 (접기/펼치기) | 글로벌 |
| `Ctrl + K` | 글로벌 커맨드 팔레트 열기 | 검색 및 빠른 이동 |
| `Alt + 1 ~ 5` | 모드 전환 (1:Wiki, 2:Study, 3:Page, 4:Practice, 5:Task) | 글로벌 |
| `Esc` | 모달/팝오버 닫기 및 포커스 해제 | 글로벌 |
