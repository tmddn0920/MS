import json
import os

import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from paths import OPENAI_CONFIG_PATH, VECTOR_DOCUMENTS_PATH


# ============================================================
# 설정
# ============================================================

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

TOP_K = 3

MAX_OUTPUT_TOKENS = 300


# ============================================================
# OpenAI 설정
# ============================================================

def load_openai_config():

    config = {}

    if OPENAI_CONFIG_PATH.exists():

        with OPENAI_CONFIG_PATH.open(
            "r",
            encoding="utf-8"
        ) as f:

            config = json.load(f)


    api_key = (
        (config.get("api_key") or "").strip()
        or os.environ.get("OPENAI_API_KEY", "")
    )


    model = (
        (config.get("model") or "").strip()
        or os.environ.get("OPENAI_MODEL", "")
        or "gpt-4o-mini"
    )


    placeholder = {
        "",
        "YOUR_API_KEY_HERE",
        "sk-여기에키",
    }


    if api_key in placeholder:

        raise RuntimeError(
            f"{OPENAI_CONFIG_PATH} 에 api_key 를 넣거나 "
            "OPENAI_API_KEY 환경 변수를 설정하세요."
        )


    return api_key, model


# ============================================================
# 1. Embedding 모델
# ============================================================

print("Embedding 모델 로딩 중...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)

print("Embedding 모델 로딩 완료.")


# ============================================================
# 2. RAG Documents
# ============================================================

with VECTOR_DOCUMENTS_PATH.open(
    "r",
    encoding="utf-8"
) as f:

    documents = json.load(f)


print(
    f"RAG 문서 {len(documents)}개 로딩 완료."
)


# ============================================================
# 3. OpenAI Client
# ============================================================

print("\nOpenAI 클라이언트 준비 중...")


OPENAI_API_KEY, OPENAI_MODEL = load_openai_config()


openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)


print("OpenAI 클라이언트 준비 완료.")
print("모델:", OPENAI_MODEL)


# ============================================================
# 4. System Prompt
# ============================================================

SYSTEM_PROMPT = """
당신은 MCM 제품을 안내하는 프리미엄 브랜드 컨시어지입니다.

고객이 소유한 제품에 대해 친절하고 전문적으로 안내하세요.
당신은 고객이나 제품의 소유자가 아닙니다.

항상 고객에게 직접 설명하는 형태로 답변하세요.
"저는 이 제품을 가지고 있습니다", "제가 소유한 제품",
"저의 제품", "제가 생성할 수 있는 정보"와 같은 표현을 사용하지 마세요.

제품을 사람처럼 의인화하지 마세요.
제품을 지칭할 때는 제품명 또는
"제품", "가방", "지갑", "의류", "신발"과 같은
자연스러운 표현을 사용하세요.

Product Information에 포함된 내용을 우선적인 사실 근거로 사용하세요.

확인되지 않은 소재, 색상, 크기, 내구성, 제조 방식,
관리법, 헤리티지 또는 스타일링 정보를
임의로 만들어내지 마세요.

고객의 질문에 직접 답변하고,
질문과 관련 없는 정보를 불필요하게 길게 설명하지 마세요.

피해야 할 행동이 있다면 먼저 명확하게 안내한 뒤,
그 이유와 권장되는 관리 방법을 자연스럽게 설명하세요.

답변은 자연스럽고 문법적으로 정확한 한국어로 작성하세요.
프리미엄 브랜드 고객 서비스에서 사용하는
정중하고 편안한 표현을 사용하세요.

일반적인 질문에는 3~6개의 문장으로 답변하세요.
필요한 경우 조금 더 자세히 설명할 수 있습니다.

같은 문장이나 표현을 반복하지 마세요.

검색, RAG, 데이터베이스, 참고 문서,
AI 모델 또는 내부 처리 과정은 언급하지 마세요.

Product Information만으로 확실하게 답변할 수 없는 내용은
추측하거나 임의로 만들어내지 마세요.

그 경우 내부 정보가 부족하거나 해당 정보가 없다고 표현하지 말고,
"정확한 내용은 MCM 공식 제품 페이지 또는 고객 서비스를 통해 확인해 주세요."
와 같이 자연스럽게 안내하세요.

답변 마지막에는 고객이 자연스럽게 다음 질문을 이어갈 수 있도록
상황에 맞는 짧은 문장으로 마무리하세요.

매번 동일한 문구를 반복하지 마세요.

최종 답변에는 고객에게 전달할 내용만 포함하세요.
"""


# ============================================================
# 5. modelCode 기준 RAG 검색
# ============================================================

