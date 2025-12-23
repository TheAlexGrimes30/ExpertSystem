import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.database import KnowledgeBaseManager
from app.expert_system import ExpertSystem

app = FastAPI(title="Экспертная система по методу Шортлиффа")

BASE_DIR = Path(__file__).resolve().parent.parent

(BASE_DIR / "static/css").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "static/js").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "templates").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "knowledge_base").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kb_manager = KnowledgeBaseManager(str(BASE_DIR / "knowledge_base"))
expert_system = ExpertSystem()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/knowledge-bases")
async def get_knowledge_bases():
    try:
        files = kb_manager.list_knowledge_bases()
        return {"success": True, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-base/{filename}")
async def load_knowledge_base(filename: str):
    try:
        data = kb_manager.load_knowledge_base(filename)
        expert_system.load_from_dict(data)
        return {
            "success": True,
            "facts": expert_system.facts,
            "rules": expert_system.rules,
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/knowledge-base/{filename}")
async def save_knowledge_base(filename: str, data: dict):
    try:
        kb_manager.save_knowledge_base(filename, data)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/knowledge-base/{filename}")
async def delete_knowledge_base(filename: str):
    try:
        kb_manager.delete_knowledge_base(filename)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/fact")
async def add_fact(fact_data: dict):
    try:
        expert_system.add_fact(fact_data["fact"], fact_data["cf"])
        return {"success": True, "facts": expert_system.facts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/fact/{fact:path}")
async def delete_fact(fact: str):
    try:
        import urllib.parse
        decoded_fact = urllib.parse.unquote(fact)
        expert_system.delete_fact(decoded_fact)
        return {"success": True, "facts": expert_system.facts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/rule")
async def add_rule(rule_data: dict):
    try:
        expert_system.add_rule(
            rule_data["conditions"],
            rule_data["conclusion"],
            rule_data["cf"]
        )
        return {"success": True, "rules": expert_system.rules}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/rule/{index}")
async def delete_rule(index: int):
    try:
        expert_system.delete_rule(index)
        return {"success": True, "rules": expert_system.rules}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/infer")
async def make_inference():
    try:
        inferred = expert_system.infer()
        return {
            "success": True,
            "inferred": inferred,
            "all_facts": expert_system.facts
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/query")
async def make_query(query_data: dict):
    try:
        query = query_data.get("query", "").strip()

        if not query:
            return {
                "success": False,
                "error": "Пустой запрос"
            }

        result = expert_system.query(query)

        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/current-state")
async def get_current_state():
    return {
        "success": True,
        "facts": expert_system.facts,
        "rules": expert_system.rules
    }


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "expert-system"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))

    print("=" * 50)
    print("Экспертная система по методу Шортлиффа")
    print("=" * 50)
    print(f"Сервер запускается на http://localhost:{port}")
    print(f"Для остановки сервера нажмите Ctrl+C")
    print("=" * 50)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )