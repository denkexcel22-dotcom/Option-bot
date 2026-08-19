"""
Pocket Option Screenshot Signal Bot
-----------------------------------
A screenshot-analysis assistant. It does NOT place trades automatically.

Setup:
  pip install openai
  Set OPENAI_API_KEY in your environment.
  Run: python pocket_option_bot.py chart.png

The bot returns BUY, SELL, or NO TRADE plus confidence and reasoning.
It is intentionally conservative: weak/unclear charts produce NO TRADE.
"""

import base64
import json
import os
import sys
from pathlib import Path

from openai import OpenAI

MODEL = "gpt-5.6-luna"

SYSTEM_PROMPT = """
You are a conservative technical-analysis assistant for binary-options-style chart screenshots.
Your job is to analyze ONLY what is visible in the supplied chart image.

Return exactly one JSON object with:
{
  "signal": "BUY" | "SELL" | "NO TRADE",
  "confidence": integer 0-100,
  "trend": "BULLISH" | "BEARISH" | "SIDEWAYS" | "UNCLEAR",
  "setup": "short description",
  "timeframe": "visible timeframe or UNKNOWN",
  "reasons": ["reason 1", "reason 2", "reason 3"],
  "risk_note": "brief warning"
}

Rules:
1. Never claim certainty or guaranteed prediction.
2. If the timeframe, candles, price scale, or chart is too unclear, use NO TRADE.
3. Prefer NO TRADE over a weak signal.
4. Analyze market structure: HH/HL, LH/LL, break of structure, pullback/retest.
5. Consider support/resistance, momentum, candle rejection, and trend alignment.
6. Do not invent indicators or prices that are not visible.
7. For BUY, require evidence that the next directional move is more likely upward.
8. For SELL, require evidence that the next directional move is more likely downward.
9. Confidence is a strength score, NOT a probability of winning.
10. This is analysis only; do not place or recommend automatic execution.
"""

def image_data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"

def analyze(path: Path):
    client = OpenAI()
    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=[{
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Analyze this Pocket Option/trading chart screenshot. "
                        "Give one conservative signal only. Do not force a trade."
                    ),
                },
                {
                    "type": "input_image",
                    "image_url": image_data_url(path),
                    "detail": "high",
                },
            ],
        }],
    )

    text = response.output_text.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        print(text)
        return

    print("\n========== POCKET OPTION BOT ==========")
    print(f"SIGNAL     : {result.get('signal')}")
    print(f"CONFIDENCE : {result.get('confidence')} / 100")
    print(f"TREND      : {result.get('trend')}")
    print(f"TIMEFRAME  : {result.get('timeframe')}")
    print(f"SETUP      : {result.get('setup')}")
    print("\nREASONS:")
    for reason in result.get("reasons", []):
        print(f" • {reason}")
    print(f"\nRISK NOTE   : {result.get('risk_note')}")
    print("========================================\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pocket_option_bot.py chart.png")
        sys.exit(1)

    image = Path(sys.argv[1])
    if not image.exists():
        print(f"Image not found: {image}")
        sys.exit(1)

    if image.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        print("Use a PNG, JPG, or JPEG screenshot.")
        sys.exit(1)

    analyze(image)
