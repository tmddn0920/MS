import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chat_openai import ask_concierge_stream


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="MCM AI Concierge API",
    version="1.0.0",
)


# ============================================================
# Request
# ============================================================

class ChatRequest(BaseModel):
    modelCode: str
    message: str


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# ============================================================
# AI Chat Streaming
# ============================================================

@app.post("/chat/stream")
def chat_stream(
    request: ChatRequest
):

    model_code = (
        request.modelCode
        or ""
    ).strip()

    message = (
        request.message
        or ""
    ).strip()


    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not model_code:

        raise HTTPException(
            status_code=400,
            detail="modelCode is required"
        )


    if not message:

        raise HTTPException(
            status_code=400,
            detail="message is required"
        )


    # --------------------------------------------------------
    # SSE Generator
    # --------------------------------------------------------

    def event_generator():

        try:

            for chunk in ask_concierge_stream(
                model_code,
                message
            ):

                payload = json.dumps(
                    {
                        "type": "delta",
                        "text": chunk
                    },
                    ensure_ascii=False
                )

                yield (
                    f"data: {payload}\n\n"
                )


            # --------------------------------------------
            # Streaming 완료
            # --------------------------------------------

            done_payload = json.dumps(
                {
                    "type": "done"
                },
                ensure_ascii=False
            )

            yield (
                f"data: {done_payload}\n\n"
            )


        except Exception as e:

            print(
                "Streaming Error:",
                repr(e)
            )


            error_payload = json.dumps(
                {
                    "type": "error",
                    "message":
                        "답변을 생성하는 중 오류가 발생했습니다."
                },
                ensure_ascii=False
            )


            yield (
                f"data: {error_payload}\n\n"
            )


    # --------------------------------------------------------
    # Streaming Response
    # --------------------------------------------------------

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
