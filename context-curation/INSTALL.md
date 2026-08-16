# context-curation 설치·운영 가이드

이 문서는 **설치·운영 담당자용**입니다. Agent가 실행 중 따라야 할 감사, 수확, 승격,
제안·적용 절차의 기준 문서는 `SKILL.md`입니다.

## 1. 설치 위치

opencode는 다른 구성요소와 마찬가지로 **단수형 디렉토리**를 씁니다
(`.opencode/agent/`, `.opencode/command/`, `.opencode/skill/`).

**프로젝트 전용:**
```
<프로젝트>/.opencode/skill/context-curation/
```

**모든 프로젝트에서 공용 (권장):**
```
~/.config/opencode/skill/context-curation/
```

이 스킬은 프로젝트마다 다시 만들 이유가 없으므로 전역 설치가 낫습니다.
압축을 풀어 폴더째로 복사하면 끝입니다.

```bash
unzip context-curation.zip -d ~/.config/opencode/skill/
opencode
```

설치 확인은 새 세션에서 `/skills` 또는 에이전트에게 "context-curation 스킬 있어?"로 하면 됩니다.

### 슬래시 커맨드도 같이 설치 (GLM 5.2 환경에서는 권장)

`command/tune-docs.md`를 커맨드 디렉토리에 복사하면 `/tune-docs`로 명시 호출할 수 있습니다.

```bash
cp ~/.config/opencode/skill/context-curation/command/tune-docs.md \
   ~/.config/opencode/command/tune-docs.md
```

스킬 자동 트리거는 모델이 description을 보고 "이 스킬을 읽어야겠다"고 판단해야 작동합니다.
Claude 계열은 이게 꽤 안정적인데, 오픈웨이트 모델은 편차가 큽니다. 명시 커맨드가 있으면
자동 트리거가 안 될 때의 대비책이 되고, 자동 트리거가 잘 되면 그냥 안 쓰면 됩니다.

## 2. 기존 셋업에 연결하기

다음 프로젝트 구조를 기준으로 연동합니다.

```
<프로젝트>/
├── AGENTS.md              ← session-context-init 이 생성
├── plan.md                ← session-context-init 이 생성
└── docs/
    ├── handoff.md         ← session-handoff 가 매 세션 갱신
    ├── session-log.md     ← session-handoff 가 append (## Session NNN 헤딩)
    ├── decisions.md       ← session-handoff 가 append
    └── .curation-state.json   ← 첫 승인 실행이 생성·관리
```

`integration/` 폴더에는 두 개의 설치 조각과 한 개의 설명 문서가 있습니다.

1. **`session-handoff-snippet.md`** — 공유 `session-handoff/SKILL.md`에 project override
   hook을 한 번 추가합니다. `docs/handoff-spec.md`가 생기면 먼저 읽고 따르게 하는 유일한
   공유 스킬 수정입니다.
2. **`agents-md-snippet.md`** — 프로젝트 AGENTS.md의 포인터 표에 한 줄을 추가합니다.
   자동 트리거가 불안정해도 5세션 주기와 문서 이상 징후를 인식하게 합니다.
3. **`README-integration.md`** — 위 두 조각과 프로젝트 로컬 handoff spec의 관계를
   설명합니다. 설치 대상은 아닙니다.

첫 승인된 curation 실행이 `docs/handoff-spec.md`와 `docs/.curation-state.json`을 필요할 때
생성합니다. 미리 placeholder 상태 파일을 복사하거나 날짜를 손으로 채우지 마세요. 상태 파일이
없거나 읽을 수 없으면 감사 스크립트는 전체 로그에서 태그를 추출한 뒤 최근 5개 세션 항목을
bootstrap 범위로 안내합니다.

`handoff-spec.md`가 생기기 전에는 기존 `session-handoff` 기본 동작이 그대로 유지됩니다.
태그와 curation 주기 검사는 첫 spec이 승인된 뒤부터 프로젝트 로컬 규칙으로 적용됩니다.

### 공유 파일 정책

큐레이션은 **프로젝트 디렉토리 밖에 아무것도 쓰지 않습니다.**

| 변경 성격 | 대상 | 적용 주체 |
|---|---|---|
| 이 프로젝트 전용 (문서 집합, 주기, 필드) | `docs/handoff-spec.md` | 큐레이션 (승인 후) |
| 일반화 가능 (모든 프로젝트가 원할 개선) | 제안서 섹션 G에 메모만 | 공유 스킬 관리자 |

전역 handoff 스킬을 여러 프로젝트가 공유하는 이상, 그 파일은 다른 프로젝트들을 함께 고려한
사람이 판단해서 바꿔야 합니다. 한 프로젝트의 튜닝 실행에서 부수적으로 바뀌면, 증거는 그
프로젝트 하나 폭이고 검토자는 그 프로젝트 문서만 보고 있는 상태가 됩니다. 게다가 전역 파일
수정은 어느 프로젝트 기록에도 흔적이 안 남아서 나중에 복원이 안 됩니다.

섹션 G는 **실행 항목이 아니라 운영자 검토용 메모**입니다. 공유 스킬 관리자가 다른 프로젝트에
미칠 영향을 확인한 뒤 별도로 적용합니다.

