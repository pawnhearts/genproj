import os

from genproj import ServiceTemplate, chdir

di = """
# Python
__pycache__
app.egg-info
*.pyc
.mypy_cache
.coverage
htmlcov
.venv
"""
df = """FROM python:3.12

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.4.15 /uv /bin/uv

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/app

COPY ./{name} /app/

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

CMD ["fastapi", "run", "--workers", "4", "{name}/main.py"]
"""
mainpy = """from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {{"message": "Hello World"}}
"""

rq = """fastapi[standard]
"""
pyproj = """[tool.poetry]
name = "{name}"
version = "0.1.0"
description = ""
authors = []
readme = "README.md"

[tool.poetry.dependencies]
python = "^{python_version}"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""

class FastApiTemplate(ServiceTemplate):
    files = {
        ".dockerignore": di,
        ".gitignore": di,
        "Dockerfile": df,
        # "requirements.txt": rq,
        "main.py": mainpy,
        "pyproject.toml": pyproj,
    }
    command = "uvicorn main:app --reload --host 0.0.0.0 --port {port} --proxy-headers"

    # def dependencies(self):
    #     return [PostgresTemplate(name='db', port=5432)]

    def write_files(self):
        super().write_files()
        with chdir(self.name):
            os.system(
                "\n".join(
                    [
                        # "poetry init",
                        "poetry add 'fastapi[standard]'",
                        "poetry export -f requirements.txt --output requirements.txt",
                        # "python3 -m venv .venv",
                        # ".venv/bin/python -m pip install --upgrade pip",
                        # ".venv/bin/python -m pip install -r requirements.txt",
                    ]
                )
            )
