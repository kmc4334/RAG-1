import os
import sys

# Ensure we can import app.main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_product_qa():
    print("=== 쇼핑몰 Q&A 로직 테스트 시작 ===")

    # 1. 테스트 데이터 저장 (Context 확보)
    product_info = """
    [제품명] 울트라 게이밍 노트북 X1
    [가격] 1,500,000원
    [보증 기간] 2년 무상 보증 (배터리 1년)
    [반품 정책] 개봉 전 7일 이내 반품 가능, 개봉 후 단순 변심 반품 불가.
    """
    
    print(f"\n[Step 1] 테스트 데이터 저장 중...\n내용: {product_info.strip()[:50]}...")
    store_response = client.post("/rag/store", json={
        "text": product_info,
        "type": "product_info"
    })
    
    if store_response.status_code == 200:
        print("-> 저장 성공")
    else:
        print(f"-> 저장 실패: {store_response.text}")
        return

    # 2. 정상 질문 테스트
    question_1 = "울트라 게이밍 노트북 X1의 보증 기간은 어떻게 되나요?"
    print(f"\n[Step 2] 질문 테스트 (정상 케이스)\n질문: {question_1}")
    
    chat_response_1 = client.post("/chat/query", json={"question": question_1})
    if chat_response_1.status_code == 200:
        ans = chat_response_1.json()["answer"]
        print(f"-> 답변: {ans}")
    else:
        print(f"-> 오류: {chat_response_1.text}")

    # 3. 정보 없는 질문 테스트 (Strict Rules 확인)
    question_2 = "이 노트북의 무게는 몇 kg 인가요?"
    print(f"\n[Step 3] 질문 테스트 (정보 부족 케이스)\n질문: {question_2}")
    
    chat_response_2 = client.post("/chat/query", json={"question": question_2})
    if chat_response_2.status_code == 200:
        ans = chat_response_2.json()["answer"]
        print(f"-> 답변: {ans}")
    else:
        print(f"-> 오류: {chat_response_2.text}")
        
    print("\n=== 테스트 종료 ===")

if __name__ == "__main__":
    test_product_qa()
