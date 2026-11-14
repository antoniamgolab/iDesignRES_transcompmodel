import re

with open(r'C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\manuscript\main.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Take only up to \appendix (line 1247)
text = ''.join(lines[:1246])

# Remove comments
text = re.sub(r'%.*', '', text)
# Remove math environments
text = re.sub(r'\\begin\{(flalign|equation|align|tabular|table|figure)\*?\}.*?\\end\{\1\*?\}', '', text, flags=re.DOTALL)
# Remove inline math
text = re.sub(r'\$[^$]*\$', '', text)
# Remove \label, \ref, \cite, \includegraphics, \hl, \url
text = re.sub(r'\\(label|ref|cite|citep|citet|url|includegraphics|hl|footnote)\{[^}]*\}', '', text)
# Expand text formatting commands
text = re.sub(r'\\(textbf|textit|emph|textrm|textsc)\{([^}]*)\}', r'\2', text)
# Remove remaining commands
text = re.sub(r'\\[a-zA-Z]+', '', text)
# Remove braces, special chars
text = re.sub(r'[{}\\_~&@|]', ' ', text)
# Collapse whitespace
text = re.sub(r'\s+', ' ', text)

words = [w for w in text.split() if len(w) > 0 and not all(c in '.,;:!?()-[]' for c in w)]
print(f'Word count (main text, excluding appendix): {len(words)}')
