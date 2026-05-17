# repair_racebox_csv.py

from pathlib import Path

# =====================================================
# KATALOG Z DANYMI
# =====================================================

INPUT_DIR = Path("DANE")

# =====================================================
# NAPRAWA PLIKÓW RaceBox_*.csv
# =====================================================

for file in INPUT_DIR.glob("MZA_*.csv"):

    print("Fixing:", file.name)

    with open(file, "r", encoding="utf-8-sig", errors="ignore") as f:
        lines = f.readlines()

    fixed_lines = []

    # nagłówek
    fixed_lines.append(lines[0])

    # pozostałe linie
    for line in lines[1:]:

        line = line.strip()

        # usuń zewnętrzne cudzysłowy
        if line.startswith('"') and line.endswith('"'):
            line = line[1:-1]

        # zamień podwójne cudzysłowy
        line = line.replace('""', '"')

        fixed_lines.append(line + "\n")

    # zapis naprawionego pliku
    with open(file, "w", encoding="utf-8-sig") as f:
        f.writelines(fixed_lines)

print("DONE")