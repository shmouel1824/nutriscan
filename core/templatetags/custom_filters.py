from django import template

register = template.Library()

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter  
def getitem(obj, key):
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return ''