from .permissions import eh_professor


def papel(request):
    """Disponibiliza 'papel' (professor/aluno) e 'nome_usuario' em todos os templates."""
    user = request.user
    if not user.is_authenticated:
        return {'papel': None}
    if eh_professor(user):
        perfil = getattr(user, 'professor', None)
        return {'papel': 'professor', 'nome_usuario': perfil.nome if perfil else user.get_username()}
    perfil = getattr(user, 'aluno', None)
    if perfil:
        return {'papel': 'aluno', 'nome_usuario': perfil.nome}
    return {'papel': None, 'nome_usuario': user.get_username()}
