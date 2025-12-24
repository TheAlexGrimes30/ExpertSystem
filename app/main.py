import os
from pathlib import Path
from typing import Dict, List
import json
import urllib.parse

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.expert_system import ExpertSystem

app = FastAPI(
    title="Универсальная экспертная система",
    description="Система логического вывода на основе метода Шортлиффа",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent

static_dir = BASE_DIR / "static"
css_dir = static_dir / "css"
js_dir = static_dir / "js"
templates_dir = BASE_DIR / "templates"
knowledge_base_dir = BASE_DIR / "knowledge_base"

for directory in [css_dir, js_dir, templates_dir, knowledge_base_dir]:
    directory.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))
expert_system = ExpertSystem()


class FactData(BaseModel):
    """
    Модель данных для представления факта в экспертной системе.

    Attributes:
        fact (str): Факт в виде строки
        cf (float): Коэффициент уверенности (confidence factor) в диапазоне от 0.0 до 1.0
    """

    fact: str
    cf: float


class RuleData(BaseModel):
    """
    Модель данных для представления правила в экспертной системе.

    Attributes:
        conditions (str): Условия правила в виде строки
        conclusion (str): Заключение правила в виде строки
        cf (float): Коэффициент уверенности правила, по умолчанию 0.5
    """

    conditions: str
    conclusion: str
    cf: float = 0.5


class QueryData(BaseModel):
    """
    Модель данных для представления запроса к экспертной системе.

    Attributes:
        query (str): Запрос в виде строки для анализа
    """

    query: str


def list_knowledge_bases() -> List[str]:
    """
    Получить список файлов баз знаний из директории knowledge_base.

    Returns:
        List[str]: Отсортированный список имен файлов с расширением .json
    """

    files = []
    for file in knowledge_base_dir.iterdir():
        if file.is_file() and file.suffix == '.json':
            files.append(file.name)
    return sorted(files)


