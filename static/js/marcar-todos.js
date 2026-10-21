(function () {
    document.querySelectorAll('.marcar-todos').forEach(function (botao) {
        var caixas = document.querySelectorAll('input[name="' + botao.dataset.alvo + '"]');
        function atualizar() {
            var todos = Array.prototype.every.call(caixas, function (c) { return c.checked; });
            botao.textContent = todos ? 'Desmarcar todos' : 'Marcar todos';
        }
        botao.addEventListener('click', function () {
            var todos = Array.prototype.every.call(caixas, function (c) { return c.checked; });
            caixas.forEach(function (c) { c.checked = !todos; });
            atualizar();
        });
        caixas.forEach(function (c) { c.addEventListener('change', atualizar); });
        atualizar();
    });
})();
