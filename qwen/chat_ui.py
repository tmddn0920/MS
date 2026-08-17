"""
MCM Product Concierge — Gradio 채팅 UI (Qwen)

실행:
    python qwen/chat_ui.py

브라우저에서 http://127.0.0.1:7860 을 엽니다.
첫 실행 시 모델 로딩에 시간이 걸립니다.
"""

import sys
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paths import PRODUCTS_PATH, load_products
from chat import ask_concierge

CUSTOM_CSS = """
.gradio-container { max-width: 880px !important; margin: auto; }
#chatbot { height: 520px; }
"""


def load_product_choices():
    if not PRODUCTS_PATH.exists():
        return ["MMKEAVE15IG001"]

    products = load_products()

    choices = []

    for product in products:
        model_code = product.get("style_number") or ""
        product_name = product.get("product_name", "")

        if not model_code:
            continue

        choices.append(f"{model_code} — {product_name}")

    return choices


PRODUCT_CHOICES = load_product_choices()


def parse_model_code(product_choice):
    if not product_choice:
        return ""

    return product_choice.split("—", 1)[0].strip()


def respond(message, history, product_choice):
    model_code = parse_model_code(product_choice)
    question = (message or "").strip()

    if not question:
        return history, ""

    history = list(history or [])
    history.append({"role": "user", "content": question})

    answer, _retrieved_docs = ask_concierge(model_code, question)

    history.append({"role": "assistant", "content": answer})

    return history, ""


def clear_chat():
    return [], ""


def build_ui():
    with gr.Blocks(title="MCM Product Concierge (Qwen)") as demo:

        gr.Markdown(
            """
            # MCM Product Concierge (Qwen)
            제품을 선택한 뒤 질문을 보내세요.
            """
        )

        product = gr.Dropdown(
            choices=PRODUCT_CHOICES,
            value=PRODUCT_CHOICES[0] if PRODUCT_CHOICES else None,
            label="제품 (Model Code)",
            interactive=True,
        )

        chatbot = gr.Chatbot(
            elem_id="chatbot",
            label="대화",
            buttons=["copy"],
        )

        with gr.Row():
            msg = gr.Textbox(
                placeholder="예: 비 오는 날 이 가방을 써도 될까요?",
                label="메시지",
                scale=5,
                autofocus=True,
            )
            send = gr.Button("보내기", variant="primary", scale=1)

        clear = gr.Button("대화 지우기")

        send.click(
            respond,
            inputs=[msg, chatbot, product],
            outputs=[chatbot, msg],
        )

        msg.submit(
            respond,
            inputs=[msg, chatbot, product],
            outputs=[chatbot, msg],
        )

        clear.click(
            clear_chat,
            outputs=[chatbot, msg],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
        css=CUSTOM_CSS,
    )
