from genproj import chdir
from .django import DjangoTemplate


class RestFrameworkTemplate(DjangoTemplate):
    def write_files(self):
        super().write_files()
        with chdir(self.name):
            self.poetry_add('django', 'djangorestframework', 'markdown', 'django-filter')
            self.poetry_export()
