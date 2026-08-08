from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Alarm API Simulator", version="1.0.0")
API_TOKEN = os.getenv("ALARM_API_TOKEN", "demo-token")


def _check_auth(authorization: Optional[str]) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


ASSETS: List[Dict[str, Any]] = [
    {
        "asset_id": "ASSET-001",
        "name": "Boiler Feed Pump 101",
        "asset_type": "Pump",
        "site": "EastRefinery",
        "unit": "Unit 1",
        "criticality": "critical",
        "manufacturer": "FlowTech",
        "health_score": 0.62,
    },
    {
        "asset_id": "ASSET-002",
        "name": "Boiler Feed Pump 102",
        "asset_type": "Pump",
        "site": "EastRefinery",
        "unit": "Unit 1",
        "criticality": "high",
        "manufacturer": "FlowTech",
        "health_score": 0.78,
    },
    {
        "asset_id": "ASSET-003",
        "name": "Compressor C-201",
        "asset_type": "Compressor",
        "site": "EastRefinery",
        "unit": "Unit 2",
        "criticality": "critical",
        "manufacturer": "TurboCore",
        "health_score": 0.54,
    },
    {
        "asset_id": "ASSET-006",
        "name": "Motor M-501",
        "asset_type": "Motor",
        "site": "SouthPlant",
        "unit": "Unit 3",
        "criticality": "high",
        "manufacturer": "Electra",
        "health_score": 0.69,
    },
    {
        "asset_id": "ASSET-007",
        "name": "Heat Exchanger HX-101",
        "asset_type": "Heat Exchanger",
        "site": "EastRefinery",
        "unit": "Unit 1",
        "criticality": "medium",
        "manufacturer": "ThermoTech",
        "health_score": 0.71,
    },
    {
        "asset_id": "ASSET-008",
        "name": "Turbine T-101",
        "asset_type": "Turbine",
        "site": "EastRefinery",
        "unit": "Unit 2",
        "criticality": "critical",
        "manufacturer": "TurboCore",
        "health_score": 0.58,
    },
    {
        "asset_id": "ASSET-009",
        "name": "Compressor C-202",
        "asset_type": "Compressor",
        "site": "SouthPlant",
        "unit": "Unit 4",
        "criticality": "high",
        "manufacturer": "TurboCore",
        "health_score": 0.83,
    },
]

ALARMS: List[Dict[str, Any]] = [
    {
        "alarm_id": "ALM-001",
        "alarm_name": "Low Suction Pressure",
        "description": "Suction pressure dropped below safe threshold.",
        "asset_id": "ASSET-001",
        "site": "EastRefinery",
        "unit": "Unit 1",
        "severity": "critical",
        "status": "active",
        "start_time": "2026-08-08T06:00:00Z",
        "ack_time": None,
    },
    {
        "alarm_id": "ALM-003",
        "alarm_name": "High Discharge Temperature",
        "description": "Compressor discharge temperature rising continuously.",
        "asset_id": "ASSET-003",
        "site": "EastRefinery",
        "unit": "Unit 2",
        "severity": "critical",
        "status": "active",
        "start_time": "2026-08-08T05:30:00Z",
        "ack_time": None,
    },
    {
        "alarm_id": "ALM-004",
        "alarm_name": "Cooling Water Low Flow",
        "description": "Cooling water flow lower than expected.",
        "asset_id": "ASSET-003",
        "site": "EastRefinery",
        "unit": "Unit 2",
        "severity": "high",
        "status": "acknowledged",
        "start_time": "2026-08-08T05:20:00Z",
        "ack_time": "2026-08-08T05:28:00Z",
    },
    {
        "alarm_id": "ALM-006",
        "alarm_name": "Motor Overload",
        "description": "Motor current exceeded overload threshold.",
        "asset_id": "ASSET-006",
        "site": "SouthPlant",
        "unit": "Unit 3",
        "severity": "high",
        "status": "active",
        "start_time": "2026-08-07T10:00:00Z",
        "ack_time": None,
    },
    {
        "alarm_id": "ALM-002",
        "alarm_name": "High Vibration",
        "description": "BFP vibration levels exceeded acceptable limit.",
        "asset_id": "ASSET-002",
        "site": "EastRefinery",
        "unit": "Unit 1",
        "severity": "high",
        "status": "active",
        "start_time": "2026-08-08T07:15:00Z",
        "ack_time": None,
    },
    {
        "alarm_id": "ALM-005",
        "alarm_name": "High Shell Temperature",
        "description": "Heat exchanger shell side temperature above operating limit.",
        "asset_id": "ASSET-007",
        "site": "EastRefinery",
        "unit": "Unit 1",
        "severity": "medium",
        "status": "acknowledged",
        "start_time": "2026-08-08T04:00:00Z",
        "ack_time": "2026-08-08T04:30:00Z",
    },
    {
        "alarm_id": "ALM-007",
        "alarm_name": "Turbine Overspeed Warning",
        "description": "Turbine speed approaching trip threshold.",
        "asset_id": "ASSET-008",
        "site": "EastRefinery",
        "unit": "Unit 2",
        "severity": "critical",
        "status": "active",
        "start_time": "2026-08-08T08:00:00Z",
        "ack_time": None,
    },
]

