import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import KnowledgeBaseManager
from app.expert_system import ExpertSystem

app = FastAPI(
    title="Универсальная экспертная система",
    description="Система логического вывода на основе метода Шортлиффа",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Создаем необходимые директории
(BASE_DIR / "static/css").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "static/js").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "templates").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "knowledge_base").mkdir(parents=True, exist_ok=True)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Инициализируем компоненты системы
kb_manager = KnowledgeBaseManager(str(BASE_DIR / "knowledge_base"))
expert_system = ExpertSystem()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница приложения"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/knowledge-bases")
async def get_knowledge_bases():
    """Получить список доступных баз знаний"""
    try:
        files = kb_manager.list_knowledge_bases()
        return {"success": True, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-base/{filename}")
async def load_knowledge_base(filename: str):
    """Загрузить базу знаний из файла"""
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
    """Сохранить текущую базу знаний в файл"""
    try:
        kb_manager.save_knowledge_base(filename, data)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/knowledge-base/{filename}")
async def delete_knowledge_base(filename: str):
    """Удалить файл базы знаний"""
    try:
        kb_manager.delete_knowledge_base(filename)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/fact")
async def add_fact(fact_data: dict):
    """Добавить новый факт"""
    try:
        expert_system.add_fact(fact_data["fact"], fact_data["cf"])
        return {"success": True, "facts": expert_system.facts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/fact/{fact:path}")
async def delete_fact(fact: str):
    """Удалить факт"""
    try:
        import urllib.parse
        decoded_fact = urllib.parse.unquote(fact)
        expert_system.delete_fact(decoded_fact)
        return {"success": True, "facts": expert_system.facts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/rule")
async def add_rule(rule_data: dict):
    """Добавить новое правило"""
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
    """Удалить правило по индексу"""
    try:
        expert_system.delete_rule(index)
        return {"success": True, "rules": expert_system.rules}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/infer")
async def make_inference():
    """Выполнить логический вывод"""
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
    """Выполнить диагностику на основе симптомов"""
    try:
        symptoms = query_data.get("query", "").strip()

        if not symptoms:
            return {
                "success": False,
                "error": "Введите симптомы через запятую (например: кашель, температура, насморк)"
            }

        result = expert_system.query(symptoms)

        # Если query возвращает success=False (ошибка)
        if "success" in result and not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Ошибка при выполнении запроса")
            }

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
    """Получить текущее состояние системы (факты и правила)"""
    return {
        "success": True,
        "facts": expert_system.facts,
        "rules": expert_system.rules
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))

    print("=" * 60)
    print("УНИВЕРСАЛЬНАЯ ЭКСПЕРТНАЯ СИСТЕМА")
    print("=" * 60)
    print("Система логического вывода на основе метода Шортлиффа")
    print("=" * 60)
    print(f"Сервер запущен: http://localhost:{port}")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )