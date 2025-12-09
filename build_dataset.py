import os
import json
from pathlib import Path
import re

LLM_READY_DIR = "llm_ready"
OUTPUT_FILE = "dataset.json"


def extract_section(text, section_name):
    """Return text belonging to a named section."""
    pattern = rf"### {section_name} ###(.*?)(?=### |\Z)"
    match = re.search(pattern, text, flags=re.S)
    return match.group(1).strip() if match else ""


def extract_old_new_files(section_text):
    """Parse blocks like:
       ----- FILE: xxx (OLD/NEW) -----
       <content>
    """
    blocks = re.split(r"----- FILE: ", section_text)
    result = {}

    for block in blocks[1:]:
        header, content = block.split(" -----", 1)
        filename = header.strip()
        content = content.strip()
        result[filename] = content

    return result


def process_commit_file(ghsa, commit_file_path):
    content = Path(commit_file_path).read_text(encoding="utf-8")

    diff = extract_section(content, "PATCH DIFF")
    changed_summary = extract_section(content, "CHANGED FILES SUMMARY")
    old_section = extract_section(content, "OLD VERSION FILES")
    new_section = extract_section(content, "NEW VERSION FILES")

    old_files = extract_old_new_files(old_section)
    new_files = extract_old_new_files(new_section)

    return {
        "ghsa_id": ghsa,
        "commit_hash": Path(commit_file_path).stem,
        "patch_diff": diff,
        "old_code": old_files,
        "new_code": new_files,
        "portability": None,
        "reason": None
    }


def build_dataset():
    dataset = []

    for ghsa in os.listdir(LLM_READY_DIR):
        ghsa_dir = os.path.join(LLM_READY_DIR, ghsa)
        if not os.path.isdir(ghsa_dir):
            continue

        for commit_file in os.listdir(ghsa_dir):
            if not commit_file.endswith(".txt"):
                continue

            full_path = os.path.join(ghsa_dir, commit_file)
            print(f"[PROCESS] {ghsa} / {commit_file}")

            entry = process_commit_file(ghsa, full_path)
            dataset.append(entry)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"\n[DONE] Dataset saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    build_dataset()
