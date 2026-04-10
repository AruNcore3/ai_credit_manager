from fastapi import FastAPI
from fastapi import Request

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, World!"}

@app.post('/webhook')
def webhook(request: Request):
    return {"message": "Webhook received"}