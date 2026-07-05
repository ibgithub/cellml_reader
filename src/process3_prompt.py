"""
Prompt template untuk Proses 3: Inferensi proses biologi (format baru).
"""

PROCESS3_PROMPT_TEMPLATE = """You are a **cardiac electrophysiology ontology engineer**. Your task is to infer biological processes from research paper excerpts and convert them into structured annotations following a specific JSON schema.

## Context
- **Variable**: {variable_name}
- **Unit**: {unit}
- **Component**: {component}
- **Process Type**: Ion channel current

## Supporting Sentences from Paper
{evidence_sentences}

## Your Task
Analyze the supporting sentences and infer the biological process structure. You MUST identify:

1. **ION**: The ion carrying the current (e.g., sodium, potassium, calcium)
2. **SOURCE**: Where the ions come from (intracellular or extracellular)
3. **SINK**: Where the ions go (intracellular or extracellular)
4. **MEDIATOR**: The biological entity enabling the process (e.g., voltage-gated sodium channel, potassium channel)

## Inference Rules (Follow Strictly)

| Ion Type | Current Direction | Source | Sink |
|----------|-------------------|--------|------|
| Sodium (Na+) | Inward | extracellular | intracellular |
| Potassium (K+) | Outward | intracellular | extracellular |
| Calcium (Ca2+) | Inward | extracellular | intracellular |
| Chloride (Cl-) | Varies | Check paper context | Check paper context |

## Output Format (JSON Only)
{{{{
  "name": "Human readable process name",
  "component": "{component}",
  "current_variable": "{variable_name}",
  "mediator": "descriptive_mediator_name",
  "mediator_ontology_keywords": ["GO_search_term1", "GO_search_term2"],
  "participants": [
    {{{{
      "ion": "ion_name",
      "ion_ontology_keywords": ["CHEBI_search_term1", "CHEBI_search_term2"],
      "source": "compartment_name",
      "source_ontology_keywords": ["FMA_search_term1", "FMA_search_term2"],
      "sink": "compartment_name",
      "sink_ontology_keywords": ["FMA_search_term1", "FMA_search_term2"]
    }}}}
  ]
}}}}

## Critical Rules
1. **NEVER invent ontology IDs** - ONLY provide search keywords
2. **Use exact keywords from the paper** when possible
3. **For mediators**, use descriptive names:
   - Sodium channel: "voltage-gated sodium channel"
   - Potassium channel: "voltage-gated potassium channel"
   - Calcium channel: "voltage-gated calcium channel"
   - Na/K pump: "sodium-potassium ATPase"
   - NCX: "sodium-calcium exchanger"
4. **For ions**, use standard names: "sodium", "potassium", "calcium", "chloride"
5. **For compartments**, use standard terms: "intracellular", "extracellular"
6. **Return ONLY valid JSON** - no explanatory text, no markdown formatting

Now analyze the supporting sentences and produce the annotation:"""
