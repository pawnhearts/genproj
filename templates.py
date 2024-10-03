import os
from pathlib import Path

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


df2 = """FROM node:lts-alpine

# install simple http server for serving static content
RUN yarn global add @vue/cli

# make the 'app' folder the current working directory
WORKDIR /app

# copy both 'package.json' and 'package-lock.json' (if available)
COPY package*.json ./

# install project dependencies
RUN npm install

COPY ./{name} /app/

# build app for production with minification
RUN npm run build

EXPOSE 8080
CMD [ "http-server", "dist" ]
"""

rq = """fastapi[standard]
"""
mainpy = """from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {{"message": "Hello World"}}
"""


class PostgresTemplate(ServiceTemplate):
    image = "postgres:15.1"
    port: int = 5432
    volumes = ["postgres_data:/var/lib/postgresql/data/"]

    def env(self):
        return {
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "POSTGRES_DB": self.name,
            "POSTGRES_PORT": self.port,
        }

    # def environment(self):
    #     return self.env()


class FastApiTemplate(ServiceTemplate):
    files = {
        ".dockerignore": di,
        ".gitignore": di,
        "Dockerfile": df,
        "requirements.txt": rq,
        "main.py": mainpy,
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
                        "python3 -m venv .venv",
                        ".venv/bin/python -m pip install --upgrade pip",
                        ".venv/bin/python -m pip install -r requirements.txt",
                    ]
                )
            )


class VueTemplate(ServiceTemplate):
    command = "yarn serve -- --port {port}"

    files = {
        ".dockerignore": di,
        ".gitignore": di,
        "Dockerfile": df2,
    }

    def write_files(self):
        super().write_files()
        path = Path(self.name)
        path.mkdir(exist_ok=True)

        with chdir(self.name):
            os.system(
                "\n".join(
                    [
                        "yarn global add @vue/cli",
                        f"vue create {self.name}",
                    ]
                )
            )