def retrieve_documents(
    model_code,
    question,
    top_k=TOP_K
):

    model_code = (
        model_code
        or ""
    ).strip()


    question = (
        question
        or ""
    ).strip()


    candidate_documents = []
    candidate_texts = []


    # --------------------------------------------------------
    # 해당 modelCode 제품만 후보
    # --------------------------------------------------------

    for doc in documents:

        if doc.get("modelCode") == model_code:

            candidate_documents.append(
                doc
            )


            search_text = (
                f"Product: {doc['product_name']}\n"
                f"ModelCode: {doc.get('modelCode', '')}\n"
                f"Topic: {doc['topic']}\n"
                f"{doc['text']}"
            )


            candidate_texts.append(
                search_text
            )


    if not candidate_documents:

        return []


    # --------------------------------------------------------
    # Question Embedding
    # --------------------------------------------------------

    query_embedding = embedding_model.encode_query(
        question,
        normalize_embeddings=True
    )


    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )


    # --------------------------------------------------------
    # Candidate Embedding
    # --------------------------------------------------------

    candidate_embeddings = embedding_model.encode_document(
        candidate_texts,
        normalize_embeddings=True
    )


    candidate_embeddings = np.asarray(
        candidate_embeddings,
        dtype="float32"
    )


    # --------------------------------------------------------
    # Cosine Similarity
    # --------------------------------------------------------

    scores = np.dot(
        candidate_embeddings,
        query_embedding
    )


    ranking = np.argsort(
        scores
    )[::-1]


    results = []


    for idx in ranking[:top_k]:

        doc = candidate_documents[
            idx
        ].copy()


        doc["score"] = float(
            scores[idx]
        )


        results.append(
            doc
        )


    return results


# ============================================================
# 6. User Prompt 생성
# ============================================================

def build_user_prompt(
    model_code,
    question,
    retrieved_docs
):

    product_name = (
        retrieved_docs[0]["product_name"]
        if retrieved_docs
        else model_code
    )


    context_parts = []


    for i, doc in enumerate(
        retrieved_docs,
        start=1
    ):

        context_parts.append(
            f"""
[Reference {i}]
Topic: {doc['topic']}
Information:
{doc['text']}
"""
        )


    context = "\n".join(
        context_parts
    )


    user_prompt = f"""
아래는 고객이 소유한 MCM 제품의 정보입니다.

[Product]
{product_name}

[Model Code]
{model_code}

[Product Information]
{context}

[Customer Question]
{question}

위 정보를 바탕으로 고객의 질문에 직접 답변하세요.
"""


    return user_prompt


# ============================================================
# 7. 일반 답변 생성
# ============================================================

def generate_answer(
    model_code,
    question,
    retrieved_docs
):

    user_prompt = build_user_prompt(
        model_code,
        question,
        retrieved_docs
    )


    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )


    return response.output_text.strip()


# ============================================================
# 8. Streaming 답변 생성
# ============================================================

def stream_answer(
    model_code,
    question,
    retrieved_docs
):

    user_prompt = build_user_prompt(
        model_code,
        question,
        retrieved_docs
    )


    stream = openai_client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        stream=True,
    )


    for event in stream:

        if event.type == "response.output_text.delta":

            yield event.delta


# ============================================================
# 9. 질문 1회 처리
# ============================================================

def ask_concierge(
    model_code,
    question,
    top_k=TOP_K
):

    model_code = (
        model_code
        or ""
    ).strip()


    question = (
        question
        or ""
    ).strip()


    if not model_code:

        return (
            "모델 코드를 입력해 주세요.",
            []
        )


    if not question:

        return (
            "질문을 입력해 주세요.",
            []
        )


    retrieved_docs = retrieve_documents(
        model_code,
        question,
        top_k
    )


    if not retrieved_docs:

        return (
            "해당 제품을 찾을 수 없습니다.",
            []
        )


    answer = generate_answer(
        model_code,
        question,
        retrieved_docs
    )


    return (
        answer,
        retrieved_docs
    )


# ============================================================
# 10. Streaming 질문 처리
# ============================================================

def ask_concierge_stream(
    model_code,
    question,
    top_k=TOP_K
):

    model_code = (
        model_code
        or ""
    ).strip()


    question = (
        question
        or ""
    ).strip()


    if not model_code:

        yield "모델 코드를 입력해 주세요."
        return


    if not question:

        yield "질문을 입력해 주세요."
        return


    retrieved_docs = retrieve_documents(
        model_code,
        question,
        top_k
    )


    if not retrieved_docs:

        yield "해당 제품을 찾을 수 없습니다."
        return


    yield from stream_answer(
        model_code,
        question,
        retrieved_docs
    )


# ============================================================
# 11. CLI 테스트
# ============================================================

def main():

    print(
        "\n"
        + "=" * 70
    )

    print(
        "MCM Product Concierge"
    )

    print(
        "LLM:",
        OPENAI_MODEL
    )

    print(
        "=" * 70
    )


    print(
        "\n종료하려면 modelCode에 exit를 입력하세요.\n"
    )


    while True:

        model_code = input(
            "Model Code "
            "(예: MMKEAVE15IG001): "
        ).strip()


        if model_code.lower() in [
            "exit",
            "quit"
        ]:

            break


        question = input(
            "질문: "
        ).strip()


        print(
            "\n[Concierge]"
        )


        # --------------------------------
        # Streaming Test
        # --------------------------------

        for chunk in ask_concierge_stream(
            model_code,
            question
        ):

            print(
                chunk,
                end="",
                flush=True
            )


        print(
            "\n"
        )


if __name__ == "__main__":

    main()
