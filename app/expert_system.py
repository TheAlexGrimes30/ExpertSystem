import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re


class ExpertSystem:
    def __init__(self):
        self.facts: Dict[str, float] = {}
        self.rules: List[Dict] = []

    def add_fact(self, fact: str, cf: float):
        """Добавить факт с коэффициентом уверенности"""
        if not 0 <= cf <= 1:
            raise ValueError("Коэффициент уверенности должен быть от 0 до 1")
        self.facts[fact] = cf

    def delete_fact(self, fact: str):
        """Удалить факт"""
        if fact in self.facts:
            del self.facts[fact]

    def parse_conditions_string(self, conditions_str: str) -> List[Dict]:
        """Парсинг строки условий в структурированный формат"""
        conditions_str = conditions_str.strip()
        if not conditions_str:
            return []

        # Нормализуем строку
        conditions_str = conditions_str.replace('(', ' ( ').replace(')', ' ) ')
        conditions_str = conditions_str.replace(',', ' , ')

        # Разбиваем на токены
        tokens = [t.strip() for t in conditions_str.split() if t.strip()]

        return self._parse_tokens(tokens)

    def _parse_tokens(self, tokens: List[str]) -> List[Dict]:
        """Рекурсивный парсинг токенов"""
        result = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            # Обработка оператора NOT
            if token.upper() == 'НЕТ':
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if next_token not in ['И', 'ИЛИ', '(', ')', ',']:
                        result.append({
                            "fact": next_token,
                            "operator": "NOT",
                            "is_group": False
                        })
                        i += 2
                    else:
                        result.append({
                            "fact": token,
                            "operator": "",
                            "is_group": False
                        })
                        i += 1
                else:
                    result.append({
                        "fact": token,
                        "operator": "",
                        "is_group": False
                    })
                    i += 1
                continue

            # Обработка оператора OR
            if token.upper() == 'ИЛИ':
                if result:
                    result[-1]["operator"] = "OR"
                i += 1
                continue

            # Обработка оператора AND
            if token.upper() == 'И':
                if result:
                    result[-1]["operator"] = "AND"
                i += 1
                continue

            # Обработка скобок
            if token == '(':
                depth = 1
                j = i + 1
                group_tokens = []

                while j < len(tokens) and depth > 0:
                    if tokens[j] == '(':
                        depth += 1
                    elif tokens[j] == ')':
                        depth -= 1

                    if depth > 0:
                        group_tokens.append(tokens[j])
                    j += 1

                # Парсим содержимое группы
                if group_tokens:
                    group_conditions = self._parse_tokens(group_tokens)

                    if len(group_conditions) > 1:
                        group_facts = []
                        for cond in group_conditions:
                            if not cond.get("is_group", False) and cond["fact"]:
                                group_facts.append(cond["fact"])

                        if group_facts:
                            result.append({
                                "fact": group_facts,
                                "operator": "",
                                "is_group": True
                            })
                        else:
                            for cond in group_conditions:
                                result.append(cond)
                    else:
                        for cond in group_conditions:
                            cond["is_group"] = True
                            result.append(cond)

                i = j
                continue

            # Обработка запятой (неявный AND)
            if token == ',':
                if result and result[-1].get("operator", "") == "":
                    result[-1]["operator"] = "AND"
                i += 1
                continue

            # Обычный факт
            if token not in [')']:
                if i > 0 and tokens[i - 1] == ',' and result:
                    result[-1]["operator"] = "AND"

                result.append({
                    "fact": token,
                    "operator": "",
                    "is_group": False
                })

            i += 1

        # Устанавливаем AND по умолчанию
        for i in range(len(result) - 1):
            if result[i].get("operator", "") == "":
                result[i]["operator"] = "AND"

        return result

    def add_rule(self, conditions, conclusion: str, cf: float):
        """Добавить правило"""
        if not 0 <= cf <= 1:
            raise ValueError("Коэффициент уверенности должен быть от 0 до 1")

        if isinstance(conditions, str):
            # Если передали строку - парсим как обычно
            conditions = self.parse_conditions_string(conditions)
        elif isinstance(conditions, list):
            # ИСПРАВЛЕНИЕ ДЛЯ JSON: ["A", "B"] → A И B
            parsed_conditions = []
            for i, condition in enumerate(conditions):
                if isinstance(condition, str):
                    parsed_conditions.append({
                        "fact": condition,
                        "operator": "AND" if i < len(conditions) - 1 else "",
                        "is_group": False
                    })
                elif isinstance(condition, dict):
                    parsed_conditions.append(condition)
            conditions = parsed_conditions

        self.rules.append({
            "if": conditions,
            "then": conclusion,
            "cf": cf
        })

    def delete_rule(self, index: int):
        """Удалить правило по индексу"""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)

    def _get_fact_cf(self, fact_name: str, operator: str = "") -> float:
        """Получить CF для факта с учетом оператора NOT"""
        cf = self.facts.get(fact_name, 0.0)
        if operator == "NOT":
            return 1.0 - cf
        return cf

    def _evaluate_single_condition(self, condition: Dict) -> float:
        """Оценить одно условие"""
        fact = condition.get("fact", "")
        operator = condition.get("operator", "").upper()
        is_group = condition.get("is_group", False)

        if is_group and isinstance(fact, list):
            cfs = [self._get_fact_cf(f, operator) for f in fact]
            return min(cfs) if cfs else 0.0
        else:
            return self._get_fact_cf(fact, operator)

    def _evaluate_conditions(self, conditions: List[Dict]) -> float:
        """Оценить все условия правила с правильной логикой AND/OR"""
        if not conditions:
            return 0.0

        if len(conditions) == 1:
            return self._evaluate_single_condition(conditions[0])

        result = None
        current_operator = "AND"

        for i, condition in enumerate(conditions):
            condition_cf = self._evaluate_single_condition(condition)
            operator = condition.get("operator", "").upper()

            if i == len(conditions) - 1:
                operator = ""

            if result is None:
                result = condition_cf
                current_operator = operator if operator else "AND"
            else:
                if current_operator == "AND":
                    result = min(result, condition_cf)
                elif current_operator == "OR":
                    result = max(result, condition_cf)
                else:
                    result = min(result, condition_cf)

                current_operator = operator if operator else "AND"

        return result if result is not None else 0.0

    def infer(self) -> Dict[str, float]:
        """Выполнить логический вывод по методу Шортлиффа"""
        new_inferences = True
        inferred = {}

        while new_inferences:
            new_inferences = False

            for rule in self.rules:
                conditions = rule["if"]
                conclusion = rule["then"]
                rule_cf = rule["cf"]

                try:
                    condition_cf = self._evaluate_conditions(conditions)

                    if condition_cf > 0:
                        result_cf = condition_cf * rule_cf

                        if conclusion not in self.facts or result_cf > self.facts[conclusion]:
                            self.facts[conclusion] = result_cf
                            inferred[conclusion] = result_cf
                            new_inferences = True
                except Exception as e:
                    continue

        return inferred

    def query(self, symptoms_input: str) -> Dict:
        """Выполнить анализ на основе введенных данных"""
        # Парсим входные данные
        parsed_conditions = self.parse_conditions_string(symptoms_input)

        if not parsed_conditions:
            return {
                "success": False,
                "error": "Введите корректные данные"
            }

        result = {
            "success": True,
            "query": symptoms_input,
            "parsed_conditions": parsed_conditions,
            "conclusions": [],
            "matched_items": [],
            "partial_matches": None
        }

        # Сопоставляем факты с базой знаний
        matched_items = []
        all_fact_names = list(self.facts.keys())

        for condition in parsed_conditions:
            fact_name = condition.get("fact", "")
            operator = condition.get("operator", "").upper()

            if isinstance(fact_name, list):
                for fact in fact_name:
                    self._match_fact(fact, operator, matched_items, all_fact_names)
            else:
                self._match_fact(fact_name, operator, matched_items, all_fact_names)

        result["matched_items"] = matched_items

        # Ключевое исправление: проверяем правила с учетом структуры запроса
        possible_conclusions = {}

        for rule in self.rules:
            # НОВАЯ ЛОГИКА: проверяем полное соответствие структуры
            if self._check_rule_structure_match(rule, parsed_conditions, matched_items):
                conclusion_name = rule["then"]
                rule_cf = rule["cf"]

                # Рассчитываем CF условий
                condition_cf = self._calculate_rule_cf(rule, matched_items)

                if condition_cf > 0:
                    conclusion_cf = condition_cf * rule_cf

                    if conclusion_name not in possible_conclusions or conclusion_cf > \
                            possible_conclusions[conclusion_name]["cf"]:
                        calculation_info = self._format_calculation(rule, matched_items, rule_cf, conclusion_cf)

                        possible_conclusions[conclusion_name] = {
                            "name": conclusion_name,
                            "cf": conclusion_cf,
                            "rule_cf": rule_cf,
                            "conditions": self._format_conditions(rule["if"]),
                            "calculation": calculation_info,
                            "min_condition_cf": condition_cf,
                            "confidence": self._get_confidence_level(conclusion_cf)
                        }

        # Добавляем выводы в результат
        for conclusion_data in possible_conclusions.values():
            result["conclusions"].append(conclusion_data)

        result["conclusions"].sort(key=lambda x: x["cf"], reverse=True)

        # Если нет точных выводов, ищем частичные совпадения
        if not result["conclusions"]:
            partial_rules = self._find_partial_matches(matched_items, parsed_conditions)
            if partial_rules:
                result["partial_matches"] = {
                    "message": "Точных выводов не найдено, но есть близкие правила",
                    "partial_rules": partial_rules
                }

        return result

    def _check_rule_structure_match(self, rule: Dict, query_conditions: List[Dict], matched_items: List[Dict]) -> bool:
        """Проверить полное соответствие структуры правила и запроса"""
        rule_conditions = rule["if"]

        # Если разное количество условий - не подходит
        if len(rule_conditions) != len(query_conditions):
            return False

        # Проверяем каждое условие
        for rule_cond, query_cond in zip(rule_conditions, query_conditions):
            # Проверяем факты
            rule_fact = rule_cond.get("fact", "")
            query_fact = query_cond.get("fact", "")

            if isinstance(rule_fact, list) and isinstance(query_fact, list):
                if set(rule_fact) != set(query_fact):
                    return False
            elif isinstance(rule_fact, list) or isinstance(query_fact, list):
                return False
            else:
                if rule_fact != query_fact:
                    return False

            # Проверяем операторы (ключевое исправление!)
            rule_operator = rule_cond.get("operator", "").upper()
            query_operator = query_cond.get("operator", "").upper()

            # Пустой оператор и "AND" считаем эквивалентными
            rule_op = "AND" if rule_operator in ["", "AND"] else rule_operator
            query_op = "AND" if query_operator in ["", "AND"] else query_operator

            if rule_op != query_op:
                return False

        # Дополнительно проверяем, что все факты из правила есть в matched_items
        for condition in rule_conditions:
            fact_name = condition.get("fact", "")
            operator = condition.get("operator", "").upper()

            if isinstance(fact_name, list):
                for fact in fact_name:
                    if not self._fact_in_matched(fact, operator, matched_items):
                        return False
            else:
                if not self._fact_in_matched(fact_name, operator, matched_items):
                    return False

        return True

    def _match_fact(self, fact_name: str, operator: str, matched_items: List[Dict], all_fact_names: List[str]) -> None:
        """Сопоставить факт с базой знаний"""
        matched = False

        # Нормализуем входной факт для поиска
        input_normalized = ' '.join(fact_name.lower().replace('_', ' ').split())

        for stored_fact in all_fact_names:
            # Нормализуем сохраненный факт
            stored_normalized = ' '.join(stored_fact.lower().replace('_', ' ').split())

            # Проверяем точное совпадение после нормализации
            if input_normalized == stored_normalized:
                cf = self.facts[stored_fact]
                if operator == "NOT":
                    cf = 1.0 - cf

                matched_items.append({
                    "input": fact_name,
                    "matched_fact": stored_fact,
                    "cf": cf,
                    "operator": operator
                })
                matched = True
                break

        if not matched:
            matched_items.append({
                "input": fact_name,
                "matched_fact": None,
                "cf": 0.0,
                "operator": operator
            })

    def _facts_match(self, input_fact: str, stored_fact: str) -> bool:
        """Проверить, соответствует ли входной факт сохраненному факту"""
        # Нормализуем оба факта: заменяем подчеркивания на пробелы, приводим к нижнему регистру
        input_normalized = ' '.join(input_fact.lower().replace('_', ' ').split())
        stored_normalized = ' '.join(stored_fact.lower().replace('_', ' ').split())

        # Проверяем точное совпадение после нормализации
        return input_normalized == stored_normalized

    def _fact_in_matched(self, fact_name: str, operator: str, matched_items: List[Dict]) -> bool:
        """Проверить, есть ли факт в сопоставленных элементах"""
        # Нормализуем факт для сравнения
        fact_normalized = ' '.join(fact_name.lower().replace('_', ' ').split())

        for item in matched_items:
            item_fact = item["matched_fact"]
            if item_fact is None:
                continue

            # Нормализуем факт из matched_items
            item_fact_normalized = ' '.join(item_fact.lower().replace('_', ' ').split())

            if item_fact_normalized == fact_normalized:
                if operator == "NOT":
                    return item["cf"] > 0
                else:
                    return item["cf"] > 0
        return False

    def _calculate_rule_cf(self, rule: Dict, matched_items: List[Dict]) -> float:
        """Рассчитать CF для правил на основе сопоставленных фактов"""
        condition_cfs = []

        for condition in rule["if"]:
            fact_name = condition.get("fact", "")
            operator = condition.get("operator", "").upper()
            is_group = condition.get("is_group", False)

            if is_group and isinstance(fact_name, list):
                group_cfs = []
                for fact in fact_name:
                    cf = self._get_matched_cf(fact, operator, matched_items)
                    if cf > 0:
                        group_cfs.append(cf)
                if group_cfs:
                    condition_cfs.append(min(group_cfs))
                else:
                    condition_cfs.append(0.0)
            else:
                cf = self._get_matched_cf(fact_name, operator, matched_items)
                condition_cfs.append(cf)

        if not condition_cfs:
            return 0.0

        result = condition_cfs[0]

        for i in range(1, len(condition_cfs)):
            operator = rule["if"][i - 1].get("operator", "").upper()
            next_cf = condition_cfs[i]

            if operator == "AND":
                result = min(result, next_cf)
            elif operator == "OR":
                result = max(result, next_cf)
            else:
                result = min(result, next_cf)

        return result

    def _get_matched_cf(self, fact_name: str, operator: str, matched_items: List[Dict]) -> float:
        """Получить CF из сопоставленных элементов"""
        # Нормализуем факт для сравнения
        fact_normalized = ' '.join(fact_name.lower().replace('_', ' ').split())

        for item in matched_items:
            if item["matched_fact"] is None:
                continue

            # Нормализуем факт из matched_items
            item_fact_normalized = ' '.join(item["matched_fact"].lower().replace('_', ' ').split())

            if item_fact_normalized == fact_normalized:
                cf = item["cf"]
                return cf
        return 0.0

    def _format_conditions(self, conditions: List[Dict]) -> List[str]:
        """Форматировать условия для отображения"""
        formatted = []

        for condition in conditions:
            fact = condition.get("fact", "")
            operator = condition.get("operator", "").upper()
            is_group = condition.get("is_group", False)

            if is_group and isinstance(fact, list):
                text = f"({', '.join(fact)})"
            else:
                text = fact

            if operator == "NOT":
                text = f"НЕТ {text}"

            formatted.append(text)

            if operator in ["AND", "OR"]:
                formatted.append(operator.lower())

        return formatted

    def _format_calculation(self, rule: Dict, matched_items: List[Dict], rule_cf: float, conclusion_cf: float) -> str:
        """Форматировать строку расчета"""
        parts = []

        for i, condition in enumerate(rule["if"]):
            fact = condition.get("fact", "")
            operator = condition.get("operator", "").upper()
            is_group = condition.get("is_group", False)

            if is_group and isinstance(fact, list):
                group_parts = []
                for f in fact:
                    cf = self._get_matched_cf(f, operator, matched_items)
                    group_parts.append(f"{cf:.2f}")

                if group_parts:
                    parts.append(f"min({', '.join(group_parts)})")
            else:
                cf = self._get_matched_cf(fact, operator, matched_items)
                parts.append(f"{cf:.2f}")

            if operator in ["AND", "OR"] and i < len(rule["if"]) - 1:
                parts.append(operator.lower())

        if len(parts) == 1:
            expression = parts[0]
        else:
            expression = " ".join(parts)

        return f"{expression} × {rule_cf:.2f} = {conclusion_cf:.4f}"

    def _find_partial_matches(self, matched_items: List[Dict], query_conditions: List[Dict]) -> List[Dict]:
        """Найти частичные совпадения с правилами"""
        partial_rules = []

        for rule in self.rules:
            matched_count = 0
            total_conditions = 0
            missing = []

            # Проверяем только факты, игнорируя операторы для частичных совпадений
            for condition in rule["if"]:
                fact = condition.get("fact", "")
                operator = condition.get("operator", "").upper()
                is_group = condition.get("is_group", False)

                if is_group and isinstance(fact, list):
                    for f in fact:
                        total_conditions += 1
                        if self._fact_in_matched(f, operator, matched_items):
                            matched_count += 1
                        else:
                            missing.append(f)
                else:
                    total_conditions += 1
                    if self._fact_in_matched(fact, operator, matched_items):
                        matched_count += 1
                    else:
                        missing.append(fact)

            if matched_count > 0 and matched_count < total_conditions:
                partial_rules.append({
                    "conclusion": rule["then"],
                    "matched": matched_count,
                    "total": total_conditions,
                    "missing": missing
                })

        return partial_rules

    def _get_confidence_level(self, cf: float) -> str:
        """Определить уровень уверенности на основе CF"""
        if cf >= 0.8:
            return "очень высокая"
        elif cf >= 0.6:
            return "высокая"
        elif cf >= 0.4:
            return "средняя"
        elif cf >= 0.2:
            return "низкая"
        else:
            return "очень низкая"

    def load_from_dict(self, data: dict):
        """Загрузить состояние системы из словаря"""
        self.facts = data.get("facts", {})
        self.rules = []

        # Преобразуем правила из формата JSON
        for rule in data.get("rules", []):
            self.add_rule(rule["if"], rule["then"], rule["cf"])

    def to_dict(self):
        """Преобразовать состояние системы в словарь"""
        return {
            "facts": self.facts,
            "rules": self.rules
        }