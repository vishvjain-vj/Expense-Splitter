from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import groups, members, expenses, settlements
from app.models.database import create_tables

app = FastAPI(
    title="Expense Splitter API",
    description="Split bills among friends. Minimises settlement transactions using greedy algorithm.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    create_tables()

app.include_router(groups.router,      prefix="/groups",      tags=["Groups"])
app.include_router(members.router,     prefix="/groups",      tags=["Members"])
app.include_router(expenses.router,    prefix="/groups",      tags=["Expenses"])
app.include_router(settlements.router, prefix="/groups",      tags=["Settlements"])

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Expense Splitter API is running"}
