(function () {
    // Mostra ou esconde alternativas e resposta correta conforme o tipo de questão.
    function iniciar(bloco) {
        var tipo = bloco.querySelector('select[name$="tipo_resposta"]');
        if (!tipo || tipo.dataset.pronto) return;
        tipo.dataset.pronto = '1';

        function campo(nome) {
            return bloco.querySelector('[data-campo="' + nome + '"]');
        }

        function atualizar() {
            var t = tipo.value;
            ['a', 'b', 'c', 'd', 'e'].forEach(function (l) {
                var alt = campo('alt_' + l), gab = campo('gab_' + l);
                if (alt) alt.hidden = t === 'aberta';
                if (gab) gab.hidden = t !== 'verdadeiro_falso';
            });
            var correta = campo('correta');
            if (correta) correta.hidden = t !== 'multipla_escolha';
            filtrarCorreta();
        }

        // Só mostra as opções que fazem sentido para o tipo escolhido.
        function filtrarCorreta() {
            var sel = bloco.querySelector('select[name$="correta"]');
            if (!sel) return;
            var t = tipo.value;
            Array.prototype.forEach.call(sel.options, function (op) {
                var v = op.value, ok = true;
                if (v === '') ok = true;
                else {
                    ok = t === 'multipla_escolha';
                    var alt = bloco.querySelector('[name$="alt_' + v.toLowerCase() + '"]');
                    if (ok && alt && !alt.value.trim()) ok = false;
                }
                op.hidden = !ok;
                op.disabled = !ok;
            });
            var atual = sel.options[sel.selectedIndex];
            if (atual && atual.disabled) sel.value = '';
        }

        bloco.querySelectorAll('input[name*="alt_"]').forEach(function (i) {
            i.addEventListener('input', filtrarCorreta);
        });

        tipo.addEventListener('change', atualizar);
        atualizar();
    }

    window.iniciarBlocoQuestao = iniciar;

    var blocos = document.querySelectorAll('.bloco-questao');
    if (blocos.length) {
        blocos.forEach(iniciar);
    } else {
        var form = document.querySelector('select[name$="tipo_resposta"]');
        if (form) iniciar(form.closest('form'));
    }
})();
