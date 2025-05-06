// Script principal para o Sistema de Gerenciamento de Matrículas

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers do Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Fechar alertas automaticamente após 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-warning):not(.alert-danger)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Ativar a aba correta com base no hash da URL
    function ativarAbaPorHash() {
        var hash = window.location.hash;
        if (hash) {
            var tabId = hash.replace('#', '');
            var tabEl = document.querySelector('button[data-bs-target="#' + tabId + '"]');
            if (tabEl) {
                var tab = new bootstrap.Tab(tabEl);
                tab.show();
            }
        }
    }
    
    // Chamar a função ao carregar a página
    ativarAbaPorHash();
    
    // Atualizar o hash da URL quando uma aba for clicada
    var tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(function(tabEl) {
        tabEl.addEventListener('shown.bs.tab', function (event) {
            var targetId = event.target.getAttribute('data-bs-target').replace('#', '');
            window.location.hash = targetId;
        });
    });
    
    // Função para confirmar ações importantes
    window.confirmarAcao = function(mensagem, callback) {
        if (confirm(mensagem)) {
            callback();
        }
    };
    
    // Função para formatar tamanho de arquivo
    window.formatarTamanho = function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    // Função para formatar data
    window.formatarData = function(dataString) {
        const data = new Date(dataString);
        return data.toLocaleDateString('pt-BR') + ' ' + data.toLocaleTimeString('pt-BR');
    };
});