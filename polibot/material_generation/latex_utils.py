import re

LATEX_SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "%": r"\%",
    "#": r"\#",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

# LLMs writing control-systems content often emit literal Unicode Greek/math
# glyphs (e.g. "the natural frequency ω") instead of LaTeX macros. pdflatex's
# default fontenc/inputenc setup doesn't have glyphs for these and fails with
# "Unicode character ... not set up for use with LaTeX". Map them to their
# macro equivalents so they render instead of aborting the build.
UNICODE_TO_LATEX = {
    # lowercase Greek
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\varepsilon", "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta",
    "ι": r"\iota", "κ": r"\kappa", "λ": r"\lambda", "μ": r"\mu",
    "ν": r"\nu", "ξ": r"\xi", "ο": "o", "π": r"\pi",
    "ρ": r"\rho", "σ": r"\sigma", "τ": r"\tau", "υ": r"\upsilon",
    "φ": r"\varphi", "χ": r"\chi", "ψ": r"\psi", "ω": r"\omega",
    # uppercase Greek
    "Α": "A", "Β": "B", "Γ": r"\Gamma", "Δ": r"\Delta", "∆": r"\Delta",
    "Ε": "E", "Ζ": "Z", "Η": "H", "Θ": r"\Theta", "Ι": "I", "Κ": "K",
    "Λ": r"\Lambda", "Μ": "M", "Ν": "N", "Ξ": r"\Xi", "Ο": "O",
    "Π": r"\Pi", "Ρ": "P", "Σ": r"\Sigma", "Τ": "T", "Υ": r"\Upsilon",
    "Φ": r"\Phi", "Χ": "X", "Ψ": r"\Psi", "Ω": r"\Omega",
    # common math symbols
    "×": r"\times", "÷": r"\div", "±": r"\pm", "∓": r"\mp",
    "≤": r"\leq", "≥": r"\geq", "≠": r"\neq", "≈": r"\approx",
    "∞": r"\infty", "∑": r"\sum", "∏": r"\prod", "∫": r"\int",
    "√": r"\sqrt", "∂": r"\partial", "∇": r"\nabla",
    "→": r"\rightarrow", "←": r"\leftarrow", "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow", "⇔": r"\Leftrightarrow",
    "∈": r"\in", "∉": r"\notin", "⊂": r"\subset", "∪": r"\cup", "∩": r"\cap",
    "∅": r"\emptyset", "∀": r"\forall", "∃": r"\exists",
    "°": r"^{\circ}", "·": r"\cdot", "…": r"\ldots",
}

# $$...$$ or $...$ segments are passed through untouched so LaTeX math keeps its meaning.
# Inline math ($...$) is confined to a single line and can't contain another literal $,
# so one stray/unbalanced $ can't make the match run away across newlines and swallow
# whole paragraphs of plain prose as "math" (LaTeX math mode collapses all whitespace,
# so swallowed prose loses its spaces -- e.g. "System matrix" -> "Systemmatrix").
# Display math ($$...$$) may still span multiple lines.
MATH_SEGMENT_RE = re.compile(r"(\$\$(?:[^$]|\$(?!\$))*\$\$|\$[^$\n]+\$)")


def _escape_plain_text(text: str) -> str:
    return "".join(LATEX_SPECIAL_CHARS.get(char, char) for char in text)


def _sanitize_unicode(text: str, *, in_math: bool) -> str:
    """Replace mapped Unicode chars with their LaTeX macro.

    Most macros (e.g. \\omega) are math-mode-only. Inside an existing $...$
    segment they can be inserted bare; in plain text they need their own
    $...$ wrapper or pdflatex errors with "Missing $ inserted".
    """
    out = []
    for char in text:
        macro = UNICODE_TO_LATEX.get(char)
        if macro is None:
            out.append(char)
        elif in_math or not ("\\" in macro or "^" in macro):
            out.append(macro)
        else:
            out.append(f"${macro}$")
    return "".join(out)


def latex_escape(value: object) -> str:
    """Escape LaTeX special characters, leaving $...$ / $$...$$ math segments untouched.

    Unicode-to-macro substitution runs last (after backslash-escaping) so the
    backslashes it introduces (e.g. omega -> \\omega) aren't themselves escaped.
    """
    text = str(value)
    parts = MATH_SEGMENT_RE.split(text)
    return "".join(
        _sanitize_unicode(part, in_math=True)
        if MATH_SEGMENT_RE.fullmatch(part)
        else _sanitize_unicode(_escape_plain_text(part), in_math=False)
        for part in parts
    )
