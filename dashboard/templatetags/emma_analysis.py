from django import template
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def emma_analysis(value):
    lines = (value or '').splitlines()
    def render(line):
        t = line.strip()
        if not t:
            return mark_safe('<div class="emma-analysis-space"></div>')
        if len(t) <= 100 and (t.endswith(chr(58)) or t.startswith(("Décision synthétique", "Comparaison prix et concurrence", "Délai et coût logistique", "Concurrence sur la livraison"))):
            return format_html('<strong class="emma-analysis-heading">{}</strong>', t)
        return format_html('<span class="emma-analysis-text">{}</span>', line)
    return format_html_join('', '{}<br>', ((render(line),) for line in lines))
