"""
Main pipeline: CellML → Synonym → PDF → Context Search → Ontology Annotation

Proses 1: Baca variabel dari CellML
Proses 2: Generate synonym + cari kalimat relevan di PDF
Proses 3: Inferensi proses biologi + lookup ontologi

Jalankan semua model yang terdaftar di config.py
"""

import json
import sys
import os

# Tambahkan root folder ke path supaya import bisa jalan
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    MODEL_NAME, DATA_DIR, OUTPUT_DIR,
    CHEBI_OBO, GO_OBO, MODELS
)
from src.cellml_reader import read_cellml
from src.llm_synonym import generate_synonyms
from src.pdf_reader import extract_pdf_text
from src.sentence_splitter import split_sentences
from src.context_search import search_context
from src.ontology_lookup import load_obo_file
from src.process3 import run_process3


def process_one_model(model_info, chebi_dict, go_dict):
    """Proses satu pasang CellML + PDF."""

    cellml_file = os.path.join(DATA_DIR, model_info["cellml"])
    pdf_file = os.path.join(DATA_DIR, model_info["pdf"])
    paper_title = model_info["paper_title"]

    # Nama untuk output file
    base_name = os.path.splitext(model_info["cellml"])[0]
    output_file = os.path.join(OUTPUT_DIR, f"{base_name}_output.json")
    annotation_file = os.path.join(OUTPUT_DIR, f"{base_name}_annotations.json")

    print(f"\n{'='*60}")
    print(f"MODEL: {model_info['cellml']}")
    print(f"{'='*60}")

    # ===== PROSES 1: Baca CellML =====
    print("\n[Proses 1] Baca variabel dari CellML...")
    variables = read_cellml(cellml_file)
    print(f"  Ditemukan {len(variables)} variabel")

    if not variables:
        print("  Tidak ada variabel, skip model ini.")
        return

    # ===== PROSES 2: Generate synonym + cari kalimat di PDF =====
    print("\n[Proses 2] Generate synonym + cari kalimat di PDF...")
    text = extract_pdf_text(pdf_file)
    sentences = split_sentences(text)
    print(f"  Ditemukan {len(sentences)} kalimat dari PDF")

    process2_results = []

    for i, variable in enumerate(variables):
        print(f"  Variabel {i+1}/{len(variables)}: {variable['variable']}")

        try:
            synonyms = generate_synonyms(variable, paper_title)
        except Exception as e:
            print(f"    ERROR synonym: {e}, skip.")
            continue

        matches = search_context(sentences, synonyms)
        print(f"    Found {len(matches)} matches")

        result = {
            "component": variable["component"],
            "variable": variable["variable"],
            "unit": variable["unit"],
            "synonyms": synonyms,
            "contexts": matches
        }
        process2_results.append(result)

    # Simpan output Proses 2
    output_p2 = {
        "paper_title": paper_title,
        "pdf_file": model_info["pdf"],
        "total_variables": len(process2_results),
        "results": process2_results
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_p2, f, indent=2, ensure_ascii=False)
    print(f"\n  Output Proses 2: {output_file}")

    # ===== PROSES 3: Inferensi proses biologi + lookup ontologi =====
    print("\n[Proses 3] Inferensi proses biologi...")

    config = {
        "model_name": MODEL_NAME,
        "chebi_dict": chebi_dict,
        "go_dict": go_dict
    }

    annotations = run_process3(process2_results, config)

    with open(annotation_file, "w", encoding="utf-8") as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)
    print(f"  Output Proses 3: {annotation_file}")

    print(f"\n  Selesai: {len(process2_results)} variabel, {len(annotations)} anotasi")


def main():
    """Jalankan pipeline untuk semua model."""

    # Pastikan folder output ada
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load ontologi (sekali saja, dipakai untuk semua model)
    print("Loading CHEBI ontology...")
    chebi_dict = load_obo_file(CHEBI_OBO)
    print(f"  Loaded {len(chebi_dict)} terms")

    print("Loading GO ontology...")
    go_dict = load_obo_file(GO_OBO)
    print(f"  Loaded {len(go_dict)} terms")

    # Proses setiap model
    for i, model_info in enumerate(MODELS):
        print(f"\n\n{'#'*60}")
        print(f"# MODEL {i+1} dari {len(MODELS)}")
        print(f"{'#'*60}")

        try:
            process_one_model(model_info, chebi_dict, go_dict)
        except Exception as e:
            print(f"\n  ERROR pada model {model_info['cellml']}: {e}")
            print(f"  Skip ke model berikutnya.\n")
            continue

    # Summary
    print(f"\n\n{'='*60}")
    print("PIPELINE SELESAI!")
    print(f"{'='*60}")
    print(f"Total model diproses: {len(MODELS)}")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
