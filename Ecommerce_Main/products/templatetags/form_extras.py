# your_app/templatetags/url_tags.py
from django import template
from urllib.parse import urlencode

register = template.Library()

@register.tag(name="url_replace")
def do_url_replace(parser, token):
    """
    Usage: {% url_replace page=5 %}
    Replaces or adds GET parameters while keeping existing ones.
    """
    import re
    from django.template.defaulttags import kwarg_re

    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError("%r tag requires at least one argument" % bits[0])

    kwargs = {}
    for arg in bits[1:]:
        match = kwarg_re.match(arg)
        if not match:
            raise template.TemplateSyntaxError("Malformed arguments to url_replace tag")
        name, value = match.groups()
        kwargs[name] = parser.compile_filter(value)

    return URLReplaceNode(kwargs)


class URLReplaceNode(template.Node):
    def __init__(self, kwargs):
        self.kwargs = kwargs

    def render(self, context):
        request = context['request']
        params = request.GET.copy()

        for key, value in self.kwargs.items():
            params[key] = value.resolve(context)

        return urlencode(params)