"""
본 프로젝트는 포스트맨을 통해 API를 호출하여,
정보가 포함된 URL에서 텍스트를 수집하고 이를 임베딩하여
벡터 데이터베이스에 저장한다.
이후 사용자가 챗봇 질의 API를 호출하면,
벡터 DB에 저장된 정보를 검색하여
RAG(Retrieval-Augmented Generation) 방식으로 답변을 생성·응답하는 시스템이다.
"""
from datetime import datetime, timezone
from typing import Any
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

from .db import (
    build_rag_context,
    delete_rag_document,
    get_collection,
    list_rag_documents,
    log_chat,
    store_rag_document,
)

app = FastAPI(title="RAG vs LLM Learning API")

# Allow local frontend to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
    ,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class RagStoreRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Knowledge text to store for RAG")
    entity: str | None = Field(None, description="Target entity for the knowledge")
    slot: str | None = Field(None, description="Information type / slot name")
    type: str | None = Field(None, description="Knowledge type: fact / history / summary")


class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")


class ChatQueryResponse(BaseModel):
    answer: str
    retrieved_documents: list[dict[str, Any]]


class ChatRouteRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    threshold: float = Field(
        0.60,
        ge=0.0,
        le=1.0,
        description="Score threshold to decide whether to use RAG.",
    )


class ChatRouteResponse(BaseModel):
    answer: str
    retrieved_documents: list[dict[str, Any]]
    route: str


class RagDocumentResponse(BaseModel):
    id: str
    text: str
    entity: str | None
    slot: str | None
    type: str | None
    created_at: str | None


class RagListResponse(BaseModel):
    documents: list[RagDocumentResponse]


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}



def helper_embed_and_store(text: str, entity: str | None = None, slot: str | None = None, k_type: str | None = None) -> None:
    client = OpenAI()
    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    print(f"\n[DEBUG] embedding_response:\n{embedding_response}\n")
    vector = embedding_response.data[0].embedding
    document = {
        "type": "rag_document",
        "text": text,
        "entity": entity,
        "slot": slot,
        "knowledge_type": k_type,
        "embedding": vector,
        "created_at": datetime.now(timezone.utc),
    }
    collection = get_collection()
    store_rag_document(collection, document)
    print(f"임베딩 내용이 저장되었습니다: {text[:50].replace('\n', ' ')}...")


@app.post("/rag/store")
def store_rag_knowledge(payload: RagStoreRequest) -> dict[str, str]:
    """
    Store user-provided knowledge for RAG.
    Steps:
      1) Embed the text with OpenAI embeddings.
      2) Save the text + embedding vector to MongoDB Atlas.
    """
    try:
        helper_embed_and_store(payload.text, payload.entity, payload.slot, payload.type)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding/Storage failed: {exc}") from exc

    return {"message": "Knowledge stored successfully."}


@app.get("/rag/list", response_model=RagListResponse)
def list_rag_knowledge() -> RagListResponse:
    """Return recent RAG knowledge documents for the frontend list."""
    collection = get_collection()
    documents = list_rag_documents(collection, limit=50)
    formatted = [
        RagDocumentResponse(
            id=doc["id"],
            text=doc["text"],
            entity=doc.get("entity"),
            slot=doc.get("slot"),
            type=doc.get("knowledge_type"),
            created_at=doc["created_at"].isoformat() if doc["created_at"] else None,
        )
        for doc in documents
    ]
    return RagListResponse(documents=formatted)


