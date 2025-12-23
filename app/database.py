import json
import os
from pathlib import Path
from typing import List, Dict


class KnowledgeBaseManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def list_knowledge_bases(self) -> List[str]:
        """Получить список всех файлов баз знаний"""
        try:
            files = [f for f in os.listdir(self.base_dir) if f.endswith('.json')]
            return sorted(files)
        except Exception as e:
            print(f"Ошибка при получении списка файлов: {e}")
            return []

    def load_knowledge_base(self, filename: str) -> Dict:
        """Загрузить базу знаний из файла"""
        try:
            filepath = self.base_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Файл {filename} не найден")

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return data
        except Exception as e:
            raise Exception(f"Ошибка при загрузке файла {filename}: {str(e)}")

    def save_knowledge_base(self, filename: str, data: Dict):
        """Сохранить базу знаний в файл"""
        try:
            if not filename.endswith('.json'):
                filename += '.json'

            filepath = self.base_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"Ошибка при сохранении файла {filename}: {str(e)}")

    def delete_knowledge_base(self, filename: str):
        """Удалить файл базы знаний"""
        try:
            filepath = self.base_dir / filename
            if filepath.exists():
                filepath.unlink()
        except Exception as e:
            raise Exception(f"Ошибка при удалении файла {filename}: {str(e)}")