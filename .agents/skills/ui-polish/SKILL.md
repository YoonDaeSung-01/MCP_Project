---
name: ui-polish
description: >-
  UI/UX craft audit and polish workflow based on Impeccable principles.
  Use when auditing interfaces, fixing visual edge cases, verifying accessibility,
  responsive behavior, keyboard shortcuts, or performing a pre-release polish pass.
---

# UI Polish Skill (Impeccable Workflow)

이 Skill은 Peter Bakaus의 `Impeccable` 시스템 철학을 바탕으로,
작성된 Frontend 코드의 완성도(Craftsmanship), 시각적 안정성, 접근성 및 엣지케이스를 점검하고 정제할 때 적용한다.

---

## 1. 5대 점검 영역 (Audit Dimensions)

UI 기능 구현이 끝난 후 아래 5가지 축으로 화면을 감사(Audit)한다.

### 1.1 접근성 및 명도 대비 (Accessibility & Contrast)
- [ ] 텍스트와 배경 간 명도 대비가 WCAG AA 기준(일반 텍스트 4.5:1, 큰 텍스트 3:1)을 충족하는가?
- [ ] 텍스트가 없는 아이콘 버튼에 명시적인 `aria-label` 또는 `title` 속성이 부여되었는가?
- [ ] 키보드로 이동 시 `:focus-visible` 상태가 명확하게 시각화되는가? (아웃라인 제거 금지)

### 1.2 레이아웃 및 오버플로우 방어 (Overflow & Responsive Defense)
- [ ] 창 크기가 줄어들었을 때 원치 않는 가로 스크롤바가 발생하지 않는가?
- [ ] 긴 제목이나 경로 텍스트가 컨테이너를 깨뜨리지 않고 말줄임표(`text-overflow: ellipsis`) 또는 적절한 줄바꿈 처리가 되어 있는가?
- [ ] 모바일/태블릿 터치 영역이 최소 `44px x 44px`을 만족하는가?
- [ ] 전체 화면 컨테이너가 모바일 주소창 변화에 대응할 수 있도록 `100dvh`를 적절히 활용하고 있는가?

### 1.3 인터랙션 상태 완전성 (State Completeness)
모든 대화형(Interactive) 컴포넌트는 아래 5가지 상태를 온전히 갖추어야 한다.
- [ ] **Default**: 기본 상태
- [ ] **Hover**: 마우스 진입 시 미세한 피드백 (배경색 전환 등)
- [ ] **Active/Pressed**: 클릭/터치 순간의 반응 (`scale(0.98)` 등)
- [ ] **Focus**: 키보드 탭 진입 시 시각적 포커스 링
- [ ] **Disabled / Loading**: 비활성화 및 처리 중 상태 (커서 `not-allowed`, 투명도 조절, 스피너)

### 1.4 정보 위계와 노이즈 제거 (Noise Reduction & Quieting)
- [ ] 불필요하게 중첩된 테두리(Border on Border)가 없는가?
- [ ] 시각적 요소가 너무 많아 산만할 경우 덜 중요한 박스의 보더를 제거하고 배경색 차이로만 구분했는가?
- [ ] 화면에서 가장 중요한 기본 액션(Primary Action)과 보조 액션(Secondary)의 시각적 비중이 명확한가?

### 1.5 키보드 우선 조작성 (Keyboard-First Navigation)
- [ ] [docs/DESIGN.md §7](../../../docs/DESIGN.md#7-인터랙션-규격-interaction-patterns)의 글로벌 단축키(`Ctrl+Enter`, `Ctrl+B`, `Ctrl+L`, `Ctrl+K`, `Esc`)가 정상 작동하는가?
- [ ] 모달이나 팝오버가 열렸을 때 `Esc` 키로 즉시 닫히며 이전 포커스로 안전하게 복귀하는가?
- [ ] 툴팁이나 버튼에 연결된 단축키 힌트(예: `Ctrl+Enter`)가 시각적으로 표시되는가?

---

## 2. 세부 정제 절차 (Step-by-Step Polish Workflow)

1. **Edge-Case Stress Test**:
   - 극단적으로 긴 텍스트, 빈 데이터 상태(Empty State), 에러 메시지 노출 상태를 브라우저에 주입해 레이아웃 붕괴를 확인한다.
2. **Visual Noise Reduction**:
   - 화면을 멀리서 바라보고, 사용자의 시선이 머물러야 할 핵심 학습/에디터 영역 외에 과도한 장식이나 눈에 띄는 보더를 단순화한다.
3. **Micro-Interaction Tuning**:
   - 전환 타이밍이 너무 느리거나(> 250ms) 즉각적이지 않은 요소를 `100 ~ 200ms` 범위로 조정하여 빠르고 기민한 조작감을 확보한다.
