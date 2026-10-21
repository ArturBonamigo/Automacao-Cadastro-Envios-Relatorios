# Automação de Cadastro, Envios e Relatórios

Automação em Python para processar planilhas de associados, normalizar nomes, cruzar cadastros com telefones, gerar listas de envio e consolidar relatórios de recebimento.

O projeto também disponibiliza executáveis para Windows, permitindo utilizar a automação sem instalar Python.

## Funcionalidades

- Leitura das bases de associados, agendados e efetivados.
- Normalização de nomes para realização dos cruzamentos.
- Identificação de registros encontrados, não encontrados, sem telefone ou ambíguos.
- Tratamento e validação de telefones brasileiros.
- Geração das listas de envio em Excel.
- Processamento dos resultados das notificações.
- Geração de relatórios por associado.
- Registro de erros em arquivos de log.
- Geração de executáveis Windows com PyInstaller.
- Validação dos executáveis em relação à execução dos scripts Python.

## Fluxo da automação

```text
Planilhas de entrada
        │
        ▼
Processamento e normalização
        │
        ▼
Cruzamento por nome
        │
        ▼
Tratamento dos telefones
        │
        ▼
Envio Agendados.xlsx
Envio Efetivados.xlsx
        │
        ▼
Resultados da campanha
        │
        ▼
Resultados Agendados.xlsx
Resultados Efetivados.xlsx
```

## Estrutura do projeto

```text
.
├── Arquivos/
│   ├── compilar_executaveis.ps1
│   ├── contatos.py
│   ├── cruzamentos.py
│   ├── execucao.py
│   ├── gerar_envios.py
│   ├── gerar_relatorios.py
│   ├── normalizacao.py
│   ├── processamento.py
│   ├── relatorios.py
│   ├── requirements-build.txt
│   └── validar_executaveis.py
│
├── Entradas/
├── Logs/
├── Modelos de Entrada/
├── Saídas/
│
├── Gerar Envios.exe
└── Gerar Relatorios.exe
```

As pastas `Entradas`, `Saídas` e `Logs` mantêm apenas seus marcadores no Git. Os arquivos locais dessas pastas são ignorados pelo `.gitignore`.

## Arquivos de entrada

Os arquivos devem ser colocados na pasta `Entradas/`, mantendo seus nomes e estrutura de colunas:

```text
Telefones de Associados 3251.xlsx
Nomes Agendados.xlsx
Nomes Efetivados.xlsx
Resultados.xlsx
```

Modelos das planilhas estão disponíveis em:

```text
Modelos de Entrada/
```

A base `Telefones de Associados 3251.xlsx` deve ter o cabeçalho na primeira linha, com as colunas `Nome Cliente`, `Telefone Celular`, `Telefone Comercial`, `Telefone Fax`, `Telefone Residencial`, `Telefone Recado` e `Email`. Não são mais ignoradas dez linhas iniciais.

> Não versione arquivos contendo dados pessoais reais. Os modelos publicados no repositório devem possuir somente dados fictícios ou devidamente anonimizados.

## Utilização

### 1. Gerar listas de envio

Atualize na pasta `Entradas`:

```text
Telefones de Associados 3251.xlsx
Nomes Agendados.xlsx
Nomes Efetivados.xlsx
```

Execute:

```text
Gerar Envios.exe
```

Serão criados em `Saídas/`:

```text
Envio Agendados.xlsx
Envio Efetivados.xlsx
```

Essa etapa não depende de `Resultados.xlsx`.

### 2. Gerar relatórios

Após obter os resultados da campanha, atualize:

```text
Entradas/Resultados.xlsx
```

Execute:

```text
Gerar Relatorios.exe
```

Dependendo dos templates encontrados no arquivo de resultados, serão gerados:

```text
Resultados Agendados.xlsx
Resultados Efetivados.xlsx
```

Arquivos existentes com o mesmo nome são substituídos. As planilhas devem estar fechadas no Excel durante a execução.

## Regras de processamento

### Normalização dos nomes

Antes do cruzamento, os nomes são normalizados:

```text
Remoção de espaços excedentes
        ↓
Remoção do prefixo numérico cadastral na base e nas listas
        ↓
Conversão para maiúsculas
        ↓
Remoção de acentos
        ↓
Comparação dos nomes
```

### Cruzamento

O cruzamento utiliza o nome normalizado.

Os registros podem receber os seguintes estados:

| Status | Significado |
|---|---|
| `encontrado` | Nome único ou cadastros de mesmo nome ligados por telefone em comum |
| `sem telefone` | Nome encontrado, mas sem telefone preenchido |
| `não encontrado` | Nome não localizado na base |
| `ambíguo` | Cadastros de mesmo nome sem ligação comprovada por telefone |

