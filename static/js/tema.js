(function () {
    var CHAVE = 'tema';
    var TEMAS = ['claro', 'escuro', 'contraste'];

    function temaSalvo() {
        try {
            var salvo = localStorage.getItem(CHAVE);
            return TEMAS.indexOf(salvo) !== -1 ? salvo : null;
        } catch (e) {
            return null;
        }
    }

    function temaDoSistema() {
        if (window.matchMedia('(prefers-contrast: more)').matches) return 'contraste';
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'escuro';
        return 'claro';
    }

    function salvar(tema) {
        try {
            localStorage.setItem(CHAVE, tema);
        } catch (e) {}
    }

    function aplicar(tema) {
        document.documentElement.setAttribute('data-tema', tema);
        document.querySelectorAll('.seletor-tema button').forEach(function (botao) {
            botao.setAttribute('aria-pressed', botao.dataset.tema === tema ? 'true' : 'false');
        });
    }

    var atual = temaSalvo() || temaDoSistema();
    document.documentElement.setAttribute('data-tema', atual);

    document.addEventListener('DOMContentLoaded', function () {
        aplicar(atual);
        document.querySelectorAll('.seletor-tema button').forEach(function (botao) {
            botao.addEventListener('click', function () {
                atual = botao.dataset.tema;
                aplicar(atual);
                salvar(atual);
            });
        });
    });
})();