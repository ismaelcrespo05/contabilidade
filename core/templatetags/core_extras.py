from django import template

register = template.Library()


@register.filter
def getattribute(obj, attr):
    """Permite acessar um atributo dinamico do objeto dentro do template:
    {{ objeto|getattribute:"nome_do_campo" }}
    """
    return getattr(obj, attr, "")