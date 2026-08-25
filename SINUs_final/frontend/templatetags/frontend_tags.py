# frontend/templatetags/frontend_tags.py
from django import template

register = template.Library()


@register.filter(name='has_attr')
def has_attr(obj, attr_name):
    """Retorna True se o objeto tiver o atributo especificado."""
    return hasattr(obj, attr_name)