@app.delete("/rag/{document_id}")
def delete_rag_knowledge(document_id: str) -> dict[str, str]:
    """Delete a single RAG knowledge document by id."""
    collection = get_collection()
    deleted = delete_rag_document(collection, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted."}


@app.post("/chat/query", response_model=ChatQueryResponse)
def chat_query(payload: ChatQueryRequest) -> ChatQueryResponse:
    """
    RAG-enabled Q&A endpoint.
    Steps:
      1) Embed the question.
      2) Retrieve similar documents from MongoDB Atlas Vector Search.
      3) Build a context block.
      4) Ask the LLM to answer with the context.
      5) Save the chat log for later study.
    """
    client = OpenAI()

    try:
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=payload.question,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {exc}") from exc

    question_vector = embedding_response.data[0].embedding

    collection = get_collection()
    retrieved = build_rag_context(collection, question_vector, limit=3)
    context_text = "\n".join([f"- {doc['text']}" for doc in retrieved])

    system_prompt = "당신은 쇼핑몰 및 제품 Q&A 어시스턴트입니다. Context에 있는 정보를 바탕으로 답변해 주세요."

    user_prompt = (
        "Context:\n"
        f"{context_text}\n\n"
        "사용자 질문:\n"
        f"{payload.question}\n\n"
        "최종 답변:"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Chat completion failed: {exc}") from exc

    answer = completion.choices[0].message.content

    log_chat(
        collection=collection,
        question=payload.question,
        answer=answer,
        retrieved_documents=retrieved,
    )

    return ChatQueryResponse(answer=answer, retrieved_documents=retrieved)


@app.post("/chat/route", response_model=ChatRouteResponse)
def chat_route(payload: ChatRouteRequest) -> ChatRouteResponse:
    """
    Simple query routing endpoint.
    If the top retrieved score is below the threshold, fall back to a plain LLM answer.
    Otherwise use RAG context.
    """
    client = OpenAI()

    try:
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=payload.question,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {exc}") from exc

    question_vector = embedding_response.data[0].embedding
    collection = get_collection()
    retrieved = build_rag_context(collection, question_vector, limit=3)

    top_score = retrieved[0]["score"] if retrieved else 0.0
    use_rag = top_score >= payload.threshold
    route = "rag" if use_rag else "llm"

    system_prompt = "당신은 쇼핑몰 및 제품 Q&A 어시스턴트입니다. Context에 있는 정보를 바탕으로 답변해 주세요."

    if use_rag:
        context_text = "\n".join([f"- {doc['text']}" for doc in retrieved])
        user_prompt = (
            "Context:\n"
            f"{context_text}\n\n"
            "사용자 질문:\n"
            f"{payload.question}\n\n"
            "최종 답변:"
        )
    else:
        # Fallback for LLM-only route, though prompts emphasize strict context usage.
        # Consistency is key, but without context, it will likely say "Not enough info".
        user_prompt = (
            "Context:\n"
            "제공된 정보가 없습니다.\n\n"
            "사용자 질문:\n"
            f"{payload.question}\n\n"
            "최종 답변:"
        )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Chat completion failed: {exc}") from exc

    answer = completion.choices[0].message.content

    log_chat(
        collection=collection,
        question=payload.question,
        answer=answer,
        retrieved_documents=retrieved if use_rag else [],
        route=route,
    )

    return ChatRouteResponse(
        answer=answer,
        retrieved_documents=retrieved if use_rag else [],
        route=route,
    )

class BusinessRequest(BaseModel):
    supplierName: str
    productName: str
    

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def extract_visible_text(html: str) -> str:
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except Exception:
        return ""

def fetch_page_text(session: requests.Session, url: str, timeout: int = 10) -> str | None:
    try:
        resp = session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        ctype = (resp.headers.get("content-type") or "").lower()
        if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
            return None

        resp.encoding = resp.apparent_encoding or resp.encoding
        return extract_visible_text(resp.text)
    except Exception:
        return None

def ddg_search(query: str, k: int = 5) -> list[str]:
    urls: list[str] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=k):
            href = r.get("href")
            if href:
                urls.append(href)
    return urls


@app.post("/business/rag")
def business_rag(payload: BusinessRequest) -> dict[str, Any]:
    print(payload)
    query = f"{payload.supplierName} {payload.productName}".strip()

    urls = ddg_search(query, k=5)
    if not urls:
        raise HTTPException(status_code=502, detail="Search returned 0 results (likely blocked or network issue).")

    texts: list[dict[str, str]] = []
    with requests.Session() as session:
        for url in urls:
            page_text = fetch_page_text(session, url)
            if not page_text:
                continue
            # 너무 커지면 응답 터지니까 페이지당 제한(원하시면 조정)
            texts.append({"url": url, "text": page_text[:20000]})

    return {
        "query": query,
        "urls": urls,
        "fetched": len(texts),
        "documents": texts,
    }

class ScrapeRequest(BaseModel):
    query: str = ""
    urls: list[str]
    store: bool = False


@app.post("/scrape")
def scrape_urls(payload: ScrapeRequest) -> dict[str, Any]:
    """
    Scrape text from the provided URLs.
    If store is True, embed and save to RAG database.
    """
    texts: list[dict[str, str]] = []
    stored_count = 0
    
    # Use a session for connection pooling
    with requests.Session() as session:
        print(f"\n[DEBUG] requests.Session object: {session}\n")
        for url in payload.urls:
            page_text = fetch_page_text(session, url)
            if page_text:
                safe_text = page_text[:20000]
                doc_info = {"url": url, "text": safe_text}
                
                if payload.store:
                    try:
                        helper_embed_and_store(safe_text, entity=payload.query or None, k_type="scraped_web_content")
                        print(f"[Scrape] Successfully stored scraped content from {url}")
                        doc_info["stored"] = True
                        stored_count += 1
                    except Exception as e:
                        doc_info["stored"] = False
                        doc_info["store_error"] = str(e)
                
                texts.append(doc_info)
            else:
                texts.append({"url": url, "error": "Failed to fetch content"})

    return {
        "query": payload.query,
        "urls": payload.urls,
        "fetched": len([t for t in texts if "text" in t]),
        "stored_count": stored_count,
        "documents": texts,
    }
