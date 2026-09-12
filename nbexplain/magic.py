"""IPython extension that provides a small ``%%explain`` cell magic."""

from __future__ import annotations

import argparse
import json
import os
import shlex
from textwrap import dedent

from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.display import Markdown, display


DEFAULT_MODEL = "openai/gpt-5-nano"
DEFAULT_ENV_VAR = "JUPYTER_OPENAI_API_KEY"
FALLBACK_ENV_VAR = "OPENAI_API_KEY"
DEFAULT_BASE_URL = "https://hub.ki.fh-swf.de/v1"
BASE_URL_ENV_VAR = "JUPYTER_OPENAI_BASE_URL"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="%%explain", add_help=False)
    parser.add_argument("--model", default=os.getenv("NBEXPLAIN_MODEL", DEFAULT_MODEL))
    parser.add_argument("--env", default=None)
    parser.add_argument("--base-url", default=os.getenv(BASE_URL_ENV_VAR, DEFAULT_BASE_URL))
    parser.add_argument("--lang", default="de")
    parser.add_argument("--max-output-tokens", type=int, default=900)
    parser.add_argument("--debug", action="store_true")
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
        - `--base-url URL`, default: `{DEFAULT_BASE_URL}` or `{BASE_URL_ENV_VAR}`
        - `--lang de|en`, default: `de`
        - `--max-output-tokens N`, default: `900`
        - `--debug`, show the raw response when no text can be extracted

        The API key is read from `{DEFAULT_ENV_VAR}` by default. If that is not
        set, `{FALLBACK_ENV_VAR}` is used as a fallback. Do not store API keys in
        notebooks.
        """
    ).strip()


def _response_text(response: object) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return str(text)

    choices = getattr(response, "choices", None) or []
    if choices:
        message = getattr(choices[0], "message", None)
        parts = []
        for attr in ("content", "reasoning_content", "reasoning", "text"):
            value = getattr(message, attr, None)
            if isinstance(value, str) and value:
                parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        item_value = item.get("text") or item.get("content")
                    else:
                        item_value = getattr(item, "text", None) or getattr(item, "content", None)
                    if item_value:
                        parts.append(str(item_value))
        if parts:
            return "\n".join(parts).strip()

    # Defensive fallback for SDK/model response shape changes.
    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            value = getattr(content, "text", None)
            if value:
                parts.append(str(value))
    return "\n".join(parts).strip()


def _response_debug(response: object) -> str:
    if hasattr(response, "model_dump"):
        data = response.model_dump(mode="json")
    elif hasattr(response, "dict"):
        data = response.dict()
    else:
        data = repr(response)
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2, ensure_ascii=False)


def _empty_response_message(response: object, debug: bool) -> str:
    choices = getattr(response, "choices", None) or []
    details = []
    if choices:
        finish_reason = getattr(choices[0], "finish_reason", None)
        if finish_reason:
            details.append(f"- `finish_reason`: `{finish_reason}`")
        message = getattr(choices[0], "message", None)
        if message is not None:
            keys = []
            if hasattr(message, "model_dump"):
                keys = [key for key, value in message.model_dump().items() if value not in (None, "", [])]
            if keys:
                details.append(f"- message fields with values: `{', '.join(keys)}`")

    text = "**The model returned no extractable text.**"
    if details:
        text += "\n\n" + "\n".join(details)
    text += "\n\nTry another model, for example: `%%explain --model gpt-5-mini`."
    if debug:
        text += "\n\nRaw response:\n\n```json\n" + _response_debug(response) + "\n```"
    else:
        text += "\n\nRun with `%%explain --debug` to show the raw response."
    return text


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

        client = OpenAI(api_key=api_key, base_url=args.base_url)
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
            request = {
                "model": args.model,
                "messages": [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": prompt},
                ],
            }
            try:
                response = client.chat.completions.create(
                    **request,
                    max_completion_tokens=args.max_output_tokens,
                )
            except Exception as first_exc:
                if "max_completion_tokens" not in str(first_exc):
                    raise
                response = client.chat.completions.create(
                    **request,
                    max_tokens=args.max_output_tokens,
                )
            explanation = _response_text(response)
        except Exception as exc:
            display(Markdown(f"**LLM call failed:** `{type(exc).__name__}: {exc}`"))
            return

        display(Markdown(explanation or _empty_response_message(response, args.debug)))


def load_ipython_extension(ipython) -> None:
    ipython.register_magics(ExplainMagic)
