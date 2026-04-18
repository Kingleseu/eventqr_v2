# retreat/templatetags/dict_extras.py
from django import template
register = template.Library()
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    # Pour liste, tuple
    if isinstance(dictionary, (list, tuple)):
        try:
            return dictionary[key]
        except (IndexError, TypeError):
            return None
    # Pour objets non compatibles
    return None



@register.filter
def split(value, delimiter=','):
    return [item.strip() for item in value.split(delimiter) if item.strip()]