RECOMMENDATIONS: Dict[str, List[str]] = {
    "ALM-001": [
        "Check suction strainer for clogging and differential pressure.",
        "Verify upstream valve position and feed tank level.",
        "Confirm instrument calibration for suction pressure transmitter.",
    ],
    "ALM-003": [
        "Inspect lube oil cooling loop and verify temperature controller.",
        "Check compressor anti-surge valve response and vibration trend.",
        "Review last 24h alarms for cooling water disturbances.",
    ],
    "ALM-006": [
        "Check for mechanical binding: inspect belt/coupling alignment.",
        "Measure phase currents and check for phase imbalance.",
        "Verify load has not increased beyond motor rated capacity.",
        "Check ventilation openings for obstruction and ambient temperature.",
    ],
    "ALM-002": [
        "Check bearing condition: listen for unusual noise, measure bearing temperature.",
        "Inspect pump coupling for wear or misalignment.",
        "Review vibration trend — sudden spike or gradual increase?",
        "Reduce flow if operating close to runout condition.",
    ],
    "ALM-007": [
        "Immediately verify speed controller setpoint and governor response.",
        "Check fuel/steam supply to turbine for surges.",
        "Prepare for emergency shutdown if speed exceeds trip threshold.",
        "Review last governing system maintenance records.",
    ],
    "ALM-005": [
        "Verify cooling water supply flow and temperature.",
        "Check for fouling on tube bundle — consider cleaning if heat transfer is reduced.",
        "Review process side inlet temperature for unexpected excursions.",
    ],
}


class TimeRange(BaseModel):
    start_time: str
    end_time: str


class SummaryRequest(BaseModel):
    asset_ids: Optional[List[str]] = None
    time_range: TimeRange
    severity: Optional[List[str]] = None
    group_by: List[str] = Field(default_factory=lambda: ["alarm_name"])
    kpis: List[str] = Field(default_factory=lambda: ["alarm_count", "recurring_rate", "avg_ack_delay"])


class TrendRequest(BaseModel):
    asset_ids: Optional[List[str]] = None
    time_range: TimeRange
    bucket: str = "daily"
    metrics: List[str] = Field(default_factory=lambda: ["alarm_count"])


class CorrelationRequest(BaseModel):
    asset_ids: List[str]
    time_range: TimeRange
    correlation_method: str = "cooccurrence"
    lag_window_minutes: int = 15
    severity_threshold: str = "medium"
    min_support: int = 1


class FloodRequest(BaseModel):
    unit: str
    time_range: TimeRange
    threshold_count: int = 10
    rolling_window_minutes: int = 10


