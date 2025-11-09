from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.files import router as files_router
from .api.kpi import router as kpi_router
from .api.vat import router as vat_router
from .api.quality import router as quality_router
from .api.recon import router as recon_router
from .api.chat import router as chat_router

app = FastAPI(title="Finance Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files_router)
app.include_router(kpi_router)
app.include_router(vat_router)
app.include_router(quality_router)
app.include_router(recon_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {"status": "ok"}
