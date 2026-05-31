from datetime import datetime
import json
import re
from dotenv import load_dotenv
from os import getenv
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

from langchain_groq import ChatGroq

load_dotenv()

# =========================================================
# LLM
# =========================================================

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=getenv("GROQ_API_KEY") # use env variable
)

# =========================================================
# GLOBAL CHAT HISTORY
# =========================================================

chat_history = []

# =========================================================
# PROMPTS
# =========================================================

KNOWLEDGE_PROMPT = """
You are an expert advisor in mud crab farming (Scylla spp.).

Your main role is to provide accurate, practical, and field-ready guidance for crab farmers.

You ONLY answer questions related to:
- Crab fattening and grow-out
- Feeding strategies and nutrition
- Molting and growth stages
- Water quality management (salinity, pH, ammonia, oxygen)
- Diseases, parasites, and health issues
- Pond or cage management systems
- Harvesting and post-harvest handling
- Best farming practices and biosecurity
- DOs and DON'Ts in crab farming operations

If a question is not related to mud crab farming or cooking crab dishes, respond with:
"I can only assist with mud crab farming and crab-related cooking ideas."

---

### 🦀 BONUS FUN MODE (Cooking & Food)
If the user asks about cooking crab, recipes, or food ideas, you MAY respond briefly and casually.

You can include:
- Simple crab cooking methods (boiling, steaming, grilling, sautéing)
- Popular crab dishes (garlic butter crab, chili crab, steamed crab, crab curry)
- Basic flavor suggestions (garlic, butter, chili, coconut milk, soy sauce)
- Easy home-style cooking tips

Keep it short, fun, and slightly playful — like a friendly kitchen assistant who loves seafood.

You may use light humor (occasionally playful tone), but do not become irrelevant or overly detailed.

---

### Response Rules:
- Be practical and action-oriented for farming topics
- Be simple and fun for cooking topics
- Avoid long lectures
- Prefer step-by-step instructions when relevant
- Stay within crab-related topics only

---

### Style:
- Friendly, conversational, slightly humorous when appropriate
- Think: “farm technician + seafood-loving home cook”
- No fluff, no unrelated topics
"""

FARMER_PROMPT = """
You are a specialist assistant for CRAB FARM monitoring only.
You must only respond to topics related to crab, crab farming, crab health, crab production, or crab farm sensor data.

If the input is unrelated to crab or crab farming, respond with:
"Unsupported query: only crab farm data is allowed.

Interpret sensor analysis results and provide:

1. Crab Fattening Status
2. Farm Condition Insight
3. Main Constraints Affecting Growth
4. Stable Conditions Supporting Growth
5. Enhancement Actions

Focus on farming decisions and recommendations.
"""

# =========================================================
# ROUTER
# =========================================================

def detect_intent(query: str):

    sensor_keywords = [
        "today",
        "yesterday",
        "logs",
        "sensor",
        "analyze",
        "analysis",
        "trend",
        "report",
        "water quality"
    ]

    q = query.lower()

    if any(word in q for word in sensor_keywords):
        return "sensor"

    return "knowledge"

# =========================================================
# HELPERS
# =========================================================

def extract_json(text: str):

    text = re.sub(r"```json|```", "", text).strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found")

    return json.loads(match.group())


def validate_date_range(start_date, end_date):

    start_dt = datetime.strptime(
        start_date,
        "%Y-%m-%d %H:%M:%S"
    )

    end_dt = datetime.strptime(
        end_date,
        "%Y-%m-%d %H:%M:%S"
    )

    return start_dt, end_dt

# =========================================================
# KNOWLEDGE AGENT
# =========================================================

