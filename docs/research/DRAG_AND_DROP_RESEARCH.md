# 메모장·워크스페이스 드래그앤드롭 검토

> 참고 기록: 이 문서는 Library 비교와 선택 근거다. 아래 구현 순서는 현재 Release 조건이 아니다.
> 현재 Release 범위는 [Project Plan](../PROJECT_PLAN.md)을 따른다.
> 기술 선택과 Multi-turn 계약은 [Architecture](../ARCHITECTURE.md)를 따른다.
> 기존 본문의 초기 수량과 후보는 현재 완료 조건이 아니다.
> 앞으로의 수정에는 [문서 작성 규칙](../DOCUMENTATION_STYLE.md)을 적용한다.

공식 자료 확인일: 2026-10-02
상태: 라이브러리 조사 및 설계 추천. 설치·통합 테스트는 진행하지 않음.

최종 채택은 [Architecture](../ARCHITECTURE.md)를 따른다. BlockNote 일반 Core와 React-Grid-Layout v2를 선택했으며 아래 비교는 선택 근거다. 다른 Library는 초기 의존성이 아니다.

사용자 요구는 세 가지 모두다. 메뉴에서 블록을 끌어 메모를 구성하고, 메모·할 일·캘린더 위젯을 배치하며, 문서 내부 블록 순서도 바꿀 수 있어야 한다.

## 1. 후보와 역할

| 후보 | 담당 영역 | 판단 |
|---|---|---|
| React-Grid-Layout | React 위젯의 격자 배치·크기 변경·반응형 레이아웃·외부 드롭 | v2 채택. 임의 좌표의 무한 캔버스와는 구분 |
| BlockNote | 블록 기반 메모 편집, 블록 드래그, 메뉴, 사용자 정의 블록 | 일반 코어 채택. 화면 위젯 배치 기능은 별도 |
| dnd-kit | 메뉴와 드롭 영역, 목록 정렬 등 사용자 정의 상호작용 | 자체 블록/카드 UI를 만들 때 유력. 완성된 텍스트 편집기나 리사이즈 레이아웃은 제공하지 않음 |
| Tiptap | 확장 가능한 텍스트 편집기와 Drag Handle | 편집 구조를 더 세밀하게 제어할 때 대안. 필요한 메뉴·블록 UI를 구성해야 함 |
| React DnD | 드래그 원본·대상과 데이터 전달, 교체 가능한 입력 백엔드 | 복잡한 타입별 드롭에 후보. 화면 배치·문서 편집은 별도 구현 |
| Pragmatic drag and drop | 웹 플랫폼 기반의 드래그앤드롭과 선택적 패키지 | 범용 대안. 코어가 접근성 조작을 자동으로 모두 제공하지 않으므로 대체 이동 메뉴 등을 구성 |

React-Grid-Layout과 dnd-kit은 MIT, BlockNote 일반 라이브러리는 MPL-2.0이다. BlockNote XL은 GPL-3.0/상용 라이선스로 구분된다. Tiptap 오픈소스 코어는 MIT이며 모든 확장·서비스가 같은 조건인 것은 아니다. React DnD는 MIT다. 초기 추천은 BlockNote 일반 기능을 사용하며 XL AI·다단 레이아웃 등은 의존하지 않는다.

react-beautiful-dnd는 공식 저장소가 아카이브되어 신규 선택에서 제외한다. dnd-kit은 현재 문서의 @dnd-kit/react API와 과거 @dnd-kit/core/@dnd-kit/sortable 예제를 구분한다. React-Grid-Layout도 v2와 이전 API를 혼용하지 않고 설치한 릴리스에 맞춘다.

## 2. 확정 조합과 연결

확정 조합은 React-Grid-Layout v2 + BlockNote 일반 코어다. dnd-kit이나 React DnD는 초기 의존성에서 제외한다. 외부 드롭과 문서 내 위치 계산이 실제 검증에서 부족할 때 필요한 범위만 추가한다. 이 조합의 적합성은 공식 기능 설명을 바탕으로 한 설계 판단이며 통합 동작을 확인한 결과는 아니다.

```text
메뉴 패널
  ├─ 위젯: 메모장 / 할 일 / 캘린더 → 격자 워크스페이스에 추가
  └─ 메모 블록: 텍스트 / 제목 / 체크리스트 / 코드 / 자료 링크
                                         → 선택한 메모에 추가

워크스페이스: React-Grid-Layout
  ├─ 메모 위젯: BlockNote, 내부 블록 편집·정렬
  ├─ 할 일 위젯: 기존 Task Service 연결
  └─ 캘린더 위젯: 기존 Calendar Service 연결
```

