import pandas as pd
import numpy as np
from scipy.stats import zscore
from sklearn.linear_model import LinearRegression

SENSOR_THRESHOLDS = {
    "do": {
        "warning": [
            [4.5, 4.9],
            [12.1, 12.5]
        ],
        "danger": [
            [0, 4.5],
            [12.5, float("inf")]
        ]
    },

    "temperature": {
        "warning": [
            [24.1, 24.5],
            [35.1, 35.5]
        ],
        "danger": [
            [float("-inf"), 24.1],
            [35.5, float("inf")]
        ]
    },

    "ph": {
        "warning": [
            [7.1, 7.4],
            [9.1, 9.5]
        ],
        "danger": [
            [float("-inf"), 7.1],
            [9.5, float("inf")]
        ]
    },

    "tds": {
        "warning": [
            [14.5, 14.9],
            [20.1, 20.5]
        ],
        "danger": [
            [float("-inf"), 14.5],
            [20.5, float("inf")]
        ]
    },

    "ammonium": {
        "warning": [
            [0.1, 0.4],
            [3.1, 3.5]
        ],
        "danger": [
            [float("-inf"), 0.1],
            [3.5, float("inf")]
        ]
    }
}

class SensorAnalyzer:

    def __init__(self, df):
        self.df = df.copy()
        self.thresholds = SENSOR_THRESHOLDS
        self.df["created_at"] = pd.to_datetime(self.df["created_at"])
    
    def classify_value(self, sensor_type, value):

        if sensor_type not in self.thresholds:
            return "UNKNOWN"

        rules = self.thresholds[sensor_type]

        for low, high in rules["danger"]:
            if low <= value <= high:
                return "DANGER"

        for low, high in rules["warning"]:
            if low <= value <= high:
                return "WARNING"

        return "NORMAL"
    
    # -----------------------------------
    # TREND ANALYSIS
    # -----------------------------------
    
    def compute_trend(self, df):
        if len(df) < 2:
            return {
                "trend": "INSUFFICIENT_DATA",
                "slope": 0.0,
                "volatility": 0.0
            }

        df = df.sort_values("created_at")

        y = df["value"].astype(float).values

        X = np.arange(len(y)).reshape(-1, 1)

        model = LinearRegression()
        model.fit(X, y)

        slope = float(model.coef_[0])
        volatility = float(np.std(y))

        if slope > 0.1:
            trend = "INCREASING"
        elif slope < -0.1:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        return {
            "trend": trend,
            "slope": round(slope, 4),
            "volatility": round(volatility, 4)
        }

    # -----------------------------------
    # ANOMALY DETECTION
    # -----------------------------------
    
    def compute_anomaly_summary(self, sensor_type, df):

        counts = {
            "normal": 0,
            "warning": 0,
            "danger": 0
        }

        first_warning = None
        last_warning = None
        first_danger = None
        last_danger = None

        for _, row in df.iterrows():
            status = self.classify_value(sensor_type, row["value"])
            t = row["created_at"]

            if status == "DANGER":
                counts["danger"] += 1
                first_danger = first_danger or t
                last_danger = t

            elif status == "WARNING":
                counts["warning"] += 1
                first_warning = first_warning or t
                last_warning = t

            else:
                counts["normal"] += 1

        return {
            "total": len(df),
            "counts": counts,
            "first_warning": str(first_warning) if first_warning else None,
            "last_warning": str(last_warning) if last_warning else None,
            "first_danger": str(first_danger) if first_danger else None,
            "last_danger": str(last_danger) if last_danger else None
        }
    
    # -----------------------------------
    # ANALYZE ALL SENSORS
    # -----------------------------------
    
    def analyze_sensor(self, sensor_type, start, end):

        df = self.df[
            (self.df["sensor_type"] == sensor_type) &
            (self.df["created_at"] >= start) &
            (self.df["created_at"] <= end)
        ]

        if len(df) == 0:
            return {
                "trend": {"trend": "NO_DATA"},
                "anomaly": None
            }

        return {
            "trend": self.compute_trend(df),
            "anomaly": self.compute_anomaly_summary(sensor_type, df)
        }
    
    def analyze_system(self, start, end):

        sensors = [
            "temperature",
            "ph",
            "tds",
            "turbidity",
            "ammonium",
            "do"
        ]

        system = {
            "time_window": f"{start} to {end}",
            "sensors": {}
        }

        risk_score = 0

        for sensor in sensors:

            report = self.analyze_sensor(sensor, start, end)

            system["sensors"][sensor] = report

            # simple risk scoring
            danger = report["anomaly"]["counts"]["danger"] if report["anomaly"] else 0
            warning = report["anomaly"]["counts"]["warning"] if report["anomaly"] else 0

            risk_score += danger * 2 + warning * 0.5

        system["overall_risk_score"] = round(min(risk_score / 100, 1.0), 2)

        if system["overall_risk_score"] > 0.7:
            system["system_health"] = "CRITICAL"
        elif system["overall_risk_score"] > 0.4:
            system["system_health"] = "WARNING"
        else:
            system["system_health"] = "STABLE"

        return system


    
# from sqlalchemy import select
# from sqlalchemy.orm import Session
# import pandas as pd
# import json
# from models import SensorLogs
# from database import engine
# from datetime import datetime

# with Session(engine) as session:

#     query = select(SensorLogs).where(
#         SensorLogs.created_at >= datetime(2026, 5, 23, 18, 42, 36)
#     )

#     results = session.execute(query).scalars().all()

#     data = [
#         {
#             "id": row.id,
#             "sensor_type": row.sensor_type,
#             "status": row.status,
#             "value": row.value,
#             "created_at": row.created_at
#         }
#         for row in results
#     ]

# df = pd.DataFrame(data)


# SENSOR_THRESHOLDS = {
#     "do": {
#         "warning": [
#             [4.5, 4.9],
#             [12.1, 12.5]
#         ],
#         "danger": [
#             [0, 4.5],
#             [12.5, float("inf")]
#         ]
#     },

#     "temperature": {
#         "warning": [
#             [24.1, 24.5],
#             [35.1, 35.5]
#         ],
#         "danger": [
#             [float("-inf"), 24.1],
#             [35.5, float("inf")]
#         ]
#     },

#     "ph": {
#         "warning": [
#             [7.1, 7.4],
#             [9.1, 9.5]
#         ],
#         "danger": [
#             [float("-inf"), 7.1],
#             [9.5, float("inf")]
#         ]
#     },

#     "tds": {
#         "warning": [
#             [14.5, 14.9],
#             [20.1, 20.5]
#         ],
#         "danger": [
#             [float("-inf"), 14.5],
#             [20.5, float("inf")]
#         ]
#     },

#     "ammonium": {
#         "warning": [
#             [0.1, 0.4],
#             [3.1, 3.5]
#         ],
#         "danger": [
#             [float("-inf"), 0.1],
#             [3.5, float("inf")]
#         ]
#     }
# }

# analyzer = SensorAnalyzer(df)

# report = analyzer.analyze_system("2026-05-18 23:00:00", "2026-05-23 21:08:53")
# print(report)