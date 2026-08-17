# MCM AI Concierge

MCM 제품 정보를 기반으로 고객 질문에 답변하는 RAG 컨시어지입니다.  
제품 식별은 `modelCode`(style_number) 기준입니다.

## 폴더 구조

```
MS/
├── api.py                  # FastAPI 스트리밍 API
├── chat_openai.py          # OpenAI RAG + 답변 생성
├── chat_ui_openai.py       # OpenAI Gradio UI
├── build_rag_documents.py  # 제품 JSON → RAG 문서
├── build_vector_db.py      # RAG 문서 → 벡터 DB
├── test_search.py          # 검색 테스트
├── paths.py                # 경로 설정
├── database/               # 원본 제품 데이터
├── rag/                    # RAG 문서 (jsonl)
├── vector_db/              # 임베딩 인덱스
├── config/                 # OpenAI 설정
└── qwen/                   # Qwen 로컬 모델 (선택)
    ├── chat.py
    └── chat_ui.py
```

## 준비

1. OpenAI API 키 설정

```bash
cp config/openai_config.example.json config/openai_config.json
# config/openai_config.json 에 api_key 입력
```

또는 환경 변수:

```bash
export OPENAI_API_KEY="sk-..."
```

2. RAG / 벡터 DB 생성 (제품 데이터 변경 시 재실행)

```bash
python build_rag_documents.py
python build_vector_db.py
```

## 실행

### OpenAI UI (권장)

```bash
python chat_ui_openai.py
```

브라우저: http://127.0.0.1:7861

### OpenAI CLI

```bash
python chat_openai.py
```

### FastAPI (백엔드 연동)

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

- Health: `GET /health`
- Chat: `POST /chat/stream`

요청 예:

```json
{
  "modelCode": "MWRAAME01CO001",
  "message": "비 오는 날 써도 될까요?"
}
```

### Qwen (로컬 GPU, 선택)

```bash
python qwen/chat.py
python qwen/chat_ui.py
```

## 데이터 흐름

```
database/mcm_products_v2.json
  → build_rag_documents.py
  → rag/documents.jsonl
  → build_vector_db.py
  → vector_db/
  → chat_openai / api
```

## 참고

- 검색 키: `modelCode` (= 제품 `style_number`)
- OpenAI 버전은 서버 배포용으로 권장
- `config/openai_config.json`은 Git에 올리지 마세요
