"""
Modul untuk generate synonym variabel CellML via LLM (Ollama).
"""

import json
import re
import ollama

from src.prompt import PROMPT_TEMPLATE
from config import MODEL_NAME, LLM_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL


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
        if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            content = response.text
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
            for line in sym_match.group(1).split('\n'):
                line_strip = line.strip()
                if line_strip.startswith(('-', '*', '\u2022', '1.', '2.', '3.', '4.', '5.')):
                    val = line_strip.strip('*- \t\u2022123456789.').split('(')[0].strip()
                    if val:
                        symbolic.append(val)
            
        # Regex fallback for Textual
        text_match = re.search(r'(?:Textual|textual|TEXTUAL):?([\s\S]*?)$', content)
        if text_match:
            for line in text_match.group(1).split('\n'):
                line_strip = line.strip()
                if line_strip.startswith(('-', '*', '\u2022', '1.', '2.', '3.', '4.', '5.')):
                    val = line_strip.strip('*- \t\u2022123456789.').split('(')[0].strip()
                    if val:
                        textual.append(val)
            
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


def _repair_json(json_text):
    """Repair a truncated JSON string by adding missing closing braces/brackets."""
    json_text = json_text.strip()
    
    # Remove trailing commas inside arrays or objects before repair
    # e.g., "key": "value", } -> "key": "value" }
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)
    
    # Count open and close braces/brackets
    open_braces = json_text.count('{')
    close_braces = json_text.count('}')
    open_brackets = json_text.count('[')
    close_brackets = json_text.count(']')
    
    # Add missing brackets/braces
    if open_brackets > close_brackets:
        json_text += ']' * (open_brackets - close_brackets)
    if open_braces > close_braces:
        json_text += '}' * (open_braces - close_braces)
        
    return json_text


def _extract_json(text):
    """Ekstrak JSON dari text LLM response.

    LLM kadang bungkus JSON dalam ```json ... ``` code block.
    Fungsi ini coba ambil JSON-nya, apapun formatnya.
    """
    text = text.strip()

    # Coba ambil dari markdown code block: ```json ... ``` atau ``` ... ```
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        # Fallback: ambil dari { pertama sampai akhir
        first = text.find("{")
        if first != -1:
            text = text[first:]

    # Coba perbaiki JSON jika terpotong
    text = _repair_json(text)
    return text
