import json

from paths import (
    PRODUCTS_PATH,
    RAG_DIR,
    RAG_DOCUMENTS_PATH,
    load_products,
)


# ============================================================
# 한글 Topic 이름
# ============================================================

CARE_TOPIC_TITLES = {
    "storage": "보관",
    "water": "수분 관리",
    "washing": "세탁",
    "drying": "건조",
    "ironing": "다림질",
    "cleaning": "세척",
    "avoid": "주의사항",
    "precautions": "추가 주의사항",
}


DIMENSION_LABELS = {
    "text": "크기",
    "strap": "스트랩",
    "strap_length": "스트랩 길이",
    "handle_drop": "핸들 드롭",
    "handle_length": "핸들 길이",
    "strap_drop": "스트랩 드롭",
}


# ============================================================
# Utility
# ============================================================

def humanize(value):

    if value is None:
        return None

    return str(value).replace("_", " ")


def join_items(items):

    if not items:
        return ""

    return ", ".join(
        str(item).strip()
        for item in items
        if item
    )


# ============================================================
# 소재 Text 변환
# ============================================================

def materials_text(materials):

    parts = []

    for item in materials or []:

        part = humanize(
            item.get("part")
        )

        material = item.get(
            "material"
        )

        percentage = item.get(
            "percentage"
        )

        if not material:
            continue

        if percentage is not None:

            value = (
                f"{material} "
                f"{percentage}%"
            )

        else:

            value = material


        if part:

            parts.append(
                f"{part}: {value}"
            )

        else:

            parts.append(
                value
            )


    return "; ".join(parts)


# ============================================================
# 치수 Text 변환
# ============================================================

def dimensions_text(dimensions):

    if not dimensions:
        return ""

    parts = []

    for key, value in dimensions.items():

        if value is None or value == "":
            continue


        label = DIMENSION_LABELS.get(
            key,
            humanize(key)
        )

        parts.append(
            f"{label}: {value}"
        )


    return ". ".join(parts)


# ============================================================
# Care Text 변환
#
# list뿐 아니라 dict 형태가 들어와도 처리
# ============================================================

def care_value_to_text(value):

    if value is None:
        return ""

    # --------------------------------
    # List
    # --------------------------------

    if isinstance(value, list):

        return join_items(value)


    # --------------------------------
    # String
    # --------------------------------

    if isinstance(value, str):

        return value.strip()


    # --------------------------------
    # Dictionary
    # --------------------------------

    if isinstance(value, dict):

        parts = []

        for key, item in value.items():

            if item is None:
                continue


            label = humanize(key)


            if isinstance(item, list):

                text = join_items(item)

            else:

                text = str(item)


            if text:

                parts.append(
                    f"{label}: {text}"
                )


        return ". ".join(parts)


    return str(value)


# ============================================================
# RAG Document 생성
# ============================================================

def make_doc(
    product,
    topic,
    title,
    text
):

    category = (
        product.get("category")
        or {}
    )


    # --------------------------------
    # 백엔드에서 받을 ModelCode
    # --------------------------------

    model_code = product.get(
        "style_number"
    )


    return {

        # --------------------------------
        # RAG 내부 document ID
        # --------------------------------

        "document_id": (
            f"{product['product_id']}_"
            f"{topic.upper()}"
        ),


        # --------------------------------
        # 내부용 Product ID
        # --------------------------------

        "product_id":
            product["product_id"],


        # --------------------------------
        # 백엔드 연동 핵심 Key
        # --------------------------------

        "modelCode":
            model_code,


        # 원본 이름도 유지
        "style_number":
            model_code,


        # --------------------------------
        # Product metadata
        # --------------------------------

        "product_name":
            product["product_name"],

        "category":
            category.get("main"),

        "subcategory":
            category.get("sub"),

        "topic":
            topic,

        "title":
            title,

        "text":
            text.strip(),
    }


# ============================================================
# Product JSON → RAG Documents
# ============================================================

