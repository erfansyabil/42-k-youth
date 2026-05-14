# Week 1

To run this project, install the required prerequisites:

## Instructions

1. Create a `.python-version` file add:

```jsx
3.14
```

1. Follow the steps [here](https://docs.astral.sh/uv/getting-started/installation/) to Install `uv`
2. Run `uv python install`, proceed with `uv init`, and `uv venv`, follow the instructions to setup virtual environment, now you can run `python` commands!
3. Use `uv add bs4 ruff pydantic` to add the BeautifulSoup, Ruff linter/formatter, and pydantic package.
    
    [uv Package Manager CRUD Cheat Sheet](https://www.notion.so/uv-Package-Manager-CRUD-Cheat-Sheet-35917c3c3ec08042b460ea9cc7838b49?pvs=21)
    
4. Create a `.gitignore` file at the root of the project, and add the following files:

```markdown
data/
src/__pycache__/
.ruff_cache/
.venv/
```
5. Extract ``0_source`` files into data folder. It should look like:

```markdown
data/0_source
```

## To run the module

1. For Module 1: Run the command `python main.py ingest`
2. For Module 2: Run the command `python main.py process`
3. For Module 3: Run the command `python main.py load`
4. For Module 4: Run the command `python main.py profiler`
5. To run all modules all at once: Run the command `python main.py all`
