from polibot.material_generation.latex_utils import latex_escape


def test_latex_escape_escapes_special_chars_outside_math():
    result = latex_escape("50% growth & profit_margin")
    assert result == r"50\% growth \& profit\_margin"


def test_latex_escape_preserves_inline_math_untouched():
    result = latex_escape(r"Solve $x^2 + 5\% = 10$ for x_1")
    assert r"$x^2 + 5\% = 10$" in result
    assert r"x\_1" in result


def test_latex_escape_stringifies_non_text_input():
    assert latex_escape(42) == "42"


def test_latex_escape_contains_stray_dollar_to_its_own_line():
    # A single unbalanced $ (e.g. currency, or a truncated equation) must not make the
    # inline-math match run away across a newline and swallow following prose as "math"
    # -- LaTeX math mode collapses whitespace, so swallowed prose loses its spaces.
    text = (
        "* $A$: System matrix: Governs the state evolution.\n"
        "* The price is $5 today\n"
        "* $C$: Output matrix: Governs the output equation."
    )
    result = latex_escape(text)
    assert "Governs the state evolution" in result
    assert "Governs the output equation" in result
    assert r"\$5 today" in result


def test_latex_escape_preserves_multiline_display_math():
    text = "$$\nH(s) = \\frac{1}{s+1}\n$$"
    result = latex_escape(text)
    assert text in result


if __name__ == "__main__":
    test_latex_escape_escapes_special_chars_outside_math()
    test_latex_escape_preserves_inline_math_untouched()
    test_latex_escape_stringifies_non_text_input()
    test_latex_escape_contains_stray_dollar_to_its_own_line()
    test_latex_escape_preserves_multiline_display_math()
    print("ok")
