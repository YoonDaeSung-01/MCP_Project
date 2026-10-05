---
name: frontend-design
description: >-
  Frontend visual design guidelines and anti-slop rules.
  Use when designing, building, or refining user interfaces, web components, layouts,
  color systems, typography, and micro-interactions.
---

# Frontend Design Skill

이 Skill은 AI 특유의 천편일률적인 템플릿(보라색 그라디언트, 무의미한 카드 나열 등)을 배제하고,
학습과 개발에 최적화된 고품질 Frontend Interface를 설계하고 구현할 때 적용한다.
기본 디자인 토큰과 규격은 [docs/DESIGN.md](../../../docs/DESIGN.md)를 단일 진실 공급원(SSOT)으로 따른다.

---

## 1. 사전 설계 원칙 (Think Before Styling)

UI Code를 작성하기 전에 다음 항목을 먼저 정의한다.

1. **사용자 맥락 (Audience & Context)**:
   - 본 App은 엔지니어가 알고리즘, 파이썬, 시스템을 깊이 있게 학습하는 개인 도구다.
   - 불필요한 장식(Dazzle)보다 **가독성, 정보 밀도, 시각적 안정감**이 최우선이다.
2. **시각적 정체성 (Tone & Identity)**:
   - Linear 및 Raycast 스타일의 절제된 다크 테마(Dark Mode First).
   - JetBrains 계열의 엔지니어링 신뢰감.
3. **의도적인 인터랙션 (Deliberate Interaction)**:
   - 마우스뿐 아니라 단축키(Keyboard-First)로 즉시 조작 가능한 구조.

---

## 2. 안티-슬롭(Anti-Slop) 디자인 규칙

AI가 생성하기 쉬운 저품질 디자인 패턴을 엄격히 배제한다.

| 금지 패턴 (Anti-Pattern) | 올바른 적용 (Best Practice) |
|---|---|
| 무의미한 보라색/형광 그라디언트 배경 | 단색 레이어드 배경 (`#0D1117`, `#161B22`)과 은은한 경계선 |
| 과도하게 둥근 모서리 (예: 24px+ 버블형) | 절제된 반경 (`4px`, `6px`, 최대 `8px`) |
| 강하고 지저분한 Drop Shadow | 1px 미세 보더(`rgba(255, 255, 255, 0.08)`)와 표면 명도 차이로 깊이감 표현 |
| 일관성 없는 마진과 패딩 | 4px / 8px 배수 그리드 (`4px`, `8px`, `12px`, `16px`, `24px`) 엄수 |
| 폰트 크기만 제각각인 텍스트 나열 | 명확한 계층(Scale 12px ~ 24px)과 Pretendard / JetBrains Mono 조합 |

---

## 3. 타이포그래피와 데이터 표시

1. **폰트 스택**:
   - UI 텍스트: `Pretendard`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif`
   - 코드 및 메트릭: `JetBrains Mono`, `Consolas`, `monospace`
2. **숫자 및 메트릭 표기**:
   - 실행 시간, 줄 번호, 토큰 카운트 등 숫자는 `font-variant-numeric: tabular-nums`를 적용하여 자릿수 흔들림을 방지한다.
3. **가독성 확보**:
   - 본문 텍스트는 최소 `14px` 이상, 행간(`line-height`)은 `1.5 ~ 1.6`을 유지한다.
   - 보조 텍스트는 주 텍스트 대비 명도 차이를 두되 WCAG AA(4.5:1 이상) 대비를 만족한다.

---

## 4. 모션 및 인터랙션 토큰

애니메이션은 시각적 과시가 아니라 사용자의 인지를 돕는 피드백으로 사용한다.

1. **지속 시간**:
   - 호버 / 포커스 / 액티브 피드백: `100ms ~ 120ms`
   - 모달 / 드롭다운 / 패널 토글: `150ms ~ 200ms`
2. **이징 (Easing)**:
   - 부드럽고 날렵한 감속 곡선: `cubic-bezier(0.16, 1, 0.3, 1)`
3. **상태 피드백**:
   - 버튼 클릭: `transform: scale(0.98)` 미세 축소.
   - 포커스 상태: 브라우저 기본 파란 아웃라인 대신 명확한 Accent 포커스 링 제공 (`:focus-visible`).
