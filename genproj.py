import os
import shlex
import sys
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from pathlib import Path
from platform import python_version

from benedict import benedict


@contextmanager
def chdir(path: Path | str, mkdir: bool = False):
    origin = Path().absolute()
    try:
        if mkdir:
            Path(path).mkdir(parents=True, exist_ok=True)
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


@dataclass
class ServiceTemplate:
    name: str
    port: int
    command = ""
    image = None
    volumes = []
    ports = None
    services = []  # other services
    environments = []

    default_compose = {
        "env_file": [".env"],
    }

    files = {}

    def compose(self):
        if self.image:
            d = {
                "image": self.image,
                "volumes": self.volumes,
            }
        else:
            d = {
                "build": f"./{self.name}",
                "volumes": [
                    f"./{self.name}:/app",
                ]
                + self.volumes,
            }
        if self.command:
            d["command"] = self.command.format(**asdict(self))
        if self.environment():
            d["environment"] = [f"{k}={v}" for k, v in self.environment().items()]
        if self.dependencies():
            d["depends_on"] = [d.name for d in self.dependencies()]
        if self.ports:
            d["ports"] = [f"{k}:{v}" for k, v in self.ports.items()]
        else:
            d["expose"] = self.port

        return {self.name: self.default_compose | d}

    def write_files(self):
        if self.files:
            path = Path(self.name)
            path.mkdir(exist_ok=True)
            with chdir(path):
                for name, template in self.files.items():
                    name = Path(name.format(**asdict(self)))
                    name.parent.mkdir(parents=True, exist_ok=True)
                    with open(name, "w") as f:
                        f.write(
                            template.format(
                                **asdict(self),
                            )
                        )

    def dependencies(self):
        return {}

    def env(self):
        return {}

    def environment(self):
        return {}

    def inject(self, compose, env, services, environments=None):
        self.services = services
        self.environments = environments
        compose["services"].update(self.compose())
        env.update(self.env())
        self.write_files()
        for dependency in self.dependencies():
            dependency.inject(compose, env)


pyproject_toml = """[tool.poetry]
name = "{name}"
version = "0.1.0"
description = ""
authors = []
readme = "README.md"

[tool.poetry.dependencies]
python = "^{python_version}"

[tool.poetry-auto-export]
output = "requirements.txt"
without_hashes = true
without = ["dev"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""


class PoetryMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files["pyproject.toml"] = pyproject_toml.format(
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}"
        )

    def poetry_add(self, *dependencies):
        for dependency in dependencies:
            os.system(f"poetry add {shlex.quote(dependency)}")

    def poetry_export(self):
        os.system("poetry export -f requirements.txt --output requirements.txt")


def generate(output_dir="build", environments=None):
    from templates.vue import VueTemplate
    from templates.fastapi import FastApiTemplate

    with chdir(output_dir, mkdir=True):

        from templates.django import DjangoTemplate

        services = [
            DjangoTemplate(name="backend2", port=8081),
            FastApiTemplate(name="backend", port=8080),
            VueTemplate(name="front", port=8081),
        ]

        compose = benedict({"services": {}})
        env = {}

        for service in services:
            service.inject(compose, env, services, environments)

        with open("compose.yml", "w") as f:
            f.write(compose.to_yaml())

        with open(".env.example", "w") as f:
            for k, v in env.items():
                f.write(f"{k}={v}\n")


if __name__ == "__main__":
    generate()
