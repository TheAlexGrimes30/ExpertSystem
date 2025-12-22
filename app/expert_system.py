class ExpertSystem:
    def __init__(self):
        self.facts = {}
        self.rules = []

    def add_fact(self, fact: str, cf: float):
        if not 0 <= cf <= 1:
            raise ValueError("Коэффициент уверенности должен быть от 0 до 1")
        self.facts[fact] = cf

    def edit_fact(self, old_fact: str, new_fact: str, new_cf: float):
        if old_fact in self.facts:
            del self.facts[old_fact]
        self.facts[new_fact] = new_cf

    def delete_fact(self, fact: str):
        if fact in self.facts:
            del self.facts[fact]

    def add_rule(self, conditions: list, conclusion: str, cf: float):
        """Добавить правило с поддержкой операторов в условиях"""
        if not 0 <= cf <= 1:
            raise ValueError("Коэффициент уверенности должен быть от 0 до 1")

        structured_conditions = []

        for i, condition in enumerate(conditions):
            if isinstance(condition, dict):
                if "fact" not in condition:
                    raise ValueError("Условие должно содержать поле 'fact'")

                operator = condition.get("operator", "").upper()
                if operator and operator not in ["AND", "OR", "NOT", ""]:
                    raise ValueError(f"Неизвестный оператор: {operator}")

                structured_conditions.append({
                    "fact": condition["fact"],
                    "operator": operator
                })
            elif isinstance(condition, str):
                operator = "AND" if i < len(conditions) - 1 else ""
                structured_conditions.append({
                    "fact": condition.strip(),
                    "operator": operator
                })
            else:
                raise ValueError(f"Неверный формат условия: {condition}")

        self.rules.append({
            "if": structured_conditions,
            "then": conclusion,
            "cf": cf
        })

    def edit_rule(self, index: int, conditions: list, conclusion: str, cf: float):
        if 0 <= index < len(self.rules):
            self.add_rule(conditions, conclusion, cf)
            old_rule = self.rules.pop(index + 1)
            self.rules[index] = old_rule

    def delete_rule(self, index: int):
        if 0 <= index < len(self.rules):
            self.rules.pop(index)

    def _evaluate_condition(self, condition: dict) -> float:
        """Оценить одно условие"""
        fact = condition["fact"]
        operator = condition.get("operator", "").upper()

        fact_cf = self.facts.get(fact, 0)

        if operator == "NOT":
            return 1.0 - fact_cf

        return fact_cf

    def _evaluate_rule_conditions(self, conditions: list) -> float:
        """Оценить все условия правила с учетом операторов"""
        if not conditions:
            return 0.0

        result = None

        for i, condition in enumerate(conditions):
            condition_cf = self._evaluate_condition(condition)
            operator = condition.get("operator", "").upper()

            if result is None:
                result = condition_cf
            elif operator == "AND":
                result = min(result, condition_cf)
            elif operator == "OR":
                result = max(result, condition_cf)
            elif operator == "NOT":
                result = min(result, condition_cf)
            else:
                result = min(result, condition_cf)

        return result if result is not None else 0.0

    def infer(self):
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
                    condition_cf = self._evaluate_rule_conditions(conditions)

                    if condition_cf > 0:
                        result_cf = condition_cf * rule_cf

                        if conclusion not in self.facts or result_cf > self.facts[conclusion]:
                            self.facts[conclusion] = result_cf
                            inferred[conclusion] = result_cf
                            new_inferences = True
                except Exception as e:
                    print(f"Ошибка при выполнении правила: {e}")
                    continue

        return inferred

    def load_from_dict(self, data: dict):
        self.facts = data.get("facts", {})
        self.rules = data.get("rules", [])

    def to_dict(self):
        return {
            "facts": self.facts,
            "rules": self.rules
        }