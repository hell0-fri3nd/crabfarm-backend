from datetime import datetime
import json
import re
from dotenv import load_dotenv
from os import getenv
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from database import engine
from models import SensorLogs
from services.sensor_analyzer import SensorAnalyzer
from .prompts import (
    INTENTION_PROMPT,
    KNOWLEDGE_PROMPT,
    SENSOR_ANALYZE_PROMPT,
    build_date_prompt,
    LOG_QUERY_PROMPT
)


load_dotenv()

class AiAssistant:
    def __init__(self):
        self.name = "AI Assistant"
        self.chat_history = []
        
        self.llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,
            api_key=getenv("GROQ_API_KEY") # use env variable
        )
                
        # Intent classifier chain
        self.intent_chain = ChatPromptTemplate.from_messages([
            ("system", INTENTION_PROMPT),
            ("human", "{query}")
        ]) | self.llm
        
        # Knowledge chain (crab farming expert)
        self.knowledge_chain = ChatPromptTemplate.from_messages([
            ("system", KNOWLEDGE_PROMPT),
            ("human", "{query}")
        ]) | self.llm

    def __detect_intent(self, query: str) -> str:
        response = self.intent_chain.invoke({"query": query})
        intent = response.content.strip().lower()

        if intent in {"sensor", "knowledge", "logs"}:
            return intent

        return "N.A"

    def __extract_json(self, text: str) -> dict:
        text = re.sub(r"```json|```", "", text).strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise ValueError("No JSON found in LLM response")

        return json.loads(match.group())

    def __validate_date_range(self, start_date: str, end_date: str):
        start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")

        return start_dt, end_dt

    def __load_sensor_dataframe(self) -> pd.DataFrame:
        with Session(engine) as session:
            results = session.execute(select(SensorLogs)).scalars().all()

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

        return pd.DataFrame(
            data,
            columns=["id", "sensor_type", "status", "value", "created_at"]
        )

    def __trim_history(self, max_exchanges=1):
        max_messages = max_exchanges * 2
        if len(self.chat_history) > max_messages:
            self.chat_history = self.chat_history[-max_messages:]

    def __get_date_range(self, query: str):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_prompt = build_date_prompt(current_datetime)

        date_response = self.llm.invoke([
            SystemMessage(content=date_prompt),
            HumanMessage(content=query)
        ])

        try:
            extracted_dates = self.__extract_json(date_response.content)
            return self.__validate_date_range(
                extracted_dates["start_date"],
                extracted_dates["end_date"]
            )
        except (ValueError, KeyError, json.JSONDecodeError):
            now = datetime.now()
            start = datetime(now.year, now.month, now.day, 0, 0, 0)
            return start, now

    def run_knowledge(self, query: str) -> str:
        messages = [SystemMessage(content=KNOWLEDGE_PROMPT)]
        messages.extend(self.chat_history)
        messages.append(HumanMessage(content=query))

        response = self.llm.invoke(messages)

        self.chat_history.append(HumanMessage(content=query))
        self.chat_history.append(AIMessage(content=response.content))

        return response.content

    def run_sensor(self, query: str) -> dict:
        start_date, end_date = self.__get_date_range(query)

        df = self.__load_sensor_dataframe()

        mask = (df["created_at"] >= start_date) & (df["created_at"] <= end_date)
        has_data = mask.any()

        if not has_data:
            messages = [SystemMessage(content=SENSOR_ANALYZE_PROMPT)]
            messages.extend(self.chat_history)
            messages.append(
                HumanMessage(content=f"""
User Request:
{query}

No sensor data is available from {start_date} to {end_date}.
Inform the user that no sensor logs exist for that time period.
"""
                )
            )
            response = self.llm.invoke(messages)
            self.chat_history.append(HumanMessage(content=query))
            self.chat_history.append(AIMessage(content=response.content))
            return {
                "query": query,
                "start_date": start_date,
                "end_date": end_date,
                "report": None,
                "farmer_explanation": response.content
            }

        analyzer = SensorAnalyzer(df)
        report = analyzer.analyze_system(start_date, end_date)
        report_json = json.dumps(report, indent=2)

        messages = [SystemMessage(content=SENSOR_ANALYZE_PROMPT)]
        messages.extend(self.chat_history)
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

        response = self.llm.invoke(messages)

        self.chat_history.append(HumanMessage(content=query))
        self.chat_history.append(AIMessage(content=response.content))

        return {
            "query": query,
            "start_date": start_date,
            "end_date": end_date,
            "report": report,
            "farmer_explanation": response.content
        }

    def run_logs_query(self, query: str) -> str:
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_prompt = LOG_QUERY_PROMPT.format(current_datetime=current_datetime)
        
        log_response = self.llm.invoke([
            SystemMessage(content=log_prompt),
            HumanMessage(content=query)
        ])

        try:
            params = self.__extract_json(log_response.content)
        except (ValueError, json.JSONDecodeError):
            return "I couldn't understand the log query. Please try rephrasing."

        df = self.__load_sensor_dataframe()
        if df.empty:
            return "No sensor logs found in the database."

        if params.get("start_date"):
            df = df[df["created_at"] >= params["start_date"]]
        if params.get("end_date"):
            df = df[df["created_at"] <= params["end_date"]]

        status_filter = params.get("status_filter", "ALL")
        if status_filter != "ALL":
            df = df[df["status"] == status_filter]

        sensor_filter = params.get("sensor_filter", "ALL")
        if sensor_filter != "ALL":
            df = df[df["sensor_type"] == sensor_filter]

        order = params.get("order", "desc")
        df = df.sort_values("created_at", ascending=(order == "asc"))

        limit = params.get("limit")
        aggregation = params.get("aggregation", "list")
        if limit and limit > 0:
            df = df.head(limit)
        elif aggregation == "list":
            df = df.head(20)

        if df.empty:
            return "No sensor logs found matching your request."

        group_by = params.get("group_by", "none")

        if aggregation == "count" and group_by == "none":
            result_text = f"**Total: {len(df)} log(s)**\n"
        elif group_by != "none":
            if group_by == "date":
                grouped = df.groupby(df["created_at"].dt.date).size().reset_index(name="count").rename(columns={"created_at": "date"})
            elif group_by == "sensor_type":
                grouped = df.groupby("sensor_type").size().reset_index(name="count")
            elif group_by == "status":
                grouped = df.groupby("status").size().reset_index(name="count")
            else:
                grouped = df.groupby(group_by).size().reset_index(name="count")
            result_text = grouped.to_string(index=False)
        else:
            display = df[["id", "sensor_type", "status", "value", "created_at"]].copy()
            display["value"] = display["value"].round(2)
            result_text = display.to_string(index=False)

        response = self.llm.invoke([
            SystemMessage(content="You present sensor log data clearly to the user in a readable table format. If showing a table, keep it as-is for clarity."),
            HumanMessage(content=f"""
User Request:
{query}

Database Query Results:
{result_text}

Present this data clearly. Show the table as formatted. If no data, inform the user.
""")
        ])

        self.chat_history.append(HumanMessage(content=query))
        self.chat_history.append(AIMessage(content=response.content))

        return response.content

    def chat(self, message: str) -> str:
        intent = self.__detect_intent(message)

        if intent == "sensor":
            result = self.run_sensor(message)
            self.__trim_history()
            return result["farmer_explanation"]

        if intent == "logs":
            response = self.run_logs_query(message)
            self.__trim_history()
            return response

        response = self.run_knowledge(message)
        self.__trim_history()
        return response

    def chat_from_db(self, message: str, db_messages: list) -> tuple:
        from langchain_core.messages import HumanMessage, AIMessage

        history = [
            HumanMessage(content=msg.content) if msg.role == "user" else AIMessage(content=msg.content)
            for msg in db_messages
        ]

        intent = self.__detect_intent(message)

        if intent == "sensor":
            result = self.__run_sensor(message, history)
            return result["farmer_explanation"], intent

        if intent == "logs":
            response = self.__run_logs_query(message, history)
            return response, intent

        response = self.__run_knowledge(message, history)
        return response, intent

    def __run_knowledge(self, query: str, history: list) -> str:
        messages = [SystemMessage(content=KNOWLEDGE_PROMPT)]
        messages.extend(history)
        messages.append(HumanMessage(content=query))
        response = self.llm.invoke(messages)
        return response.content

    def __run_sensor(self, query: str, history: list) -> dict:
        start_date, end_date = self.__get_date_range(query)
        df = self.__load_sensor_dataframe()
        mask = (df["created_at"] >= start_date) & (df["created_at"] <= end_date)
        has_data = mask.any()

        if not has_data:
            messages = [SystemMessage(content=SENSOR_ANALYZE_PROMPT)]
            messages.extend(history)
            messages.append(HumanMessage(content=f"""
User Request:
{query}

No sensor data is available from {start_date} to {end_date}.
Inform the user that no sensor logs exist for that time period.
"""))
            response = self.llm.invoke(messages)
            return {
                "query": query,
                "start_date": start_date,
                "end_date": end_date,
                "report": None,
                "farmer_explanation": response.content
            }

        analyzer = SensorAnalyzer(df)
        report = analyzer.analyze_system(start_date, end_date)
        report_json = json.dumps(report, indent=2)

        messages = [SystemMessage(content=SENSOR_ANALYZE_PROMPT)]
        messages.extend(history)
        messages.append(HumanMessage(content=f"""
User Request:
{query}

Sensor Analysis:
{report_json}
"""))

        response = self.llm.invoke(messages)

        return {
            "query": query,
            "start_date": start_date,
            "end_date": end_date,
            "report": report,
            "farmer_explanation": response.content
        }

    def __run_logs_query(self, query: str, history: list) -> str:
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_prompt = LOG_QUERY_PROMPT.format(current_datetime=current_datetime)

        log_response = self.llm.invoke([
            SystemMessage(content=log_prompt),
            HumanMessage(content=query)
        ])

        try:
            params = self.__extract_json(log_response.content)
        except (ValueError, json.JSONDecodeError):
            return "I couldn't understand the log query. Please try rephrasing."

        df = self.__load_sensor_dataframe()
        if df.empty:
            return "No sensor logs found in the database."

        if params.get("start_date"):
            df = df[df["created_at"] >= params["start_date"]]
        if params.get("end_date"):
            df = df[df["created_at"] <= params["end_date"]]

        status_filter = params.get("status_filter", "ALL")
        if status_filter != "ALL":
            df = df[df["status"] == status_filter]

        sensor_filter = params.get("sensor_filter", "ALL")
        if sensor_filter != "ALL":
            df = df[df["sensor_type"] == sensor_filter]

        order = params.get("order", "desc")
        df = df.sort_values("created_at", ascending=(order == "asc"))

        limit = params.get("limit")
        aggregation = params.get("aggregation", "list")
        if limit and limit > 0:
            df = df.head(limit)
        elif aggregation == "list":
            df = df.head(20)

        if df.empty:
            return "No sensor logs found matching your request."

        group_by = params.get("group_by", "none")

        if aggregation == "count" and group_by == "none":
            result_text = f"**Total: {len(df)} log(s)**\n"
        elif group_by != "none":
            if group_by == "date":
                grouped = df.groupby(df["created_at"].dt.date).size().reset_index(name="count").rename(columns={"created_at": "date"})
            elif group_by == "sensor_type":
                grouped = df.groupby("sensor_type").size().reset_index(name="count")
            elif group_by == "status":
                grouped = df.groupby("status").size().reset_index(name="count")
            else:
                grouped = df.groupby(group_by).size().reset_index(name="count")
            result_text = grouped.to_string(index=False)
        else:
            display = df[["id", "sensor_type", "status", "value", "created_at"]].copy()
            display["value"] = display["value"].round(2)
            result_text = display.to_string(index=False)

        response = self.llm.invoke([
            SystemMessage(content="You present sensor log data clearly to the user in a readable table format. If showing a table, keep it as-is for clarity."),
            HumanMessage(content=f"""
User Request:
{query}

Database Query Results:
{result_text}

Present this data clearly. Show the table as formatted. If no data, inform the user.
""")
        ])

        return response.content

assistant = AiAssistant()

if __name__ == "__main__":
    while True:
        message = input("You: ")

        if message.lower() in ["exit", "quit"]:
            break

        response = assistant.chat(message)

        print(f"AI: {response}")