`session-handoff`가 프로젝트 로컬(`.opencode/skill/`)에 있다면 이 구분이 사라집니다.
전부 프로젝트 범위이고 spec 파일도 선택사항이며, SKILL.md를 직접 고쳐도 됩니다.

## 3. 사용법

명시적으로 부르는 경우:

```
AGENTS.md가 너무 커진 것 같아. context-curation 스킬로 문서 레이어 정리해줘.
```

또는 그냥 상황만 말해도 트리거되도록 description을 써 두었습니다:

```
에이전트가 자꾸 같은 걸 까먹어. 문서 구조 좀 손봐줘.
M2 마일스톤 끝났으니 문서 정리하자.
```

에이전트는 감사 → 수확 → 분류 → 제안 순으로 진행하고
`docs/_tuning-proposal.md`를 쓴 뒤 **멈춥니다.** 승인 전에는 아무것도 안 고칩니다.
제안서를 읽고 항목별로 승인/거부하면 그때 적용합니다.

## 4. 감사 스크립트 단독 실행

스킬 없이 현황만 보고 싶을 때:

```bash
python ~/.config/opencode/skill/context-curation/scripts/docs_inventory.py --root .
# project-local installation:
# python .opencode/skill/context-curation/scripts/docs_inventory.py --root .
```

표준 라이브러리만 쓰고 네트워크 접근이 없어서 사내망에서 그대로 돕니다.
Python 3.8 이상이면 됩니다. 환경에서 실행 파일 이름이 `python3`이면 그 이름을 사용하세요.

주요 옵션:

| 옵션 | 기본값 | 의미 |
|---|---|---|
| `--l0-budget` | 2000 | AGENTS.md 토큰 상한 |
| `--l1-budget` | 1500 | plan.md / handoff.md 상한 |
| `--stale-days` | 90 | 이보다 오래된 문서를 의심 대상으로 표시 |
| `--dup-threshold` | 0.45 | 문단 중복 판정 유사도 (0~1) |
| `--context-window` | 200000 | 수확 범위를 계산할 컨텍스트 크기 |
| `--bootstrap-sessions` | 5 | 상태 파일이 없을 때 본문을 읽을 최근 세션 수 |
| `--json` | | 사람 대신 에이전트가 읽을 형식 |

토큰 수치는 문자 수 기반 **추정치**입니다(한글은 1.5자/토큰, ASCII는 4자/토큰 가정).
±20% 정도로 보시면 되고, 절대값보다 추세를 보는 용도입니다.
사내 모델의 실제 토크나이저와는 다르므로, 정확한 값이 필요하면
`estimate_tokens()` 함수만 사내 토크나이저로 바꿔 끼우면 됩니다.

## 5. 운영 설정

### L0 예산

기본값은 2,000 토큰입니다. 이 값은 비용 한도가 아니라 AGENTS.md를 라우팅 표로 유지하기 위한
형태 제약이므로, 컨텍스트가 크다는 이유만으로 올리지 마세요. 조정이 꼭 필요하면 다음 세 곳을
같이 변경합니다.

1. `SKILL.md`의 레이어 표
2. `references/agents-md-contract.md`의 Budget enforcement
3. 감사기 실행의 `--l0-budget` 또는 스크립트 기본값

### 사내 모델

- 외부 API나 추가 Python 패키지는 필요하지 않습니다. Python 3.8+만 준비하세요.
- 자동 스킬 트리거가 불안정하면 `/tune-docs` 명령을 사용하세요.
- 처음 두세 번은 제안서가 생성된 뒤 실제 문서가 승인 전에 바뀌지 않았는지 확인하세요.
- 짧은 컨텍스트 모델보다 감사 결과와 세션 기록을 함께 처리할 수 있는 모델을 사용하세요.

## 6. 문제 해결

| 증상 | 확인할 것 |
|---|---|
| `/tune-docs`가 없음 | `command/tune-docs.md`를 `~/.config/opencode/command/`에 복사했는지 확인 |
| 자동 호출이 안 됨 | AGENTS.md에 `integration/agents-md-snippet.md`를 추가했는지 확인 |
| handoff spec이 무시됨 | 공유 `session-handoff/SKILL.md`에 project-override hook이 있는지 확인 |
| 감사기가 실행되지 않음 | Python 3.8+와 설치 위치에 맞는 스크립트 경로 확인 |
| 상태 파일이 없음 | 정상적인 첫 실행일 수 있음; 직접 만들지 말고 첫 승인 실행에서 생성 |
| 승인 전에 문서가 변경됨 | 적용하지 말고 제안서만 남긴 뒤 `SKILL.md`의 Step 5 준수 여부 확인 |
| 섹션 G가 자동 적용됨 | 되돌린 뒤 공유 스킬 관리자가 영향 범위를 별도로 검토 |

`references/`를 읽지 않는 것 자체는 오류가 아닙니다. 정상 경로는 `SKILL.md`만으로 완결되고,
참조 문서는 경계 사례나 상세 포맷이 필요할 때만 읽습니다.
