#!/bin/bash

# Garantir que o diretório de logs exista com as permissões corretas
mkdir -p /usr/src/app/logs

# Tornar o arquivo de log acessível e garantir permissões
touch /usr/src/app/logs/petcare.json.log 2>/dev/null || true

# Se o script está sendo executado como root (como é comum no Docker),
# garantir as permissões corretas antes de mudar para o usuário appuser
if [ "$(id -u)" = "0" ]; then
    # Ajustar permissões se estivermos como root
    chown -R appuser:appuser /usr/src/app/logs 2>/dev/null || true
    chmod -R 755 /usr/src/app/logs 2>/dev/null || true
fi

# Mudar para o diretório do app
cd /usr/src/app

# Executar o comando original
exec "$@"
