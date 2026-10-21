from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from alunos.models import Aluno
from usuarios.permissions import eh_professor, professor_required
from . import slides as servico_slides
from .forms import (MateriaForm, AulaForm, AtividadeForm, QuestaoForm, CorrecaoForm, SlidesForm,
                    AtribuirAulaForm, AtribuirAtividadeForm)
from .models import Materia, Aula, SlideAula, Atividade, Questao, Progresso, Resposta


def _aluno(request):
    return getattr(request.user, 'aluno', None)


def _professor(request):
    return getattr(request.user, 'professor', None)


def _visiveis(qs, request):
    """Professor/admin vê tudo; aluno vê só o que foi atribuído a ele."""
    if eh_professor(request.user):
        return qs
    aluno = _aluno(request)
    return qs.filter(alunos=aluno).distinct() if aluno else qs.none()


# ---------- Início ----------

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'atividades/landing.html')
    ctx = {}
    if eh_professor(request.user):
        ctx.update(
            total_alunos=Aluno.objects.count(),
            total_materias=Materia.objects.count(),
            total_atividades=Atividade.objects.count(),
            pendentes=Progresso.objects.filter(status='aguardando_correcao').select_related('aluno', 'atividade'),
        )
    elif _aluno(request):
        progressos = Progresso.objects.filter(aluno=_aluno(request))
        feitas = progressos.filter(status__in=['concluido', 'aguardando_correcao']).values_list('atividade_id', flat=True)
        ctx.update(
            a_fazer=Atividade.objects.filter(alunos=_aluno(request)).exclude(pk__in=feitas).count(),
            ultimas_notas=progressos.filter(status='concluido', pontuacao__isnull=False)
                                    .select_related('atividade').order_by('-data_conclusao')[:3],
        )
    return render(request, 'atividades/inicio.html', ctx)


# ---------- Matérias e aulas ----------

@login_required
def materias(request):
    if eh_professor(request.user):
        lista = Materia.objects.all()
    else:
        aluno = _aluno(request)
        lista = (Materia.objects.filter(Q(aulas__alunos=aluno) | Q(atividades__alunos=aluno)).distinct()
                 if aluno else Materia.objects.none())
    return render(request, 'atividades/materias.html', {'materias': lista})


@professor_required
def materia_nova(request):
    form = MateriaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        materia = form.save()
        messages.success(request, f'Matéria "{materia.nome}" criada.')
        return redirect('materia', pk=materia.pk)
    return render(request, 'atividades/formulario.html', {
        'form': form, 'titulo': 'Nova matéria', 'voltar': 'materias'})


