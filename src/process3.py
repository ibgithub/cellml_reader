"""
Proses 3: Inferensi proses biologi dan lookup ontologi.

Input: hasil dari Proses 2 (variabel + kalimat yang ditemukan)
Output: anotasi terstruktur dengan ID ontologi
"""

import json
import ollama

from src.process3_prompt import PROCESS3_PROMPT_TEMPLATE
from src.ontology_lookup import load_obo_file, search_ontology


def run_process3(process2_results, config):
    """Jalankan Proses 3 untuk semua variabel.

    Args:
        process2_results: List dari dict hasil Proses 2
            Setiap item berisi: component, variable, unit, synonyms, contexts
        config: Dict konfigurasi (model_name, chebi_dict, go_dict)

    Returns:
        List of dict anotasi terstruktur
    """
    annotations = []

    for i, var_result in enumerate(process2_results):

        variable_name = var_result["variable"]
        component = var_result["component"]
        unit = var_result["unit"]
        contexts = var_result["contexts"]

        print(f"  [Proses 3] Variabel {i+1}: {variable_name}")

        # Ambil kalimat-kalimat sebagai evidence
        evidence_sentences = []
        for ctx in contexts[:5]:  # Maksimal 5 kalimat sebagai evidence
            evidence_sentences.append(ctx["sentence"])

        # Kalau tidak ada evidence, skip
        if not evidence_sentences:
            print(f"    Tidak ada kalimat evidence, skip.")
            continue

        # Buat prompt
        evidence_text = "\n".join(
            f"- {s}" for s in evidence_sentences
        )

        prompt = PROCESS3_PROMPT_TEMPLATE.format(
            variable_name=variable_name,
            unit=unit,
            component=component,
            evidence_sentences=evidence_text
        )

        # Kirim ke LLM
        try:
            response = ollama.chat(
                model=config["model_name"],
                messages=[{"role": "user", "content": prompt}]
            )
            content = response["message"]["content"]
        except Exception as e:
            print(f"    ERROR LLM: {e}")
            continue

        # Parse JSON dari response LLM
        from src.llm_synonym import _extract_json
        try:
            json_text = _extract_json(content)
            llm_result = json.loads(json_text)
        except Exception as e:
            print(f"    ERROR parse JSON: {e}")
            print(f"    Raw response: {content[:200]}")
            continue

        # Ambil data dari LLM result
        inferred = llm_result.get("inferred_process", llm_result)

        # Lookup ontologi berdasarkan keywords dari LLM
        annotation = build_annotation(inferred, component, variable_name, config)
        annotations.append(annotation)

        print(f"    OK: {annotation['name']}")

    return annotations


def build_annotation(inferred, component, variable_name, config):
    """Bangun anotasi final dengan lookup ontologi.

    Args:
        inferred: Dict hasil dari LLM
        component: Nama komponen CellML
        variable_name: Nama variabel CellML
        config: Dict yang berisi chebi_dict dan go_dict

    Returns:
        Dict anotasi terstruktur dengan ID ontologi
    """
    chebi_dict = config["chebi_dict"]
    go_dict = config["go_dict"]

    # Cari source identity dari CHEBI
    source_keywords = inferred.get("source_identity_keywords", [])
    source_identity = None
    for kw in source_keywords:
        source_identity = search_ontology(chebi_dict, kw)
        if source_identity:
            break

    # Cari sink identity dari CHEBI
    sink_keywords = inferred.get("sink_identity_keywords", [])
    sink_identity = None
    for kw in sink_keywords:
        sink_identity = search_ontology(chebi_dict, kw)
        if sink_identity:
            break

    # Cari mediator identity dari GO
    mediator_keywords = inferred.get("mediator_identity_keywords", [])
    mediator_identity = None
    for kw in mediator_keywords:
        mediator_identity = search_ontology(go_dict, kw)
        if mediator_identity:
            break

    # Bangun output terstruktur
    annotation = {
        "name": inferred.get("name", f"{component.replace('_', ' ').title()}"),
        "description": inferred.get("description", ""),
        "source": inferred.get("source", f"source_{variable_name}"),
        "source_identity": source_identity or "NOT_FOUND",
        "source_is_part_of": inferred.get("source_location", "extracellular"),
        "sink": inferred.get("sink", f"sink_{variable_name}"),
        "sink_identity": sink_identity or "NOT_FOUND",
        "sink_is_part_of": inferred.get("sink_location", "intracellular"),
        "mediator": inferred.get("mediator", f"mediator_{variable_name}_channel"),
        "mediator_identity": mediator_identity or "NOT_FOUND",
        "model_reference": f"process_{variable_name}",
        "model_property": f"{component}.{variable_name}",
        "model_ontology": "opb:OPB_00318",
        "evidence_sentences": inferred.get("evidence_sentences", [])
    }

    return annotation
