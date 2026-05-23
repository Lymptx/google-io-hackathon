"""GMI Cloud and RocketRide client wrapper.

Supports both direct OpenAI-compatible API calls to GMI Cloud and
routed pipeline execution via RocketRide.
"""

import json
import logging
from typing import Any, Optional

import openai

from src.config import (
    CLIP_SUMMARY_DIR,
    GMI_API_KEY,
    GMI_BASE_URL,
    TACTICS_DIR,
    VISION_MODEL,
    ROCKETRIDE_URI,
    ROCKETRIDE_APIKEY,
    ROCKETRIDE_PIPE_PATH,
    ROCKETRIDE_SOURCE,
    ROCKETRIDE_TASK_TOKEN,
)

logger = logging.getLogger(__name__)

def _load_rocketride() -> tuple[Any, Any]:
    """Import RocketRide only when the optional transport is requested."""
    try:
        from rocketride.client import RocketRideClient
        from rocketride.schema.question import Question
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "RocketRide transport requires the optional 'rocketride' package. "
            "Install it or use transport='direct'."
        ) from exc
    return RocketRideClient, Question

class GmiClient:
    """Wraps OpenAI SDK (for direct GMI) and RocketRide Client."""

    def __init__(self, transport: str = "direct") -> None:
        """Initialise the client with a chosen transport: 'direct' or 'rocketride'."""
        self.transport = transport
        
        # Direct GMI Client (Async)
        self._openai_client = openai.AsyncOpenAI(
            base_url=GMI_BASE_URL,
            api_key=GMI_API_KEY,
        )
        
        # RocketRide Client
        self._rr_client: Optional[Any] = None
        self._rr_token: Optional[str] = None
        
        logger.info("GmiClient initialised with transport=%s", transport)

    async def initialize(self) -> None:
        """Connects and boots up RocketRide if using rocketride transport."""
        if self.transport == "rocketride" and not self._rr_client:
            RocketRideClient, _ = _load_rocketride()
            logger.info("Initializing RocketRide client on %s", ROCKETRIDE_URI)
            self._rr_client = RocketRideClient(
                uri=ROCKETRIDE_URI,
                auth=ROCKETRIDE_APIKEY,
            )
            # Connect to RocketRide server
            await self._rr_client.connect()
            
            # Start/use our designated coach pipeline
            logger.info("Loading RocketRide pipeline: %s", ROCKETRIDE_PIPE_PATH)
            task_info = await self._rr_client.use(
                filepath=ROCKETRIDE_PIPE_PATH,
                source=ROCKETRIDE_SOURCE,
                token=ROCKETRIDE_TASK_TOKEN,
                use_existing=True,
                env={
                    "GMI_API_KEY": GMI_API_KEY,
                    "ROCKETRIDE_CLIP_SUMMARY_PATH": CLIP_SUMMARY_DIR,
                    "ROCKETRIDE_TACTICS_PATH": TACTICS_DIR,
                },
            )
            self._rr_token = task_info["token"]
            logger.info("RocketRide pipeline ready. Token: %s", self._rr_token)

    async def close(self) -> None:
        """Close connections cleanly."""
        if self._rr_client:
            logger.info("Disconnecting RocketRide client...")
            await self._rr_client.disconnect()
            self._rr_client = None
            self._rr_token = None

    async def chat(self, messages: list[dict], model: str) -> str:
        """Send messages and return the plain text reply."""
        if self.transport == "rocketride":
            await self.initialize()
            _, Question = _load_rocketride()
            
            # Compile messages into a clean prompt string for RocketRide's chat node
            # The chat node expects a single user question or context
            prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
            
            q = Question()
            q.addQuestion(prompt)
            
            resp = await self._rr_client.chat(token=self._rr_token, question=q)
            if resp and "answers" in resp and len(resp["answers"]) > 0:
                return resp["answers"][0]
            raise ValueError(f"RocketRide returned empty chat answer: {resp}")
            
        else:
            # Direct GMI Call
            resp = await self._openai_client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return resp.choices[0].message.content or ""

    async def chat_json(self, messages: list[dict], model: str) -> dict:
        """Send messages and expect a structured JSON-object reply."""
        if self.transport == "rocketride":
            await self.initialize()
            _, Question = _load_rocketride()
            
            prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
            
            q = Question(expectJson=True)
            q.addQuestion(prompt)
            q.addInstruction("Format", "Return valid JSON object matching the requested schema. Do not enclose in markdown blocks.")
            
            resp = await self._rr_client.chat(token=self._rr_token, question=q)
            if resp and "answers" in resp and len(resp["answers"]) > 0:
                answer = resp["answers"][0]
                if isinstance(answer, dict):
                    return answer
                try:
                    return json.loads(str(answer))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"RocketRide returned malformed JSON answer string: {answer}") from exc
            raise ValueError(f"RocketRide returned empty chat JSON: {resp}")
            
        else:
            # Direct GMI Call
            resp = await self._openai_client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            if content is None:
                raise ValueError("Model returned no content (expected JSON).")
            try:
                return json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Model returned non-JSON content: {content!r}") from exc

    async def vision_json(
        self,
        image_b64: str,
        prompt: str,
        model: str = VISION_MODEL,
    ) -> dict:
        """Analyse a base-64-encoded JPEG image and return a JSON reply.

        Always uses direct GMI vision endpoint since VLM/Vision inputs
        require raw base64 frame mapping, keeping the ingestion pipeline fast.
        """
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}",
                    },
                },
            ],
        }
        resp = await self._openai_client.chat.completions.create(
            model=model,
            messages=[message],
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        if content is None:
            raise ValueError("Model returned no content (expected JSON).")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Model returned non-JSON content: {content!r}") from exc