def load_knowledge_base(filename: str) -> Dict:
    """
    Загрузить базу знаний из JSON файла.

    Args:
        filename (str): Имя файла базы знаний

    Returns:
        Dict: Словарь с данными базы знаний
    """

    filepath = knowledge_base_dir / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_knowledge_base(filename: str, data: Dict) -> None:
    """
    Сохранить базу знаний в JSON файл.

    Args:
        filename (str): Имя файла для сохранения
        data (Dict): Данные базы знаний для сохранения
    """

    if not filename.endswith('.json'):
        filename += '.json'

    filepath = knowledge_base_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def delete_knowledge_base(filename: str) -> None:
    """
    Удалить файл базы знаний.

    Args:
        filename (str): Имя файла для удаления

    Raises:
        HTTPException: Если файл не найден (статус 404)
    """

    filepath = knowledge_base_dir / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    filepath.unlink()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Обработчик GET запроса для главной страницы приложения.

    Args:
        request (Request): Объект запроса FastAPI

    Returns:
        TemplateResponse: HTML страница index.html
    """

    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/knowledge-bases")
async def get_knowledge_bases():
    """
    API endpoint для получения списка доступных баз знаний.

    Returns:
        JSONResponse: Объект с флагом успеха и списком файлов
    """

    try:
        files = list_knowledge_bases()
        return JSONResponse(content={"success": True, "files": files})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-base/{filename}")
async def load_knowledge_base_endpoint(filename: str):
    """
    API endpoint для загрузки базы знаний из файла в экспертную систему.

    Args:
        filename (str): Имя файла базы знаний

    Returns:
        JSONResponse: Объект с данными базы знаний и текущим состоянием системы
    """

    try:
        data = load_knowledge_base(filename)
        expert_system.load_from_dict(data)
        return JSONResponse(content={
            "success": True,
            "facts": expert_system.facts,
            "rules": expert_system.rules,
            "filename": filename
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/knowledge-base/{filename}")
async def save_knowledge_base_endpoint(filename: str):
    """
    API endpoint для сохранения текущей базы знаний в файл.

    Args:
        filename (str): Имя файла для сохранения

    Returns:
        JSONResponse: Объект с флагом успеха операции
    """

    try:
        data = expert_system.to_dict()
        save_knowledge_base(filename, data)
        return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/knowledge-base/{filename}")
async def delete_knowledge_base_endpoint(filename: str):
    """
    API endpoint для удаления файла базы знаний.

    Args:
        filename (str): Имя файла для удаления

    Returns:
        JSONResponse: Объект с флагом успеха операции
    """

    try:
        delete_knowledge_base(filename)
        return JSONResponse(content={"success": True})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/fact")
async def add_fact(fact_data: FactData):
    """
    API endpoint для добавления нового факта в экспертную систему.

    Args:
        fact_data (FactData): Данные факта (текст и коэффициент уверенности)

    Returns:
        JSONResponse: Объект с флагом успеха и обновленным списком фактов
    """

    try:
        expert_system.add_fact(fact_data.fact, fact_data.cf)
        return JSONResponse(content={
            "success": True,
            "facts": expert_system.facts
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/fact/{fact:path}")
async def delete_fact(fact: str):
    """
    API endpoint для удаления факта из экспертной системы.

    Args:
        fact (str): URL-кодированный текст факта для удаления

    Returns:
        JSONResponse: Объект с флагом успеха и обновленным списком фактов
    """

    try:
        decoded_fact = urllib.parse.unquote(fact)
        expert_system.delete_fact(decoded_fact)
        return JSONResponse(content={
            "success": True,
            "facts": expert_system.facts
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/rule")
async def add_rule(rule_data: RuleData):
    """
    API endpoint для добавления нового правила в экспертную систему.

    Args:
        rule_data (RuleData): Данные правила (условия, заключение и коэффициент уверенности)

    Returns:
        JSONResponse: Объект с флагом успеха и обновленным списком правил
    """

    try:
        if not rule_data.conditions.strip():
            raise HTTPException(status_code=400, detail="Условия не могут быть пустыми")

        if not rule_data.conclusion.strip():
            raise HTTPException(status_code=400, detail="Заключение не может быть пустым")

        expert_system.add_rule(rule_data.conditions, rule_data.conclusion, rule_data.cf)

        return JSONResponse(content={
            "success": True,
            "rules": expert_system.rules
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/rule/{index}")
async def delete_rule(index: int):
    """
    API endpoint для удаления правила по индексу.

    Args:
        index (int): Индекс правила в списке правил

    Returns:
        JSONResponse: Объект с флагом успеха и обновленным списком правил
    """

    try:
        expert_system.delete_rule(index)
        return JSONResponse(content={
            "success": True,
            "rules": expert_system.rules
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/infer")
async def make_inference():
    """
    API endpoint для выполнения логического вывода в экспертной системе.

    Returns:
        JSONResponse: Объект с результатами вывода и текущим состоянием фактов
    """

    try:
        inferred = expert_system.infer()
        return JSONResponse(content={
            "success": True,
            "inferred": inferred,
            "all_facts": expert_system.facts
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/query")
async def make_query(query_data: QueryData):
    """
    API endpoint для выполнения анализа на основе введенных данных.

    Args:
        query_data (QueryData): Данные запроса для анализа

    Returns:
        JSONResponse: Объект с результатом анализа или сообщением об ошибке
    """

    try:
        query = query_data.query.strip()

        if not query:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Введите данные для анализа"
                }
            )

        result = expert_system.query(query)

        if "success" in result and not result["success"]:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result.get("error", "Ошибка при выполнении запроса")
                }
            )

        return JSONResponse(content={
            "success": True,
            "result": result
        })
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.get("/api/current-state")
async def get_current_state():
    """
    API endpoint для получения текущего состояния экспертной системы.

    Returns:
        JSONResponse: Объект с текущими фактами и правилами системы
    """

    return JSONResponse(content={
        "success": True,
        "facts": expert_system.facts,
        "rules": expert_system.rules
    })


@app.post("/api/clear-all")
async def clear_all():
    """
    API endpoint для очистки всех данных экспертной системы.

    Returns:
        JSONResponse: Объект с флагом успеха и сообщением
    """

    try:
        expert_system.facts = {}
        expert_system.rules = []
        return JSONResponse(content={
            "success": True,
            "message": "Все данные очищены"
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    """
    Точка входа для запуска FastAPI приложения.
    """

    port = int(os.getenv("PORT", 8000))

    print(f"Сервер запущен: http://localhost:{port}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )