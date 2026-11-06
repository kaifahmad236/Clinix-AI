"""
Verified Clinical Knowledge Base for ClinixAI.
Provides reference definitions, normal reference ranges, and clinical significance
for common diagnostic lab panels (CBC, CMP, Lipid Profile, Thyroid, Renal, Liver, Vitamins).
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.llm_config import get_embeddings

logger = logging.getLogger(__name__)

KB_COLLECTION_NAME = "clinixai_medical_knowledge"
_kb_vector_store: Optional[Chroma] = None

# Curated reference guidelines based on standard clinical lab references (NIH / Mayo Clinic / WHO)
CLINICAL_KNOWLEDGE_DOCS = [
    {
        "topic": "Complete Blood Count (CBC) - Hemoglobin & Hematocrit",
        "content": (
            "Complete Blood Count (CBC) Reference Guidelines:\n"
            "- Hemoglobin (Hb): Normal adult male: 13.8 - 17.2 g/dL; adult female: 12.1 - 15.1 g/dL.\n"
            "  Low Hemoglobin (<12 g/dL) indicates anemia, potential iron deficiency, blood loss, or bone marrow conditions.\n"
            "  High Hemoglobin (>17.5 g/dL) can occur in dehydration, smoking, chronic hypoxemia, or polycythemia.\n"
            "- Hematocrit (Hct): Normal male: 40.7% - 50.3%; female: 36.1% - 44.3%.\n"
            "- Red Blood Cells (RBC): Normal: 4.5 - 5.9 million/mcL (males), 4.1 - 5.1 million/mcL (females)."
        ),
    },
    {
        "topic": "Complete Blood Count (CBC) - White Blood Cells & Platelets",
        "content": (
            "CBC White Blood Cells (WBC) and Platelets Reference:\n"
            "- White Blood Cell Count (WBC): Normal: 4,500 - 11,000 cells/mcL (4.5 - 11.0 x 10^9/L).\n"
            "  High WBC (Leukocytosis, >11,000): Common in bacterial or viral infections, inflammation, severe stress, or leukemia.\n"
            "  Low WBC (Leukopenia, <4,000): Can indicate viral infections, autoimmune disorders, bone marrow suppression, or medication side effects.\n"
            "- Platelet Count: Normal: 150,000 - 450,000 /mcL (150 - 450 x 10^9/L).\n"
            "  Thrombocytopenia (<150,000): Increased risk of bruising, petechiae, or prolonged bleeding.\n"
            "  Thrombocytosis (>450,000): Reactive inflammation, iron deficiency, or essential thrombocythemia."
        ),
    },
    {
        "topic": "Lipid Profile - Cholesterol & Triglycerides",
        "content": (
            "Standard Lipid Profile Reference Ranges & Clinical Significance:\n"
            "- Total Cholesterol: Desirable: <200 mg/dL; Borderline high: 200 - 239 mg/dL; High: >=240 mg/dL.\n"
            "- LDL Cholesterol ('Bad' Cholesterol): Optimal: <100 mg/dL; Near optimal: 100 - 129 mg/dL; Borderline: 130 - 159 mg/dL; High: 160 - 189 mg/dL; Very high: >=190 mg/dL.\n"
            "  Elevated LDL is a primary risk factor for atherosclerosis and cardiovascular disease.\n"
            "- HDL Cholesterol ('Good' Cholesterol): Protective/High: >=60 mg/dL; Normal: 40 - 59 mg/dL; Low: <40 mg/dL (men), <50 mg/dL (women).\n"
            "- Triglycerides: Normal: <150 mg/dL; Borderline: 150 - 199 mg/dL; High: 200 - 499 mg/dL; Very high: >=500 mg/dL (elevates pancreatitis risk)."
        ),
    },
    {
        "topic": "Comprehensive Metabolic Panel (CMP) - Glucose & Kidney Function",
        "content": (
            "Metabolic & Renal Function Reference Guidelines:\n"
            "- Fasting Blood Glucose: Normal: 70 - 99 mg/dL; Impaired fasting glucose (Prediabetes): 100 - 125 mg/dL; Diabetes indicator: >=126 mg/dL on repeated testing.\n"
            "- HbA1c (Glycated Hemoglobin): Normal: <5.7%; Prediabetes: 5.7% - 6.4%; Diabetes: >=6.5%.\n"
            "- Serum Creatinine: Normal: 0.7 - 1.3 mg/dL (adult men), 0.6 - 1.1 mg/dL (adult women). Elevated creatinine indicates reduced glomerular filtration.\n"
            "- eGFR (Estimated Glomerular Filtration Rate): Normal: >=90 mL/min/1.73m2. Values between 60-89 indicate mildly decreased filtration; <60 for >3 months indicates Chronic Kidney Disease (CKD).\n"
            "- Blood Urea Nitrogen (BUN): Normal: 7 - 20 mg/dL. Elevated in dehydration or renal dysfunction."
        ),
    },
    {
        "topic": "Liver Function Tests (LFTs)",
        "content": (
            "Liver Panel (Hepatic Function) Reference Guidelines:\n"
            "- ALT (Alanine Aminotransferase): Normal: 7 - 56 units/L. Specific marker for hepatocellular injury (hepatitis, fatty liver, medication toxicity).\n"
            "- AST (Aspartate Aminotransferase): Normal: 10 - 40 units/L. Found in liver, heart, and skeletal muscle.\n"
            "- Alkaline Phosphatase (ALP): Normal: 44 - 147 IU/L. Elevated in biliary obstruction, gallstones, or bone conditions.\n"
            "- Total Bilirubin: Normal: 0.2 - 1.2 mg/dL. Levels above 2.5 - 3.0 mg/dL cause noticeable jaundice.\n"
            "- Albumin: Normal: 3.5 - 5.0 g/dL. Marker of hepatic synthesis and nutritional status."
        ),
    },
    {
        "topic": "Thyroid Panel (TSH, Free T3, Free T4)",
        "content": (
            "Thyroid Function Guidelines:\n"
            "- TSH (Thyroid Stimulating Hormone): Normal: 0.4 - 4.0 uIU/mL (or mIU/L).\n"
            "  High TSH (>4.5 uIU/mL): Indicates Hypothyroidism (underactive thyroid); symptoms include fatigue, weight gain, cold intolerance, dry skin.\n"
            "  Low TSH (<0.4 uIU/mL): Indicates Hyperthyroidism (overactive thyroid); symptoms include palpitations, anxiety, heat intolerance, weight loss.\n"
            "- Free T4 (Thyroxine): Normal: 0.8 - 1.8 ng/dL.\n"
            "- Free T3 (Triiodothyronine): Normal: 2.3 - 4.2 pg/mL."
        ),
    },
    {
        "topic": "Electrolytes & Vital Minerals (Sodium, Potassium, Calcium)",
        "content": (
            "Electrolyte Reference Guidelines:\n"
            "- Sodium: Normal: 135 - 145 mmol/L. Hyponatremia (<135) or Hypernatremia (>145) affects fluid balance and neurological stability.\n"
            "- Potassium: Normal: 3.5 - 5.0 mmol/L. Critical for cardiac conduction. Hypokalemia (<3.5) and Hyperkalemia (>5.0) are red-flag conditions requiring prompt evaluation for cardiac arrhythmias.\n"
            "- Serum Calcium: Normal: 8.5 - 10.2 mg/dL.\n"
            "- Vitamin D (25-Hydroxy): Deficient: <20 ng/mL; Insufficient: 20 - 29 ng/mL; Optimal: 30 - 100 ng/mL."
        ),
    },
]


def get_kb_vector_store() -> Chroma:
    """Returns singleton Chroma collection for clinical knowledge base."""
    global _kb_vector_store
    if _kb_vector_store is not None:
        return _kb_vector_store

    embeddings = get_embeddings()
    _kb_vector_store = Chroma(
        collection_name=KB_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )
    return _kb_vector_store


def ensure_knowledge_base_indexed() -> None:
    """Initializes and seeds the medical knowledge base if empty."""
    vs = get_kb_vector_store()
    try:
        count = len(vs.get()["ids"])
        if count >= len(CLINICAL_KNOWLEDGE_DOCS):
            return  # Already populated
    except Exception:
        pass

    texts = [doc["content"] for doc in CLINICAL_KNOWLEDGE_DOCS]
    metadatas = [
        {"topic": doc["topic"], "source": "Clinical Reference Guidelines"}
        for doc in CLINICAL_KNOWLEDGE_DOCS
    ]
    ids = [f"kb_{i}" for i in range(len(CLINICAL_KNOWLEDGE_DOCS))]

    vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    logger.info(f"Initialized ClinixAI Medical Knowledge Base with {len(texts)} guideline topics.")


def retrieve_medical_knowledge(query: str, top_k: int = 1) -> List[Dict[str, Any]]:
    """Retrieves relevant verified clinical guidelines for context augmentation."""
    ensure_knowledge_base_indexed()
    vs = get_kb_vector_store()

    try:
        results = vs.similarity_search_with_score(query=query, k=top_k)
    except Exception as e:
        logger.warning(f"KB retrieval failed: {e}")
        return []

    kb_chunks = []
    for doc, dist in results:
        # Distance filter to avoid irrelevant noise
        if dist is not None and dist > 1.35:
            continue

        meta = doc.metadata or {}
        topic = meta.get("topic", "Medical Guidelines")
        kb_chunks.append({
            "text": doc.page_content,
            "topic": topic,
            "citation": f"Clinical Guidelines: {topic}",
        })

    return kb_chunks

