from genproj import ServiceTemplate


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
