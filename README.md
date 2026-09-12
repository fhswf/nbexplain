# nbexplain

`nbexplain` provides a small IPython cell magic for didactic explanations of
Python code in Jupyter notebooks.

It is intentionally narrow: no chat sidebar, no notebook agent, no code
execution. The magic sends the cell source to an OpenAI-compatible endpoint and
renders the explanation below the cell as Markdown.

## Install

From GitHub:

```bash
uv add git+https://github.com/fhswf/nbexplain.git
```

For local development:

```bash
uv add --editable .
```

## API Endpoint And Key

By default, `nbexplain` uses the FH SWF KI Hub endpoint:

```text
https://hub.ki.fh-swf.de/v1
```

Set the notebook-specific API key in the environment before starting JupyterLab:

```bash
export JUPYTER_OPENAI_API_KEY=sk-...
jupyter lab
```

Do not store API keys in notebooks.

To use another OpenAI-compatible endpoint:

```bash
export JUPYTER_OPENAI_BASE_URL=https://example.edu/v1
jupyter lab
```

`nbexplain` checks `JUPYTER_OPENAI_API_KEY` first and falls back to
`OPENAI_API_KEY` if needed. The endpoint defaults to the FH SWF KI Hub and can
be overridden with `JUPYTER_OPENAI_BASE_URL`.

## Usage

Load the extension once in a notebook:

```python
%load_ext nbexplain
```

Then explain a code cell:

```python
%%explain
a = 0
for i in range(10):
    a += 1
```

Use a different model:

```python
%%explain --model gpt-5-mini
a = 0
for i in range(10):
    a += 1
```

Explain in English:

```python
%%explain --lang en
x = 3
y = x + 4
print(y)
```

## Configuration

Environment variables:

- `JUPYTER_OPENAI_API_KEY`: preferred OpenAI API key for notebook use
- `OPENAI_API_KEY`: fallback API key
- `JUPYTER_OPENAI_BASE_URL`: optional OpenAI-compatible base URL; defaults to `https://hub.ki.fh-swf.de/v1`
- `NBEXPLAIN_MODEL`: default model, optional; defaults to `gpt-5-nano`

Cell magic options:

- `--model MODEL`
- `--env ENV_VAR`
- `--base-url URL`
- `--lang de|en`
- `--max-output-tokens N`

## License

MIT
