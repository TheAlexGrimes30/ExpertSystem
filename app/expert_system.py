class ExpertSystem:
    def __init__(self):
        self.facts = {}
        self.rules = []

    def add_fact(self, fact: str, cf: float):
        """Добавить факт с коэффициентом уверенности"""
        if not 0 <= cf <= 1:
            raise ValueError("Коэффициент уверенности должен быть от 0 до 1")
        self.facts[fact] = cf

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

    def query(self, symptoms_input: str):
        """Выполнить диагностику на основе введенных симптомов"""
        # Очищаем и нормализуем ввод
        symptoms = [s.strip().lower() for s in symptoms_input.split(',') if s.strip()]

        if not symptoms:
            return {
                "success": False,
                "error": "Введите симптомы через запятую"
            }

        result = {
            "success": True,
            "query": symptoms_input,
            "diagnoses": [],
            "matched_symptoms": [],
            "missing_for_diagnosis": {},
            "no_diagnosis_info": None
        }

        # 1. Определяем, какие симптомы есть в базе знаний
        matched_symptoms = []
        for symptom in symptoms:
            found = False
            for fact_name in self.facts.keys():
                fact_lower = fact_name.lower()
                symptom_lower = symptom.lower()
                # Проверяем частичное совпадение
                if (symptom_lower in fact_lower or
                        fact_lower in symptom_lower or
                        any(word in symptom_lower for word in fact_lower.split()) or
                        any(word in fact_lower for word in symptom_lower.split())):
                    matched_symptoms.append({
                        "input": symptom,
                        "matched_fact": fact_name,
                        "cf": self.facts[fact_name]
                    })
                    found = True
                    break

            if not found:
                matched_symptoms.append({
                    "input": symptom,
                    "matched_fact": None,
                    "cf": 0.0
                })

        result["matched_symptoms"] = matched_symptoms

        # 2. Ищем диагнозы на основе правил
        possible_diagnoses = {}

        for rule in self.rules:
            diagnosis_name = rule["then"]
            rule_cf = rule["cf"]

            # Анализируем условия правила
            rule_conditions = []
            condition_results = []

            for condition in rule["if"]:
                fact = condition["fact"]
                operator = condition.get("operator", "").upper()

                # Ищем соответствие среди симптомов
                condition_matched = False
                condition_cf = 0.0

                for symptom_info in matched_symptoms:
                    if symptom_info["matched_fact"] == fact:
                        if operator == "NOT":
                            # Для NOT: уверенность = 1 - уверенность наличия
                            condition_cf = 1.0 - symptom_info["cf"]
                            condition_matched = (condition_cf > 0)
                        else:
                            condition_cf = symptom_info["cf"]
                            condition_matched = (condition_cf > 0)
                        break

                rule_conditions.append({
                    "fact": fact,
                    "operator": operator,
                    "matched": condition_matched,
                    "cf": condition_cf
                })

                condition_results.append(condition_matched)

            # Проверяем, выполнено ли правило
            rule_satisfied = False

            # Простая логика: все условия должны быть выполнены
            if all(condition_results):
                rule_satisfied = True
            else:
                # Проверяем сложные условия с операторами
                # Пока реализуем простую логику AND
                continue

            if rule_satisfied:
                # Рассчитываем CF для этого правила
                condition_cfs = [cond["cf"] for cond in rule_conditions if cond["matched"]]

                if condition_cfs:
                    min_condition_cf = min(condition_cfs)
                    diagnosis_cf = min_condition_cf * rule_cf

                    if diagnosis_name not in possible_diagnoses or diagnosis_cf > possible_diagnoses[diagnosis_name][
                        "cf"]:
                        possible_diagnoses[diagnosis_name] = {
                            "name": diagnosis_name,
                            "cf": diagnosis_cf,
                            "rule_cf": rule_cf,
                            "conditions": [f"{cond['fact']}" + (f" {cond['operator']}" if cond['operator'] else "")
                                           for cond in rule_conditions],
                            "matched_conditions": [cond["fact"] for cond in rule_conditions if cond["matched"]],
                            "min_condition_cf": min_condition_cf
                        }

        # 3. Формируем результаты
        for diagnosis_data in possible_diagnoses.values():
            confidence = self._get_confidence_level(diagnosis_data["cf"])
            result["diagnoses"].append({
                **diagnosis_data,
                "confidence": confidence
            })

        # Сортируем по уверенности (CF)
        result["diagnoses"].sort(key=lambda x: x["cf"], reverse=True)

        # 4. Если диагнозов нет, собираем информацию
        if not result["diagnoses"]:
            # Ищем правила, которые почти сработали
            almost_rules = []
            for rule in self.rules:
                matched_count = 0
                total_conditions = len(rule["if"])

                for condition in rule["if"]:
                    fact = condition["fact"]
                    operator = condition.get("operator", "").upper()

                    for symptom_info in matched_symptoms:
                        if symptom_info["matched_fact"] == fact:
                            if operator == "NOT":
                                # Для NOT нужно отсутствие симптома
                                if symptom_info["cf"] < 0.5:  # Если уверенность в наличии < 0.5, считаем отсутствует
                                    matched_count += 1
                            else:
                                matched_count += 1
                            break

                if matched_count > 0 and matched_count < total_conditions:
                    almost_rules.append({
                        "diagnosis": rule["then"],
                        "matched": matched_count,
                        "total": total_conditions,
                        "missing": [cond["fact"] for cond in rule["if"] if cond["fact"] not in
                                    [s["matched_fact"] for s in matched_symptoms if s["matched_fact"]]]
                    })

            if almost_rules:
                result["no_diagnosis_info"] = {
                    "message": "Не удалось поставить точный диагноз",
                    "almost_rules": almost_rules
                }

        return result

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
        self.rules = data.get("rules", [])

    def to_dict(self):
        """Преобразовать состояние системы в словарь"""
        return {
            "facts": self.facts,
            "rules": self.rules
        }