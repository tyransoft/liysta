from django import template
import re

register = template.Library()

@register.filter
def smart_split(value):
    if not value:
        return []
    
    return [item.strip() for item in re.split(r'[,،]\s*', value) if item.strip()]