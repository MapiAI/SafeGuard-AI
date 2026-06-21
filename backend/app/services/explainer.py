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

def generate_explanation(message: str, categories: list, retrieved_docs: str = "", previous_messages: list = [], relationship_summary: str = "") -> dict:
    """
    Generate an ethical explanation and three response strategies for a classified message.
    Grounds the response exclusively in retrieved educational documents (RAG).
    Considers relationship history for contextual pattern analysis.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    categories_text = ", ".join([c["category"] for c in categories]) if categories else "none"

    # Context block
    context_block = ""
    if relationship_summary:
        context_block += f"\nRELATIONSHIP HISTORY SUMMARY:\n{relationship_summary}\n"
    else:
        context_block += "\nRELATIONSHIP HISTORY SUMMARY: No history available yet. This is the first message analyzed in this case.\n"
    if previous_messages:
        context_block += "\nRECENT MESSAGES (chronological, with risk level):\n"
        for m in previous_messages:
            cats = ", ".join([c["category"] for c in m["categories"]]) if m["categories"] else "none"
            context_block += f"- [{m['risk_level']}] \"{m['content']}\" (patterns: {cats})\n"

    user_prompt = f"""
The following message has been analyzed and these communication patterns were detected: {categories_text}.

Message analyzed: "{message}"
{context_block}
Retrieved educational documents:
{retrieved_docs if retrieved_docs else "No relevant documents retrieved."}

Based EXCLUSIVELY on the retrieved documents above, please provide:
1. EXPLANATION: A brief educational explanation (2-3 sentences) of the detected communication patterns, grounded in the retrieved documents. If relationship history is provided, consider it to identify behavioral cycles such as escalation followed by reconciliation.
2. RESPONSE_STRATEGIES: Three general communication approaches, labeled as:
    - Assertive: a direct, boundary-setting approach
    - Neutral: a de-personalised, factual approach
    - De-escalation: a calm, tension-reducing approach
3. UPDATED_SUMMARY: Update the relationship history in 3-4 sentences max. Focus on behavioral patterns, escalation trends, and cycles observed across messages. If no history exists yet, create an initial summary based on this message alone.

Format your response as JSON with keys: "explanation", "response_strategies", "updated_summary", "context_risk_level".
response_strategies should be a list of objects with keys: "type", "example", "description".
Add this disclaimer to each strategy: "This example is generated for educational purposes and may not be appropriate for every situation."
CONTEXT_RISK_LEVEL must be one of: "none", "low", "medium", "high".
Rules:
- If no relationship history exists and no toxic patterns are detected in the current message, return "none". No exceptions.
- If relationship history exists, assess the current message in that context.
- Never assign a risk level higher than "low" to a clearly neutral greeting or everyday message regardless of history.
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
    result["context_note"] = "This analysis considers the relationship history and recent messages. Communication patterns may differ when evaluated within the broader context of a conversation or relationship."
    return result