"""
Prompt template untuk Proses 3: Inferensi proses biologi.
"""

PROCESS3_PROMPT_TEMPLATE = """You are a **cardiac electrophysiology ontology engineer**. Your task is to infer biological processes from research paper excerpts and convert them into structured annotations.

## Context
- **Variable**: {variable_name}
- **Unit**: {unit}
- **Component**: {component}
- **Process Type**: Ion channel current

## Supporting Sentences from Paper
{evidence_sentences}

## Task: Infer Biological Process Structure
For this ion channel process, you MUST identify:
1. **SOURCE**: Where the ions come from (typically extracellular space for inward currents)
2. **SINK**: Where the ions go (typically intracellular space)
3. **MEDIATOR**: The biological entity enabling the process (ion channel, pump, exchanger)

## Inference Rules (Follow Strictly)
- For sodium current (i_Na): source=extracellular, sink=intracellular, mediator=sodium channel
- For potassium current (i_K): source=intracellular, sink=extracellular, mediator=potassium channel
- For leakage current (i_L): source=extracellular, sink=intracellular, mediator=leak channel

## Output Format (JSON Only)
{{{{
  "inferred_process": {{{{
    "name": "process name",
    "description": "Brief description based on paper evidence",
    "source": "source_ionname",
    "source_location": "extracellular or intracellular",
    "source_identity_keywords": ["keyword for CHEBI search"],
    "sink": "sink_ionname",
    "sink_location": "extracellular or intracellular",
    "sink_identity_keywords": ["keyword for CHEBI search"],
    "mediator": "mediator_channelname",
    "mediator_identity_keywords": ["keyword for GO search"],
    "model_property": "{component}.{variable_name}",
    "evidence_sentences": ["sentence1", "sentence2"]
  }}}}
}}}}

## Important Rules:
1. **NEVER invent ontology IDs** - ONLY provide keywords for searching
2. **If current direction ambiguous**, assume physiological direction based on ion type
3. **Use exact keywords from the paper** when possible
4. **Return ONLY valid JSON** - no explanatory text

Now analyze the supporting sentences and produce the annotation."""
