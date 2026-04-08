"""
Ovozni matnga o'girish (Whisper) va matndan tranzaksiya ma'lumotini ajratish (GPT).
"""
import json
import logging
import tempfile
import os
from pathlib import Path
from dataclasses import dataclass

from openai import AsyncOpenAI
from data.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


@dataclass
class ParsedTransaction:
    type: str          # "income" yoki "expense"
    amount: float
    category: str      # kategoriya nomi
    description: str
    confidence: float  # 0.0 - 1.0, past bo'lsa foydalanuvchidan so'raymiz


SYSTEM_PROMPT = """Sen moliyaviy yordamchi assistantsan.
Foydalanuvchi xabaridan quyidagi ma'lumotlarni JSON formatda ajrat.

Qaytariladigan format:
{
  "type": "income" yoki "expense",
  "amount": raqam (faqat son, valyuta belgisi yo'q),
  "category": kategoriya nomi,
  "description": qisqa tavsif,
  "confidence": 0.0 dan 1.0 gacha (qanchalik aniq tushundim)
}

Kategoriyalar: Oziq-ovqat, Transport, Kiyim-kechak, Uy-joy, Kommunal,
Sog'liq, Ta'lim, Ko'ngilochar, Sport, Go'zallik, Sovg'a, Sayohat,
Maosh, Freelance, Biznes, Investitsiya, Sovrin, Boshqa

Misollar:
- "50 ming non uchun" → expense, 50000, Oziq-ovqat, "non"
- "taksi 15000" → expense, 15000, Transport, "taksi"
- "maosh 3 million" → income, 3000000, Maosh, "oylik maosh"
- "Alibek menga 200 ming berdi" → income, 200000, Boshqa, "Alibekdan"

Muhim: "ming" = x1000, "million" / "mln" = x1000000.
Faqat JSON qaytار, hech qanday izoh yozma."""


async def voice_to_text(file_bytes: bytes, file_ext: str = "ogg") -> str:
    """Ovozli xabarni matnga o'girish (Whisper API)."""
    with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uz",  # O'zbek tili; aniqlay olmasa avtomatik fallback
            )
        return transcript.text.strip()
    finally:
        os.unlink(tmp_path)


async def parse_transaction_text(text: str) -> ParsedTransaction | None:
    """Matndan tranzaksiya ma'lumotini ajratish (GPT-4o-mini)."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=150,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        return ParsedTransaction(
            type=data.get("type", "expense"),
            amount=float(data.get("amount", 0)),
            category=data.get("category", "Boshqa"),
            description=data.get("description", text[:100]),
            confidence=float(data.get("confidence", 0.5)),
        )

    except Exception as e:
        logger.error(f"GPT parse xatoligi: {e}")
        return None


async def process_voice_message(file_bytes: bytes) -> tuple[str, ParsedTransaction | None]:
    """
    Ovozni matnga, so'ng tranzaksiya ma'lumotiga o'girish.
    Qaytaradi: (matn, parsed_result)
    """
    text = await voice_to_text(file_bytes)
    if not text:
        return "", None

    parsed = await parse_transaction_text(text)
    return text, parsed