def build_documents(products):

    docs = []


    for product in products:

        name = product[
            "product_name"
        ]

        description = (
            product.get("description")
            or {}
        )

        care = (
            product.get("care")
            or {}
        )

        structured_care = (
            care.get("structured")
            or {}
        )


        # ====================================================
        # 1. Overview
        # ====================================================

        summary = (
            description.get("summary")
            or ""
        )


        if summary:

            docs.append(
                make_doc(
                    product,
                    "overview",
                    f"{name} 개요",
                    (
                        f"{name} 제품 개요: "
                        f"{summary}"
                    ),
                )
            )


        # ====================================================
        # 2. Description / Heritage
        #
        # 공식 상세 Description을 따로 분리
        # ====================================================

        paraphrase = (
            description.get(
                "official_description_paraphrase"
            )
            or ""
        )

        concepts = join_items(
            description.get(
                "key_concepts"
            )
            or []
        )


        description_parts = []


        if paraphrase:

            description_parts.append(
                paraphrase
            )


        if concepts:

            description_parts.append(
                f"핵심 키워드: {concepts}."
            )


        if description_parts:

            docs.append(
                make_doc(
                    product,
                    "description_heritage",
                    f"{name} 디자인 및 헤리티지",
                    " ".join(
                        description_parts
                    ),
                )
            )


        # ====================================================
        # 3. Specifications
        # ====================================================

        spec_parts = []


        if product.get(
            "style_number"
        ):

            spec_parts.append(
                "스타일 넘버: "
                f"{product['style_number']}"
            )


        if product.get(
            "color"
        ):

            spec_parts.append(
                "컬러: "
                f"{humanize(product['color'])}"
            )


        if product.get(
            "size"
        ):

            spec_parts.append(
                "사이즈: "
                f"{product['size']}"
            )


        if product.get(
            "country_of_origin"
        ):

            spec_parts.append(
                "원산지: "
                f"{product['country_of_origin']}"
            )


        if product.get(
            "sustainability"
        ):

            spec_parts.append(
                "지속가능성: "
                f"{product['sustainability']}"
            )


        dim_text = dimensions_text(
            product.get(
                "dimensions"
            )
        )


        if dim_text:

            spec_parts.append(
                dim_text
            )


        if spec_parts:

            docs.append(
                make_doc(
                    product,
                    "specifications",
                    f"{name} 제품 사양",
                    (
                        f"{name}의 제품 사양입니다. "
                        + ". ".join(
                            spec_parts
                        )
                        + "."
                    ),
                )
            )


        # ====================================================
        # 4. Materials
        # ====================================================

        material_text = materials_text(
            product.get(
                "materials"
            )
        )


        if material_text:

            docs.append(
                make_doc(
                    product,
                    "materials",
                    f"{name} 소재",
                    (
                        f"{name}의 소재 구성: "
                        f"{material_text}."
                    ),
                )
            )


        # ====================================================
        # 5. Features
        # ====================================================

        features = (
            product.get(
                "features"
            )
            or []
        )


        if features:

            docs.append(
                make_doc(
                    product,
                    "features",
                    f"{name} 주요 특징",
                    (
                        f"{name}의 주요 기능 및 "
                        f"디테일: "
                        f"{join_items(features)}."
                    ),
                )
            )


        # ====================================================
        # 6. Raw Official Care
        #
        # MCM 공식 관리 탭 원문/정리본
        # ====================================================

        raw_care = care.get(
            "raw_official_care"
        )


        if raw_care:

            docs.append(
                make_doc(
                    product,
                    "care",
                    f"{name} 공식 관리 안내",
                    (
                        f"{name}의 공식 관리 안내: "
                        f"{raw_care}"
                    ),
                )
            )


        # ====================================================
        # 7. Structured Care
        #
        # washing / water / cleaning / storage ...
        # 각각 별도 RAG chunk
        # ====================================================

        for key, value in (
            structured_care.items()
        ):

            if not value:
                continue


            text = care_value_to_text(
                value
            )


            if not text:
                continue


            title_ko = (
                CARE_TOPIC_TITLES.get(
                    key,
                    humanize(key)
                )
            )


            docs.append(
                make_doc(
                    product,
                    f"care_{key}",
                    f"{name} {title_ko}",
                    (
                        f"{name}의 {title_ko} 안내: "
                        f"{text}."
                    ),
                )
            )


    return docs


# ============================================================
# Main
# ============================================================

def main():

    products = load_products()

    docs = build_documents(
        products
    )


    RAG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    with RAG_DOCUMENTS_PATH.open(
        "w",
        encoding="utf-8"
    ) as f:

        for doc in docs:

            f.write(
                json.dumps(
                    doc,
                    ensure_ascii=False
                )
                + "\n"
            )


    print(
        f"Created {len(docs)} documents "
        f"from {len(products)} products "
        f"({PRODUCTS_PATH.name}) "
        f"-> {RAG_DOCUMENTS_PATH}"
    )


    # --------------------------------
    # 테스트용 첫 문서 출력
    # --------------------------------

    if docs:

        print(
            "\nExample document:"
        )

        print(
            json.dumps(
                docs[0],
                ensure_ascii=False,
                indent=2
            )
        )


if __name__ == "__main__":

    main()
