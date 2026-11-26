"""Pydantic request and response schemas for the OSINT IG HTTP API."""
from typing import Optional

from pydantic import BaseModel, Field


class BaseInvestigationRequest(BaseModel):
    target: Optional[str] = None
    verbose: bool = False
    max_items: Optional[int] = None
    cache_ttl_seconds: Optional[int] = None
    run_id: Optional[str] = None


class CancelRequest(BaseModel):
    run_id: str


class ToolCallRequest(BaseModel):
    name: str
    args: dict = Field(default_factory=dict)


class RunRequest(BaseInvestigationRequest):
    calls: list[ToolCallRequest]


class QueryResponse(BaseModel):
    target: Optional[str] = None
    target_id: Optional[int] = None
    backend: str
    api_calls_total: int
    answer: str = ""
    tool_calls: list


class SessionIdRequest(BaseModel):
    sessionid: str


class CredentialsRequest(BaseModel):
    username: str
    password: str


class GeminiConfigRequest(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None
    enabled: Optional[bool] = None


class GeminiVerifyRequest(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None


class GeminiAnalyzeRequest(BaseModel):
    target: Optional[str] = None
    results: list = Field(default_factory=list)
    analysis_type: str = "investigation_summary"
    question: Optional[str] = None


class DownloadRequest(BaseModel):
    urls: list
    name: str = "media"


class ReportExportRequest(BaseModel):
    run: dict
    format: str = "html"
