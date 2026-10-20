(function () {
    var secao = document.getElementById('slides');
    if (!secao) return;

    var palco = document.getElementById('slides-palco');
    var controles = document.getElementById('slides-controles');
    var status = document.getElementById('slides-status');
    var anterior = document.getElementById('slide-anterior');
    var proximo = document.getElementById('slide-proximo');
    var telaCheia = document.getElementById('slide-tela-cheia');
    var slides = palco.querySelectorAll('.slide');
    var total = slides.length;
    var atual = 0;

    secao.classList.add('slides-ativo');
    controles.hidden = false;

    function mostrar(i) {
        if (i < 0 || i >= total) return;
        atual = i;
        slides.forEach(function (s, n) { s.hidden = n !== atual; });
        status.textContent = 'Slide ' + (atual + 1) + ' de ' + total;
        anterior.disabled = atual === 0;
        proximo.disabled = atual === total - 1;
        var seguinte = slides[atual + 1];
        if (seguinte) {
            var img = seguinte.querySelector('img');
            if (img) img.loading = 'eager';
        }
    }

    anterior.addEventListener('click', function () { mostrar(atual - 1); });
    proximo.addEventListener('click', function () { mostrar(atual + 1); });

    telaCheia.addEventListener('click', function () {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else if (palco.requestFullscreen) {
            palco.requestFullscreen();
        }
    });

    document.addEventListener('keydown', function (e) {
        var alvo = e.target;
        var digitando = alvo && (alvo.tagName === 'INPUT' || alvo.tagName === 'TEXTAREA' || alvo.tagName === 'SELECT');
        if (digitando || e.altKey || e.ctrlKey || e.metaKey) return;
        if (e.key === 'ArrowRight') { mostrar(atual + 1); e.preventDefault(); }
        if (e.key === 'ArrowLeft') { mostrar(atual - 1); e.preventDefault(); }
    });

    mostrar(0);
})();
