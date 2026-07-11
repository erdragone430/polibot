from polibot.material_generation.exercises import Exercise
from polibot.material_generation.lessons import Lesson, Slide
from polibot.material_generation.pdf_renderer import render_lesson_tex, render_tex


def test_render_tex_escapes_plain_text_but_preserves_math():
    exercise = Exercise(
        statement=r"What is 50% of $x^2$ when x_1 = 10?",
        data={"x_1": 10},
        solution=r"Answer: $x^2 \times 0.5$",
    )
    tex = render_tex("Algebra Quiz", [exercise])

    assert r"50\%" in tex
    assert r"$x^2$" in tex
    assert r"x\_1" in tex
    assert r"$x^2 \times 0.5$" in tex


def test_render_lesson_tex_converts_unicode_symbols_to_latex_macros():
    lesson = Lesson(
        topic="Second-order response",
        slides=[
            Slide(
                title="Damping",
                content=r"The frequency ω_n and step ∆ shift phase φ by θ, given $ω = 2π f$.",
            ),
        ],
    )
    tex = render_lesson_tex(lesson)

    assert r"$\omega$" in tex
    assert r"$\Delta$" in tex
    assert r"$\varphi$" in tex
    assert r"$\theta$" in tex
    assert r"$\omega = 2\pi f$" in tex
    assert "ω" not in tex and "∆" not in tex and "φ" not in tex


def test_render_lesson_tex_escapes_plain_text_but_preserves_math():
    lesson = Lesson(
        topic="Recursion & You",
        slides=[
            Slide(title="Intro", content=r"Consider $f(n) = f(n-1)$, a 50% simpler case."),
            Slide(title="Base case", content="Every recursive call needs one."),
        ],
    )
    tex = render_lesson_tex(lesson)

    assert r"Recursion \& You" in tex
    assert r"$f(n) = f(n-1)$" in tex
    assert r"50\%" in tex
    assert "Base case" in tex


if __name__ == "__main__":
    test_render_tex_escapes_plain_text_but_preserves_math()
    test_render_lesson_tex_converts_unicode_symbols_to_latex_macros()
    test_render_lesson_tex_escapes_plain_text_but_preserves_math()
    print("ok")
