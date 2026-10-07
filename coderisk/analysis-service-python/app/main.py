from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.analyze_api import router as analyze_router
from app.api.health_api import router as health_router
from app.api.problem_api import router as problem_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="CodeRisk Analysis Service",
        version="0.1.0",
        description="Internal FastAPI service for PICAS analysis pipelines.",
    )
    app.include_router(health_router)
    app.include_router(analyze_router)
    app.include_router(problem_router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "errorCode": "ANALYSIS_REQUEST_INVALID",
                "message": str(exc.detail),
                "analysisVersion": "0.1.0",
                "configVersion": "dev",
                "result": None,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "errorCode": "ANALYSIS_SERVICE_ERROR",
                "message": str(exc),
                "analysisVersion": "0.1.0",
                "configVersion": "dev",
                "result": None,
            },
        )

    return app


app = create_app()
