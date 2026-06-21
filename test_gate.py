from transformers import pipeline

gate = pipeline("text-classification", model="models/toxic_gate")

tests = [
    "Why you don't answer me? Do you think I'm stupid?",
    "I need to know where you are at all times.",
    "If you leave me I will make sure you regret it.",
    "You are too sensitive, stop overreacting.",
    "Good morning! How are you?",
    "Can we meet tomorrow at 10am?",
    "I felt hurt when you said that, can we discuss it?",
]

for msg in tests:
    r = gate(msg)[0]
    print(f"[{r['label']:9}] {r['score']:.3f} | {msg}")