class RationalizationRequest(BaseModel):
    asset_ids: Optional[List[str]] = None
    time_range: TimeRange
    recurrence_threshold: int = 5


class PriorityRequest(BaseModel):
    alarm_id: str


class RecommendationRequest(BaseModel):
    alarm_id: str
    include_related: bool = True
    include_asset_context: bool = True
    include_historical_pattern: bool = True


class CalculationGenerateRequest(BaseModel):
    calculation_type: str
    filters: Dict[str, Any]


class CalculationExecuteRequest(BaseModel):
    calculation_id: str
    filters: Dict[str, Any]


def _find_asset(asset_id: str) -> Dict[str, Any]:
    for asset in ASSETS:
        if asset["asset_id"] == asset_id:
            return asset
    raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")


def _find_alarm(alarm_id: str) -> Dict[str, Any]:
    for alarm in ALARMS:
        if alarm["alarm_id"] == alarm_id:
            return alarm
    raise HTTPException(status_code=404, detail=f"Alarm '{alarm_id}' not found")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "alarm-api"}


@app.get("/assets/search")
def search_assets(
    query: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    site: Optional[str] = None,
    unit: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
):
    _check_auth(authorization)
    q = query.lower().strip()

    def _match(asset: Dict[str, Any]) -> bool:
        if q and q not in asset["name"].lower() and q not in asset["asset_type"].lower():
            return False
        if site and asset["site"] != site:
            return False
        if unit and asset["unit"] != unit:
            return False
        return True

    results = [a for a in ASSETS if _match(a)]
    return {"results": results[:limit], "total": len(results)}


@app.get("/assets/{asset_id}/metadata")
def asset_metadata(asset_id: str, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    asset = _find_asset(asset_id)
    open_alarm_count = sum(1 for a in ALARMS if a["asset_id"] == asset_id and a["status"] != "closed")
    return {
        **asset,
        "open_alarm_count": open_alarm_count,
        "last_maintenance": "2026-07-10",
        "next_maintenance": "2026-10-10",
    }


@app.get("/alarms")
def list_alarms(
    asset_id: Optional[str] = None,
    site: Optional[str] = None,
    unit: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = "start_time",
    sort_order: str = "desc",
    authorization: Optional[str] = Header(default=None),
):
    _check_auth(authorization)
    data = ALARMS[:]

    if asset_id:
        data = [a for a in data if a["asset_id"] == asset_id]
    if site:
        data = [a for a in data if a["site"] == site]
    if unit:
        data = [a for a in data if a["unit"] == unit]
    if status:
        data = [a for a in data if a["status"] == status]
    if severity:
        data = [a for a in data if a["severity"] == severity]

    reverse = sort_order.lower() == "desc"
    if sort_by in {"start_time", "severity", "alarm_name"}:
        data.sort(key=lambda item: item.get(sort_by) or "", reverse=reverse)

    total = len(data)
    start = (page - 1) * page_size
    end = start + page_size
    paged = data[start:end]

    return {
        "data": paged,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
        },
    }


