(function () {
    var lista = document.getElementById('lista-questoes');
    var modelo = document.getElementById('modelo-questao');
    var total = document.getElementById('id_q-TOTAL_FORMS');
    var adicionar = document.getElementById('adicionar-questao');
    var remover = document.getElementById('remover-questao');
    if (!lista || !modelo || !total) return;

    function numerar() {
        lista.querySelectorAll('.bloco-questao').forEach(function (bloco, i) {
            var num = bloco.querySelector('.num');
            if (num) num.textContent = i + 1;
        });
        remover.disabled = lista.querySelectorAll('.bloco-questao').length <= 1;
    }

    adicionar.addEventListener('click', function () {
        var n = parseInt(total.value, 10);
        var caixa = document.createElement('div');
        caixa.innerHTML = modelo.innerHTML.replace(/__prefix__/g, n);
        var bloco = caixa.firstElementChild;
        lista.appendChild(bloco);
        total.value = n + 1;
        if (window.iniciarBlocoQuestao) window.iniciarBlocoQuestao(bloco);
        numerar();
        var primeiro = bloco.querySelector('textarea, input:not([type=hidden])');
        if (primeiro) primeiro.focus();
    });

    remover.addEventListener('click', function () {
        var blocos = lista.querySelectorAll('.bloco-questao');
        if (blocos.length <= 1) return;
        lista.removeChild(blocos[blocos.length - 1]);
        total.value = parseInt(total.value, 10) - 1;
        numerar();
    });

    numerar();
})();
