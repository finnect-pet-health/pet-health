# PetFinect (가제)

> 반려견 AI 헬스케어 + 의료비 예측·적금 통합 플랫폼
> **FIN:NECT 챌린지 2026 출품작** (AI 트랙 · AI 헬스케어 & 라이프스타일)

케어테일 워치+AI로 반려견 건강 이상을 조기에 잡고, 예상 의료비를 미리 알려 자동 적금을 권장하며, 가족이 함께 케어하고 보호소 후원으로 사회적 가치까지 잇는 가족형 펫케어 OS.

## 모노레포 구조

```
.
├── apps/
│   ├── mobile/        React Native (Expo) - iOS/Android 앱
│   ├── api/           FastAPI - 클라우드 백엔드 API
│   └── ai-server/     FastAPI - 로컬 RTX 5090 AI 추론 서버
├── packages/
│   ├── shared-types/  OpenAPI codegen (TS + Python)
│   └── ui/            React Native 공통 컴포넌트
├── infra/
│   ├── etl/           공공데이터 동물병원 ETL
│   └── tunnels/       Cloudflare Tunnel 설정
├── docs/
│   ├── proposal-outline.md     사업계획서 초안
│   ├── specs/                  서브시스템 상세 설계
│   └── spikes/                 외부 API 연동 가이드
└── docker-compose.yml          Postgres + Redis + API (개발용)
```

## 빠른 시작

```bash
# 1. 환경변수 준비
cp .env.example .env
# (필수 키: KAKAO_REST_API_KEY, KAKAO_NATIVE_APP_KEY, CARETAIL_CLIENT_ID, ...)

# 2. 인프라 기동 (Postgres + Redis)
docker compose up -d postgres redis

# 3. 백엔드 API
cd apps/api
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 4. 로컬 AI 서버 (별도 머신/RTX 5090)
cd apps/ai-server
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --port 8800

# 5. 모바일 앱
cd apps/mobile
pnpm install
pnpm start         # Expo dev server
```

## 주요 문서

- [시스템 아키텍처 plan](../../.claude/plans/ai-compressed-codd.md)
- [사업계획서 초안](docs/proposal-outline.md)
- [Auth & Family RBAC spec](docs/specs/auth-and-family.md)
- [AI 헬스 분석 spec](docs/specs/02-health-analysis.md)
- [의료비 예측·적금 spec](docs/specs/05-medical-budget-savings.md)
- [외부 API 연동 가이드](docs/spikes/external-apis.md)

## 일정

| 마일스톤 | 일정 |
|---|---|
| 서류 제출 | 2026-05-25 |
| 결과 발표 | 2026-06-05 |
| 지역 예선 | 2026-06-30 ~ 07-10 |
| 통합 본선 | 2026-08-24 ~ 08-28 |

## 라이선스

Private (대회 출품용). 본선 통과 후 라이선스 정책 결정.
