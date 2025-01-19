from fastapi import FastAPI
from mangum import Mangum

from .routes import peeps, users

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "root!"}


app.include_router(peeps.router)
app.include_router(users.router)

handler = Mangum(app)
