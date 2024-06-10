from django.core.exceptions import ValidationError


def validate_pdf_extension(value):
    if not value.name.endswith('.pdf'):
        raise ValidationError('Permitido apenas arquivos em formato PDF.')