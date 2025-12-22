import json
from pathlib import Path
from typing import List, Dict, Any


class KnowledgeBaseManager:
    def __init__(self, base_dir: str = "knowledge_base"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def list_knowledge_bases(self) -> List[str]:
        return [f.name for f in self.base_dir.glob("*.json")]

    def load_knowledge_base(self, filename: str) -> Dict[str, Any]:
        filepath = self.base_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File {filename} not found")

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_knowledge_base(self, filename: str, data: Dict[str, Any]) -> None:
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = self.base_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def delete_knowledge_base(self, filename: str) -> None:
        filepath = self.base_dir / filename
        if filepath.exists():
            filepath.unlink()
        else:
            raise FileNotFoundError(f"Файл {filename} не найден")