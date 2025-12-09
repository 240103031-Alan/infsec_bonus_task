import json

def parse_advisories(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        advisories = json.load(f)

    results = []

    for adv in advisories:
        ghsa_id = adv.get("ghsa_id")
        source = adv.get("source_code_location")
        refs = adv.get("references", [])

        # vulnerabilities list: can contain 1 or 2 records
        vulns = adv.get("vulnerabilities", [])

        # default values
        vulnerable_old = None
        patched_old = None
        vulnerable_new = None
        patched_new = None
        ecosystem = None

        # Parse vulnerable ranges
        if len(vulns) >= 1:
            ecosystem = vulns[0]["package"]["ecosystem"]
            vulnerable_old = vulns[0].get("vulnerable_version_range")
            patched_old = vulns[0].get("first_patched_version")

        if len(vulns) >= 2:
            vulnerable_new = vulns[1].get("vulnerable_version_range")
            patched_new = vulns[1].get("first_patched_version")

        result_entry = {
            "ghsa_id": ghsa_id,
            "source_code_location": source,
            "ecosystem": ecosystem,

            "vulnerable_version_old": vulnerable_old,
            "patched_version_old": patched_old,

            "vulnerable_version_new": vulnerable_new,
            "patched_version_new": patched_new,

            "references": refs
        }

        results.append(result_entry)

    # save parsed output
    with open(output_path, "w", encoding="utf-8") as f_out:
        json.dump(results, f_out, indent=2, ensure_ascii=False)

    print(f"Saved parsed advisories to: {output_path}")


if __name__ == "__main__":
    parse_advisories("advisories.json", "parsed_output.json")
