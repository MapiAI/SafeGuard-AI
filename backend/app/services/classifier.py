# HuggingFace classification service.
# Uses toxic-bert as gate (toxic/non-toxic) and bart-large-mnli for category detection.

from transformers import pipeline
from pathlib import Path

# Descriptive labels for zero-shot classification — more context helps bart-large-mnli
LABEL_MAP = {
    "controlling behavior that limits personal freedom and autonomy": "control",
    "emotional manipulation that exploits feelings to influence behavior": "manipulation",
    "direct threats and intimidation": "threat",
    "psychological pressure and emotional coercion": "psychological pressure",
    "jealousy and possessive behavior": "jealousy",
    "isolation from friends and family": "isolation",
    "gaslighting and reality distortion": "gaslighting",
    "humiliation and degradation": "humiliation",
    "explicit verbal aggression and insults": "aggressive language",
    "coercion and forced compliance": "coercion"
}

CANDIDATE_LABELS = list(LABEL_MAP.keys())

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

def classify_message(text: str, strict: bool = True) -> dict:
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

    # Lower threshold if relationship has toxic history
    non_toxic_threshold = 0.92 if strict else 0.75
    
    if not is_toxic and gate_confidence >= non_toxic_threshold:
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

    threshold = 0.80

    detected = [
        {"category": LABEL_MAP[label], "confidence": round(score, 3)}
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

    # Risk score: weighted average of all 10 categories and max category score
    # avg_all gives nuance, max_score amplifies when at least one category is strong
    all_scores = {LABEL_MAP[label]: round(score, 3)
                for label, score in zip(result["labels"], result["scores"])}

    avg_all = sum(all_scores.values()) / len(all_scores)
    max_score = max(all_scores.values())
    risk_score = round((avg_all + max_score) / 2, 3)

    if risk_score >= 0.80:
        risk_level = "high"
    elif risk_score >= 0.60:
        risk_level = "medium"
    elif risk_score > 0.20:
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