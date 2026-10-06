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


## Estrutura do projeto

.
├── Arquivos/
│   ├── compilar_executaveis.ps1
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

As pastas `Entradas`, `Saídas` e `Logs` mantêm apenas seus marcadores no Git. Os arquivos locais dessas pastas são ignorados pelo `.gitignore`.

## Arquivos de entrada

Os arquivos devem ser colocados na pasta `Entradas/`, mantendo seus nomes e estrutura de colunas:

Telefones de Associados Ativos e Inativos.xlsx
Nomes Agendados.xlsx
Nomes Efetivados.xlsx
Resultados.xlsx

Modelos das planilhas estão disponíveis em:

Modelos de Entrada/

## Utilização

### 1. Gerar listas de envio

Atualize na pasta `Entradas`:

```text
Telefones de Associados Ativos e Inativos.xlsx
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
| `encontrado` | Nome único na base e com pelo menos um telefone |
| `sem telefone` | Nome encontrado, mas sem telefone preenchido |
| `não encontrado` | Nome não localizado na base |
| `ambíguo` | Mais de um registro possui o mesmo nome normalizado |

Registros ambíguos não têm um associado escolhido automaticamente.

### Telefones

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

O arquivo `Resultados.xlsx` é utilizado para identificar quais notificações foram efetivamente recebidas.

Um associado é marcado como:

```text
Enviada
```

quando pelo menos um de seus telefones válidos aparece com o status `Recebido` no resultado da campanha correspondente.

Caso contrário:

```text
Não enviado
```

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