def build_date_prompt(current_datetime):
    return f"""
Current datetime: {current_datetime}

You are a date range extraction engine.

Extract the date range requested by the user.

Return ONLY valid JSON.

Format:

{{
  "start_date": "YYYY-MM-DD HH:MM:SS",
  "end_date": "YYYY-MM-DD HH:MM:SS",
  "period_description": "human readable period"
}}

Examples:

User: analyze yesterday logs

{{
  "start_date": "2026-05-30 00:00:00",
  "end_date": "2026-05-30 23:59:59",
  "period_description": "yesterday"
}}

User: analyze last week

{{
  "start_date": "2026-05-24 00:00:00",
  "end_date": "2026-05-31 12:00:00",
  "period_description": "last week"
}}

User: analyze latest logs

{{
  "start_date": "2026-05-18 20:51:46",
  "end_date": "2026-05-23 21:20:33",
  "period_description": "latest_logs"
}}

Rules:

- latest logs means most recent available logs
- recent logs means most recent available logs
- return JSON only
"""

def run_knowledge(query: str):

    messages = [
        SystemMessage(content=KNOWLEDGE_PROMPT)
    ]

    # include conversation history
    messages.extend(chat_history)

    messages.append(
        HumanMessage(content=query)
    )

    response = llm.invoke(messages)

    # save history
    chat_history.append(
        HumanMessage(content=query)
    )

    chat_history.append(
        AIMessage(content=response.content)
    )

    return response.content


# =========================================================
# SENSOR AGENT
# =========================================================

from sqlalchemy import select
from sqlalchemy.orm import Session
import pandas as pd
import json
from models import SensorLogs
from database import engine
from datetime import datetime

with Session(engine) as session:

    query = select(SensorLogs).where(
        SensorLogs.created_at >= datetime(2026, 5, 23, 18, 42, 36)
    )

    results = session.execute(query).scalars().all()

    data = [
        {
            "id": row.id,
            "sensor_type": row.sensor_type,
            "status": row.status,
            "value": row.value,
            "created_at": row.created_at
        }
        for row in results
    ]

df = pd.DataFrame(data)
from . import sensor_analyzer
analyzer = sensor_analyzer.SensorAnalyzer(df)

def run_sensor(query: str):

    # STEP 1
    now = datetime.now()

    current_datetime = now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # STEP 2
    date_prompt = build_date_prompt(
        current_datetime
    )

    # STEP 3
    date_response = llm.invoke([
        SystemMessage(content=date_prompt),
        HumanMessage(content=query)
    ])

    extracted_dates = extract_json(
        date_response.content
    )

    print(extracted_dates)
    
    
    start_date, end_date = validate_date_range(
        extracted_dates["start_date"],
        extracted_dates["end_date"]
    )

    # STEP 4
    report = analyzer.analyze_system(
        start_date,
        end_date
    )

    report_json = json.dumps(
        report,
        indent=2
    )

    # STEP 5
    messages = [
        SystemMessage(content=FARMER_PROMPT)
    ]

    # include history
    messages.extend(chat_history)

    messages.append(
        HumanMessage(
            content=f"""
User Request:
{query}

Sensor Analysis:
{report_json}
"""
        )
    )

    farmer_response = llm.invoke(messages)

    # save history
    chat_history.append(
        HumanMessage(content=query)
    )

    chat_history.append(
        AIMessage(
            content=farmer_response.content
        )
    )

    return {
        "query": query,
        "start_date": start_date,
        "end_date": end_date,
        "report": report,
        "farmer_explanation":
            farmer_response.content
    }

# =========================================================
# MAIN ENTRY
# =========================================================

def chat(query: str):

    intent = detect_intent(query)

    if intent != "knowledge":
        
        result = run_sensor(query)
        return result["farmer_explanation"]

    return run_knowledge(query)


# =========================================================
# CLI
# =========================================================

if __name__ == "__main__":

    print("Mud Crab AI Assistant\n")

    while True:

        query = input("You: ")

        if query.lower() in [
            "exit",
            "quit"
        ]:
            break

        response = chat(query)

        print("\nAI:")
        print(response)
        print("\n" + "=" * 50)