from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Dict benzeri yapılardan anahtar ile değer çekmek için filtre."""
    try:
        return mapping.get(key)
    except Exception:
        return None
