class ExpertSystem:
    def __init__(self):
        self.facts = {}
        self.rules = []

    def add_fact(self, fact: str, cf: float):
        """Добавить факт с коэффициентом уверенности"""
        if not 0 <= cf <= 1:
            raise ValueError("Коэффициент уверенности должен быть от 0 до 1")
        self.facts[fact] = cf

    def edit_fact(self, old_fact: str, new_fact: str, new_cf: float):
        """Изменить существующий факт"""
        if old_fact in self.facts:
            del self.facts[old_fact]
        self.facts[new_fact] = new_cf

    def delete_fact(self, fact: str):
        """Удалить факт"""
        if fact in self.facts:
            del self.facts[fact]

    def add_rule(self, conditions: list, conclusion: str, cf: float):
        """Добавить правило"""
        if not 0 <= cf <= 1:
            raise ValueError("Коэффициент уверенности должен быть от 0 до 1")

        structured_conditions = []

        for condition in conditions:
            if isinstance(condition, dict):
                structured_conditions.append({
                    "fact": condition.get("fact", ""),
                    "operator": condition.get("operator", "").upper()
                })
            else:
                structured_conditions.append({
                    "fact": str(condition).strip(),
                    "operator": ""
                })

        self.rules.append({
            "if": structured_conditions,
            "then": conclusion,
            "cf": cf
        })

    def edit_rule(self, index: int, conditions: list, conclusion: str, cf: float):
        """Изменить существующее правило"""
        if 0 <= index < len(self.rules):
            self.add_rule(conditions, conclusion, cf)
            old_rule = self.rules.pop(index + 1)
            self.rules[index] = old_rule

    def delete_rule(self, index: int):
        """Удалить правило по индексу"""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)

    def _evaluate_condition(self, condition: dict) -> float:
        """Оценить одно условие"""
        fact = condition.get("fact", "")
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
                if i < len(conditions) - 1:
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

    def query(self, query_fact: str):
        """Выполнить запрос к экспертной системе"""
        result = {
            "query": query_fact,
            "found_directly": False,
            "direct_cf": 0.0,
            "can_be_inferred": False,
            "max_possible_cf": 0.0,
            "rules_that_can_infer": [],
            "required_facts": [],
            "suggestions": []
        }

        if query_fact in self.facts:
            result["found_directly"] = True
            result["direct_cf"] = self.facts[query_fact]

        rules_that_conclude = []
        for rule in self.rules:
            if rule["then"] == query_fact:
                rules_that_conclude.append(rule)

        if rules_that_conclude:
            result["can_be_inferred"] = True

            for rule in rules_that_conclude:
                condition_cfs = []
                required_facts_for_rule = []

                for condition in rule["if"]:
                    fact = condition.get("fact", "")
                    operator = condition.get("operator", "").upper()

                    if fact in self.facts:
                        fact_cf = self.facts[fact]
                        if operator == "NOT":
                            condition_cf = 1.0 - fact_cf
                        else:
                            condition_cf = fact_cf
                        required_facts_for_rule.append({
                            "fact": fact,
                            "in_facts": True,
                            "cf": fact_cf,
                            "required": True
                        })
                    else:
                        condition_cf = 1.0
                        required_facts_for_rule.append({
                            "fact": fact,
                            "in_facts": False,
                            "cf": 0.0,
                            "required": True
                        })

                    condition_cfs.append(condition_cf)

                if condition_cfs:
                    condition_cf = min(condition_cfs) if condition_cfs else 0.0
                else:
                    condition_cf = 0.0

                max_cf_for_rule = condition_cf * rule["cf"]

                result["rules_that_can_infer"].append({
                    "rule": rule,
                    "condition_cfs": condition_cfs,
                    "max_cf": max_cf_for_rule
                })

                for fact_info in required_facts_for_rule:
                    if not any(f["fact"] == fact_info["fact"] for f in result["required_facts"]):
                        result["required_facts"].append(fact_info)

            if result["rules_that_can_infer"]:
                result["max_possible_cf"] = max(
                    rule_info["max_cf"]
                    for rule_info in result["rules_that_can_infer"]
                )

        if not result["found_directly"] and not result["can_be_inferred"]:
            query_lower = query_fact.lower()
            for fact in self.facts.keys():
                if query_lower in fact.lower() or fact.lower() in query_lower:
                    result["suggestions"].append(fact)

            result["suggestions"] = result["suggestions"][:5]

        return result

    def load_from_dict(self, data: dict):
        """Загрузить состояние системы из словаря"""
        self.facts = data.get("facts", {})
        self.rules = data.get("rules", [])

    def to_dict(self):
        """Преобразовать состояние системы в словарь"""
        return {
            "facts": self.facts,
            "rules": self.rules
        }