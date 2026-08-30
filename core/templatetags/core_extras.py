from django import template
from core.permissoes import pode_editar as _pode_editar, pode_excluir as _pode_excluir

register = template.Library()


@register.filter
def getattribute(obj, attr):
    """Permite acessar um atributo dinamico do objeto dentro do template:
    {{ objeto|getattribute:"nome_do_campo" }}
    """
    return getattr(obj, attr, "")

@register.filter
def pode_editar(user):
    return _pode_editar(user)


@register.filter
def pode_excluir(user):
    return _pode_excluir(user)