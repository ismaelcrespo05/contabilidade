from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def obter_papel(user):
    perfil = getattr(user, "perfil", None)
    return perfil.papel if perfil else None


def pode_editar(user):
    """Administrador, Contador e Auxiliar podem criar/editar registros."""
    return obter_papel(user) in ("ADMIN", "CONTADOR", "AUXILIAR")


def pode_excluir(user):
    """Só Administrador e Contador podem excluir registros."""
    return obter_papel(user) in ("ADMIN", "CONTADOR")


def e_administrador(user):
    """Só Administrador acessa a gestão de usuários."""
    return obter_papel(user) == "ADMIN"


def requer_edicao(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not pode_editar(request.user):
            messages.error(request, "Seu perfil (Consulta) não tem permissão para editar.")
            return redirect("painel_dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


def requer_exclusao(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not pode_excluir(request.user):
            messages.error(request, "Seu perfil não tem permissão para excluir registros.")
            return redirect("painel_dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


def requer_administrador(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not e_administrador(request.user):
            messages.error(request, "Apenas administradores podem acessar essa área.")
            return redirect("painel_dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


class RequerEdicaoMixin:
    """Para views baseadas em classe (ListView, DeleteView, etc.)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not pode_editar(request.user):
            messages.error(request, "Seu perfil (Consulta) não tem permissão para editar.")
            return redirect("painel_dashboard")
        return super().dispatch(request, *args, **kwargs)


class RequerExclusaoMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not pode_excluir(request.user):
            messages.error(request, "Seu perfil não tem permissão para excluir registros.")
            return redirect("painel_dashboard")
        return super().dispatch(request, *args, **kwargs)