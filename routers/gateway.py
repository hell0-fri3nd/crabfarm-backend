from fastapi import APIRouter, Request, Response
from services import JWTManager
import httpx



Gateway = APIRouter(prefix="/api/v1/gateway", tags=["API Gateway"])
jwt_manager = JWTManager()
SERVICES = {
    "raspberry": "http://192.168.1.19:4573",
}


@Gateway.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@jwt_manager.requires_access
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        return {"error": "Service not found"}

    url = SERVICES[service] + (f"/{path}" if path else "")

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=await request.body(),
            params=request.query_params,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type"),
    )