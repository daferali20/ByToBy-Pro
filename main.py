# main.py
from fastapi import FastAPI
from api.endpoints import company, portfolio
from utils.logger import get_logger

logger = get_logger("Main")

app = FastAPI(
    title="ByToBy Pro",
    description="Stock Market Analysis Platform",
    version="1.0.0"
)

# Register routers
app.include_router(company.router)
app.include_router(portfolio.router)

@app.get("/")
async def root():
    return {"message": "ByToBy Pro API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
