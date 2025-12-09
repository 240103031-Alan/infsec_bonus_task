import os
import json
from pathlib import Path

LLM_INPUT_DIR = "llm_input"
LLM_READY_DIR = "llm_ready"

PROMPT_HEADER = """
#################### LLM PATCH ANALYSIS PACKAGE ####################

You are a security patch migration expert.

Your task:
1. Look at the OLD code (vulnerable).
2. Look at the NEW code (patched).
3. Look at the DIFF.
4. Decide whether the patch can be applied to the old version:
   - Yes      → applies cleanly
   - Maybe    → applies with adjustments
   - No       → cannot be applied
5. Provide a short explanation.

IMPORTANT:
Return ONLY JSON of this form:

{
  "portability": "Yes/Maybe/No",
  "reason": "<short explanation>"
}

####################################################################
"""


def build_llm_package():
    Path(LLM_READY_DIR).mkdir(exist_ok=True)

    # iterate advisories
    for ghsa in os.listdir(LLM_INPUT_DIR):
        ghsa_path = os.path.join(LLM_INPUT_DIR, ghsa)
        if not os.path.isdir(ghsa_path):
            continue

        print(f"\n[INFO] Processing advisory {ghsa}")
        output_adv_dir = os.path.join(LLM_READY_DIR, ghsa)
        Path(output_adv_dir).mkdir(exist_ok=True)

        # iterate commits
        for commit_hash in os.listdir(ghsa_path):
            commit_path = os.path.join(ghsa_path, commit_hash)
            if not os.path.isdir(commit_path):
                continue

            print(f"[INFO]   Processing commit {commit_hash}")

            diff_file = os.path.join(commit_path, "patch.diff")
            summary_file = os.path.join(commit_path, "summary.json")
            old_dir = os.path.join(commit_path, "old")
            new_dir = os.path.join(commit_path, "new")

            # read diff
            diff_text = open(diff_file, "r", encoding="utf-8").read()

            # read summary
            summary = json.load(open(summary_file, "r", encoding="utf-8"))

            # build text for LLM
            llm_text = PROMPT_HEADER + "\n\n"

            llm_text += "### PATCH DIFF ###\n"
            llm_text += diff_text + "\n\n"

            llm_text += "### CHANGED FILES SUMMARY ###\n"
            llm_text += json.dumps(summary, indent=2) + "\n\n"

            # old code
            llm_text += "### OLD VERSION FILES ###\n"
            for f in os.listdir(old_dir):
                fpath = os.path.join(old_dir, f)
                llm_text += f"\n----- FILE: {f} (OLD) -----\n"
                llm_text += open(fpath, "r", encoding="utf-8").read()
                llm_text += "\n\n"

            # new code
            llm_text += "### NEW VERSION FILES ###\n"
            for f in os.listdir(new_dir):
                fpath = os.path.join(new_dir, f)
                llm_text += f"\n----- FILE: {f} (NEW) -----\n"
                llm_text += open(fpath, "r", encoding="utf-8").read()
                llm_text += "\n\n"

            # save final package
            output_file = os.path.join(output_adv_dir, f"{commit_hash}.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(llm_text)

            print(f"[OK] Built LLM package: {output_file}")

    print("\n[ALL DONE] Your LLM-ready packages are inside:", LLM_READY_DIR)


if __name__ == "__main__":
    build_llm_package()
