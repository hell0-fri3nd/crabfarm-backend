import pandas as pd
import numpy as np
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

    "turbidity": {
        "warning": [
            [10, 20],
            [40, 50]
        ],
        "danger": [
            [float("-inf"), 10],
            [50, float("inf")]
        ]
    },

    "ammonium": {
        "warning": [
            [1.0, 3.0]
        ],
        "danger": [
            [3.0, float("inf")]
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
            "danger": 0,
            "unknown": 0
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

            elif status == "UNKNOWN":
                counts["unknown"] += 1

            else:
                counts["normal"] += 1

        total = len(df)
        def pct(n):
            return round(n / total * 100, 1) if total else 0.0

        return {
            "total": total,
            "counts": counts,
            "percentages": {
                "normal": pct(counts["normal"]),
                "warning": pct(counts["warning"]),
                "danger": pct(counts["danger"]),
                "unknown": pct(counts["unknown"])
            },
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
            "thresholds": self.thresholds,
            "sensors": {}
        }

        sensor_risks = {}

        for sensor in sensors:

            report = self.analyze_sensor(sensor, start, end)

            system["sensors"][sensor] = report

            anomaly = report["anomaly"]
            if anomaly and anomaly["total"] > 0:
                danger_pct = anomaly["percentages"]["danger"]
                warning_pct = anomaly["percentages"]["warning"]
                sensor_risk = round((danger_pct * 1.0 + warning_pct * 0.3) / 100, 4)
            else:
                sensor_risk = 0.0

            sensor_risks[sensor] = sensor_risk

        system["sensor_risk_scores"] = sensor_risks

        overall = sum(sensor_risks.values()) / len(sensors) if sensors else 0.0
        system["overall_risk_score"] = round(overall, 2)

        if system["overall_risk_score"] > 0.7:
            system["system_health"] = "CRITICAL"
        elif system["overall_risk_score"] > 0.4:
            system["system_health"] = "WARNING"
        else:
            system["system_health"] = "STABLE"

        return system