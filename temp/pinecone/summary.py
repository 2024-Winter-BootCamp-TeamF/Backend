import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from lanchain_openai import ChatOpenAI
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from pineconeTest import pc

from config.settings import PINECONE_API_KEY

# .env 파일에서 환경 변수 로드
load_dotenv()

# Pinecone API 키와 OpenAI API 키 로드
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OpenAI_API_Key")

# 인덱스 이름 설정
index_name = "selective-time"

# 인덱스 열기
index = pc.Index(index_name)

# 모델 및 토크나이저 설정
model_name = "BM-K/KoSimCSE-roberta-multitask"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# 검색 함수 정의
def search_documents(doc_id):
    try:
        # Pinecone 인덱스에서 ID를 사용해 데이터 조회
        result = index.fetch(ids=[doc_id])

        if not result or "vectors" not in result:
            return f"No data found for ID: {doc_id}"

        vector_data = result["vectors"].get(doc_id)
        if vector_data:
            metadata = vector_data.get("metadata", {})
            vector = vector_data.get("vector", [])
            return {"id": doc_id, "metadata": metadata, "vector": vector}
        else:
            return f"No data found for ID: {doc_id}"
    except Exception as e:
        return f"Error fetching data for ID {doc_id}: {str(e)}"




