import json

from cellml_reader import read_cellml
from llm_synonym import generate_synonyms
from pdf_reader import extract_pdf_text
from sentence_splitter import split_sentences
from context_search import search_context


# ===== Konfigurasi =====

CELLML_FILE = "hodgkin_huxley.cellml"
PDF_FILE = "hodgkin_huxley.pdf"
OUTPUT_FILE = "hodgkin_huxley_output.json"

PAPER_TITLE = (
    "A quantitative description of membrane current "
    "and its application to conduction and excitation in nerve"
)


# ===== Tahap 1: Baca CellML =====

variables = read_cellml(CELLML_FILE)
print(f"\nDitemukan {len(variables)} variabel dari CellML\n")


# ===== Tahap 2: Baca PDF dan split kalimat =====

text = extract_pdf_text(PDF_FILE)
sentences = split_sentences(text)
print(f"Ditemukan {len(sentences)} kalimat dari PDF\n")


# ===== Tahap 3: Proses setiap variabel =====

all_results = []

for i, variable in enumerate(variables):

    print(f"--- Proses variabel {i+1} dari {len(variables)}: {variable['variable']} ---")

    # Generate synonym dari LLM
    try:
        synonyms = generate_synonyms(variable, PAPER_TITLE)
    except Exception as e:
        print(f"  ERROR generate synonym: {e}")
        print(f"  Skip variabel ini.\n")
        continue

    # Cari kalimat yang cocok
    matches = search_context(sentences, synonyms)

    print(f"  Found {len(matches)} matching sentences\n")

    # Simpan hasil
    result = {
        "component": variable["component"],
        "variable": variable["variable"],
        "unit": variable["unit"],
        "synonyms": synonyms,
        "contexts": matches
    }

    all_results.append(result)


# ===== Tahap 4: Simpan ke JSON =====

output = {
    "paper_title": PAPER_TITLE,
    "pdf_file": PDF_FILE,
    "total_variables": len(all_results),
    "results": all_results
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n===== SELESAI =====")
print(f"Total variabel diproses: {len(all_results)}")
print(f"Output tersimpan di: {OUTPUT_FILE}")
