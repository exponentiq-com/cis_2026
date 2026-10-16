# -*- coding: utf-8 -*-
"""Question catalogue — wording taken from the CIS 2026 questionnaire."""

from __future__ import annotations

import re
import unicodedata

# G20 leader list — Q26 / Q27 questionnaire sequence (data spelling for Xi).
G20_LEADERS_ORDER = [
    "Mahamoud Ali Youssouf (Chairperson of the African Union Commission)",
    "Javier Milei (President of Argentina)",
    "Anthony Albanese (Prime Minister of Australia)",
    "Luiz Inácio Lula da Silva (President of Brazil)",
    "Mark Carney (Prime Minister of Canada)",
    "Xi Jinping (President of China)",
    "Ursula von der Leyen (President of the European Commission)",
    "Emmanuel Macron (President of France)",
    "Friedrich Merz (Chancellor of Germany)",
    "Narendra Modi (Prime Minister of India)",
    "Prabowo Subianto (President of Indonesia)",
    "Giorgia Meloni (Prime Minister of Italy)",
    "Sanae Takaichi (Prime Minister of Japan)",
    "Claudia Sheinbaum Pardo (President of Mexico)",
    "Vladimir Vladimirovich Putin (President of Russia)",
    "Mohammed bin Salman bin Abdulaziz Al Saud (Crown Prince and Prime Minister of Saudi Arabia)",
    "Cyril Ramaphosa (President of South Africa)",
    "Lee Jae Myung (President of South Korea)",
    "Recep Tayyip Erdoğan (President of Türkiye)",
    "Andy Burnham (Prime Minister of the United Kingdom)",
    "Donald Trump (President of the United States)",
    "Don't know/Hard to answer",
]


def _norm_label(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s)).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\s+", " ", s)
    # Treat DK / refuse / numeric 999 as one bucket for ordering
    if s in {"999", "nan", "none"} or re.search(
        r"don'?t know|hard to answer|refuse|difficult to answer", s
    ):
        return "__dk__"
    # QRE “Probable” vs data “Probably”
    s = s.replace("probably,", "probable,").replace("probably ", "probable ")
    return s


def resolve_order(present_values, qre_order: list[str] | None) -> list[str] | None:
    """Map actual data labels onto QRE option order (fuzzy match on wording)."""
    if not qre_order:
        return None
    present = []
    seen = set()
    for v in present_values:
        if v is None:
            continue
        s = str(v).strip()
        if not s or s.lower() in {"nan", "none"}:
            continue
        if s not in seen:
            present.append(s)
            seen.add(s)

    # Prefer a readable DK label over bare "999"
    by_norm: dict[str, list[str]] = {}
    for p in present:
        by_norm.setdefault(_norm_label(p), []).append(p)

    def _pick(variants: list[str]) -> str:
        non_num = [v for v in variants if not v.isdigit()]
        return non_num[0] if non_num else variants[0]

    resolved: list[str] = []
    used: set[str] = set()
    for opt in qre_order:
        key = _norm_label(opt)
        variants = by_norm.get(key)
        match = _pick(variants) if variants else None
        if match is None:
            # prefix match for truncated Excel cells
            for p in present:
                if p in used:
                    continue
                if _norm_label(p).startswith(key[:48]) or key.startswith(
                    _norm_label(p)[:48]
                ):
                    match = p
                    key = _norm_label(p)
                    variants = by_norm.get(key, [p])
                    break
        if match and match not in used:
            resolved.append(match)
            # Consume every synonym (e.g. 999 + Don't know…) for this slot
            for v in variants or [match]:
                used.add(v)

    for p in present:
        if p not in used:
            resolved.append(p)
    return resolved


