# RAG vs LLM 학습 프로젝트

아래는 프로젝트의 간단한 폴더 구조입니다.

```
.
├── backend
│   ├── app
│   │   ├── __init__.py
│   │   ├── db.py
│   │   └── main.py
│   └── requirements.txt
└── frontend
    ├── app.js
    ├── index.html
    └── styles.css
```

## 환경 변수

아래 환경 변수는 백엔드 실행 시 필요합니다. `python-dotenv`를 사용하므로
`backend/.env`에 환경 변수를 저장하면 자동으로 로드됩니다.

- `MONGODB_URI`: MongoDB Atlas 접속 문자열
- `MONGODB_DB`: 데이터베이스 이름 (기본값: `rag_learning`)
- `MONGODB_COLLECTION`: 컬렉션 이름 (기본값: `rag_documents`)
- `VECTOR_INDEX_NAME`: Vector Search 인덱스 이름 (기본값: `rag_vector_index`)
- `OPENAI_API_KEY`: OpenAI API 키

예시 (`backend/.env`):
```
MONGODB_URI=mongodb+srv://...
OPENAI_API_KEY=sk-...
```

## 기술 스택

- **Backend**: Python, FastAPI, MongoDB Atlas (Vector Search), OpenAI API, DuckDuckGo Search, BeautifulSoup
- **Frontend**: HTML, JavaScript (Vanilla), CSS

## 시스템 구조 (Architecture)

이 프로젝트는 **RAG (Retrieval-Augmented Generation)** 패턴을 사용하여 정확한 답변을 제공합니다.

```mermaid
graph TD
    User[사용자] -->|1. 입력/질문| FE[Frontend (Web UI)]
    FE -->|2. API 요청| BE[Backend (FastAPI)]
    
    subgraph "Backend Process"
        BE -->|3. 텍스트 임베딩| AI_Embed[OpenAI (Embedding Model)]
        AI_Embed -.->|Vector| BE
        
        BE -->|4. 데이터 저장/검색| DB[(MongoDB Atlas\nVector Search)]
        DB -.->|5. 관련 지식(Context)| BE
        
        BE -->|6. 프롬프트 구성 (질문+Context)| AI_Chat[OpenAI (GPT-4o)]
        AI_Chat -.->|7. 답변 생성| BE
    end
    
    BE -->|8. 최종 응답| FE
    FE -->|9. 화면 표시| User
```

### 동작 원리
1.  **지식 저장**: 사용자가 입력한 데이터는 임베딩(숫자 벡터)으로 변환되어 **MongoDB Atlas**에 저장됩니다.
2.  **검색 (Retrieval)**: 사용자가 질문하면, 질문을 벡터로 변환하여 DB에서 가장 유사한 내용을 찾습니다 (Vector Search).
3.  **생성 (Generation)**: 찾아낸 내용(Context)과 질문을 합쳐 **GPT-4o**에게 보냅니다.
4.  **응답**: LLM은 오직 제공된 Context에 기반하여 답변을 생성합니다.

## 주요 API 기능

이 프로젝트는 RAG와 일반 LLM의 차이를 학습하기 위해 다양한 엔드포인트를 제공합니다.

### 1. RAG 및 데이터 관리
- **`/rag/store`**: 텍스트 데이터를 임베딩하여 벡터 DB에 저장합니다.
- **`/rag/list`**: 저장된 지식 목록을 조회합니다.
- **`/rag/{document_id}`** (DELETE): 특정 지식을 삭제합니다.

### 2. 챗봇 및 검색
- **`/chat/query`**: 저장된 지식을 기반으로 답변합니다 (RAG).
- **`/chat/route`**: 질문의 유사도 점수에 따라 RAG 사용 여부를 동적으로 결정합니다.

### 3. 웹 수집 및 확장 기능
- **`/business/rag`**: 특정 공급사와 제품을 검색(DuckDuckGo)하여 관련 웹페이지 정보를 수집합니다.
- **`/scrape`**: 지정된 URL의 내용을 스크래핑하고, 옵션에 따라 바로 RAG 데이터로 저장할 수 있습니다.

## 💾 데이터 저장 방법 (Data Storage)

챗봇이 답변할 지식을 추가하는 두 가지 방법입니다.

### 방법 1: 웹 화면 사용 (가장 쉬움)
1. **[http://localhost:5500](http://localhost:5500)** 에 접속합니다.
2. 왼쪽 **"지식 추가"** 입력창에 제품 정보나 정책을 입력합니다.
   - 예: `[제품명] 로스트아크, [출시일] 2018년`
3. **"지식 저장하기"** 버튼을 클릭합니다.

### 방법 2: API 사용 (Postman 등)
**POST** `http://127.0.0.1:8000/rag/store`
- **Header**: `Content-Type: application/json`
- **Body**:
  ```json
  {
    "text": "여기에 챗봇이 알았으면 하는 정보를 입력하세요.",
    "type": "manual_entry"
  }
  ```

## 실행 방법 (예시)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

프론트엔드는 `frontend/index.html`을 브라우저에서 열어 사용합니다.
React는 CDN으로 로드되므로 별도 빌드 과정이 필요하지 않습니다.

##캡쳐
<img width="887" height="698" alt="image" src="https://github.com/user-attachments/assets/d1ded200-5b04-4e05-92d1-94c4ebf83872" />
Postman
<img width="1858" height="724" alt="image" src="https://github.com/user-attachments/assets/090cb8c0-eaa4-447b-a5fe-9f36b98ad71d" />
MongoDB Atlas
<img width="1902" height="913" alt="image" src="https://github.com/user-attachments/assets/d6e5d193-b28c-4d5a-bc19-6a069c3cb829" />
ChatBot


