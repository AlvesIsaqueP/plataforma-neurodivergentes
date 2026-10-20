from rest_framework.permissions import BasePermission, SAFE_METHODS


def eh_professor(user):
    """Professor cadastrado ou administrador."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or hasattr(user, 'professor')


class SomenteProfessor(BasePermission):
    """Só professor (ou admin) lê e escreve."""
    def has_permission(self, request, view):
        return eh_professor(request.user)


class ProfessorEscreveTodosLeem(BasePermission):
    """Logado pode ler; só professor (ou admin) cria, edita ou apaga."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return eh_professor(request.user)


def professor_required(view):
    """Decorator para páginas: exige login e perfil de professor (ou admin)."""
    from functools import wraps
    from django.contrib.auth.decorators import login_required
    from django.core.exceptions import PermissionDenied

    @wraps(view)
    @login_required
    def envolvida(request, *args, **kwargs):
        if not eh_professor(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return envolvida
