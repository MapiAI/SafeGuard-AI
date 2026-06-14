# PII detection and anonymisation service.
# Detects and replaces personally identifiable information before sending text to external AI models.

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Load engines once at startup
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# PII entity types to detect and anonymise
PII_ENTITIES = [
    "PERSON",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "LOCATION",
    "DATE_TIME",
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "URL",
    "NRP"  # Nationality, Religion, Political group
]

def anonymise_text(text: str, language: str = "en") -> dict:
    """
    Detect and anonymise PII in a text before sending to external AI models.
    Returns anonymised text and a list of detected PII entities.
    """
    # Detect PII
    results = analyzer.analyze(
        text=text,
        entities=PII_ENTITIES,
        language=language
    )

    # Anonymise detected PII
    anonymised = anonymizer.anonymize(
        text=text,
        analyzer_results=results
    )

    # Build list of detected entities for logging
    detected_pii = [
        {
            "entity_type": result.entity_type,
            "start": result.start,
            "end": result.end,
            "score": round(result.score, 3)
        }
        for result in results
    ]

    return {
        "original_text": text,
        "anonymised_text": anonymised.text,
        "detected_pii": detected_pii,
        "has_pii": len(detected_pii) > 0
    }