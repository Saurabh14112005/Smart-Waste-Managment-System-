from pydantic import BaseModel, Field
from typing import List, Optional


class BinTelemetry(BaseModel):
    id: int
    location: str
    lat: float
    lon: float
    fill_level: int
    gas_level: float
    temperature: float
    battery: float
    status: str


class AIResponse(BaseModel):
    label: str
    confidence: float
    guidance: str
    inference_time: int


class RouteMetrics(BaseModel):
    total_distance: str
    total_time: str
    bins_collected: int
    fuel_saved: str
    co2_saved: str


class RouteResponse(BaseModel):
    route: List[dict]
    metrics: RouteMetrics


class HealthStatus(BaseModel):
    api_status: str
    ai_engine: str
    database: str
    uptime: str
    version: str


class IoTUpdateRequest(BaseModel):
    bin_id: int
    fill_level: int
    gas_level: float
    temperature: float
    humidity: Optional[float] = None
    battery: float
    mode: str = "Real"
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone: Optional[str] = None
    tenant_id: Optional[str] = Field(default=None, description="Defaults to server DEFAULT_TENANT_ID")


class BinCreate(BaseModel):
    """Register a bin that hardware or dashboard will address by id."""

    id: int
    location: str
    lat: float
    lon: float
    zone: str = "UNKNOWN"
    waste_type: str = "Mixed"
    fill_level: int = 0
    gas_level: float = 0.0
    temp: float = 25.0
    battery: int = 100
    moisture: int = 0
    status: str = "NORMAL"
    tenant_id: str = "default"


class BinBulkRequest(BaseModel):
    bins: List[BinCreate] = Field(..., max_length=2000)
