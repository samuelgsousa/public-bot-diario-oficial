# Bot-diario-oficial

Uma aplicação que realiza pesquisas judiciais no DJE e TJSP, extrai dados relevantes, armazena no banco de dados e exporta informações para CSV. Criada para facilitar a extração e organização de dados judiciais.

<br>

## Funcionalidades

1. **Pesquisa automatizada** no site do DJE.
2. Extração e organização de dados diretamente da fonte oficial.
3. Exportação de resultados para arquivos **CSV** organizados por data.
4. Suporte para múltiplas contas, permitindo contornar limites de consulta diários.
5. Retomada de consultas inacabadas, garantindo que nenhuma pesquisa seja perdida.

<br>

## Instalação

> Se já estiver instalado na máquina, pode pular essa etapa.

Clone este repositório:

`git clone https://github.com/samuelgsousa/public-bot-diario-oficial`

Crie um ambiente virtual e instale as dependências:

```python
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configurar o Banco de Dados

1. Configure o banco de dados utilizando o script banco_de_dados_TJSP.sql localizado na pasta raiz do projeto.
2. Adicione as contas de acesso ao site ESAJ - TJSP na tabela `contas`, incluindo o nome de usuário e senha. Os demais campos serão preenchidos automaticamente.

>Dica: Utilize o pgAdmin para gerenciar o banco de dados com facilidade.

<br>

## Uso e Como depurar corretamente:

1 - No terminal, inicie a aplicação com o comando:

`streamlit run app/main.py`

2 - Na aba "Run and Debug" do Streamlit, selecione "Attach to Streamlit" para monitorar a execução e diagnosticar problemas.

> Obs: ainda não foi configurada uma forma de rodar a aplicação sem o modo de depuração

3 - Na interface exibida, forneça os dados solicitados e escolha uma das opções:

- Buscar no DJE - TJSP: Inicia uma nova consulta utilizando as palavras chaves fornecidas

- Continuar última execução: Essa opção só ficará disponível caso houver alguma consulta que não foi finalizada na última execução

> Dica: a palavra chave recomendada no momento é **expeça-se o ofício requisitório OU defiro a expedição do ofício requisitório**

<br>

# TJSP - Etapas 

> Video de demonstração em Desenvolvimento

<br>

## Resultados 

Quando a aplicação estiver na etapa de processar os precatórios, é possível acompanhar os resultados de duas formas

### 1. Tabela `req_pagamentos` no Banco de Dados
Utilize o pgAdmin para visualizar a tabela `req_pagamentos`, que contém todas as requisições de pagamento válidas extraídas pela aplicação.

### 2. Arquivo CSV Exportado
Os resultados também são salvos em `processos > TJSP`, em arquivos CSV com o formato `processos_YYYY-MM-DD.csv`, onde YYYY-MM-DD representa a data atual (ex: `processos_2024-12-18 - TJSP Diário.csv`).

>Nota: Um arquivo consolidado chamado `processos_geral.csv` é atualizado continuamente com todas as requisições processadas.

<br>

## Problemas Conhecidos
- Limite de consultas excedido: Este erro ocorre geralmente após atingir o limite de 1.000 consultas diárias utilizando a mesma conta no ESAJ. Quando isso acontece, a aplicação alterna automaticamente para outra conta disponível, enquanto marca a conta que excedeu o limite como indisponível até o próximo dia.
- Sessão expirada: A aplicação reinicia automaticamente a sessão e continua o processamento.

<br>


# Estrutura do banco de dados

O banco de dados foi criado não só para armazenar as informações de forma mais segura, como também garantir que a aplicação possa retomar de onde parou caso seja encerrada antes da consulta ser concluída. 
Ele foi criado utilizando constraints para evitar precatórios e processos duplicados nas tabelas `req_pagamentos` e `dje_process_numbers` respectivamente. Então não se preocupe com dados duplicados
Abaixo segue a explicação de cada tabela.

<br>

## contas

A tabela contas contém todas as contas que serão usadas para realizar consultas no site do ESAJ.

<br>

### Exemplo

| id       | usuario       | senha    | limite_atingido | data_limite |
|----------|---------------|----------|-----------------|-------------|
|      1   | 12345678912   | exemplo1 | true            | 2025-01-06  |
|      2   | 21987654321   | senha23  | false           | null        |

<br>

### Explicação

| coluna           | tipo      | função |
|------------------|-----------|--------|
| id               | INT       | Auto-explicativo |
| usuario          | varchar   | usuário para logar no ESAJ (geralmente o CPF) |
| senha            | varchar   | senha para logar no ESAJ |
| limite_atingido  | boolean   | determina se aquela conta já atingiu o limite diário. Por padrão é **false** |
| data_limite      | date      | Assim que a conta atinge o limite diário, esse campo armazena a data atual. Quando a aplicação for executada novamente, se a `data_limite` for menor que a data no momento da execução, esse campo se tornará nulo e o campo `limite_atingido` voltará a ser **false**|

<br>

## historico_exec

Essa tabela é responsável por armazenar cada execução. Bem como seu status e também o status de [paginação](#)

### Exemplo

| id  | palavra_chave  | prec_encontrados  | data_inicio          | data_fim             | status           | pagina_atual  | mensagens_erro  | data_exec  | paginacao_conc  |
|-----|----------------|-------------------|----------------------|----------------------|------------------|---------------|-----------------|------------|-----------------|
| 58  | teste          | null              | 2024-12-16 00:00:00  |	2024-12-16 00:00:00  | interrompido 	|   15	        |	null          | 2024-12-16 | false           |

<br>

### Explicação

| coluna           | tipo      | função |
|------------------|-----------|--------|
| id               | INT       | Auto-explicativo |
| palavra_chave    | TEXT      | Palavra chave usada para buscar processos no DJE |
| prec_encontrados | INT       | *Não utilizado* - Número total de precatórios encontrados |
| data_inicio      | timestamp | Range de início da busca |
| data_fim         | timestamp | Range limite da busca |
| status           | [status_tipo](#status_tipo) | **TYPE** novo criado por mim. **DEFAULT** - não concluido. Mais detalhes abaixo |
| pagina_atual     | INT       | Quando a aplicação inicia a busca, o site do DJE separa os precatórios em páginas de 10 em 10, resultando em dezenas ou centenas de páginas. Este campo sempre armazena qual página está sendo analisada no momento. É utilizado principalmente em casos de interrupções, para continuar a partir da última página |
| mensagens_erro   | TEXT      | *Não utilizado* |
| data_exec        | timestamp | Data em que a execução foi iniciada pela primeira vez |
| paginacao_conc   | boolean   | Serve para verificar se a extração de processos no DJE foi concluída. Usado em caso de interrupções, para pular essa etapa e ir direto para a etapa de processamento dos precatórios no ESAJ |

<br>

### status_tipo

Type com 3 valores, usado para classificar o status de cada execução

| status        | significado |
|---------------|-------------|
| concluído     | Todo o processo de busca, extração e exportação foi concluído com sucesso |
| não concluido | A consulta não foi finalizada. Se uma consulta estiver com esse status quando a aplicação for iniciada, será exibido um botão que permite continuar de onde parou. Só é possível existir uma execução com esse status por vez |
| interrompido  | Ocorre quando uma consulta não é concluída, e ao invés de retomar, o usuário inicia outra. Não será possível retomar ela novamente, e não é recomendado alterar esse status manualmente para tentar de novo, pois os processos pendentes referentes a ela já foram **excluídos** | 

<br>

## dje_process_numbers

Tabela **TEMPORÁRIA** responsável por armazenar todos os processos extraídos na primeira etapa de busca avançada no DJE. Toda vez que uma nova consulta é iniciada essa tabela será limpa.
Uma constraint garante que cod_processo seja único. Se um valor que já existe for adicionado novamente, o próprio banco de dados irá ignorar. Isso evita que o script analise um mesmo processo mais de uma vez.

### Exemplo

| id  | cod_processo              | range_ini           | range_end           | num_req | last_req | processado |
|-----|---------------------------|---------------------|---------------------|---------|----------|------------|
|1862 | 1002616-05.2019.8.26.0053 | 2025-01-07 00:00:00 | 2025-01-07 00:00:00 |	0       | 1 	   |   true     |
|1863 | 1015686-05.2024.8.26.0053 | 2025-01-07 00:00:00 | 2025-01-07 00:00:00 |	25      | 17 	   |   false    |
|1864 | 1002317-05.2022.8.26.0053 | 2025-01-07 00:00:00 | 2025-01-07 00:00:00 |	0       | 1 	   |   false    |

<br>

### Explicação

| coluna           | tipo           | função |
|------------------|----------------|--------|
| id               | INT            | Auto-explicativo |
| cod_processo     | varchar UNIQUE | código do processo. Uma constraint  |
| range_ini        | timestamp      | *Não utilizado* |
| range_end        | timestamp      | *Não utilizado* |
| num_req          | INT            | Número de precatórios que aquele processo possui |
| last_req         | INT            | Sempre que um precatório do processo for completamente analisado, esse valor será atualizado. Em casos de interrupção, o script retomará a partir desse número, ao invés de começar tudo novo. Obs: esse número **NÃO É** o número do precatório em sí, apenas um índice usado exclusivamente para essa finalidade|
| processado       | Boolean        | Determina se o processo já foi completamente analisado. Por padrão é **false**|

> É comum que processos que não tenham precatórios ou não possam ser acessados tenham **processado** como **true**, **num_req** como **0**, e **last_req** como **1**

<br>

## req_pagamentos

Tabela que contém todos os precatórios com valor acima do mínimo estipulado.
Uma constraint garante que a combinação de `seq` e `cod_processo` seja única. Garantindo que não hajam precatórios duplicados

<br>

### Exemplo

| id  | nome_req                   | cpf_req        | cod_processo               | seq  | advogado                              | valor_processo  | data doc   | data_emissão_termo_dec  | ent_devedora                   | princ_liq | link                     | exportado |
|-----|----------------------------|----------------|----------------------------|------|---------------------------------------|-----------------|------------|-------------------------|--------------------------------|-----------|--------------------------|-----------|
| 360 | Brat junior XCX da Silva   | 365.365.365-XX | 0017399-48.2021.8.26.0053  |   1  | Stephanie Joanne Angelina Germanotta 	| 360365.69	      | 2023-08-29 | 2023-08-29              | SPPREV - SÃO PAULO PREVIDÊNCIA | 21613.77  | https://esaj.tjsp.jus.br | true      |
| 361 | Elizabeth Grant            | XXX.XXX.XXX-XX | 0017399-48.2021.8.26.0053  |   2  | Stephanie Joanne Angelina Germanotta 	| 290375.75	      | 2023-08-29 | 2023-08-29              | SPPREV - SÃO PAULO PREVIDÊNCIA | 19613.67  | https://esaj.tjsp.jus.br | true      |
| 362 | Congratulasheyla Oliveira  | XXX.XXX.XXX-XX | 0017399-48.2021.8.26.0053  |   5  | Stephanie Joanne Angelina Germanotta 	| 332385.88	      | 2023-08-29 | 2023-08-29              | SPPREV - SÃO PAULO PREVIDÊNCIA | 24913.80  | https://esaj.tjsp.jus.br | false     |

<br>

### Explicação

| coluna                | tipo                              | função |
|-----------------------|-----------------------------------|--------|
|id                     | INT                               | Auto-explicativo |
|nome_req               | varchar                           | Nome do requerente |
|cpf_req                | varchar                           | CPF do requerente |
|cod_processo           | varchar UNIQUE (com **seq**)      | Código do processo principal |
|seq                    | INT UNIQUE (com **cod_processo**) | Sequência do precatório no código do processo. Um processo pode ter múltiplos incidentes, que são identificados por números sequenciais. Por exemplo, se o processo **0017399-48.2021.8.26.0053** tem 3 incidentes, eles serão **0017399-48.2021.8.26.0053/01**, **0017399-48.2021.8.26.0053/02** e **0017399-48.2021.8.26.0053/3**. cod_processo + "/" + seq formam o número do incidente. **Atenção**: nem todos os incidentes são precatórios! O script faz a extração apenas dos que são.|
|advogado               | varchar                           | Nome do advogado do precatório |
|valor_processo         | numeric                           | Valor do precatório. Deve sempre ser maior que o mínimo estipulado em painel.py |
|data doc               | date                              | Data do documento |
|data_emissão_termo_dec | date                              | Data de emissão do termo de declaração |
|ent_devedora           | varchar                           | Entidade devedora |
|princ_liq              | numeric                           | Principal líquido |
|link                   | text                              | Link do precatório no site do ESAJ |
|exportado              | boolean                           | Determina se esse precatório foi exportado para CSV. Por padrão é **false**. Quando é exportado, o script altera o valor para True |

> **exportado** e **id** são as únicas colunas que não são enviadas ao CSV

> Durante a exportação, `cod_processo` e `seq` são juntados em uma única coluna, separados por "/"