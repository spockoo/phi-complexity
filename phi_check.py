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
            text = path.read_text(errors="ignore").lower()
            for keyword in BLOCKED_KEYWORDS:
                if keyword in text:
                    blocked.append((file, keyword))
        except Exception:
            continue

if blocked:
    print("❌ Commit bloqué. Mots ou pratiques interdits détectés :")
    for file, word in blocked:
        print(f"  {file} -> {word}")
    sys.exit(1)

print("✅ Audit phi-check réussi.")
sys.exit(0)
