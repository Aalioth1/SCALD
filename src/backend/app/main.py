from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.bultos import router as bultos_router
from app.api.v1.hojas_ruta import router as hojas_ruta_router
from app.api.v1.pistoleo import router as pistoleo_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models.bulto import Bulto
from app.models.hoja_ruta import HojaRuta
from app.models.incidencia import Incidencia
from app.models.pistoleo import Pistoleo
from app.models.rol import Rol
from app.models.usuario import Usuario

settings = get_settings()
app = FastAPI(title="SCALD API", version="0.1.0", description="Backend para gestión y auditoría logística de despachos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.allowed_origins == "*" else settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(hojas_ruta_router)
app.include_router(bultos_router)
app.include_router(pistoleo_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}
