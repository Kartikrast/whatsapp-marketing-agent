import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from routes.webhook import route
from routes.send_templates import route as send_template_route
from routes.send_customs import route as send_custom_route

load_dotenv(override=True)

# Make ai-agent importable from the sibling folder
from agent.agent import Agent 


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = Agent()
    yield


app = FastAPI(
    title="WhatsApp Marketing Agent",
    description="WhatsApp Marketing Agent",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(route.router)
app.include_router(send_template_route.router)
app.include_router(send_custom_route.router)

@app.get("/")
def read_root():
    return {"Welcome to the WhatsApp Marketing Agent"}