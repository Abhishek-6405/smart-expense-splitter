from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import users, groups, expenses, balances, ai_parse

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Expense Splitter API",
    description="Splitwise-style expense splitting with AI features",
    version="1.0.0"
)

# CORS - allows React frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(groups.router, prefix="/api/groups", tags=["Groups"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["Expenses"])
app.include_router(balances.router, prefix="/api/groups", tags=["Balances"])
app.include_router(ai_parse.router, prefix="/api/ai", tags=["AI"])

@app.get("/")
def root():
    return {"message": "Smart Expense Splitter API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