@app.get("/alarms/{alarm_id}")
def alarm_detail(alarm_id: str, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    alarm = _find_alarm(alarm_id)
    asset = _find_asset(alarm["asset_id"])
    return {**alarm, "asset": asset}


@app.post("/alarms/summary")
def alarm_summary(req: SummaryRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    data = ALARMS[:]
    if req.asset_ids:
        data = [a for a in data if a["asset_id"] in req.asset_ids]
    if req.severity:
        data = [a for a in data if a["severity"] in req.severity]

    by_name = Counter(a["alarm_name"] for a in data)
    rows = [{"alarm_name": name, "alarm_count": count} for name, count in by_name.items()]
    return {
        "summary": rows,
        "kpis": {
            "alarm_count": len(data),
            "recurring_rate": round(min(1.0, len(data) / 10.0), 2),
            "avg_ack_delay_minutes": 6.5,
        },
        "time_range": req.time_range.model_dump(),
    }


@app.post("/alarms/trends")
def alarm_trends(req: TrendRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    start = datetime.fromisoformat(req.time_range.start_time.replace("Z", "+00:00"))
    buckets = []
    for idx in range(7):
        ts = start + timedelta(days=idx)
        buckets.append(
            {
                "bucket_start": ts.isoformat().replace("+00:00", "Z"),
                "alarm_count": max(1, 8 - idx),
                "critical_count": max(0, 3 - idx // 2),
            }
        )
    return {"bucket": req.bucket, "series": buckets, "metrics": req.metrics}


@app.post("/alarms/correlation")
def correlate_alarms(req: CorrelationRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    related = [a for a in ALARMS if a["asset_id"] in req.asset_ids]
    pairs = []
    for i in range(len(related)):
        for j in range(i + 1, len(related)):
            pairs.append(
                {
                    "source_alarm": related[i]["alarm_id"],
                    "target_alarm": related[j]["alarm_id"],
                    "score": 0.82,
                    "method": req.correlation_method,
                }
            )
    return {"correlations": pairs[:10], "count": len(pairs)}


@app.post("/alarms/flood-analysis")
def flood_analysis(req: FloodRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    window_count = len([a for a in ALARMS if a["unit"] == req.unit])
    is_flood = window_count >= req.threshold_count
    return {
        "unit": req.unit,
        "window_count": window_count,
        "threshold": req.threshold_count,
        "is_flood": is_flood,
        "analysis_time": _iso_now(),
    }


@app.post("/alarms/rationalization-candidates")
def rationalization_candidates(req: RationalizationRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    candidates = []
    for alarm in ALARMS:
        if req.asset_ids and alarm["asset_id"] not in req.asset_ids:
            continue
        candidates.append(
            {
                "alarm_id": alarm["alarm_id"],
                "alarm_name": alarm["alarm_name"],
                "recurrence": 6,
                "candidate_type": "nuisance",
            }
        )
    return {"candidates": candidates, "threshold": req.recurrence_threshold}


@app.post("/alarms/priority-score")
def priority_score(req: PriorityRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    alarm = _find_alarm(req.alarm_id)
    severity_weight = {"low": 0.2, "medium": 0.45, "high": 0.72, "critical": 0.92}
    score = severity_weight.get(alarm["severity"], 0.5)
    label = "critical" if score >= 0.85 else "high" if score >= 0.7 else "medium"
    return {
        "alarm_id": req.alarm_id,
        "priority_score": round(score, 2),
        "priority_label": label,
        "drivers": ["severity", "asset criticality", "recurrence"],
    }


@app.post("/recommendations/operator-actions")
def operator_actions(req: RecommendationRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    alarm = _find_alarm(req.alarm_id)
    asset = _find_asset(alarm["asset_id"])
    actions = RECOMMENDATIONS.get(req.alarm_id, ["Escalate to shift engineer and review SOP."])
    return {
        "alarm_id": req.alarm_id,
        "asset_id": alarm["asset_id"],
        "recommended_actions": [{"step": idx + 1, "action": a} for idx, a in enumerate(actions)],
        "likely_causes": ["Instrument drift", "Flow restriction", "Cooling disturbance"],
        "asset_context": {
            "name": asset["name"],
            "criticality": asset["criticality"],
            "health_score": asset["health_score"],
        },
    }


@app.post("/calculation-code/generate")
def generate_calculation(req: CalculationGenerateRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    calc_id = f"CALC-{req.calculation_type.upper()}"
    return {
        "calculation_id": calc_id,
        "calculation_type": req.calculation_type,
        "generated_code": "result = alarm_count / hours",
        "filters": req.filters,
    }


@app.post("/calculation-code/execute")
def execute_calculation(req: CalculationExecuteRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    return {
        "calculation_id": req.calculation_id,
        "executed_at": _iso_now(),
        "result": {
            "value": 1.73,
            "unit": "events/hour",
        },
        "filters": req.filters,
    }