@login_required
def materia_detalhe(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    return render(request, 'atividades/materia.html', {
        'materia': materia,
        'aulas': _visiveis(materia.aulas.all(), request),
        'atividades': _visiveis(materia.atividades.all(), request),
    })


@login_required
def aulas(request):
    lista = _visiveis(Aula.objects.select_related('materia'), request).order_by('materia__nome', 'criado_em')
    return render(request, 'atividades/aulas.html', {'aulas': lista})


@professor_required
def aula_nova(request):
    form = AulaForm(request.POST or None, initial={'materia': request.GET.get('materia')})
    if request.method == 'POST' and form.is_valid():
        aula = form.save(commit=False)
        aula.criado_por = _professor(request)
        aula.save()
        form.save_m2m()
        messages.success(request, 'Aula criada. Agora você pode enviar os slides em PDF.')
        return redirect('aula', pk=aula.pk)
    return render(request, 'atividades/formulario.html', {
        'form': form, 'titulo': 'Nova aula', 'voltar': 'aulas'})


@professor_required
def aula_atribuir(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    form = AtribuirAulaForm(request.POST if request.method == 'POST' else None, instance=aula)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Alunos da aula atualizados.')
        return redirect('aula', pk=pk)
    return render(request, 'atividades/formulario.html', {
        'form': form, 'titulo': f'Quem recebe: {aula.titulo}', 'voltar': 'aula', 'voltar_pk': pk})


@login_required
def aula_detalhe(request, pk):
    aula = get_object_or_404(_visiveis(Aula.objects.select_related('materia'), request), pk=pk)
    return render(request, 'atividades/aula.html', {
        'aula': aula, 'slides': list(aula.slides.all()), 'form_slides': SlidesForm(),
        'alunos_aula': aula.alunos.order_by('nome')})


@professor_required
def aula_slides(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    if request.method != 'POST':
        return redirect('aula', pk=pk)
    form = SlidesForm(request.POST, request.FILES)
    if not form.is_valid():
        for erro in form.errors.get('pdf', ['Envie um arquivo PDF.']):
            messages.error(request, erro)
        return redirect('aula', pk=pk)
    try:
        novos = servico_slides.enviar_pdf(aula.pk, form.cleaned_data['pdf'].read())
    except servico_slides.ErroSlides as erro:
        messages.error(request, str(erro))
        return redirect('aula', pk=pk)

    antigos = list(aula.slides.values_list('caminho', flat=True))
    with transaction.atomic():
        aula.slides.all().delete()
        SlideAula.objects.bulk_create(
            [SlideAula(aula=aula, numero=n, caminho=c, texto=t) for n, c, t in novos])
    servico_slides.apagar(antigos)
    messages.success(request, f'{len(novos)} slides enviados.')
    return redirect('aula', pk=pk)


@professor_required
def aula_slides_remover(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    if request.method == 'POST':
        antigos = list(aula.slides.values_list('caminho', flat=True))
        aula.slides.all().delete()
        servico_slides.apagar(antigos)
        messages.success(request, 'Slides removidos.')
    return redirect('aula', pk=pk)


# ---------- Atividades ----------

@login_required
def atividades(request):
    lista = _visiveis(Atividade.objects.select_related('materia'), request).order_by('materia__nome', 'titulo')
    status = {}
    aluno = _aluno(request)
    if aluno and not eh_professor(request.user):
        status = {p.atividade_id: p for p in Progresso.objects.filter(aluno=aluno)}
    for a in lista:
        a.progresso_aluno = status.get(a.pk)
    return render(request, 'atividades/atividades.html', {'atividades': lista})


@professor_required
def atividade_nova(request):
    form = AtividadeForm(request.POST or None, initial={'materia': request.GET.get('materia')})
    if request.method == 'POST' and form.is_valid():
        atividade = form.save(commit=False)
        atividade.criado_por = _professor(request)
        atividade.save()
        form.save_m2m()
        messages.success(request, 'Atividade criada. Agora adicione as questões, se quiser.')
        return redirect('atividade', pk=atividade.pk)
    return render(request, 'atividades/formulario.html', {
        'form': form, 'titulo': 'Nova atividade', 'voltar': 'atividades'})


@professor_required
def atividade_atribuir(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    form = AtribuirAtividadeForm(request.POST if request.method == 'POST' else None, instance=atividade)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Alunos da atividade atualizados.')
        return redirect('atividade', pk=pk)
    return render(request, 'atividades/formulario.html', {
        'form': form, 'titulo': f'Quem recebe: {atividade.titulo}', 'voltar': 'atividade', 'voltar_pk': pk})


@login_required
def atividade_detalhe(request, pk):
    atividade = get_object_or_404(_visiveis(Atividade.objects.select_related('materia'), request), pk=pk)
    ctx = {'atividade': atividade, 'questoes': atividade.questoes.all(),
           'alunos_atividade': atividade.alunos.order_by('nome')}
    if eh_professor(request.user):
        ctx['entregas'] = atividade.progressos.select_related('aluno').exclude(status='nao_iniciado')
        return render(request, 'atividades/atividade_professor.html', ctx)
    aluno = _aluno(request)
    if not aluno:
        return render(request, 'atividades/atividade_aluno.html', ctx)
    progresso = Progresso.objects.filter(aluno=aluno, atividade=atividade).first()
    ctx['progresso'] = progresso
    if progresso and progresso.status in ('aguardando_correcao', 'concluido'):
        ctx['respostas'] = {r.questao_id: r for r in progresso.respostas.all()}
    return render(request, 'atividades/atividade_aluno.html', ctx)


@professor_required
def questao_nova(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    form = QuestaoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        questao = form.save(commit=False)
        questao.atividade = atividade
        questao.save()
        messages.success(request, 'Questão adicionada.')
        return redirect('atividade', pk=atividade.pk)
    return render(request, 'atividades/formulario.html', {
        'form': form, 'titulo': f'Nova questão em {atividade.titulo}',
        'voltar': 'atividade', 'voltar_pk': atividade.pk})


@login_required
def responder(request, pk):
    """O aluno envia as respostas. Objetivas são corrigidas na hora; abertas vão para o professor."""
    atividade = get_object_or_404(_visiveis(Atividade.objects.all(), request), pk=pk)
    aluno = _aluno(request)
    if request.method != 'POST' or not aluno:
        return redirect('atividade', pk=pk)

    questoes = list(atividade.questoes.all())
    with transaction.atomic():
        progresso, _ = Progresso.objects.select_for_update().get_or_create(aluno=aluno, atividade=atividade)
        if progresso.status in ('aguardando_correcao', 'concluido'):
            messages.error(request, 'Você já enviou esta atividade.')
            return redirect('atividade', pk=pk)

        respostas, faltando = [], False
        for q in questoes:
            texto = request.POST.get(f'q_{q.pk}', '').strip()
            if not texto:
                faltando = True
            respostas.append((q, texto))
        if faltando:
            messages.error(request, 'Responda todas as questões antes de enviar.')
            return redirect('atividade', pk=pk)

        agora = timezone.now()
        objetivas = acertos = 0
        tem_aberta = False
        for q, texto in respostas:
            if q.tipo_resposta == 'aberta':
                tem_aberta = True
                correta = None
            else:
                objetivas += 1
                correta = texto == q.resposta_correta
                acertos += 1 if correta else 0
            Resposta.objects.update_or_create(progresso=progresso, questao=q,
                                              defaults={'texto': texto, 'correta': correta})
        progresso.enviado_em = agora
        if tem_aberta:
            progresso.status = 'aguardando_correcao'
            progresso.pontuacao = None
        else:
            progresso.status = 'concluido'
            progresso.data_conclusao = agora
            progresso.pontuacao = round(10 * acertos / objetivas, 1) if objetivas else None
        progresso.save()

    if progresso.status == 'aguardando_correcao':
        messages.success(request, 'Respostas enviadas. O professor vai corrigir as questões abertas.')
    else:
        messages.success(request, 'Respostas enviadas.')
    return redirect('atividade', pk=pk)


# ---------- Notas, alunos e correção ----------

@login_required
def notas(request):
    if eh_professor(request.user):
        progressos = Progresso.objects.exclude(status='nao_iniciado').select_related('aluno', 'atividade__materia')
        pendentes = progressos.filter(status='aguardando_correcao')
        return render(request, 'atividades/notas_professor.html', {
            'progressos': progressos.order_by('aluno__nome', 'atividade__titulo'), 'pendentes': pendentes})
    aluno = _aluno(request)
    progressos = (Progresso.objects.filter(aluno=aluno).exclude(status='nao_iniciado')
                  .select_related('atividade__materia') if aluno else [])
    return render(request, 'atividades/notas_aluno.html', {'progressos': progressos})


@professor_required
def alunos(request):
    return render(request, 'atividades/alunos.html', {'alunos': Aluno.objects.filter(usuario__isnull=False).order_by('nome')})


@professor_required
def aluno_detalhe(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    progressos = aluno.progressos.exclude(status='nao_iniciado').select_related('atividade__materia')
    return render(request, 'atividades/aluno_detalhe.html', {
        'aluno': aluno, 'progressos': progressos,
        'aulas_aluno': aluno.aulas_atribuidas.select_related('materia'),
        'atividades_aluno': aluno.atividades_atribuidas.select_related('materia')})


@professor_required
def corrigir(request, pk):
    progresso = get_object_or_404(Progresso.objects.select_related('aluno', 'atividade'), pk=pk)
    if progresso.status == 'nao_iniciado':
        return redirect('notas')
    respostas = progresso.respostas.select_related('questao')
    form = CorrecaoForm(request.POST or None, initial={'nota': progresso.pontuacao, 'comentario': progresso.comentario})
    if request.method == 'POST' and form.is_valid():
        progresso.pontuacao = float(form.cleaned_data['nota'])
        progresso.comentario = form.cleaned_data['comentario']
        progresso.status = 'concluido'
        progresso.data_conclusao = timezone.now()
        progresso.save()
        messages.success(request, f'Correção de {progresso.aluno.nome} salva.')
        return redirect('notas')
    return render(request, 'atividades/corrigir.html', {
        'progresso': progresso, 'respostas': respostas, 'form': form})
