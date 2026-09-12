"""IPython extension that provides a small ``%%explain`` cell magic."""

from __future__ import annotations

import argparse
import os
import shlex
from textwrap import dedent

from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.display import Markdown, display


DEFAULT_MODEL = "gpt-5-nano"
DEFAULT_ENV_VAR = "JUPYTER_OPENAI_API_KEY"
FALLBACK_ENV_VAR = "OPENAI_API_KEY"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="%%explain", add_help=False)
    parser.add_argument("--model", default=os.getenv("NBEXPLAIN_MODEL", DEFAULT_MODEL))
    parser.add_argument("--env", default=None)
    parser.add_argument("--lang", default="de")
    parser.add_argument("--max-output-tokens", type=int, default=900)
    parser.add_argument("-h", "--help", action="store_true")
    return parser


def _help_text() -> str:
    return dedent(
        f"""
        ### `%%explain`

        Explains the code in the current cell without executing it.

        **Example**

        ```python
        %%explain
        a = 0
        for i in range(10):
            a += 1
        ```

        **Options**

        - `--model MODEL`, default: `{DEFAULT_MODEL}` or `NBEXPLAIN_MODEL`
        - `--env ENV_VAR`, default: `{DEFAULT_ENV_VAR}` with `{FALLBACK_ENV_VAR}` fallback
        - `--lang de|en`, default: `de`
        - `--max-output-tokens N`, default: `900`

        The API key is read from `{DEFAULT_ENV_VAR}` by default. If that is not
        set, `{FALLBACK_ENV_VAR}` is used as a fallback. Do not store API keys in
        notebooks.
        """
    ).strip()


def _response_text(response: object) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return str(text)

    # Defensive fallback for SDK/model response shape changes.
    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            value = getattr(content, "text", None)
            if value:
                parts.append(str(value))
    return "\n".join(parts).strip()


@magics_class
class ExplainMagic(Magics):
    @cell_magic
    def explain(self, line: str, cell: str) -> None:
        parser = _parser()
        try:
            args = parser.parse_args(shlex.split(line))
        except SystemExit:
            display(Markdown(_help_text()))
            return

        if args.help:
            display(Markdown(_help_text()))
            return

        env_vars = [args.env] if args.env else [DEFAULT_ENV_VAR, FALLBACK_ENV_VAR]
        api_key = None
        for candidate in env_vars:
            value = os.getenv(candidate)
            if value:
                api_key = value
                break

        if not api_key:
            env_hint = "`, `".join(env_vars)
            display(
                Markdown(
                    f"**No API key found.** Checked: `{env_hint}`.\n\n"
                    "Start JupyterLab, for example, with:\n\n"
                    f"```bash\nexport {env_vars[0]}=sk-...\n"
                    "jupyter lab\n```"
                )
            )
            return

        code = cell.strip("\n")
        if not code.strip():
            display(Markdown("The `%%explain` cell does not contain code."))
            return

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        if args.lang.lower().startswith("en"):
            instruction = (
                "Explain Python code for learners. Be concise, didactic, and concrete. "
                "Explain execution step by step. Do not rewrite the code unless it helps "
                "explain a concept."
            )
            prompt = f"Explain this Python code step by step:\n\n```python\n{code}\n```"
        else:
            instruction = (
                "Erklaere Python-Code fuer Lernende. Sei knapp, didaktisch und konkret. "
                "Erklaere die Ausfuehrung Schritt fuer Schritt. Schreibe den Code nicht "
                "neu, ausser es hilft beim Verstaendnis."
            )
            prompt = f"Erklaere diesen Python-Code Schritt fuer Schritt:\n\n```python\n{code}\n```"

        try:
            response = client.responses.create(
                model=args.model,
                instructions=instruction,
                input=prompt,
                max_output_tokens=args.max_output_tokens,
            )
            explanation = _response_text(response)
        except Exception as exc:
            display(Markdown(f"**LLM call failed:** `{type(exc).__name__}: {exc}`"))
            return

        display(Markdown(explanation or "_The model returned no text._"))


def load_ipython_extension(ipython) -> None:
    ipython.register_magics(ExplainMagic)
