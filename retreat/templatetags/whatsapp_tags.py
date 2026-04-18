from django import template
import urllib.parse

register = template.Library()

@register.simple_tag
def get_whatsapp_link(telephone, message):
    if telephone:
        msg = message.replace(" ", "%20").replace("\n", "%0A")
        return f"http://wa.me/{telephone.replace('+', '')}?text={msg}"
    return "#"
