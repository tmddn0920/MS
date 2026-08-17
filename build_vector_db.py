import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from paths import (
    RAG_DOCUMENTS_PATH,
    VECTOR_DB_DIR,
    VECTOR_DOCUMENTS_PATH,
    VECTOR_INDEX_PATH,
)


MODEL_NAME = "BAAI/bge-m3"


documents = []

with RAG_DOCUMENTS_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        if line:
            documents.append(json.loads(line))


print(f"총 {len(documents)}개의 RAG 문서를 불러왔습니다.")


print("\nEmbedding 모델을 불러오는 중입니다...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding 모델 로딩 완료.")


texts = []

for doc in documents:

    search_text = (
        f"Product: {doc['product_name']}\n"
        f"ModelCode: {doc.get('modelCode', '')}\n"
        f"Category: {doc.get('category', '')}\n"
        f"Subcategory: {doc.get('subcategory', '')}\n"
        f"Topic: {doc['topic']}\n"
        f"{doc['text']}"
    )

    texts.append(search_text)


print("\nRAG 문서를 embedding으로 변환하는 중입니다...")

embeddings = model.encode_document(
    texts,
    normalize_embeddings=True,
    show_progress_bar=True
)

embeddings = np.asarray(embeddings, dtype="float32")

print("Embedding 완료.")
print("Embedding shape:", embeddings.shape)


dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

print("\nFAISS index 생성 완료.")
print("저장된 vector 수:", index.ntotal)


VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

faiss.write_index(
    index,
    str(VECTOR_INDEX_PATH)
)

with VECTOR_DOCUMENTS_PATH.open("w", encoding="utf-8") as f:

    json.dump(
        documents,
        f,
        ensure_ascii=False,
        indent=2
    )


print("\n완료!")
print(VECTOR_INDEX_PATH)
print(VECTOR_DOCUMENTS_PATH)
print("파일이 생성되었습니다.")
