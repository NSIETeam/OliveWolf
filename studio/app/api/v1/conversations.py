from fastapi import APIRouter

from app.schemas import ConversationTestRequest, ConversationTestResponse

router = APIRouter()


@router.post("/test", response_model=ConversationTestResponse)
def test_conversation(payload: ConversationTestRequest):
    # Production path:
    # 1. Resolve tenant/project/avatar.
    # 2. Retrieve relevant knowledge chunks.
    # 3. Call LLM provider.
    # 4. Optionally enqueue realtime render session.
    answer = (
        "This is an OliveWolf Studio mock response. "
        "The production worker will connect this endpoint to knowledge retrieval, LLM, TTS and avatar rendering."
    )
    return ConversationTestResponse(answer=answer, mode="mock")