# Sections follow the questionnaire structure (closed questions only).
QUESTIONS: list[dict] = [
    # --- Part I: General impressions ---
    {
        "id": "q2",
        "section": "General impressions",
        "label": "Q2. Interest in China",
        "text": "How interested are you in China?",
        "kind": "single",
        "col": "q2",
        "order": [
            "Extremely interested",
            "Very interested",
            "Somewhat interested",
            "Slightly interested",
            "Not interested at all",
        ],
        "positive": ["Extremely interested", "Very interested"],
    },
    {
        "id": "q3",
        "section": "General impressions",
        "label": "Q3. Attitude toward China",
        "text": "From a subjective perspective, what is your attitude toward China?",
        "kind": "single",
        "col": "q3",
        "order": [
            "Strongly favorable",
            "Favorable",
            "Slightly favorable",
            "Neither favorable nor unfavorable",
            "Slightly unfavorable",
            "Unfavorable",
            "Strongly unfavorable",
        ],
        "positive": ["Strongly favorable", "Favorable", "Slightly favorable"],
    },
    {
        "id": "q4",
        "section": "General impressions",
        "label": "Q4. Knowledge of China",
        "text": "From an objective perspective, how much do you know about China?",
        "kind": "single",
        "col": "q4",
        "order": ["Very well", "Much", "Some", "A little", "Nothing"],
        "positive": ["Very well", "Much"],
    },
    {
        "id": "q5",
        "section": "General impressions",
        "label": "Q5. China–your country relationship",
        "text": "China is a/an … of/for your country, in consideration of the relationship between your country and China.",
        "kind": "single",
        "col": "q5",
        "order": [
            "Strategic cooperative partner",
            "Friendly country",
            "Country with normal relations",
            "Competitor",
            "Enemy",
            "Other",
        ],
        "positive": ["Strategic cooperative partner", "Friendly country"],
    },
    {
        "id": "q6",
        "section": "General impressions",
        "label": "Q6. Desired future relationship",
        "text": "What change would you like to see for the relationship between your country and China in the future?",
        "kind": "single",
        "col": "q6",
        "order": [
            "Much closer and much more friendly",
            "Closer and more friendly",
            "Status quo",
            "More distant",
            "More hostile",
            "Other",
        ],
        "positive": ["Much closer and much more friendly", "Closer and more friendly"],
    },
    {
        "id": "q7",
        "section": "General impressions",
        "label": "Q7. Visit to Chinese mainland",
        "text": "Have you visited the Chinese mainland in the past year?",
        "kind": "single",
        "col": "q7",
        "order": [
            "Have never been to the Chinese mainland",
            "Not in the past year, but had been there before",
            "Visited in the past year and had also been there before",
            "Only visited in the past year",
        ],
        "positive": None,
    },
    # --- Impressions battery ---
    {
        "id": "q11a",
        "section": "Impressions of China",
        "label": "Q11(1). Overall impression of China",
        "text": "What is your impression of China? — Overall impression of China",
        "kind": "single",
        "col": "q11a",
        "order": [
            "Very good",
            "Good",
            "Neutral (Slightly good)",
            "Neutral (Slightly bad)",
            "Bad",
            "Very bad",
            "Don't know/Hard to answer",
        ],
        "positive": ["Very good", "Good", "Neutral (Slightly good)"],
    },
    {
        "id": "q11b",
        "section": "Impressions of China",
        "label": "Q11(2). China’s economic development",
        "text": "What is your impression of China? — Impression of China’s economic development",
        "kind": "single",
        "col": "q11b",
        "order": [
            "Very good",
            "Good",
            "Neutral (Slightly good)",
            "Neutral (Slightly bad)",
            "Bad",
            "Very bad",
            "Don't know/Hard to answer",
        ],
        "positive": ["Very good", "Good", "Neutral (Slightly good)"],
    },
    {
        "id": "q11c",
        "section": "Impressions of China",
        "label": "Q11(3). China’s science and technology",
        "text": "What is your impression of China? — Impression of China’s science and technology",
        "kind": "single",
        "col": "q11c",
        "order": [
            "Very good",
            "Good",
            "Neutral (Slightly good)",
            "Neutral (Slightly bad)",
            "Bad",
            "Very bad",
            "Don't know/Hard to answer",
        ],
        "positive": ["Very good", "Good", "Neutral (Slightly good)"],
    },
    {
        "id": "q11e",
        "section": "Impressions of China",
        "label": "Q11(5). Chinese culture",
        "text": "What is your impression of China? — Impression of Chinese culture",
        "kind": "single",
        "col": "q11e",
        "order": [
            "Very good",
            "Good",
            "Neutral (Slightly good)",
            "Neutral (Slightly bad)",
            "Bad",
            "Very bad",
            "Don't know/Hard to answer",
        ],
        "positive": ["Very good", "Good", "Neutral (Slightly good)"],
    },
    {
        "id": "q11f",
        "section": "Impressions of China",
        "label": "Q11(6). Chinese government",
        "text": "What is your impression of China? — Impression of the Chinese government",
        "kind": "single",
        "col": "q11f",
        "order": [
            "Very good",
            "Good",
            "Neutral (Slightly good)",
            "Neutral (Slightly bad)",
            "Bad",
            "Very bad",
            "Don't know/Hard to answer",
        ],
        "positive": ["Very good", "Good", "Neutral (Slightly good)"],
    },
    {
        "id": "q12a",
        "section": "Impressions of Chinese people",
        "label": "Q12(1). Overall impression of Chinese people",
        "text": "What is your impression of the Chinese people? — Overall impression",
        "kind": "single",
        "col": "q12a",
        "order": [
            "Very good",
            "Good",
            "Neutral (Slightly good)",
            "Neutral (Slightly bad)",
            "Bad",
            "Very bad",
            "Don't know/Hard to answer",
        ],
        "positive": ["Very good", "Good", "Neutral (Slightly good)"],
    },
    # --- Society / economy / soft power ---
    {
        "id": "q14",
        "section": "Society and soft power",
        "label": "Q14. Willingness to try a Chinese way of life",
        "text": "Around the world, a growing number of young people are embracing the “Chinese way of life”… Would you be willing to try it?",
        "kind": "single",
        "col": "q14",
        "order": [
            "Very willing",
            "Somewhat willing",
            "Not very willing",
            "Not at all",
            "Don't know/Hard to answer",
        ],
        "positive": ["Very willing", "Somewhat willing"],
    },
    {
        "id": "q15",
        "section": "Society and soft power",
        "label": "Q15. View of public safety in China",
        "text": "In 2025, 98.23% of Chinese respondents reported a sense of public safety… How would you describe public safety in China?",
        "kind": "single",
        "col": "q15",
        "order": [
            "Safest in the world",
            "Among the safest in the world",
            "At the global average level",
            "Relatively poor",
            "Don't know/Hard to answer",
        ],
        "positive": ["Safest in the world", "Among the safest in the world"],
    },
    {
        "id": "q16",
        "section": "Society and soft power",
        "label": "Q16. Confidence in China’s economic growth",
        "text": "Are you confident about China’s sustained economic growth in the next 10 years?",
        "kind": "single",
        "col": "q16",
        "order": [
            "Highly confident",
            "Moderately confident",
            "Slightly confident",
            "Not confident",
            "Don't know/Hard to answer",
        ],
        "positive": ["Highly confident", "Moderately confident"],
    },
    {
        "id": "q24",
        "section": "Leadership and governance",
        "label": "Q24. View of Xi Jinping’s governance experience",
        "text": "From being sent to the countryside as an “educated youth” at the age of 15 to becoming the nation’s highest leader…",
        "kind": "single",
        "col": "q24",
        "order": [
            "Agree",
            "Generally agree",
            "Generally disagree",
            "Disagree",
            "Don't know/Hard to answer",
        ],
        "positive": ["Agree", "Generally agree"],
    },
    {
        "id": "q25",
        "section": "Leadership and governance",
        "label": "Q25. Global initiatives proposed by Xi Jinping",
        "text": "In the face of global peace, development, security and governance deficits, Xi Jinping has proposed concepts such as a community with a shared future for humanity, the Belt and Road Initiative, and the Global Development / Security / Civilization / Governance Initiatives…",
        "kind": "single",
        "col": "q25",
        "order": [
            "Agree",
            "Generally agree",
            "Generally disagree",
            "Disagree",
            "Don't know/Hard to answer",
        ],
        "positive": ["Agree", "Generally agree"],
    },
    {
        "id": "q26",
        "section": "Leadership and governance",
        "label": "Q26. Strongest leadership among G20 leaders",
        "text": "Among the incumbent leaders of G20 members, who do you think demonstrates the strongest leadership?",
        "kind": "single",
        "col": "q26",
        "order": list(G20_LEADERS_ORDER),
        "positive": None,
        "highlight": "Xi Jinping (President of China)",
    },
    {
        "id": "q27",
        "section": "Leadership and governance",
        "label": "Q27. Most respected / responsible G20 leader",
        "text": "Among the incumbent leaders of G20 members, who do you think is the most respected and most responsible?",
        "kind": "single",
        "col": "q27",
        "order": list(G20_LEADERS_ORDER),
        "positive": None,
        "highlight": "Xi Jinping (President of China)",
    },
    # --- International role ---
    {
        "id": "q29",
        "section": "International role",
        "label": "Q29. China playing a bigger role internationally",
        "text": "Do you expect or oppose China to play a bigger and greater role in international affairs in the future?",
        "kind": "single",
        "col": "q29",
        "order": [
            "Extremely expect",
            "Expect",
            "Slightly expect",
            "Absolutely neutral",
            "Slightly oppose",
            "Oppose",
            "Extremely oppose",
            "Don't know/Hard to answer",
        ],
        "positive": ["Extremely expect", "Expect", "Slightly expect"],
    },
    {
        "id": "q32",
        "section": "International role",
        "label": "Q32. Possibility of China becoming the most powerful country",
        "text": "Is it possible for China to become the most powerful country in the world in terms of comprehensive national strength? If yes, when?",
        "kind": "single",
        "col": "q32",
        # Data uses “Probably”; QRE uses “Probable” — resolve_order normalises both.
        "order": [
            "Probable, within 5 years",
            "Probable, within 5-10 years",
            "Possible, within 10-20 years",
            "Possible, within 20-30 years",
            "Possible, within 30-50 years",
            "Perhaps, within 50-100 years",
            "Perhaps, more than 100 years",
            "Absolutely impossible",
            "Don't know/Hard to answer",
        ],
        "positive": None,
    },
    {
        "id": "q36",
        "section": "International role",
        "label": "Q36. One-China principle",
        "text": "The Chinese government states that there is only one China in the world, and Taiwan is an inalienable part of China’s territory…",
        "kind": "single",
        "col": "q36",
        "order": [
            "Agree",
            "Generally agree",
            "Generally disagree",
            "Disagree",
            "Don't know/Hard to answer",
        ],
        "positive": ["Agree", "Generally agree"],
    },
    {
        "id": "q39",
        "section": "International role",
        "label": "Q39. China’s role in regional conflict / peace talks",
        "text": "Since the outbreak of the US-Israel-Iran conflict… China has been committed to promoting peace talks. How should China act?",
        "kind": "single",
        "col": "q39",
        "order": [
            "Play a leading role in promoting peace talks",
            "Play a supporting role in promoting peace talks",
            "Stay neutral and provide necessary humanitarian assistance",
            "Stay uninvolved, with no participation at all",
            "Don't know/Hard to answer",
        ],
        "positive": [
            "Play a leading role in promoting peace talks",
            "Play a supporting role in promoting peace talks",
        ],
    },
    {
        "id": "q41",
        "section": "International order",
        "label": "Q41. Preferred evolution of the international order",
        "text": "How would you like the international order to evolve in the coming years?",
        "kind": "single",
        "col": "q41",
        "order": [
            "A multipolar world system: equal and orderly multipolarity with every country participating equitably in international affairs",
            "A unipolar system: a single superpower dominating international affairs",
            "A bipolar configuration: alliances forming two opposing blocs for mutual confrontation or containment",
            "Disorderly competition among states: regression to the law of the jungle where the strong bully the weak",
            "Don't know/Hard to answer",
        ],
        "positive": None,
    },
    {
        "id": "q42",
        "section": "China–US relations",
        "label": "Q42. Reaction to Trump’s visit / talks with Xi",
        "text": "From May 13 to 15, US President Donald Trump paid a state visit to China and held long and friendly talks with President Xi Jinping…",
        "kind": "single",
        "col": "q42",
        "order": [
            "I warmly welcome it, as it will improve bilateral relations and help both sides manage their differences properly.",
            "I am relatively optimistic; I acknowledge the positive signals, while recognizing that what truly matters is the follow-up action.",
            "I remain skeptical; it seems like a short-term, superficial easing of tensions, and I am concerned about potential risks or negative impacts down the road.",
            "I am disappointed and dissatisfied; the talks did not achieve the expected results, and President Trump's visit to China was a failure.",
            "Don't know/Hard to answer",
        ],
        "positive": None,
    },
    {
        "id": "q44",
        "section": "China–US relations",
        "label": "Q44. Trump’s remarks on Xi / China",
        "text": "US President Trump has repeatedly stated that President Xi is a great leader, that China is a great country…",
        "kind": "single",
        "col": "q44",
        "order": [
            "Agree",
            "Basically agree",
            "Basically disagree",
            "Disagree",
            "Don't know/Hard to answer",
        ],
        "positive": ["Agree", "Basically agree"],
    },
    {
        "id": "q45",
        "section": "China–US relations",
        "label": "Q45. Desired change in U.S.–China relations",
        "text": "What changes are you willing to see in the U.S.-China relationship in the coming year?",
        "kind": "single",
        "col": "q45",
        "order": [
            "Toward conflict",
            "Maintain status quo",
            "Toward friendliness",
            "Don't know/Hard to answer",
        ],
        "positive": ["Toward friendliness"],
    },
    {
        "id": "q46",
        "section": "China–US relations",
        "label": "Q46. More favorable opinion: China or the U.S.",
        "text": "Which country do you have a more favorable opinion of, China or the U.S.?",
        "kind": "single",
        "col": "q46",
        "order": ["China", "U.S.", "Almost equal", "Don't know/Hard to answer"],
        "positive": ["China"],
        "highlight": "China",
    },
]


def sections() -> list[str]:
    seen = []
    for q in QUESTIONS:
        if q["section"] not in seen:
            seen.append(q["section"])
    return seen


def by_id(qid: str) -> dict:
    for q in QUESTIONS:
        if q["id"] == qid:
            return q
    raise KeyError(qid)
