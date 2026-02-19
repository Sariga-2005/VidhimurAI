import sys
import io
import json
import os
import logging
from pathlib import Path

# Fix for Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configure logging immediately
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure we can import 'app' modules as expected by empower.py
# empower.py imports like: from app.config import ...
# So we need 'backend' directory in sys.path so 'app' is resolvable.
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))

from app.services.empower import analyze_empowerment
from services.draft_generator import DraftGenerator
from services.simplifier import Simplifier
from services.translator import Translator
from services.research_ai_enhancer import ResearchAIEnhancer
from services.roadmap_generator import RoadmapGenerator

import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # 1. Define the input description
    description = (
        "I bought a mobile phone and product malfuncted before warranty period"
        
    )
    
    print(f"--- INPUT DESCRIPTION ---\n{description}\n")

    # 2. Keyword Extraction / Empowerment Analysis
    print("Running Empowerment Analysis...")
    try:
        empower_response = analyze_empowerment(description)
        # Convert Pydantic model to dict
        empower_data = empower_response.dict()
        print("Empower Analysis Complete.")
    except Exception as e:
        print(f"Error in Empowerment Analysis: {e}")
        return

    # 3. Draft Generation
    print("Generating Draft...")
    draft_gen = DraftGenerator()
    draft_result = draft_gen.generate_draft(empower_data)
    draft_text = draft_result.get("draft_text", "")
    print("Draft Generation Complete.")

    # 4. Simplification
    print("Simplifying Draft...")
    simplifier = Simplifier()
    simplified_result = simplifier.simplify(draft_text)
    print("Simplification Complete.")

    # 5. Translation
    print("Translating Draft...")
    translator = Translator()
    translated_result = translator.translate(draft_text, "Hindi")
    print("Translation Complete.")

    # 6. Research Enhancement
    print("Enhancing Research...")
    # Construct research data for enhancer
    # Enhancer expects: total_cases, top_cases, most_influential_case
    precedents = empower_data.get("precedents", [])
    research_input = {
        "total_cases": len(precedents),
        "top_cases": precedents,
        "most_influential_case": precedents[0] if precedents else None
    }
    
    enhancer = ResearchAIEnhancer()
    enhanced_result = enhancer.enhance_research(research_input)
    print("Research Enhancement Complete.")

    # 7. Roadmap Generation
    print("Generating Legal Roadmap...")
    roadmap_gen = RoadmapGenerator()
    roadmap_result = roadmap_gen.generate_roadmap(empower_data)
    print("Roadmap Generation Complete.")
    
    # 8. Write to output.txt
    output_file = "output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("INTEGRATED SYSTEM OUTPUT\n")
        f.write("==================================================\n\n")
        
        f.write(f"INPUT DESCRIPTION:\n{description}\n\n")
        
        f.write("--------------------------------------------------\n")
        f.write("1. STRUCTURED ANALYSIS (EMPOWER)\n")
        f.write("--------------------------------------------------\n")
        f.write(json.dumps(empower_data, indent=2, ensure_ascii=False))
        f.write("\n\n")
        
        f.write("--------------------------------------------------\n")
        f.write("2. GENERATED DRAFT\n")
        f.write("--------------------------------------------------\n")
        f.write(json.dumps(draft_result, indent=2, ensure_ascii=False))
        f.write("\n\n")
        
        f.write("--------------------------------------------------\n")
        f.write("3. SIMPLIFIED SUMMARY\n")
        f.write("--------------------------------------------------\n")
        f.write(json.dumps(simplified_result, indent=2, ensure_ascii=False))
        f.write("\n\n")

        f.write("--------------------------------------------------\n")
        f.write("4. TRANSLATED DRAFT (HINDI)\n")
        f.write("--------------------------------------------------\n")
        f.write(json.dumps(translated_result, indent=2, ensure_ascii=False))
        f.write("\n\n")

        f.write("--------------------------------------------------\n")
        f.write("5. ENHANCED RESEARCH INSIGHTS\n")
        f.write("--------------------------------------------------\n")
        f.write(json.dumps(enhanced_result, indent=2, ensure_ascii=False))
        f.write("\n\n")

        f.write("--------------------------------------------------\n")
        f.write("6. LEGAL ROADMAP\n")
        f.write("--------------------------------------------------\n")
        f.write(json.dumps(roadmap_result, indent=2, ensure_ascii=False))
        f.write("\n\n")

    print(f"\nAll outputs written to {output_file}")

if __name__ == "__main__":
    main()
