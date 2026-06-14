# OpenAI GPT service for generating ethical explanations and response strategies.
# Uses RAG-grounded, policy-compliant prompts to explain detected communication patterns.

import json
from openai import OpenAI
from app.core.config import settings

SYSTEM_PROMPT = """
You are an educational communication assistant for SafeGuard AI.

ALWAYS:
- Analyze linguistic patterns only, never people
- Use hedged language: "may suggest", "is often associated with", "could indicate"
- Base your explanations EXCLUSIVELY on the retrieved educational documents provided
- Be concise, clear, and non-judgmental
- Present response strategies as general educational examples only

NEVER:
- Diagnose individuals or assign mental health labels
- Attribute intent or guilt to any person
- Provide legal or psychological advice
- Recommend ending relationships or reporting someone
- Identify, classify, or label individuals as abusers, stalkers, or similar
- Use knowledge outside of the retrieved documents

If the retrieved documents do not contain relevant information, say:
"Educational resources on this specific pattern are not available in our knowledge base."

If asked to label a person, explain that SafeGuard AI analyzes communication patterns, not people.
"""

def generate_explanation(message: str, categories: list, retrieved_docs: str = "") -> dict:
    """
    Generate an ethical explanation and three response strategies for a classified message.
    Grounds the response exclusively in retrieved educational documents (RAG).
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    categories_text = ", ".join([c["category"] for c in categories]) if categories else "none"

    user_prompt = f"""
The following message has been analyzed and these communication patterns were detected: {categories_text}.

Message analyzed: "{message}"

Retrieved educational documents:
{retrieved_docs if retrieved_docs else "No relevant documents retrieved."}

Based EXCLUSIVELY on the retrieved documents above, please provide:
1. EXPLANATION: A brief educational explanation (2-3 sentences) of the detected communication patterns, grounded in the retrieved documents.
2. RESPONSE_STRATEGIES: Three general communication approaches, labeled as:
   - Assertive: a direct, boundary-setting approach
   - Neutral: a de-personalised, factual approach
   - De-escalation: a calm, tension-reducing approach

Format your response as JSON with keys: "explanation", "response_strategies".
response_strategies should be a list of objects with keys: "type", "example", "description".
Add this disclaimer to each strategy: "This example is generated for educational purposes and may not be appropriate for every situation."
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.4
    )

    result = json.loads(response.choices[0].message.content)
    return result