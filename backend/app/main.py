import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("windscope")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Professional enterprise analytics API for UK day-ahead wind forecast evaluation against Elexon BMRS outturns.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "description": "UK Wind Forecast Intelligence platform analyzing Elexon BMRS FUELHH actuals vs WINDFOR forecasts.",
    }