메뉴에는 어떤 곳에 놓을 수 있는지 표시한다. 메뉴 항목은 템플릿이므로 드롭하면 새 인스턴스를 생성하고 메뉴에서는 사라지지 않는다. 기존 위젯 이동은 같은 ID를 유지한다. 블록 종류는 허용된 스키마로 변환한다. 외부 메뉴에서 메모로 넣는 동작은 앱이 드롭 위치를 해석하고 editor.insertBlocks 같은 편집 API에 연결해야 한다. 기본 드래그 기능만으로 이 연결이 완성된다고 가정하지 않는다.

격자 배치는 화면의 행·열과 크기로 정리하는 방식이다. 사용자 요구가 겹치는 창이나 무한 캔버스의 임의 좌표 이동까지 포함하면 별도 검토한다. 현재는 기능 추가 없이 세 요구를 충족할 수 있는 격자 방식부터 검증한다.

## 3. 구현 시 필요한 계약

- 위젯 이동은 상단 손잡이, 문서 블록 이동은 내부 손잡이로 시작한다. 텍스트 선택·한글 입력·스크롤을 드래그로 오인하지 않는다.
- 위젯·문서 블록 드롭 구역을 구분하고 한 드롭이 두 동작을 일으키지 않게 한다. 캘린더 내부 일정 이동도 외부 위젯 이동과 구분한다.
- 격자 좌표·크기·화면 크기별 배치와 메모 블록 JSON을 별도로 저장한다. 영구 ID와 스키마 버전을 사용하고 재시작 후 복원한다.
- 메모 내용 저장은 변경 이벤트를 모아 처리하고, 위젯 위치는 드롭·리사이즈 종료에 저장한다. 저장 중·완료·실패 상태를 표시하며 실패 시 내용을 보존한다.
- 메모의 체크리스트는 기본적으로 메모 내용이다. 실제 할 일과 연결하려면 task_id를 가진 연결 블록/위젯으로 구분하고 Task Service를 사용한다.
- 위젯 제거와 메모 원문 삭제를 구분한다. 캘린더 위젯을 닫아도 실제 일정은 삭제되지 않는다.
- 직접 추가 버튼, 위/아래 이동 메뉴, 키보드 조작을 제공한다. 모바일에서는 좁은 화면에 맞게 세로 배치한다.
- 메모를 AI에 전달할 때 선택 범위를 명확히 한다. 모든 메모를 자동으로 Memory에 넣지 않는다. 이후 메모 Tool도 같은 Note Service를 사용하고 기존 Harness에서 실행한다.
- BlockNote 블록 JSON을 편집 원본으로 유지하고 Markdown은 내보내기 형식으로 다룬다. 사용자 정의 블록과 위키 링크가 Markdown 왕복에서 보존되는지는 별도 검증한다. 기존 위키는 자동 수정하지 않는다.

## 4. 작은 검증부터

메뉴 항목 드롭 → 메모 위젯 생성 → 한글·코드·체크리스트 작성 → 내부 블록 정렬 → 위젯 이동·크기 변경 → 저장·새로고침 복원 순으로 검증한다. 그다음 실제 할 일·캘린더 위젯을 연결하고 중첩 드래그를 확인한다. 대표 실패는 입력 중 위젯 이동, 잘못된 대상 드롭, 저장 실패, 취소, 좁은 화면에서 위치 손실이다.

## 5. 공식 근거

- [React-Grid-Layout: 기능·외부 드롭·라이선스](https://github.com/react-grid-layout/react-grid-layout)
- [BlockNote: 문서·블록 커스터마이징](https://www.blocknotejs.org/docs)
- [BlockNote: 기능·라이선스 구분](https://www.blocknotejs.org/pricing)
- [BlockNote: 편집 API](https://www.blocknotejs.org/docs/reference/editor/manipulating-content)
- [dnd-kit: React 시작](https://dndkit.com/react/quickstart/)
- [dnd-kit: 라이선스·입력 방식](https://github.com/clauderic/dnd-kit)
- [Tiptap: 편집기 구조](https://tiptap.dev/docs/editor/getting-started/overview)
- [Tiptap: Drag Handle](https://tiptap.dev/docs/editor/extensions/functionality/drag-handle)
- [React DnD: 공식 문서](https://react-dnd.github.io/react-dnd/docs/)
- [Pragmatic drag and drop: 접근성](https://atlassian.design/components/pragmatic-drag-and-drop/accessibility-guidelines)
- [react-beautiful-dnd: 공식 아카이브 상태](https://github.com/atlassian/react-beautiful-dnd)
