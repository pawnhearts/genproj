import os
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from pathlib import Path

from benedict import benedict


@contextmanager
def chdir(path: Path | str):
    origin = Path().absolute()
    try:
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
                    name = Path(name)
                    name.parent.mkdir(parents=True, exist_ok=True)
                    with open(name, "w") as f:
                        f.write(template.format(**asdict(self)))

    def dependencies(self):
        return {}

    def env(self):
        return {}

    def environment(self):
        return {}

    def inject(self, compose, env):
        compose["services"].update(self.compose())
        env.update(self.env())
        self.write_files()
        for dependency in self.dependencies():
            dependency.inject(compose, env)


def generate():
    from templates import FastApiTemplate, VueTemplate

    services = [FastApiTemplate(name="backend", port=8080), VueTemplate(name='front', port=8081)]

    compose = benedict({"services": {}})
    env = {}

    for service in services:
        service.services = services
        service.inject(compose, env)

    with open("compose.yml", "w") as f:
        f.write(compose.to_yaml())

    with open(".env.example", "w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")


if __name__ == "__main__":
    generate()
