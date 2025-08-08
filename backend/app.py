from fastapi import FastAPI

app = FastAPI(title="HCAdminAPI")

@app.get("/api/test")
async def test():
    return {"status": "ok"}

# For Vercel
handler = app