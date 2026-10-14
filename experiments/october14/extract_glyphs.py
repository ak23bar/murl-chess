"""Optional source audit: python -m experiments.october14.extract_glyphs.

Requires pypdf. The manual transcription does not depend on this extraction.
"""
import json
import re
from pathlib import Path
from pypdf import PdfReader

root=Path('deliverables/october14/source')
pdf=PdfReader(root/'Positions2.pdf')
pages=[re.findall(r'(?m)^([1-8]) ([A-Za-z0-9]{8})$',p.extract_text()) for p in pdf.pages]
assert [len(p) for p in pages]==[32,48,48,32]
(root/'extracted_board_glyphs.json').write_text(json.dumps(pages,indent=2))
