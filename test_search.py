import json

import numpy as np
from sentence_transformers import SentenceTransformer

from paths import VECTOR_DOCUMENTS_PATH


MODEL_NAME = "BAAI/bge-m3"

TOP_K = 3


print("Embedding 모델을 불러오는 중...")

model = SentenceTransformer(MODEL_NAME)

print("완료.\n")


with VECTOR_DOCUMENTS_PATH.open("r", encoding="utf-8") as f:
    documents = json.load(f)


while True:

    print("=" * 70)

    product_id = input(
        "제품 ID를 입력하세요 (예: BAG_001): "
    ).strip()

    if product_id.lower() in ["exit", "quit"]:
        break

    question = input(
        "질문을 입력하세요: "
    ).strip()

    if question.lower() in ["exit", "quit"]:
        break


    candidate_documents = []
    candidate_texts = []

    for doc in documents:

        if doc["product_id"] == product_id:

            candidate_documents.append(doc)

            candidate_texts.append(
                f"Product: {doc['product_name']}\n"
                f"Topic: {doc['topic']}\n"
                f"{doc['text']}"
            )


    if len(candidate_documents) == 0:

        print("\n해당 product_id를 찾을 수 없습니다.\n")
        continue


    query_embedding = model.encode_query(
        question,
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )


    candidate_embeddings = model.encode_document(
        candidate_texts,
        normalize_embeddings=True
    )

    candidate_embeddings = np.asarray(
        candidate_embeddings,
        dtype="float32"
    )


    scores = np.dot(
        candidate_embeddings,
        query_embedding
    )


    ranking = np.argsort(scores)[::-1]


    print("\n검색 결과\n")


    for rank, idx in enumerate(
        ranking[:TOP_K],
        start=1
    ):

        doc = candidate_documents[idx]

        print("-" * 70)

        print(f"TOP {rank}")

        print(
            f"Score      : {scores[idx]:.4f}"
        )

        print(
            f"Document ID: {doc['document_id']}"
        )

        print(
            f"Product    : {doc['product_name']}"
        )

        print(
            f"Topic      : {doc['topic']}"
        )

        print("\nText:")

        print(doc["text"])

        print()


    print()
