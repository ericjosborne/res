"""49_tex2docx.py -- Word version of the paper. Run after pdflatex (needs the .aux): python python/49_tex2docx.py && cd paper && pandoc minwage_teens_pandoc.tex -f latex -t docx -o minwage_teens.docx --resource-path=.
Pre-process minwage_teens.tex for pandoc: inline tables, resolve \\ref/\\eqref from the .aux, expand natbib cites from the
bibitem labels, number sections (A-E in the appendix), plain-text table notes, figure paths, bibliography as paragraphs."""
import re, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1] / "paper"; s = (P / "minwage_teens.tex").read_text(); aux = (P / "minwage_teens.aux").read_text()
# 1. inline tables
s = re.sub(r"\\input\{tables/([^}]+)\}", lambda m: (P / "tables" / (m.group(1) + ".tex")).read_text(), s)
# 2. refs from aux
lab = {m.group(1): m.group(2) for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux)}
s = re.sub(r"\\eqref\{([^}]+)\}", lambda m: "(" + lab.get(m.group(1), "??") + ")", s)
s = re.sub(r"\\ref\{([^}]+)\}", lambda m: lab.get(m.group(1), "??"), s)
s = s.replace("~", " ")  # after refs: "Table 15", non-breaking not needed in Word
# 3. citations
bib = {m.group(2): m.group(1) for m in re.finditer(r"\\bibitem\[([^\]]+)\]\{([^}]+)\}", s)}
def lab_t(k): L = bib.get(k, k); return re.sub(r"\(", " (", L, count=1)
def lab_p(k): L = bib.get(k, k); return re.sub(r"\((\d{4}[a-z]?)\)$", r", \1", L)
s = re.sub(r"\\citet\{([^}]+)\}", lambda m: "; ".join(lab_t(k.strip()) for k in m.group(1).split(",")), s)
s = re.sub(r"\\citep\{([^}]+)\}", lambda m: "(" + "; ".join(lab_p(k.strip()) for k in m.group(1).split(",")) + ")", s)
s = re.sub(r"\\cite\{([^}]+)\}", lambda m: "(" + "; ".join(lab_p(k.strip()) for k in m.group(1).split(",")) + ")", s)
# 4. section numbering (main 1..n, appendix A..)
out, n, sub, app = [], 0, 0, None
for line in s.split("\n"):
    if line.startswith("\\appendix"): app = 0; n = 0; out.append(line); continue
    m = re.match(r"\\section\{(.*)\}(\\label\{[^}]*\})?$", line)
    if m:
        n += 1; sub = 0; num = chr(64 + n) if app is not None else str(n)
        out.append(f"\\section{{{num} {m.group(1)}}}"); continue
    m = re.match(r"\\subsection\{(.*)\}(\\label\{[^}]*\})?$", line)
    if m:
        sub += 1; num = (chr(64 + n) if app is not None else str(n)) + f".{sub}"
        out.append(f"\\subsection{{{num} {m.group(1)}}}"); continue
    out.append(line)
s = "\n".join(out)
# 5. table notes and figure minipages as plain paragraphs; captions carry their number
s = re.sub(r"\\begin\{tablenotes\}\\(?:footnotesize|scriptsize)\s*\\item\s*", "\n\n\\\\noindent\\\\small Notes: ", s); s = s.replace("\\end{tablenotes}", "")
s = re.sub(r"\\begin\{minipage\}\{\\textwidth\}\\footnotesize\s*", "\n\n\\\\noindent\\\\small Notes: ", s); s = s.replace("\\end{minipage}", "")
# numbered captions: find each table/figure env and its label number via the original label (captured before removal)
orig = (P / "minwage_teens.tex").read_text()
cap_num = {}
for env in ("table", "figure"):
    for m in re.finditer(r"\\begin\{" + env + r"\}.*?\\end\{" + env + r"\}", orig, flags=re.S):
        blk = m.group(0); c = re.search(r"\\caption\{(.*)\}", blk); l = re.search(r"\\label\{([^}]+)\}", blk)
        if c and l: cap_num[c.group(1)] = (env.capitalize(), lab.get(l.group(1), "?"))
def fix_caption(m):
    cap = m.group(1); cap_res = re.sub(r"\\ref\{([^}]+)\}", lambda x: lab.get(x.group(1), "??"), cap).replace("~", " ")
    key = next((k for k in cap_num if re.sub(r"\\ref\{([^}]+)\}", lambda x: lab.get(x.group(1), "??"), k).replace("~", " ") == cap_res), None)
    if key: env, num = cap_num[key]; return "\\caption{" + f"{env} {num}: " + cap_res + "}"
    return m.group(0)
s = re.sub(r"\\caption\{(.*)\}", fix_caption, s)
s = re.sub(r"\\label\{[^}]*\}", "", s)
# 6. figures: explicit path with extension
s = re.sub(r"\\includegraphics\[([^]]*)\]\{([^}]+)\}", lambda m: "\n\\includegraphics[" + m.group(1) + "]{figures/" + m.group(2) + ".png}\n", s)
# 7. bibliography as paragraphs
s = re.sub(r"\\begin\{thebibliography\}\{[^}]*\}", "\\\\section*{References}", s); s = s.replace("\\end{thebibliography}", "")
s = re.sub(r"\\bibitem\[[^\]]+\]\{[^}]+\}\s*", "\\\\noindent ", s)
s = re.sub(r"\\cmidrule\([^)]*\)\{[^}]*\}", "", s)  # pandoc does not know booktabs cmidrule
# wider first column for tables (pandoc takes relative widths from p{} specs)
s = re.sub(r"\\begin\{tabular\}\{l(c+)\}", lambda m: "\\begin{tabular}{p{0.30\\textwidth}" + "".join("p{%.3f\\textwidth}" % (0.68 / len(m.group(1))) for _ in m.group(1)) + "}", s)
s = re.sub(r"\$\^\{(\*+)\}\$", lambda m: "\\textsuperscript{" + m.group(1) + "}", s)  # significance stars as text superscripts
# 8. misc
s = s.replace("\\captionsetup{font=small,labelfont=bf}", "").replace("\\onehalfspacing", "").replace("\\graphicspath{{figures/}}", "")
s = s.replace("\\clearpage", "").replace("[H]", "")
(P / "minwage_teens_pandoc.tex").write_text(s); print("prepared", len(s))

if "--post" in sys.argv:  # after pandoc: widen the first column of every table (pandoc ignores p{} widths)
    import zipfile, shutil
    src = P / "minwage_teens.docx"; tmp = P / "minwage_teens_tmp.docx"
    zin = zipfile.ZipFile(src); zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/document.xml":
            x = data.decode()
            def grid(m):
                n = len(re.findall(r"<w:gridCol", m.group(1))); W = 9360; first = int(W * 0.30); rest = (W - first) // max(n - 1, 1)
                return "<w:tblGrid>" + '<w:gridCol w:w="%d"/>' % first + ''.join('<w:gridCol w:w="%d"/>' % rest for _ in range(n - 1)) + "</w:tblGrid>"
            x = re.sub(r"<w:tblGrid>(.*?)</w:tblGrid>", grid, x)
            x = x.replace('<w:tblW w:type="auto" w:w="0" />', '<w:tblW w:type="dxa" w:w="9360" />')
            data = x.encode()
        zout.writestr(item, data)
    zin.close(); zout.close(); shutil.move(tmp, src); print("post-processed", src.name)
