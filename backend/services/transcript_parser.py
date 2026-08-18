import json
import os
from pathlib import Path
import fitz
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv("../.env", override=True)
google_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=google_api_key)


def extract_speakers(text):
    """
    Uses the LLM only to identify every unique speaker appearing
    in the transcript.

    Returns: list[str]
        Exact speaker strings sorted by descending length.
    """

    prompt = """
You are given an earnings call transcript.

Your ONLY task is to identify every UNIQUE speaker.

Rules:

1. Return list of speakers names, transcript ticker, company name, transcript quarter, transcript year.
2. Give more focus on extracting speaker names and preserve the speaker names EXACTLY as written.
but remove any surrounding decorative delimiters such as:
<< >>
[[ ]]
( )
Do not remove commas or company affiliations

3. Do NOT normalize names.
4. Do NOT shorten names.
5. Keep company affiliations if present.
6. Include Operator.
7. Do NOT include titles like CEO, CFO unless they are actually part of the speaker label.
8. Do NOT invent speakers.
9. Return JSON only.

Example output:

{
    "ticker": "AMZN",
    "company_name": "Amazon",
    "transcript_quarter": 2,
    "transcript_year": 2023
    "speakers": [
        "Keith Weiss, Morgan Stanley",
        "Mark Moerdler, Bernstein",
        "Satya Nadella",
        "Amy Hood",
        "Brett Iversen",
        "Operator"
    ]
}
"""
    response = client.models.generate_content(
    model="models/gemini-3.6-flash",
    contents=f"This the given transcript, strictly follow the rules :\n\n{text}",
    config=types.GenerateContentConfig(
        system_instruction=prompt,
        response_mime_type="application/json",
        temperature=0.3
    )
    )

    text = response.text
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(text)

        speakers = data["speakers"]
        symbol = data["ticker"]
        quarter = data["transcript_quarter"]
        year = data["transcript_year"]
        company_name = data["company_name"]
        
        print("=" * 30)
        print("Confidence:", data.get("confidence"))
        print(f"Extracted Ticker: {symbol} ({company_name}) - Q{quarter} {year}")
        print("=" * 30)

        return speakers ,company_name, symbol, quarter, year

    except Exception as e:
        print(e)
        return [], None, None, None, None

def to_structured_content(text, speakers):
    # Match longer names first
    speakers = sorted(speakers, key=len, reverse=True)

    structured = []

    current_speaker = "Unknown"
    current_text = ""

    for line in text.split("\n"):
        line = line.strip()

        if not line:
            continue

        found = False

        for speaker in speakers:
            idx = line.lower().find(speaker.lower())
            if idx != -1:
                # Save previous speaker block
                if current_text.strip():
                    structured.append({
                        "speaker": current_speaker,
                        "text": current_text.strip()
                    })

                current_speaker = speaker

                # Everything after the speaker name belongs to speech
                spoken = line[idx + len(speaker):]
                spoken = spoken.lstrip(" :-,\t") # remove from left (start)

                current_text = spoken
                found = True
                break

        if not found:
            current_text += " " + line

    # Save last speaker block
    if current_text.strip():
        structured.append({
            "speaker": current_speaker,
            "text": current_text.strip()
        })

    return structured

def load_transcript(filepath):
    """
    Load PDF, TXT or JSON transcript and return a normalized dictionary.
    """
    # ---------- JSON ----------
    if str(filepath).endswith(".json"):
        filepath = Path(filepath)
        with open(filepath, encoding="utf-8") as f:
            raw = json.load(f)

        return {
            "structured_content": raw["structured_content"],
            "content": raw["content"],
            "symbol": raw["symbol"] if "symbol" in raw else "UNKNOWN",
            "company_name": raw["company_name"] if "company_name" in raw else "UNKNOWN",
            "quarter": raw["quarter"] if "quarter" in raw else None,
            "year": raw["year"] if "year" in raw else None,
            "date": raw["date"] if "date" in raw else None
        }

    # ---------- PDF ----------
    elif str(filepath).endswith(".pdf"):
        filepath = Path(filepath)
        with fitz.open(filepath) as doc: # list of pages
            full_text = "\n".join(page.get_text("text") for page in doc)
        
        # with open("sample.txt", "w") as f:
        #     json.dump(full_text, f)
        speakers, company_name, symbol, quarter, year = extract_speakers(full_text)
        print(company_name, symbol, quarter, year)
        structured_content = to_structured_content(full_text, speakers)

        return {
            "structured_content": structured_content,
            "content": full_text,
            "symbol": symbol,
            "company_name": company_name,
            "quarter": quarter,
            "year": year,
            "date": None
        }

    else:
        raise ValueError(f"Unsupported file type")



