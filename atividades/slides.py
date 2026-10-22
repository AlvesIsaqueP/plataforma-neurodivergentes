"""Converte um PDF em imagens (uma por página) e guarda no Supabase Storage."""
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

import pymupdf
from django.conf import settings

TAMANHO_MAXIMO = 20 * 1024 * 1024   # 20 MB
PAGINAS_MAXIMAS = 40


class ErroSlides(Exception):
    """Erro com mensagem amigável para mostrar ao professor."""


def configurado():
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SECRET_KEY and settings.SUPABASE_BUCKET)


def url_publica(caminho):
    base = settings.SUPABASE_URL.rstrip('/')
    return f"{base}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{urllib.parse.quote(caminho)}"


def converter_pdf(dados, dpi=110):
    """Devolve uma lista de (bytes_jpeg, texto) com uma entrada por página."""
    if len(dados) > TAMANHO_MAXIMO:
        raise ErroSlides('O PDF é maior que 20 MB.')
    try:
        doc = pymupdf.open(stream=dados, filetype='pdf')
    except Exception:
        raise ErroSlides('Não consegui abrir esse arquivo. Envie um PDF válido.')
    with doc:
        if doc.needs_pass:
            raise ErroSlides('O PDF tem senha. Envie uma versão sem senha.')
        if doc.page_count == 0:
            raise ErroSlides('O PDF não tem páginas.')
        if doc.page_count > PAGINAS_MAXIMAS:
            raise ErroSlides(f'O PDF tem {doc.page_count} páginas. O máximo é {PAGINAS_MAXIMAS}.')
        paginas = []
        for pagina in doc:
            imagem = pagina.get_pixmap(dpi=dpi).tobytes('jpeg', jpg_quality=80)
            paginas.append((imagem, pagina.get_text().strip()))
        return paginas


def _requisicao(metodo, caminho_api, corpo=None, tipo=None, tempo_limite=20):
    cabecalhos = {
        'Authorization': f'Bearer {settings.SUPABASE_SECRET_KEY}',
        'apikey': settings.SUPABASE_SECRET_KEY,
    }
    if tipo:
        cabecalhos['Content-Type'] = tipo
    req = urllib.request.Request(
        settings.SUPABASE_URL.rstrip('/') + caminho_api, data=corpo, method=metodo, headers=cabecalhos)
    with urllib.request.urlopen(req, timeout=tempo_limite) as resp:
        return resp.read()


def enviar(caminho, conteudo, tipo='image/jpeg', tempo_limite=20):
    _requisicao(
        'POST',
        f"/storage/v1/object/{settings.SUPABASE_BUCKET}/{urllib.parse.quote(caminho)}",
        conteudo, tipo, tempo_limite)


def apagar(caminhos):
    """Remove arquivos do bucket. Falhas são ignoradas (sobra de arquivo não quebra nada)."""
    if not caminhos or not configurado():
        return
    try:
        _requisicao('DELETE', f"/storage/v1/object/{settings.SUPABASE_BUCKET}",
                    json.dumps({'prefixes': list(caminhos)}).encode(), 'application/json')
    except Exception:
        pass


def enviar_pdf(aula_id, dados, prefixo='aula', dpi=110):
    """Converte o PDF e envia as páginas. Devolve lista de (numero, caminho, texto)."""
    if not configurado():
        raise ErroSlides('O armazenamento de slides ainda não está configurado no servidor.')
    paginas = converter_pdf(dados, dpi)
    pasta = f"{prefixo}-{aula_id}/{uuid.uuid4().hex[:10]}"
    itens = [(i, f"{pasta}/pagina-{i}.jpg", imagem, texto) for i, (imagem, texto) in enumerate(paginas, start=1)]
    enviados = []
    try:
        with ThreadPoolExecutor(max_workers=6) as pool:
            for item, _ in zip(itens, pool.map(lambda it: enviar(it[1], it[2]), itens)):
                enviados.append(item[1])
    except Exception:
        apagar([c for _, c, _, _ in itens])
        raise ErroSlides('Não consegui enviar os slides para o armazenamento. Tente de novo em instantes.')
    return [(n, caminho, texto) for n, caminho, _, texto in itens]
