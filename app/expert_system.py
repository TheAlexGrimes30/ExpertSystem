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

    def parse_conditions_string(self, conditions_str: str):
        """Парсинг строки условий со скобками и операторами"""
        conditions = []
        tokens = conditions_str.split(',')

        i = 0
        while i < len(tokens):
            token = tokens[i].strip()

            # Если токен пустой, пропускаем
            if not token:
                i += 1
                continue

            # Проверяем операторы
            if token.upper() in ['И', 'ИЛИ', 'НЕТ']:
                if conditions:
                    # Добавляем оператор к последнему условию
                    conditions[-1]["operator"] = token.upper()
                i += 1
                continue

            # Обработка скобок
            if '(' in token:
                # Нашли начало группы
                group_tokens = []
                group_depth = 1
                current_token = token

                # Собираем все токены группы
                while i < len(tokens) and group_depth > 0:
                    current_token = tokens[i].strip()

                    # Считаем открывающие скобки
                    open_count = current_token.count('(')
                    close_count = current_token.count(')')
                    group_depth += open_count - close_count

                    # Убираем скобки из токена
                    clean_token = current_token.replace('(', '').replace(')', '').strip()
                    if clean_token and clean_token.upper() not in ['И', 'ИЛИ', 'НЕТ']:
                        group_tokens.append(clean_token)

                    i += 1

                # Если есть оператор после группы
                if i < len(tokens) and tokens[i].strip().upper() in ['И', 'ИЛИ', 'НЕТ']:
                    operator = tokens[i].strip().upper()
                    i += 1
                else:
                    operator = ''

                # Создаем группу условий
                conditions.append({
                    "fact": group_tokens,  # Список фактов для группы
                    "operator": operator,
                    "is_group": True
                })
                continue

            # Обычный факт
            conditions.append({
                "fact": token,
                "operator": '',
                "is_group": False
            })
            i += 1

        return conditions

    def add_rule(self, conditions: list, conclusion: str, cf: float):
        """Добавить правило"""
        if not 0 <= cf <= 1:
            raise ValueError("Коэффициент уверенности должен быть от 0 до 1")

        structured_conditions = []

        for condition in conditions:
            if isinstance(condition, dict):
                # Уже структурированное условие
                if condition.get("is_group", False):
                    # Обрабатываем группу
                    group_facts = condition.get("fact", [])
                    if isinstance(group_facts, list):
                        for fact in group_facts:
                            structured_conditions.append({
                                "fact": fact,
                                "operator": condition.get("operator", "").upper(),
                                "is_group": True
                            })
                    else:
                        structured_conditions.append({
                            "fact": group_facts,
                            "operator": condition.get("operator", "").upper(),
                            "is_group": True
                        })
                else:
                    structured_conditions.append({
                        "fact": condition.get("fact", ""),
                        "operator": condition.get("operator", "").upper(),
                        "is_group": False
                    })
            elif isinstance(condition, str):
                # Парсим строку
                parsed = self.parse_conditions_string(condition)
                structured_conditions.extend(parsed)
            else:
                structured_conditions.append({
                    "fact": str(condition).strip(),
                    "operator": "",
                    "is_group": False
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
        is_group = condition.get("is_group", False)

        fact_cf = self.facts.get(fact, 0)

        if operator == "NOT":
            return 1.0 - fact_cf

        return fact_cf

    def _evaluate_group_conditions(self, group_conditions: list) -> float:
        """Оценить группу условий"""
        if not group_conditions:
            return 0.0

        result = None
        current_operator = "AND"  # По умолчанию для группы

        for condition in group_conditions:
            condition_cf = self._evaluate_condition(condition)
            operator = condition.get("operator", "").upper()

            if result is None:
                result = condition_cf
            elif operator == "AND" or current_operator == "AND":
                result = min(result, condition_cf)
                current_operator = operator
            elif operator == "OR":
                result = max(result, condition_cf)
                current_operator = operator
            else:
                result = min(result, condition_cf)

        return result if result is not None else 0.0

    def _evaluate_rule_conditions(self, conditions: list) -> float:
        """Оценить все условия правила с учетом операторов и групп"""
        if not conditions:
            return 0.0

        result = None
        current_operator = "AND"  # По умолчанию AND

        i = 0
        while i < len(conditions):
            condition = conditions[i]

            if condition.get("is_group", False):
                # Это группа условий
                # Находим все условия группы
                group_conditions = []
                while i < len(conditions) and conditions[i].get("is_group", False):
                    group_conditions.append(conditions[i])
                    i += 1

                condition_cf = self._evaluate_group_conditions(group_conditions)
                group_operator = group_conditions[-1]["operator"] if group_conditions else ""
            else:
                condition_cf = self._evaluate_condition(condition)
                group_operator = condition.get("operator", "")
                i += 1

            if result is None:
                result = condition_cf
                current_operator = group_operator
            elif current_operator == "AND" or group_operator == "AND":
                result = min(result, condition_cf)
                current_operator = group_operator
            elif group_operator == "OR":
                result = max(result, condition_cf)
                current_operator = group_operator
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
        # Очищаем и нормализуем ввод - пользователь вводит просто симптомы через запятую
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
                fact = condition.get("fact", "")
                operator = condition.get("operator", "").upper()
                is_group = condition.get("is_group", False)

                if is_group and isinstance(fact, list):
                    # Это группа условий - проверяем каждый факт в группе
                    group_matched = True
                    group_cfs = []

                    for group_fact in fact:
                        # Ищем соответствие среди симптомов
                        fact_matched = False
                        fact_cf = 0.0

                        for symptom_info in matched_symptoms:
                            if symptom_info["matched_fact"] == group_fact:
                                if operator == "NOT":
                                    # Для NOT: уверенность = 1 - уверенность наличия
                                    fact_cf = 1.0 - symptom_info["cf"]
                                    fact_matched = (fact_cf > 0)
                                else:
                                    fact_cf = symptom_info["cf"]
                                    fact_matched = (fact_cf > 0)
                                break

                        group_matched = group_matched and fact_matched
                        if fact_matched:
                            group_cfs.append(fact_cf)

                    # Добавляем группу как одно условие
                    if group_matched and group_cfs:
                        min_group_cf = min(group_cfs)
                        rule_conditions.append({
                            "fact": f"группа: {', '.join(fact)}",
                            "operator": operator,
                            "matched": True,
                            "cf": min_group_cf,
                            "is_group": True
                        })
                        condition_results.append(True)
                    else:
                        rule_conditions.append({
                            "fact": f"группа: {', '.join(fact)}",
                            "operator": operator,
                            "matched": False,
                            "cf": 0.0,
                            "is_group": True
                        })
                        condition_results.append(False)
                else:
                    # Обычное условие (не группа)
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
                        "cf": condition_cf,
                        "is_group": False
                    })

                    condition_results.append(condition_matched)

            # Проверяем, выполнено ли правило
            # Для правил со скобками нужно учитывать логику групп
            rule_satisfied = False

            if all(condition_results):
                rule_satisfied = True
            else:
                # Проверяем более сложную логику с операторами
                # Упрощенная проверка - если есть хотя бы одно выполненное условие
                # В реальной системе здесь должна быть полноценная логическая проверка
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
                            "min_condition_cf": min_condition_cf,
                            "is_group_rule": any(cond.get("is_group", False) for cond in rule_conditions)
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
                total_conditions = 0

                for condition in rule["if"]:
                    fact = condition.get("fact", "")
                    operator = condition.get("operator", "").upper()
                    is_group = condition.get("is_group", False)

                    if is_group and isinstance(fact, list):
                        # Группа условий
                        for group_fact in fact:
                            total_conditions += 1
                            for symptom_info in matched_symptoms:
                                if symptom_info["matched_fact"] == group_fact:
                                    if operator == "NOT":
                                        # Для NOT нужно отсутствие симптома
                                        if symptom_info["cf"] < 0.5:
                                            matched_count += 1
                                    else:
                                        matched_count += 1
                                    break
                    else:
                        # Одиночное условие
                        total_conditions += 1
                        for symptom_info in matched_symptoms:
                            if symptom_info["matched_fact"] == fact:
                                if operator == "NOT":
                                    # Для NOT нужно отсутствие симптома
                                    if symptom_info["cf"] < 0.5:
                                        matched_count += 1
                                else:
                                    matched_count += 1
                                break

                if matched_count > 0 and matched_count < total_conditions:
                    # Собираем недостающие условия
                    missing_conditions = []
                    for condition in rule["if"]:
                        fact = condition.get("fact", "")
                        is_group = condition.get("is_group", False)

                        if is_group and isinstance(fact, list):
                            for group_fact in fact:
                                found = any(s["matched_fact"] == group_fact for s in matched_symptoms)
                                if not found:
                                    missing_conditions.append(group_fact)
                        else:
                            found = any(s["matched_fact"] == fact for s in matched_symptoms)
                            if not found:
                                missing_conditions.append(fact)

                    almost_rules.append({
                        "diagnosis": rule["then"],
                        "matched": matched_count,
                        "total": total_conditions,
                        "missing": missing_conditions
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