def find_qa_start(structured_content):
    for i, turn in enumerate(structured_content):
        text_lower = turn["text"].lower()
        if turn["speaker"] == "Operator":
            starts_qa = (
                "first question" in text_lower
                or "take our first" in text_lower
                or "go first to" in text_lower
                or "we will now begin the question" in text_lower
                or "we'll now open" in text_lower
            )
            if starts_qa:
                print(f"Starting index found in 'find_qa_start' is {i}")
                return i
    return int(len(structured_content) * 0.4)

def extract_qa_pairs(qa_section):
    pairs = []
    i = 0
    while i < len(qa_section):
        turn = qa_section[i]
        if turn["speaker"] == "Operator":
            i += 1
            continue

        question_speaker = turn["speaker"]
        question_text = turn["text"]
        answer_parts = []
        j = i + 1

        while j < len(qa_section) and qa_section[j]["speaker"] != "Operator":
            if qa_section[j]["speaker"] == question_speaker:
                break
            answer_parts.append(qa_section[j]["text"])
            j =j + 1
        answer_text = " ".join(answer_parts)
        if answer_parts and is_genuine_pair(question_text,answer_text ):
            pairs.append({
                "analyst": question_speaker,
                "question": question_text,
                "answer": answer_text,
                "question_word_count": len(question_text.split()),
                "answer_word_count": len(" ".join(answer_parts).split())
            })

        i = j if j > i else i + 1
    print("Total QnA pair is: ") 
    print(len(pairs))
    return pairs

greeting_phrases = [
    "thanks", "thank you", "good morning", "good afternoon",
    "good evening", "congratulations", "that's all from me",
    "appreciate it", "welcome back",
]
question_words = [
    "what", "why", "how", "when", "where", "which", "who",
    "can", "could", "would", "should", "do you", "did you",
    "are you", "is there", "will you",
]
NUMBER_PATTERN = re.compile(
    r'\$[\d,]+(?:\.\d+)?(?:\s?(?:billion|million|trillion))?|[\d,]+(?:\.\d+)?%|[\d]+\s?(?:basis\s?points?|bps)',
    re.IGNORECASE
)

def is_genuine_pair(question, answer):
    q = question.lower().strip()
    word_count = len(q.split())

    has_greeting = False
    for phrase in greeting_phrases:
        if phrase in q:
            has_greeting = True
            break    
    
    has_question_word = False
    for word in question_words:
        if word in q:
            has_question_word = True
            break
    
    has_question_mark = "?" in q
    answer_has_number = bool(NUMBER_PATTERN.search(answer))

    if answer_has_number:
        return True
    if word_count < 8 and has_greeting:
        return False

    if not has_question_word and not has_question_mark:
        return False

    return True

# FIND AND SEPERATE QnA 
def split_sections(structured_content):
    qna_start = find_qa_start(structured_content)
    pre_qna = structured_content[:qna_start]
    qna_section = structured_content[qna_start:]
    qna_pairs = extract_qa_pairs(qna_section)
    return pre_qna, qna_pairs


guidance_words = ["we expect", "we anticipate", "we project", "we forecast", "going forward", "outlook", "next quarter", "full year"]
# EXTRACT GUIDANCE SENTENCES 
def extract_guidance_sentences(text):    
    sentences = text.split(". ")
    
    guidance_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for word in guidance_words:
            if word in sentence_lower:
                guidance_sentences.append(sentence.strip())
                break
    
    return guidance_sentences
