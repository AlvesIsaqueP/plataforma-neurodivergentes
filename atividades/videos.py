"""Vídeos das aulas: link do YouTube (reproduzido dentro do site) ou arquivo próprio."""
import re
import uuid
from urllib.parse import urlparse, parse_qs

from . import slides as armazenamento

TAMANHO_MAXIMO_VIDEO = 50 * 1024 * 1024   # 50 MB (limite do plano gratuito do Supabase)
EXTENSOES = {'mp4': 'video/mp4', 'webm': 'video/webm'}


def extrair_youtube_id(texto):
    """Devolve o ID de 11 caracteres de um link do YouTube, ou '' se não for válido."""
    u = urlparse((texto or '').strip())
    host = (u.hostname or '').lower()
    for prefixo in ('www.', 'm.'):
        if host.startswith(prefixo):
            host = host[len(prefixo):]
    video_id = ''
    if host == 'youtu.be':
        video_id = u.path.strip('/').split('/')[0]
    elif host in ('youtube.com', 'youtube-nocookie.com'):
        if u.path == '/watch':
            video_id = parse_qs(u.query).get('v', [''])[0]
        else:
            partes = u.path.strip('/').split('/')
            if len(partes) > 1 and partes[0] in ('embed', 'shorts', 'live', 'v'):
                video_id = partes[1]
    return video_id if re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id) else ''


def enviar_video(aula_id, arquivo):
    """Envia o arquivo de vídeo ao armazenamento. Devolve o caminho dentro do bucket."""
    if not armazenamento.configurado():
        raise armazenamento.ErroSlides('O armazenamento ainda não está configurado no servidor.')
    nome = arquivo.name.lower()
    extensao = nome.rsplit('.', 1)[-1] if '.' in nome else ''
    if extensao not in EXTENSOES:
        raise armazenamento.ErroSlides('Envie um vídeo MP4 ou WebM.')
    if arquivo.size > TAMANHO_MAXIMO_VIDEO:
        raise armazenamento.ErroSlides('O vídeo é maior que 50 MB. Comprima o vídeo ou use um link do YouTube.')
    caminho = f"videos/aula-{aula_id}/{uuid.uuid4().hex[:10]}.{extensao}"
    try:
        armazenamento.enviar(caminho, arquivo.read(), EXTENSOES[extensao], tempo_limite=600)
    except Exception:
        raise armazenamento.ErroSlides('Não consegui enviar o vídeo. Tente de novo em instantes.')
    return caminho
