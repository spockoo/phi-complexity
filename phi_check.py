import sys
import pathlib

BLOCKED_KEYWORDS = [
    "nmap",
    "metasploit",
    "crack",
    "bruteforce",
    "reverse shell",
    "hydra",
    "john",
]

blocked = []

for file in sys.argv[1:]:
    path = pathlib.Path(file)
    if path.is_file():
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                found_keyword = False
                for line in f:
                    line_lower = line.lower()
                    for keyword in BLOCKED_KEYWORDS:
                        if keyword in line_lower:
                            blocked.append((file, keyword))
                            found_keyword = True
                            break
                    if found_keyword:
                        break
        except OSError:
            continue

if blocked:
    print("❌ Commit bloqué. Mots ou pratiques interdits détectés :")
    for file, word in blocked:
        print(f"  {file} -> {word}")
    sys.exit(1)

print("✅ Audit phi-check réussi.")
sys.exit(0)
