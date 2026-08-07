"""
Guidance extraction service.
Uses Groq LLM to extract structured forward guidance claims.
"""

import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MEASURABLE_METRICS = [
     # Direct income statement fields
    "revenue", "total revenue", "gross profit", "operating income",
    "net income", "r&d", "research and development", "operating expenses",
    "ebit", "ebitda", "tax expense", "income tax",
    # Derived metrics
    "gross margin", "operating margin", "net margin", "net income margin",
    "profit margin", "Pre-tax Margin",
    # From earnings history
    "eps", "earnings per share",
    # Common aliases
    "top line", "bottom line", "sales"
]


def contains_measurable_metric(sentence):
    sentence = sentence.lower()
    for metric in MEASURABLE_METRICS:
        pattern = r"\b" + re.escape(metric.lower()) + r"\b"
        if re.search(pattern, sentence):
            return True

    return False

def infer_next_quarter(current_quarter, current_year):
    """Returns (quarter, year) for next quarter."""
    if current_quarter == 4:
        return 1, current_year + 1
    return current_quarter + 1, current_year

def quarter_inference_context(transcript_quarter, transcript_year):
    next_q, next_y = infer_next_quarter(transcript_quarter, transcript_year)

    return f"""
TIME PERIOD INFERENCE RULES for this transcript (Q{transcript_quarter} {transcript_year}):
- "next quarter" = Q{next_q} {next_y}
- "next fiscal quarter" = Q{next_q} {next_y}
- "this quarter" or "current quarter" = Q{transcript_quarter} {transcript_year}
Fiscal year guidance: (FY as target_period)
- "full year {transcript_year}" or "fiscal {transcript_year}" = FY {transcript_year}
- "FY{transcript_year}" = FY {transcript_year}
- "full year {transcript_year+1}" or "FY {transcript_year+1}" = FY {transcript_year+1}
Half-year guidance:
- "first half" = H1 {transcript_year}
- "second half" = H2 {transcript_year}
Explicit quarter references:
- "Q1 {transcript_year+1}" = Q1 {transcript_year+1}
- If NO time period mentioned at all → assume Q{next_q} {next_y} (next quarter)
- NEVER leave target_period or target_year as null
"""


def extract_guidance(
    guidance_sentences: list,
    symbol,
    quarter,
    year
) -> list:
    """
    Extract structured guidance claims from forward guidance sentences.
    Pre-filters by measurable metrics before calling LLM.
    """
    if not guidance_sentences:
        return []

    # Pre-filter — no LLM cost for obvious non-guidance sentences
    filtered = [s for s in guidance_sentences if contains_measurable_metric(s)]
    if not filtered:
        return []

    sentences_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(filtered))
    quarter_context = quarter_inference_context(quarter, year)

    prompt = f"""You are a financial analyst extracting verifiable forward guidance from an earnings call transcript.
IMPORTANT: Only extract guidance that is seems a future claim, not a past report. Each sentence should be about future. Otherwise skip it. 
Company: 
<company>
{symbol}
</company>
Transcript Quarter: Q{quarter} {year}

<transcript_context>
{quarter_context}
</transcript_context>

Guidance sentences to analyze:
<guidance_sentences>
{sentences_text}
</guidance_sentences>

For each valid guidance claim, return a JSON object with exactly these fields:
{{
  "metric": "standardized metric name from the sentence",
  "raw_value": "exact value as stated e.g. 43.5-44.5% or $90B or high single digits",
  "value_low": <lower bound as float, null if not applicable>,
  "value_high": <upper bound as float, null if not applicable>,
  "value_unit": "%" or "B" or "M" or "absolute",
  "target_period": "Q1 | Q2 | Q3 | Q4 | FY | H1 | H2, NEVER null",
  "target_year": <integer e.g. 2023, NEVER null>,
  "guidance horizon":"indicates the periods over which the guidance is expected to be fulfilled e.g. 1 quarter or 2 quarters "
  "confidence": <0.0-1.0, how confident you are this is real measurable guidance>,
  "raw_sentence": "original sentence"
}}

Return ONLY a JSON array of valid claims. If no valid measurable guidance found, return [].
No other text."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system",
             "content": "You are a strict financial analyst. Follow the instruction to find out genuine future guidance."
            },
            {"role": "user",
             "content": prompt
            }
        ],
        temperature=0.1
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(text)

        if not isinstance(result, list):
            return []

        cleaned = []
        next_q, next_y = infer_next_quarter(quarter, year)

        for item in result:
            cleaned.append(item)

        return cleaned

    except Exception as e:
        print(f"  Extraction error: {e}")
        return []
