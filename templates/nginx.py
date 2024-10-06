from genproj import ServiceTemplate

conf = """
include /etc/nginx/sites/*.conf;
server {
listen 80;
include /etc/nginx/endpoints/*.conf;
}
"""

class NginxTemplate(ServiceTemplate):
    image = "nginx:latest"
    ports: {80: 80, 443: 443}
    volumes = ["./nginx/nginx.conf:/etc/nginx/nginx.conf:ro"]

    files = {'nginx.comf': conf}

    def env(self):
        return {
        }

    # def environment(self):
    #     return self.env()
