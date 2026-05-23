import json
import pytest
from types import SimpleNamespace
from src.gmi_client import GmiClient

def _make_stub(content: str):
    """Return a stub for chat.completions.create."""
    async def stub(**kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content)
                )
            ]
        )
    return stub

@pytest.mark.asyncio
async def test_vision_json_parses():
    client = GmiClient(transport="direct")
    client._openai_client.chat.completions.create = _make_stub('{"summary": "test"}')
    
    result = await client.vision_json("Zm9v", "describe")
    assert result == {"summary": "test"}

@pytest.mark.asyncio
async def test_chat_json_raises_on_bad_json():
    client = GmiClient(transport="direct")
    client._openai_client.chat.completions.create = _make_stub("not json")
    
    with pytest.raises(ValueError):
        await client.chat_json(
            [{"role": "user", "content": "return json"}],
            model="google/gemini-3.1-flash-lite-preview",
        )
