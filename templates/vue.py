import os
from pathlib import Path

from genproj import ServiceTemplate, chdir

di = '''
.DS_Store
node_modules/
/dist/

# local env files
.env.local
.env.*.local

# Log files
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Editor directories and files
.idea
.vscode
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw*
'''
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


class VueTemplate(ServiceTemplate):
    """
    vue service template.
    Requires vue-cli
    """
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
