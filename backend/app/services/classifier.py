# HuggingFace classification service.
# Uses toxic-bert as gate (toxic/non-toxic) and bart-large-mnli for category detection.

from transformers import pipeline
from pathlib import Path

CANDIDATE_LABELS = [
    "control",
    "manipulation",
    "threat",
    "psychological pressure",
    "jealousy",
    "isolation",
    "gaslighting",
    "humiliation",
    "aggressive language",
    "coercion"
]

GATE_MODEL_PATH = str(Path(__file__).parent.parent.parent.parent / "models" / "toxic_gate")


# Load fine-tuned gate model
toxic_gate = pipeline(
    task="text-classification",
    model=GATE_MODEL_PATH
)

zero_shot_classifier = pipeline(
    task="zero-shot-classification",
    model="facebook/bart-large-mnli"
)

def classify_message(text: str) -> dict:
    # HuggingFace classification service.
    # Two-stage pipeline: fine-tuned DistilBERT gate (toxic/non-toxic) 
    # and facebook/bart-large-mnli for multi-label category detection.

    # Stage 1 — toxic-bert gate
    gate_result = toxic_gate(text)[0]
    label = gate_result["label"]
    score = round(gate_result["score"], 3)

    # Fine-tuned DistilBERT returns the label with highest confidence
    # if label is "toxic" with low score → uncertain, pass to bart classifier
    # if label is "non-toxic" with high score → definitely non-toxic, stop pipeline
    if label == "toxic":
        is_toxic = score >= 0.7  # only toxic if confident
        gate_confidence = score
    else:
        is_toxic = False
        gate_confidence = score

    if not is_toxic and gate_confidence >= 0.85:
        return {
            "detected_categories": [],
            "risk_score": 0.0,
            "risk_level": "none",
            "gate": "non-toxic",
            "gate_confidence": gate_confidence
        }

    # Stage 2 — bart-large-mnli category detection
    result = zero_shot_classifier(
        text,
        CANDIDATE_LABELS,
        hypothesis_template="This message is an example of {} in a personal or workplace relationship.",
        multi_label=True
    )

    threshold = 0.5

    detected = [
        {"category": label, "confidence": round(score, 3)}
        for label, score in zip(result["labels"], result["scores"])
            if score >= threshold
    ]

    if not detected:
        return {
            "detected_categories": [],
            "risk_score": 0.0,
            "risk_level": "none",
            "gate": "no categories above threshold",
            "gate_confidence": gate_confidence
        }

    risk_score = round(
        sum(c["confidence"] for c in detected) / len(detected), 3
    )

    if risk_score >= 0.7:
        risk_level = "high"
    elif risk_score >= 0.5:
        risk_level = "medium"
    elif risk_score > 0:
        risk_level = "low"
    else:
        risk_level = "none"

    return {
        "detected_categories": detected,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "gate": "toxic",
        "gate_confidence": gate_confidence
    }