from typing import List, Dict, Any

SYSTEM_RAG_PROMPT = """You are CodeLens AI, an expert AI Software Engineer and Repository Assistant.
Your task is to provide accurate, deep technical answers based STRICTLY on the provided repository code context.

RULES:
1. NEVER hallucinate features, imports, functions, or file structures not present in the context.
2. If the answer cannot be determined from the provided context, state clearly: "Based on the retrieved repository code, this information is not present."
3. ALWAYS cite file paths and exact line numbers in your explanations using Markdown links or brackets, e.g., `backend/auth/login.py:52-88`.
4. When context contains large raw tables, HTML tags, or repetitive links, SUMMARIZE them into clean, concise Markdown bullet points instead of reproducing raw HTML tags.
5. Be concise, precise, and professional.
"""


def build_rag_prompt(query: str, retrieved_chunks: List[Dict[str, Any]], conversation_history: str = "") -> str:
    context_str = ""
    for idx, item in enumerate(retrieved_chunks, 1):
        c = item
        context_str += (
            f"--- CODE CONTEXT [{idx}] ---\n"
            f"File: {c['file_path']}\n"
            f"Lines: {c['start_line']}-{c['end_line']}\n"
            f"Type: {c['chunk_type'].upper()}\n"
        )
        if c.get("name"):
            context_str += f"Name: {c['name']}\n"
        if c.get("parent_scope"):
            context_str += f"Parent Scope: {c['parent_scope']}\n"
        context_str += f"\nCode Content:\n{c['content']}\n\n"

    history_str = f"PREVIOUS CHAT CONVERSATION:\n{conversation_history}\n\n" if conversation_history else ""

    prompt = (
        f"{history_str}"
        f"RETRIEVED CODE CONTEXT FROM REPOSITORY:\n"
        f"{context_str}\n"
        f"USER QUESTION:\n{query}\n\n"
        f"INSTRUCTION:\n"
        f"Answer the user's question accurately using ONLY the code context above. "
        f"Cite exact relative file paths and line ranges."
    )
    return prompt
