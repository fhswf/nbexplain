# nbexplain

`nbexplain` provides a small IPython cell magic for didactic explanations of
Python code in Jupyter notebooks.

It is intentionally narrow: no chat sidebar, no notebook agent, no code
execution. The magic sends the cell source to an OpenAI model and renders the
explanation below the cell as Markdown.

## Install

From GitHub:

```bash
uv add git+https://github.com/fhswf/nbexplain.git
```

For local development:

```bash
uv add --editable .
```

## API Key

Set the OpenAI API key in the environment before starting JupyterLab:

```bash
export OPENAI_API_KEY=sk-...
jupyter lab
```

Do not store API keys in notebooks.

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

- `OPENAI_API_KEY`: OpenAI API key
- `NBEXPLAIN_MODEL`: default model, optional; defaults to `gpt-5-nano`

Cell magic options:

- `--model MODEL`
- `--env ENV_VAR`
- `--lang de|en`
- `--max-output-tokens N`

## License

MIT