Quando há cadastros de mesmo nome com telefone válido em comum, todos os números válidos desses cadastros são reunidos, sem repetições. A comparação ignora espaços e hífens, seguindo a mesma validação de telefone dos envios. Para três ou mais registros, todos precisam estar ligados por telefones compartilhados, inclusive por uma cadeia de registros; um cadastro isolado impede a liberação do grupo. Campos vazios, `-2` e telefones inválidos não comprovam essa ligação.

Cadastros de mesmo nome sem essa ligação ficam fora das listas automáticas. Seus números válidos aparecem no relatório para revisão, com `status_envio` igual a `Não enviado` e `observacao` igual a `números diversos para nomes iguais, mandar manualmente`. O gerador de envios também informa a quantidade desses nomes na tela.

### Telefones

O valor `-2`, numérico ou em texto, é tratado como telefone vazio na leitura da base. Os demais telefones seguem as mesmas regras de tratamento e validação.

São aceitos telefones nos formatos:

```text
(DD)XXXXXXXX
(DD)XXXXXXXXX
```

Os telefones válidos são separados em:

```text
DDI | DDD | telefone
```

O DDI utilizado é:

```text
55
```

Telefones duplicados são removidos das listas finais.

## Relatórios

O arquivo `Resultados.xlsx` é utilizado para identificar quais notificações foram enviadas.

Um associado é marcado como:

```text
Enviada
```

quando pelo menos um de seus telefones válidos aparece com o status `Enviado`, `Recebido` ou `Lido` no resultado da campanha correspondente. `Enviado` conta como envio, mesmo sem confirmação de recebimento.

O relatório conta nomes únicos, enquanto a plataforma conta notificações por telefone. Um nome com dois telefones aparece uma única vez no relatório.

A coluna `telefones` reúne os números válidos encontrados na base para cada nome, com DDI e DDD, separados por `; ` e sem repetições. Inclui também telefones com falha ou sem notificação na campanha e os números de cadastros que exigem revisão manual. Nomes não encontrados ou sem telefone válido ficam com essa coluna vazia.

Caso contrário:

```text
Não enviado
```

Os relatórios possuem as colunas `nome`, `status_envio`, `telefones`, `e-mail` e `observacao`. O e-mail da base é preenchido apenas para associados com `status_envio` igual a `Não enviado`, inclusive quando não há telefone válido. Para `Enviada`, a coluna fica vazia.

O e-mail é associado pelo mesmo nome normalizado quando o cadastro é único ou os registros repetidos foram confirmados pelo telefone em comum. Nesses registros confirmados, e-mails distintos são reunidos com `; `, sem repetir endereços. Nomes não encontrados ou ambíguos ficam sem e-mail. Campos vazios ou com `NÃO INFORMADO` também ficam vazios no relatório. O e-mail não interfere no status nem nas listas de envio.

## Logs e erros

Se ocorrer uma falha, a aplicação tenta registrar os detalhes em:

```text
Logs/Gerar Envios - erro.log
Logs/Gerar Relatorios - erro.log
```

Os programas utilizam os seguintes códigos de saída:

```text
0 = sucesso
1 = erro
```

Para executar pelo terminal sem aguardar `Enter` ao final:

```powershell
.\Gerar Envios.exe --sem-pausa
.\Gerar Relatorios.exe --sem-pausa
```

## Desenvolvimento

### Tecnologias

```text
Python 3.14
pandas 3.0.6
openpyxl 3.1.5
PyInstaller 6.22.3
```

As dependências utilizadas para geração dos executáveis estão registradas em:

```text
Arquivos/requirements-build.txt
```

### Executar pelo Python

Na raiz do projeto:

```powershell
python Arquivos/gerar_envios.py
python Arquivos/gerar_relatorios.py
```

## Gerar os executáveis

No Windows, com Python instalado:

```powershell
powershell -ExecutionPolicy Bypass -File .\Arquivos\compilar_executaveis.ps1
```

O script cria o ambiente de compilação e gera:

```text
Gerar Envios.exe
Gerar Relatorios.exe
```

na raiz do projeto.

## Validar os executáveis

Para comparar as saídas dos executáveis com as produzidas diretamente pelo Python:

```powershell
python Arquivos/validar_executaveis.py
```

A validação executa cópias isoladas e verifica se os arquivos Excel produzidos são equivalentes.

## Versionamento

O projeto utiliza versionamento semântico no formato:

```text
MAJOR.MINOR.PATCH
```

Exemplos:

```text
v0.1.0 → primeira versão funcional
v0.2.0 → nova funcionalidade
v0.2.1 → correção de problema
v1.0.0 → primeira versão considerada estável
```

Os executáveis distribuídos devem preferencialmente ser publicados através de **GitHub Releases**, associados à respectiva tag da versão, em vez de permanecerem versionados diretamente junto ao código-fonte.
