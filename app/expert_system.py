class ExpertSystem:
    def __init__(self):
        self.facts = {}
        self.rules = []

    def add_fact(self, fact: str, cf: float) -> None:
        if not 0 <= cf <= 1:
            raise ValueError("The confidence coefficient should be between 0 and 1")
        self.facts[fact] = cf

    def edit_fact(self, old_fact: str, new_fact: str, new_cf: float) -> None:
        if old_fact in self.facts:
            del self.facts[old_fact]
        self.facts[new_fact] = new_cf

    def delete_fact(self, fact: str) -> None:
        if fact in self.facts:
            del self.facts[fact]

    def add_rule(self, conditions: list, conclusion: str, cf: float) -> None:
        if not 0 <= cf <= 1:
            raise ValueError("The confidence coefficient should be between 0 and 1")
        self.rules.append({{
            "if": conditions,
            "then": conclusion,
            "cf": cf
        }})

    def edit_rule(self, index: int, conditions: list, conclusion: str, cf: float) -> None:
        if 0 <= index <= len(self.rules):
            self.rules[index] = {
                "if": conditions,
                "then": conclusion,
                "cf": cf
            }

    def delete_rule(self, index: int) -> None:
        if 0 <= index < len(self.rules):
            self.rules.pop(index)

    def infer(self) -> dict:
        new_inference = True
        inferred = {}

        while new_inference:
            new_inference = False
            for rule in self.rules:
                conditions = rule["if"]
                conclusion = rule["then"]
                rule_cf = rule["cf"]

                known_conditions = [
                    self.facts.get(cond) for cond in conditions
                    if cond in self.facts
                ]

                if len(known_conditions) == len(conditions):
                    min_cf = min(known_conditions) if known_conditions else 0
                    result_cf = min_cf * rule_cf

                    if conclusion not in self.facts or result_cf > self.facts[conclusion]:
                        self.facts[conclusion] = result_cf
                        inferred[conclusion] = result_cf
                        new_inferences = True

        return inferred

    def load_from_dict(self, data: dict) -> None:
        self.facts = data.get("facts", {})
        self.rules = data.get("rules", [])

    def to_dict(self) -> dict:
        return {
            "facts": self.facts,
            "rules": self.rules
        }