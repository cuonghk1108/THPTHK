import re

with open(r"C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js", "r", encoding="utf-8", errors="ignore") as f:
    js = f.read()

lines = js.split("\n")

# Find blocks of template literals assigned to innerHTML
findings = []
for idx, line in enumerate(lines):
    if ".innerHTML" in line:
        # inspect surrounding lines (up to 30 lines down)
        block = "\n".join(lines[idx:min(len(lines), idx+35)])
        # Find all ${...}
        matches = re.findall(r'\${([^}]+)}', block)
        for m in matches:
            m_clean = m.strip()
            # If it's a ternary or complex expr, check if there's raw variable access without escapeHtml
            # Ignore purely numeric or boolean checks or known safe tags
            if any(prop in m_clean for prop in ['.name', '.full_name', '.username', '.title', '.content', '.notes', '.reason', '.description', '.email', '.phone', '.feedback']):
                if 'escapeHtml' not in m_clean:
                    findings.append((idx + 1, m_clean))

print(f"Total potential unescaped items: {len(findings)}")
for f in findings[:20]:
    print(f"Line {f[0]}: ${{{f[1]}}}")
