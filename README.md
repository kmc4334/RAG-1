RAG vs LLM 학습 프로젝트

이 프로젝트는 RAG(Retrieval-Augmented Generation) 와
일반 LLM(컨텍스트 없이 응답) 의 차이를 직접 비교·학습하기 위한 실습용 프로젝트입니다.

웹 또는 API(Postman)를 통해 지식을 저장하고,
사용자 질문 시 벡터 검색 기반(RAG) 으로 답변이 생성되는 전체 흐름을 구현했습니다.

📁 프로젝트 폴더 구조
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

🔐 환경 변수 설정

백엔드는 python-dotenv를 사용하며,
아래 환경 변수는 backend/.env 파일에 설정해야 합니다.

필수 환경 변수

MONGODB_URI : MongoDB Atlas 접속 문자열

MONGODB_DB : 데이터베이스 이름 (기본값: rag_learning)

MONGODB_COLLECTION : 컬렉션 이름 (기본값: rag_documents)

VECTOR_INDEX_NAME : Vector Search 인덱스 이름 (기본값: rag_vector_index)

OPENAI_API_KEY : OpenAI API 키

예시 (backend/.env)
MONGODB_URI=mongodb+srv://...
OPENAI_API_KEY=sk-...

🛠 기술 스택
Backend

Python

FastAPI

MongoDB Atlas (Vector Search)

OpenAI API

DuckDuckGo Search

BeautifulSoup

Frontend

HTML

JavaScript (Vanilla)

CSS

🧠 시스템 아키텍처 (Architecture)

본 프로젝트는 RAG 패턴을 기반으로 동작합니다.

graph TD
    User[사용자] -->|1. 입력/질문| FE[Frontend (Web UI)]
    FE -->|2. API 요청| BE[Backend (FastAPI)]
    
    subgraph "Backend Process"
        BE -->|3. 텍스트 임베딩| AI_Embed[OpenAI (Embedding Model)]
        AI_Embed -.->|Vector| BE
        
        BE -->|4. 데이터 저장/검색| DB[(MongoDB Atlas\nVector Search)]
        DB -.->|5. 관련 지식(Context)| BE
        
        BE -->|6. 프롬프트 구성 (질문 + Context)| AI_Chat[OpenAI (GPT-4o)]
        AI_Chat -.->|7. 답변 생성| BE
    end
    
    BE -->|8. 최종 응답| FE
    FE -->|9. 화면 표시| User

⚙️ 동작 원리

지식 저장

입력된 텍스트를 임베딩(벡터)으로 변환하여 MongoDB Atlas에 저장

검색 (Retrieval)

사용자 질문을 벡터로 변환

Vector Search를 통해 가장 유사한 문서를 검색

생성 (Generation)

검색된 Context + 사용자 질문을 GPT-4o에 전달

Context 기반 답변 생성

응답

최종 답변을 사용자에게 반환

🚀 주요 API 기능
1. RAG 및 데이터 관리

POST /rag/store
텍스트 데이터를 임베딩하여 벡터 DB에 저장

GET /rag/list
저장된 지식 목록 조회

DELETE /rag/{document_id}
특정 지식 삭제

2. 챗봇 및 질의

POST /chat/query
저장된 지식을 기반으로 답변 생성 (RAG)

POST /chat/route
질문 유사도에 따라

RAG 사용

일반 LLM 사용
을 동적으로 분기

3. 웹 수집 및 확장 기능

POST /business/rag
DuckDuckGo를 이용해 특정 공급사·제품 관련 웹 페이지 검색 및 수집

POST /scrape
지정된 URL을 스크래핑하고
옵션에 따라 즉시 RAG 데이터로 저장

💾 데이터 저장 방법
방법 1️⃣ 웹 UI 사용 (권장)

http://localhost:5500 접속

왼쪽 지식 추가 입력창에 정보 입력

예: [제품명] 로스트아크, [출시일] 2018년

지식 저장하기 버튼 클릭

방법 2️⃣ API 사용 (Postman)

POST http://127.0.0.1:8000/rag/store

Headers

Content-Type: application/json


Body

{
  "text": "여기에 챗봇이 알았으면 하는 정보를 입력하세요.",
  "type": "manual_entry"
}

▶ 실행 방법
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload


프론트엔드는 frontend/index.html을 브라우저에서 직접 열어 사용합니다.
(빌드 과정 없음)

📸 실행 화면 캡처
Postman
<img width="1858" height="724" alt="image" src="https://github.com/user-attachments/assets/090cb8c0-eaa4-447b-a5fe-9f36b98ad71d" />
MongoDB Atlas
<img width="1902" height="913" alt="image" src="https://github.com/user-attachments/assets/d6e5d193-b28c-4d5a-bc19-6a069c3cb829" />
Chatbot UI
<img width="887" height="698" alt="image" src="https://github.com/user-attachments/assets/d1ded200-5b04-4e05-92d1-94c4ebf83872" />


