from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from alunos.models import Aluno
from usuarios.permissions import eh_professor, professor_required
from . import slides as servico_slides
from . import videos as servico_videos
from .forms import (MateriaForm, AulaForm, AtividadeForm, QuestaoForm, CorrecaoForm, SlidesForm, MaterialForm,
                    AtribuirAulaForm, AtribuirAtividadeForm, VideoForm)
from .models import Materia, Aula, SlideAula, MaterialAula, Atividade, Questao, Progresso, Resposta


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
        'aula': aula, 'slides': list(aula.slides.all()), 'material': list(aula.material.all()), 'form_slides': SlidesForm(), 'form_video': VideoForm(),
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
def aula_material(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    if request.method != 'POST':
        return redirect('aula', pk=pk)
    form = MaterialForm(request.POST, request.FILES)
    if not form.is_valid():
        for erro in form.errors.get('pdf', ['Envie um arquivo PDF.']):
            messages.error(request, erro)
        return redirect('aula', pk=pk)
    try:
        novos = servico_slides.enviar_pdf(aula.pk, form.cleaned_data['pdf'].read(), prefixo='material', dpi=130)
    except servico_slides.ErroSlides as erro:
        messages.error(request, str(erro))
        return redirect('aula', pk=pk)

    antigos = list(aula.material.values_list('caminho', flat=True))
    with transaction.atomic():
        aula.material.all().delete()
        MaterialAula.objects.bulk_create(
            [MaterialAula(aula=aula, numero=n, caminho=c, texto=t) for n, c, t in novos])
    servico_slides.apagar(antigos)
    messages.success(request, f'Material de aprofundamento enviado ({len(novos)} páginas).')
    return redirect('aula', pk=pk)


@professor_required
def aula_material_remover(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    if request.method == 'POST':
        antigos = list(aula.material.values_list('caminho', flat=True))
        aula.material.all().delete()
        servico_slides.apagar(antigos)
        messages.success(request, 'Material de aprofundamento removido.')
    return redirect('aula', pk=pk)


@professor_required
def aula_video(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    if request.method != 'POST':
        return redirect('aula', pk=pk)
    form = VideoForm(request.POST, request.FILES)
    if not form.is_valid():
        for lista in form.errors.values():
            for erro in lista:
                messages.error(request, erro)
        return redirect('aula', pk=pk)
    antigo = aula.video_caminho
    if form.cleaned_data.get('youtube_id'):
        aula.youtube_id, aula.video_caminho = form.cleaned_data['youtube_id'], ''
    else:
        try:
            caminho = servico_videos.enviar_video(aula.pk, form.cleaned_data['arquivo'])
        except servico_slides.ErroSlides as erro:
            messages.error(request, str(erro))
            return redirect('aula', pk=pk)
        aula.youtube_id, aula.video_caminho = '', caminho
    aula.save()
    servico_slides.apagar([antigo] if antigo and antigo != aula.video_caminho else [])
    messages.success(request, 'Vídeo da aula salvo.')
    return redirect('aula', pk=pk)


@professor_required
def aula_video_remover(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    if request.method == 'POST':
        antigo = aula.video_caminho
        aula.youtube_id, aula.video_caminho = '', ''
        aula.save()
        servico_slides.apagar([antigo] if antigo else [])
        messages.success(request, 'Vídeo removido.')
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


QuestaoFormSet = modelformset_factory(Questao, form=QuestaoForm, extra=1, can_delete=False)


@professor_required
def atividade_nova(request):
    enviado = request.method == 'POST'
    form = AtividadeForm(request.POST if enviado else None, initial={'materia': request.GET.get('materia')})
    formset = QuestaoFormSet(request.POST if enviado else None, queryset=Questao.objects.none(), prefix='q')
    if enviado and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            atividade = form.save(commit=False)
            atividade.criado_por = _professor(request)
            atividade.save()
            form.save_m2m()
            total = 0
            for f in formset:
                if f.has_changed():
                    questao = f.save(commit=False)
                    questao.atividade = atividade
                    questao.save()
                    total += 1
        messages.success(request, f'Atividade criada com {total} questão(ões).' if total
                         else 'Atividade criada. Você pode adicionar questões quando quiser.')
        return redirect('atividade', pk=atividade.pk)
    return render(request, 'atividades/atividade_nova.html', {'form': form, 'formset': formset})


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


@professor_required
def questao_editar(request, pk):
    questao = get_object_or_404(Questao, pk=pk)
    form = QuestaoForm(request.POST if request.method == 'POST' else None, instance=questao)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Questão atualizada.')
        return redirect('atividade', pk=questao.atividade_id)
    total = questao.respostas.count()
    aviso = (f'{total} aluno(s) já responderam. Mudar alternativas, resposta certa ou valor '
             'não recalcula as notas que já foram dadas.') if total else ''
    return render(request, 'atividades/formulario.html', {
        'form': form, 'titulo': 'Editar questão', 'aviso': aviso,
        'voltar': 'atividade', 'voltar_pk': questao.atividade_id})


@login_required
def responder(request, pk):
    """O aluno envia as respostas. O quiz é corrigido na hora; questões abertas vão para o professor."""
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
            if q.afirmativas:
                marcadas = [request.POST.get(f'q_{q.pk}_{l}', '') for l, _, _ in q.afirmativas]
                texto = ','.join(marcadas) if all(m in ('V', 'F') for m in marcadas) else ''
            else:
                texto = request.POST.get(f'q_{q.pk}', '').strip()
            if not texto:
                faltando = True
            respostas.append((q, texto))
        if faltando:
            messages.error(request, 'Responda todas as questões antes de enviar.')
            return redirect('atividade', pk=pk)

        agora = timezone.now()
        tem_aberta = False
        for q, texto in respostas:
            if q.tipo_resposta == 'aberta':
                tem_aberta = True
                correta, pontos = None, None
            else:
                correta, pontos = q.pontuar(texto)
            Resposta.objects.update_or_create(progresso=progresso, questao=q,
                                              defaults={'texto': texto, 'correta': correta, 'pontos': pontos})
        progresso.enviado_em = agora
        if tem_aberta:
            progresso.status = 'aguardando_correcao'
            progresso.pontuacao = None
        else:
            progresso.status = 'concluido'
            progresso.data_conclusao = agora
            progresso.pontuacao = progresso.calcular_nota()
        progresso.save()

    if progresso.status == 'aguardando_correcao':
        messages.success(request, 'Respostas enviadas. O professor vai corrigir as questões escritas.')
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
    respostas = list(progresso.respostas.select_related('questao').order_by('questao_id'))
    abertas = [r for r in respostas if r.questao.tipo_resposta == 'aberta']
    form = CorrecaoForm(abertas, request.POST if request.method == 'POST' else None,
                        initial={'comentario': progresso.comentario})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            for r in abertas:
                r.pontos = float(form.cleaned_data[f'nota_{r.pk}'])
                r.save(update_fields=['pontos'])
            progresso.comentario = form.cleaned_data['comentario']
            progresso.pontuacao = progresso.calcular_nota()
            progresso.status = 'concluido'
            progresso.data_conclusao = progresso.data_conclusao or timezone.now()
            progresso.save()
        messages.success(request, f'Correção de {progresso.aluno.nome} salva.')
        return redirect('notas')
    campos = {f'nota_{r.pk}': form[f'nota_{r.pk}'] for r in abertas}
    for r in respostas:
        r.campo_nota = campos.get(f'nota_{r.pk}')
    objetivas = [r for r in respostas if r.questao.tipo_resposta != 'aberta']
    return render(request, 'atividades/corrigir.html', {
        'progresso': progresso, 'respostas': respostas, 'form': form,
        'pontos_quiz': sum(r.pontos_efetivos or 0 for r in objetivas),
        'total_quiz': sum(r.questao.peso for r in objetivas), 'tem_quiz': bool(objetivas)})


# ---------- Exclusões ----------

def _caminhos_slides(aulas):
    """Imagens dos slides e arquivos de vídeo das aulas, para apagar do armazenamento."""
    caminhos = list(SlideAula.objects.filter(aula__in=aulas).values_list('caminho', flat=True))
    caminhos += list(MaterialAula.objects.filter(aula__in=aulas).values_list('caminho', flat=True))
    caminhos += [c for c in aulas.values_list('video_caminho', flat=True) if c]
    return caminhos


def _confirmar(request, titulo, avisos, cancelar):
    return render(request, 'atividades/confirmar_exclusao.html', {
        'titulo': titulo, 'avisos': avisos, 'cancelar': cancelar})


@professor_required
def materia_excluir(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    if request.method == 'POST':
        caminhos = _caminhos_slides(materia.aulas.all())
        nome = materia.nome
        materia.delete()
        servico_slides.apagar(caminhos)
        messages.success(request, f'Matéria "{nome}" excluída.')
        return redirect('materias')
    avisos = [f'{materia.aulas.count()} aula(s) e {materia.atividades.count()} atividade(s) desta matéria '
              'serão apagadas junto, com as respostas e notas dos alunos.', 'Essa ação não pode ser desfeita.']
    return _confirmar(request, f'Excluir a matéria "{materia.nome}"?', avisos, reverse('materia', args=[pk]))


@professor_required
def aula_excluir(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    if request.method == 'POST':
        caminhos = _caminhos_slides(Aula.objects.filter(pk=aula.pk))
        materia_pk, titulo = aula.materia_id, aula.titulo
        aula.delete()
        servico_slides.apagar(caminhos)
        messages.success(request, f'Aula "{titulo}" excluída.')
        return redirect('materia', pk=materia_pk)
    avisos = [f'Os {aula.slides.count()} slide(s) e as {aula.material.count()} página(s) de material desta aula também serão apagados.', 'Essa ação não pode ser desfeita.']
    return _confirmar(request, f'Excluir a aula "{aula.titulo}"?', avisos, reverse('aula', args=[pk]))


@professor_required
def atividade_excluir(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    if request.method == 'POST':
        titulo = atividade.titulo
        atividade.delete()
        messages.success(request, f'Atividade "{titulo}" excluída.')
        return redirect('atividades')
    avisos = [f'{atividade.questoes.count()} questão(ões) e {atividade.progressos.count()} entrega(s) de alunos '
              'serão apagadas junto, com as notas.', 'Essa ação não pode ser desfeita.']
    return _confirmar(request, f'Excluir a atividade "{atividade.titulo}"?', avisos, reverse('atividade', args=[pk]))


@professor_required
def questao_excluir(request, pk):
    questao = get_object_or_404(Questao, pk=pk)
    atividade_pk = questao.atividade_id
    if request.method == 'POST':
        questao.delete()
        messages.success(request, 'Questão excluída.')
        return redirect('atividade', pk=atividade_pk)
    avisos = [f'{questao.respostas.count()} resposta(s) de alunos a esta questão serão apagadas.',
              'As notas já calculadas não mudam.', 'Essa ação não pode ser desfeita.']
    return _confirmar(request, 'Excluir esta questão?', avisos, reverse('atividade', args=[atividade_pk]))
