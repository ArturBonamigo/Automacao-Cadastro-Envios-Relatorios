# Como usar

Mantenha esta estrutura em uma pasta com permissão de escrita:

```text
Automação Cadastro/
  Gerar Envios.exe
  Gerar Relatorios.exe
  Entradas/
    Telefones de Associados 3251.xlsx
    Nomes Agendados.xlsx
    Nomes Efetivados.xlsx
    Resultados.xlsx
  Saídas/
  Logs/
  Arquivos/
    gerar_envios.py
    gerar_relatorios.py
    execucao.py
    contatos.py
    processamento.py
    normalizacao.py
    cruzamentos.py
    relatorios.py
    compilar_executaveis.ps1
    requirements-build.txt
    validar_executaveis.py
    LEIA-ME Executaveis.md
    .venv-build/
    build/
```

1. Atualize as planilhas em `Entradas`, mantendo os nomes e as colunas atuais.
2. Dê dois cliques em `Gerar Envios.exe` para gerar `Envio Agendados.xlsx` e `Envio Efetivados.xlsx` em `Saídas`. Esta etapa não precisa de `Resultados.xlsx`.
3. Após obter os resultados das notificações, atualize `Entradas/Resultados.xlsx` e execute `Gerar Relatorios.exe`. Ele gera `Resultados Agendados.xlsx` e/ou `Resultados Efetivados.xlsx`, conforme os templates presentes na entrada.

A base `Telefones de Associados 3251.xlsx` usa o cabeçalho na primeira linha: `Nome Cliente`, `Telefone Celular`, `Telefone Comercial`, `Telefone Fax`, `Telefone Residencial`, `Telefone Recado` e `Email`. Telefones com `-2` são considerados vazios; as demais regras de telefone permanecem iguais.

O prefixo numérico cadastral é removido tanto na base quanto nas listas de nomes. Cadastros de mesmo nome são reunidos quando seus telefones válidos comprovam a ligação entre todos os registros. Todos os números válidos são aproveitados, sem repetir. Se algum cadastro ficar isolado, o grupo fica fora da lista automática e o gerador avisa na tela.

Os relatórios possuem as colunas `nome`, `status_envio`, `telefones`, `e-mail` e `observacao`. Grupos de mesmo nome sem telefone em comum permanecem como `Não enviado`, com os números para conferência e a observação `números diversos para nomes iguais, mandar manualmente`.

O e-mail é preenchido somente para `Não enviado`, quando o cadastro é único ou os registros de mesmo nome foram confirmados por telefone em comum. Endereços distintos desses registros confirmados são reunidos sem repetir. Campos vazios ou com `NÃO INFORMADO` ficam vazios. As regras de sucesso da campanha e de formato dos telefones continuam iguais.

Os arquivos de saída com o mesmo nome são substituídos. Feche-os no Excel antes de executar. Quando um template está ausente nos resultados, o relatório daquele grupo não é atualizado; um arquivo antigo pode permanecer em `Saídas`, e o programa informa isso na tela.

A janela mostra a conclusão ou o erro e aguarda Enter para fechar. Em caso de erro, os detalhes são salvos em `Logs/Gerar Envios - erro.log` ou `Logs/Gerar Relatorios - erro.log`, quando houver permissão. A pasta é criada automaticamente, se necessário. Cada programa substitui seu próprio log ao registrar um novo erro.

Para usar em outro computador Windows de arquitetura compatível, copie os dois executáveis e a pasta `Entradas`. A pasta `Saídas` é criada automaticamente. Não é necessário instalar Python nem copiar os arquivos `.py`. As planilhas de entrada permanecem externas e podem ser atualizadas a cada execução.

## Recompilar após alterar o código

Em um computador com Python 3.14 e acesso à internet, execute `Arquivos/compilar_executaveis.ps1` pelo PowerShell. Ele prepara o ambiente `Arquivos/.venv-build` e recompila os dois programas na pasta principal usando as versões de `Arquivos/requirements-build.txt`. Código, documentação, dependências de construção e testes ficam em `Arquivos`; essa pasta não é necessária para executar os `.exe`.

Para executar pelo código, use os inicializadores `Arquivos/gerar_envios.py` e `Arquivos/gerar_relatorios.py`. Eles localizam `Entradas`, `Saídas` e `Logs` na pasta principal, mesmo quando iniciados de outra pasta. `Arquivos/validar_executaveis.py` testa cópias locais sem substituir suas saídas de trabalho.

Para execução automatizada pelo terminal, o argumento `--sem-pausa` evita a espera por Enter. Código de saída 0 indica sucesso; 1 indica erro.
