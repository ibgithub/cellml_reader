"""
Modul untuk generate synonym variabel CellML via LLM (Ollama).
"""

import json
import re
import ollama

from src.prompt import PROMPT_TEMPLATE
from config import MODEL_NAME


def generate_synonyms(variable_info, paper_title):
    """Generate synonym untuk satu variabel CellML via LLM.

    Args:
        variable_info: Dict dengan keys "component", "variable", "unit"
        paper_title: Judul paper PDF

    Returns:
        Dict dengan keys "symbolic" dan "textual"
    """
    from src.database import check_llm_cache, save_llm_cache

    prompt = PROMPT_TEMPLATE.format(
        variable=variable_info["variable"],
        component=variable_info["component"],
        unit=variable_info["unit"],
        paper_title=paper_title
    )

    cached_content = check_llm_cache(prompt)
    if cached_content:
        content = cached_content
        print("    [LLM Cache Hit] Menggunakan response sinonim dari cache.")
    else:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format="json"
        )
        content = response["message"]["content"]
        save_llm_cache(prompt, content)

    print("\n===== RAW LLM RESPONSE =====")
    try:
        print(content)
    except UnicodeEncodeError:
        print(content.encode('ascii', errors='replace').decode('ascii'))
    print("============================\n")

    # Ekstrak JSON dari response (handle markdown code block)
    try:
        json_text = _extract_json(content)
        return json.loads(json_text)
    except Exception as e:
        print(f"    [Warning] Failed to parse JSON from response: {e}. Attempting regex fallback...")
        symbolic = []
        textual = []
        
        # Regex fallback for Symbolic
        sym_match = re.search(r'(?:Symbolic|symbolic|SYMBOLIC):?([\s\S]*?)(?:Textual|textual|TEXTUAL|$)', content)
        if sym_match:
            symbolic = [line.strip('*- \t\u2022').split('(')[0].strip() for line in sym_match.group(1).strip().split('\n') if line.strip()]
            
        # Regex fallback for Textual
        text_match = re.search(r'(?:Textual|textual|TEXTUAL):?([\s\S]*?)$', content)
        if text_match:
            textual = [line.strip('*- \t\u2022').split('(')[0].strip() for line in text_match.group(1).strip().split('\n') if line.strip()]
            
        # Clean up empty items
        symbolic = [s for s in symbolic if s]
        textual = [t for t in textual if t]
        
        # Fallback to defaults if empty
        if not symbolic:
            symbolic = [variable_info["variable"]]
        if not textual:
            textual = [variable_info["component"].replace("_", " ")]
            
        return {
            "symbolic": symbolic,
            "textual": textual
        }


def _extract_json(text):
    """Ekstrak JSON dari text LLM response.

    LLM kadang bungkus JSON dalam ```json ... ``` code block.
    Fungsi ini coba ambil JSON-nya, apapun formatnya.
    """
    text = text.strip()

    # Coba langsung parse (kalau sudah bare JSON)
    if text.startswith("{"):
        return text

    # Coba ambil dari markdown code block: ```json ... ``` atau ``` ... ```
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: ambil antara { pertama dan } terakhir
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        return text[first:last + 1]

    # Kalau tetap gagal, kembalikan text asli (biar json.loads yang raise error)
    return text
