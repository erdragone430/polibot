import shutil
import subprocess
import tempfile
from pathlib import Path

import jinja2

from polibot.material_generation.exercises import Exercise
from polibot.material_generation.latex_utils import latex_escape
from polibot.material_generation.lessons import Lesson

TEMPLATE_DIR = Path(__file__).parent / "templates"
EXERCISES_TEMPLATE_NAME = "exercises.tex.jinja2"
LESSONS_TEMPLATE_NAME = "lessons.tex.jinja2"

# custom delimiters so Jinja's {{ }} / {% %} don't collide with LaTeX's own braces
_env = jinja2.Environment(
    block_start_string="\\BLOCK{",
    block_end_string="}",
    variable_start_string="\\VAR{",
    variable_end_string="}",
    comment_start_string="\\#{",
    comment_end_string="}",
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
)
_env.filters["latex_escape"] = latex_escape


def render_tex(title: str, exercises: list[Exercise]) -> str:
    template = _env.get_template(EXERCISES_TEMPLATE_NAME)
    return template.render(title=title, exercises=exercises)


def render_lesson_tex(lesson: Lesson) -> str:
    template = _env.get_template(LESSONS_TEMPLATE_NAME)
    return template.render(lesson=lesson)


def _compile_tex_to_pdf(tex_source: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)

    with tempfile.TemporaryDirectory() as build_dir_str:
        build_dir = Path(build_dir_str)
        tex_path = build_dir / "document.tex"
        tex_path.write_text(tex_source, encoding="utf-8")

        try:
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory",
                    str(build_dir),
                    str(tex_path),
                ],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "pdflatex not found on PATH; install a TeX distribution (e.g. TeX Live / MacTeX)."
            ) from exc

        if result.returncode != 0:
            raise RuntimeError(f"pdflatex failed:\n{result.stdout[-2000:]}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(build_dir / "document.pdf"), str(output_path))

    return output_path


def render_exercises_pdf(title: str, exercises: list[Exercise], output_path: str | Path) -> Path:
    return _compile_tex_to_pdf(render_tex(title, exercises), output_path)


def render_lesson_pdf(lesson: Lesson, output_path: str | Path) -> Path:
    return _compile_tex_to_pdf(render_lesson_tex(lesson), output_path)
