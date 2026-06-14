# HuggingFace classification service.
# Uses toxic-bert as gate (toxic/non-toxic) and bart-large-mnli for category detection.

from transformers import pipeline
from pathlib import Path

TOXIC_LABELS = [
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

NEUTRAL_LABELS = [
    "neutral communication",
    "friendly conversation",
    "normal request",
    "positive interaction",
    "everyday coordination",
    "expression of gratitude",
    "casual greeting",
    "professional communication"
]

CANDIDATE_LABELS = TOXIC_LABELS + NEUTRAL_LABELS

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
    """
    Two-stage classification:
    1. toxic gate — is the message toxic at all?
    2. bart-large-mnli — which specific categories?
    """
    # Stage 1 — toxic-bert gate
    gate_result = toxic_gate(text)[0]
    label = gate_result["label"]
    score = round(gate_result["score"], 3)

    # toxic-bert returns the label with highest confidence
    # if label is "toxic" with low score → actually non-toxic
    # if label is "non-toxic" with high score → definitely non-toxic
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
    toxic_detected = []
    neutral_score = 0.0

    for label, score in zip(result["labels"], result["scores"]):
        if label in NEUTRAL_LABELS:
            neutral_score = max(neutral_score, score)
        elif score >= threshold:
            toxic_detected.append({
                "category": label,
                "confidence": round(score, 3)
            })

    if not toxic_detected:
        return {
            "detected_categories": [],
            "risk_score": 0.0,
            "risk_level": "none",
            "gate": "toxic-bert passed, no categories above threshold",
            "gate_confidence": gate_confidence
        }

    risk_score = round(
        sum(c["confidence"] for c in toxic_detected) / len(toxic_detected), 3
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
        "detected_categories": toxic_detected,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "gate": "toxic",
        "gate_confidence": gate_confidence
    }