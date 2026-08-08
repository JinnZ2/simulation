# assumption_lab.py
# A playground for exploring labels, categories, and assumptions.
# Based on the scientific method applied to categories themselves.

class AssumptionPlayground:
    def __init__(self):
        self.labels = {}
    
    def add_label(self, name, definition, hidden_assumptions, context):
        self.labels[name] = {
            "definition": definition,
            "hidden_assumptions": hidden_assumptions,
            "context": context,
            "questions": [],
            "counterexamples": []
        }
    
    def ask_questions(self, label_name):
        # Generate a set of questions that challenge the label
        label = self.labels.get(label_name)
        if not label:
            return "Label not found."
        questions = [
            f"What does '{label_name}' assume about time?",
            f"What does '{label_name}' assume about the observer?",
            f"Can '{label_name}' be applied universally, or is it context-dependent?",
            f"What would a counterexample to '{label_name}' look like?",
            f"If '{label_name}' were redefined by a different culture, what would change?"
        ]
        return questions
    
    def add_counterexample(self, label_name, example):
        self.labels[label_name]["counterexamples"].append(example)
    
    def show_summary(self, label_name):
        label = self.labels.get(label_name)
        if not label:
            return "Label not found."
        return {
            "definition": label["definition"],
            "assumptions": label["hidden_assumptions"],
            "questions": self.ask_questions(label_name),
            "counterexamples": label["counterexamples"]
        }

# Example usage:
playground = AssumptionPlayground()
playground.add_label(
    name="Efficiency",
    definition="Using the least resources to achieve a goal.",
    hidden_assumptions="It assumes resources are finite, time is linear, and the goal is fixed.",
    context="Industrial production, logistics."
)
print(playground.ask_questions("Efficiency"))
