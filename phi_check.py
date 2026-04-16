import sys
import pathlib

BLOCKED_KEYWORDS = [
    'nmap', 'metasploit', 'crack', 'bruteforce', 'reverse shell', 'hydra', 'john'
]

for file in sys.argv[1:]:
    path = pathlib.Path(file)
    if path.is_file():
        try:
            text = path.read_text(errors='ignore').lower()
            for keyword in BLOCKED_KEYWORDS:
                if keyword in text:
                    print(f"❌ Commit bloqué : Le fichier '{file}' contient le mot clé interdit : '{keyword}'")
                    sys.exit(1)
        except Exception:
            continue
print("✅ Audit phi-check réussi.")
sys.exit(0)
