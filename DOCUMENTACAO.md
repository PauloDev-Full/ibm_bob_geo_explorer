# 📚 ibm_bob_geo_explorer — Documentação Completa do Projeto

> ⚠️ **Nota:** Este arquivo é a documentação histórica original. O ponto de entrada oficial do projeto é o [`README.md`](README.md) na raiz do repositório.

> **Projeto:** ibm_bob_geo_explorer com IBM Bob + MCP Server
> **Objetivo:** Explorar trilhas de formação da plataforma DIO (Digital Innovation One) diretamente pelo chat do IBM Bob, usando comandos de linguagem natural ou slash commands.
> **Stack:** Python · TypeScript · Node.js · IBM Bob · MCP (Model Context Protocol)

---

## Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura](#2-arquitetura)
3. [Estrutura de Arquivos](#3-estrutura-de-arquivos)
4. [Como Configurar e Executar](#4-como-configurar-e-executar)
5. [Slash Commands do Bob](#5-slash-commands-do-bob)
6. [Ferramentas MCP (Tools)](#6-ferramentas-mcp-tools)
7. [Fonte de Dados — trilhas\_dio.json](#7-fonte-de-dados--trilhas_diojson)
8. [Módulo Python — dio\_commands.py](#8-módulo-python--dio_commandspy)
9. [Servidor MCP TypeScript](#9-servidor-mcp-typescript)
10. [Testes Automatizados](#10-testes-automatizados)
11. [Prompts Usados Durante o Desenvolvimento](#11-prompts-usados-durante-o-desenvolvimento)
12. [Modos de Uso](#12-modos-de-uso)
13. [Dicas para Futuros Profissionais](#13-dicas-para-futuros-profissionais)
14. [Glossário](#14-glossário)

---

## 1. Visão Geral do Projeto

O **DIO Explorer** é um projeto que integra o **IBM Bob** (assistente de IA para desenvolvedores) com a **DIO** (Digital Innovation One) por meio de um **servidor MCP** (Model Context Protocol).

### O que ele faz?

- Permite consultar trilhas de formação tecnológica da DIO diretamente pelo chat do Bob.
- Gera desafios de código personalizados por tecnologia e nível.
- Emite certificados fictícios de conclusão de trilha.
- Expõe tudo isso tanto via **slash commands** (interface do Bob) quanto via **ferramentas MCP** (API para automação).

### Por que é relevante?

Este projeto é um **caso de uso real** de como integrar um modelo de IA (IBM Bob) com fontes de dados externas e lógica de negócio personalizada, usando o padrão aberto MCP. É um excelente projeto de portfólio para quem quer aprender sobre:

- Integração de IA com sistemas externos
- Criação de servidores MCP
- Automação de fluxos de aprendizado
- Testes automatizados em Python

---

## 2. Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    IBM Bob (Chat)                    │
│  ┌─────────────────┐    ┌────────────────────────┐  │
│  │  Slash Commands  │    │     MCP Tools (Chat)   │  │
│  │  /trilha        │    │  list_trilhas           │  │
│  │  /desafio       │    │  trilha                 │  │
│  │  /certificado   │    │  desafio                │  │
│  └────────┬────────┘    │  certificado            │  │
│           │             └────────────┬───────────┘  │
└───────────┼──────────────────────────┼──────────────┘
            │                          │ stdio (MCP protocol)
            │                          ▼
            │              ┌───────────────────────────┐
            │              │  DIO Explorer MCP Server  │
            │              │  (TypeScript / Node.js)   │
            │              │                           │
            │              │  dio_explorer/mcp/        │
            │              │  ├── src/index.ts  ←stdio │
            │              │  ├── src/http.ts  ←HTTP   │
            │              │  └── src/dio.ts   ←lógica │
            │              └────────────┬──────────────┘
            │                           │
            ▼                           ▼
┌─────────────────────────────────────────────────────┐
│              Fonte de Dados                         │
│    dio_explorer/data/trilhas_dio.json               │
│    (10 trilhas · Python, Java, React, Node.js…)     │
└─────────────────────────────────────────────────────┘
```

O Bob se conecta ao servidor MCP via **transporte stdio** (processo filho). O servidor lê o arquivo JSON de trilhas e responde às chamadas de ferramentas do Bob.

Há também um **modo HTTP** (`http.ts`) para integrações externas via API REST, com suporte a autenticação por API Key e infraestrutura pronta para TLS/SSO via proxy reverso.

---

## 3. Estrutura de Arquivos

```
ibm_bob_geo/
├── .bob/
│   ├── mcp.json                    ← Registro do servidor MCP no Bob
│   └── commands/
│       ├── trilha.md               ← Slash command /trilha
│       ├── desafio.md              ← Slash command /desafio
│       └── certificado.md          ← Slash command /certificado
│
└── dio_explorer/
    ├── data/
    │   └── trilhas_dio.json        ← Base de dados das trilhas DIO
    │
    ├── src/
    │   ├── __init__.py
    │   └── dio_commands.py         ← Lógica core em Python (testável)
    │
    ├── tests/
    │   ├── __init__.py
    │   └── test_dio_commands.py    ← Suite de testes pytest (160+ testes)
    │
    └── mcp/
        ├── package.json
        ├── tsconfig.json
        ├── README.md
        └── src/
            ├── index.ts            ← Servidor MCP — transporte stdio
            ├── http.ts             ← Servidor MCP — transporte HTTP
            └── dio.ts              ← Lógica core em TypeScript (mirror do Python)
```

---

## 4. Como Configurar e Executar

### Pré-requisitos

| Ferramenta | Versão mínima | Para que serve |
|---|---|---|
| Node.js | 18+ | Executar o servidor MCP |
| npm | 8+ | Instalar dependências JS |
| Python | 3.10+ | Rodar os testes automatizados |
| IBM Bob | qualquer | Interface de chat com IA |

### Passo 1 — Compilar o servidor MCP

```bash
cd dio_explorer/mcp
npm install
npm run build
```

Isso gera o diretório `build/` com `index.js` (stdio) e `http.js` (HTTP).

### Passo 2 — Registrar no Bob

O arquivo `.bob/mcp.json` já está configurado:

```json
{
  "mcpServers": {
    "dio-explorer": {
      "command": "node",
      "args": [
        "CAMINHO_ABSOLUTO/dio_explorer/mcp/build/index.js"
      ],
      "env": {}
    }
  }
}
```

> ⚠️ **Importante:** Substitua `CAMINHO_ABSOLUTO` pelo caminho real do projeto na sua máquina.

### Passo 3 — Rodar os testes Python

```bash
cd dio_explorer
python -m pytest tests/ -v
```

### Passo 4 (opcional) — Iniciar o servidor HTTP

```bash
PORT=3000 API_KEY=minha-chave node dio_explorer/mcp/build/http.js
```

---

## 5. Slash Commands do Bob

Os slash commands são atalhos de linguagem natural definidos em `.bob/commands/`. Eles funcionam como prompts estruturados que o Bob executa automaticamente quando você os digita no chat.

### `/trilha <tecnologia>`

**Descrição:** Exibe o plano de estudos completo de uma trilha DIO.

**Arquivo:** [`.bob/commands/trilha.md`](.bob/commands/trilha.md)

**Uso:**
```
/trilha Python
/trilha Java
/trilha React
/trilha Node.js
```

**O que o Bob faz internamente:**
1. Lê o arquivo `dio_explorer/data/trilhas_dio.json`
2. Busca a trilha pela tecnologia (case-insensitive)
3. Formata e exibe: nível, módulos, carga horária, XP, badges, lives, promoções

**Saída esperada:**
```markdown
# 🎯 Trilha: Formação Python Developer

> Aprenda Python do zero ao avançado...

| Campo     | Detalhe     |
|-----------|-------------|
| 🏆 Nível  | Básico ao Avançado |
| 📦 Módulos | 8          |
...

## 📚 Módulos do Plano de Estudos
📖 1. Fundamentos de Python
📖 2. Programação Orientada a Objetos
...
```

---

### `/desafio <tecnologia> <nivel>`

**Descrição:** Gera um desafio de código personalizado para a tecnologia e nível escolhidos.

**Arquivo:** [`.bob/commands/desafio.md`](.bob/commands/desafio.md)

**Uso:**
```
/desafio Python iniciante
/desafio Java intermediário
/desafio React avançado
/desafio Node.js avançado
```

**Níveis aceitos:** `iniciante` · `intermediário` · `avançado`

> Se um nível inválido for informado, o Bob assume `intermediário` e avisa o usuário.

**O que o Bob faz internamente:**
1. Valida se a tecnologia existe no JSON
2. Normaliza o nível (aceita variações sem acento: `avancado`, `intermediario`)
3. Seleciona um template de desafio específico da tecnologia (se disponível) ou genérico
4. Gera o desafio formatado com descrição, exemplos, dica e critérios de aceitação

**Saída esperada:**
```markdown
# ⚡ Desafio de Código — Java

> 🎯 **Nível:** avançado | ⏱️ **Tempo sugerido:** 90 minutos

## 📋 Descrição do Desafio
Desenvolva uma API RESTful com Spring Boot...

## 🧪 Exemplos
Entrada: POST /products  Body: {"name":"Notebook","price":4500.0}
Saída:   201 Created  Body: {"id":1,"name":"Notebook"...}

## ✅ Critérios de Aceitação
- [ ] O código deve resolver todos os exemplos
- [ ] Cobertura de testes ≥ 80%
```

---

### `/certificado <nome> <tecnologia>`

**Descrição:** Emite um certificado fictício de conclusão de trilha.

**Arquivo:** [`.bob/commands/certificado.md`](.bob/commands/certificado.md)

**Uso:**
```
/certificado "Ana Silva" Python
/certificado "João Santos" Java
/certificado "Maria Oliveira" React
```

**O que o Bob faz internamente:**
1. Busca a trilha no JSON pela tecnologia
2. Obtém a data atual do sistema
3. Gera um ID único no formato `DIO-JAVA-2025-ABCDEF`
4. Formata o certificado com todos os dados da trilha e badges conquistadas

**Saída esperada:**
```
╔══════════════════════════════════════════════════════════════════╗
║                    🎓  CERTIFICADO DE CONCLUSÃO                  ║
║                     [ DIO — Digital Innovation One ]            ║
╚══════════════════════════════════════════════════════════════════╝

## Certificamos que
# ✨ Ana Silva ✨
concluiu com êxito a formação
## 🏆 Formação Python Developer

📅 Data de Emissão: 01/07/2025
🔑 ID do Certificado: DIO-PYTHON-2025-K3X7MN
🌐 Verificar em: https://www.dio.me/certificate
```

---

## 6. Ferramentas MCP (Tools)

As ferramentas MCP são expostas pelo servidor e podem ser chamadas pelo Bob via linguagem natural **sem precisar de slash commands**. O Bob decide automaticamente qual ferramenta usar com base na sua mensagem.

| Tool | Descrição | Parâmetros |
|---|---|---|
| `list_trilhas` | Lista todas as trilhas disponíveis com metadados | — |
| `trilha` | Overview completo de uma trilha | `tecnologia` (string) |
| `desafio` | Gera um desafio de código | `tecnologia`, `nivel?` (opcional) |
| `certificado` | Emite certificado de conclusão | `nome`, `tecnologia` |

### Exemplos de linguagem natural que ativam as tools:

```
"liste todas as trilhas disponíveis"         → list_trilhas
"mostre a trilha de Python"                  → trilha(tecnologia: "Python")
"quero um desafio de Java avançado"          → desafio(tecnologia: "Java", nivel: "avançado")
"emita o certificado de Ana para React"      → certificado(nome: "Ana", tecnologia: "React")
```

### Modo HTTP (API REST)

Para integrações externas, o servidor também pode ser iniciado como API REST:

```bash
# Iniciar servidor HTTP
PORT=3000 API_KEY=minha-chave node dio_explorer/mcp/build/http.js

# Health check
curl http://localhost:3000/health

# Chamar uma tool via API
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer minha-chave" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "trilha",
      "arguments": { "tecnologia": "Python" }
    }
  }'
```

### Variáveis de ambiente do servidor HTTP

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta TCP do servidor |
| `API_KEY` | *(vazio)* | Chave Bearer para autenticação. Se vazio, sem autenticação |
| `ALLOWED_ORIGIN` | `*` | Header CORS `Access-Control-Allow-Origin` |

---

## 7. Fonte de Dados — trilhas\_dio.json

**Arquivo:** [`dio_explorer/data/trilhas_dio.json`](dio_explorer/data/trilhas_dio.json)

O coração do projeto é um arquivo JSON com dados de 10 trilhas de formação da DIO. É o único local onde os dados das trilhas estão definidos — tanto o servidor MCP quanto o módulo Python leem deste arquivo.

### Estrutura do JSON

```json
{
  "fonte": "https://dio.me",
  "ultima_atualizacao": "2025-01-01",
  "trilhas_formacao": [
    {
      "id": 1,
      "nome": "Formação Python Developer",
      "tecnologia": "Python",
      "nivel": "Básico ao Avançado",
      "numero_de_modulos": 8,
      "xp_total": 19040,
      "duracao_horas": 68,
      "descricao": "...",
      "badges_disponiveis": [
        { "nome": "Python Essentials", "descricao": "...", "xp_requerido": 3000 }
      ],
      "promocoes": {
        "desconto_disponivel": true,
        "percentual_desconto": 50,
        "descricao_promocao": "...",
        "validade_promocao": "2025-09-13"
      },
      "vitalicio": {
        "disponivel": true,
        "preco_vitalicio_brl": 1497,
        "descricao": "..."
      },
      "lives_ao_vivo": [
        { "titulo": "...", "frequencia": "Quinzenal", "plataforma": "YouTube" }
      ],
      "conteudos_modulos": ["Fundamentos de Python", "POO", "..."],
      "certificado": true,
      "plano_requerido": "Pro"
    }
  ],
  "resumo": {
    "total_trilhas": 10,
    "tecnologias_cobertas": ["Python", "Java", "React", "..."],
    "xp_total_disponivel": 185000,
    "total_badges": 30,
    "total_horas_conteudo": 650,
    "planos_disponiveis": { "free": "...", "pro_mensal": "...", ... }
  }
}
```

### Tecnologias cobertas

Use `/trilha <tecnologia>` ou a tool `list_trilhas` para ver a lista completa e atualizada. Entre as tecnologias presentes estão: **Python, Java, React, Node.js, Angular, Vue.js, Spring Boot, Docker, Kubernetes** e outras.

---

## 8. Módulo Python — dio\_commands.py

**Arquivo:** [`dio_explorer/src/dio_commands.py`](dio_explorer/src/dio_commands.py)

Este módulo é a implementação de referência da lógica de negócio em Python. Foi desenvolvido com foco em testabilidade — todas as funções são puras, recebem `data_path` como parâmetro opcional e retornam strings Markdown.

### Funções públicas

#### `load_data(data_path=None) → dict`
Carrega o JSON de trilhas do disco. Aceita um caminho alternativo para facilitar testes.

#### `find_trilha(data, tecnologia) → dict | None`
Busca case-insensitive pelo campo `tecnologia` no array `trilhas_formacao`. Retorna `None` se não encontrar.

#### `list_tecnologias(data) → list[str]`
Retorna todos os nomes de tecnologia disponíveis no dataset.

#### `cmd_trilha(tecnologia, data_path=None) → str`
Renderiza o plano de estudos completo. Lança `ValueError` se a tecnologia não existir.

#### `cmd_desafio(tecnologia, nivel="intermediário", data_path=None) → tuple[str, str]`
Gera um desafio de código. Retorna `(markdown_output, effective_level)`.  
O `effective_level` pode diferir do `nivel` informado se o valor for inválido.

#### `cmd_certificado(nome, tecnologia, data_path=None, cert_id=None) → str`
Emite um certificado fictício. O parâmetro `cert_id` pode ser fixado para tornar a saída determinística nos testes.

### Templates de desafio

O módulo tem templates específicos por tecnologia (ex: Java tem desafios de `TaskManager` e `API Spring Boot`) e templates genéricos usados como fallback para todas as outras tecnologias:

| Nível | Template genérico |
|---|---|
| iniciante | Verificador de Palíndromo (15 min) |
| intermediário | Anagramas em Grupos (40 min) |
| avançado | LRU Cache O(1) (60 min) |

---

## 9. Servidor MCP TypeScript

O servidor MCP é o componente que conecta o Bob com a lógica de negócio. Está implementado em TypeScript e compilado para JavaScript.

### Arquivos

| Arquivo | Descrição |
|---|---|
| [`dio.ts`](dio_explorer/mcp/src/dio.ts) | Mirror em TypeScript da lógica do `dio_commands.py`. Funções `cmdTrilha`, `cmdDesafio`, `cmdCertificado`. |
| [`index.ts`](dio_explorer/mcp/src/index.ts) | Servidor MCP com transporte **stdio** — usado pelo Bob localmente via `.bob/mcp.json` |
| [`http.ts`](dio_explorer/mcp/src/http.ts) | Servidor MCP com transporte **HTTP** — usado para integrações externas e APIs |

### Dependências

```json
{
  "@modelcontextprotocol/sdk": "^1.13.1",
  "express": "^4.19.2",
  "zod": "^3.24.4"
}
```

- **`@modelcontextprotocol/sdk`** — SDK oficial do MCP para criar servidores compatíveis
- **`express`** — servidor HTTP para o modo de API REST
- **`zod`** — validação de schema dos parâmetros das tools

### Registro de ferramentas (pattern usado)

```typescript
server.registerTool(
  "trilha",
  {
    description: "Retorna o overview completo de uma trilha de formação DIO.",
    inputSchema: z.object({
      tecnologia: z.string().describe("Nome da tecnologia. Case-insensitive."),
    }),
  },
  async ({ tecnologia }) => {
    const result = cmdTrilha(tecnologia);
    return { content: [{ type: "text", text: result }] };
  }
);
```

---

## 10. Testes Automatizados

**Arquivo:** [`dio_explorer/tests/test_dio_commands.py`](dio_explorer/tests/test_dio_commands.py)

O projeto tem uma suite robusta de testes em **pytest** com mais de 160 casos de teste organizados em classes.

### Executar os testes

```bash
# Todos os testes
python -m pytest dio_explorer/tests/ -v

# Com cobertura de código
python -m pytest dio_explorer/tests/ --cov=dio_explorer/src --cov-report=term-missing

# Apenas uma classe
python -m pytest dio_explorer/tests/test_dio_commands.py::TestCmdTrilha -v
```

### Classes de teste

| Classe | O que testa |
|---|---|
| `TestNormaliseLevel` | Normalização de nível (com/sem acento, maiúsculas) |
| `TestGenerateCertId` | Formato e unicidade do ID do certificado |
| `TestLoadData` | Carregamento do JSON (arquivo real, mock, arquivo ausente) |
| `TestFindTrilha` | Busca case-insensitive de trilhas |
| `TestListTecnologias` | Listagem de tecnologias |
| `TestCmdTrilha` | Output do comando /trilha (15+ casos) |
| `TestCmdDesafio` | Output do comando /desafio (15+ casos) |
| `TestCmdCertificado` | Output do comando /certificado (18+ casos) |
| `TestFullFlow` | Testes de integração ponta a ponta |

### Estratégia de teste

- **Testes unitários** com dados mock (`_SAMPLE_DATA`) para isolamento e velocidade
- **Testes de integração** com o arquivo real `trilhas_dio.json` (ex: `test_real_file_java_trilha`)
- **Testes de edge cases**: tecnologia não encontrada, nível inválido, strings vazias
- **`cert_id` injetável** para tornar o certificado determinístico nos testes

---

## 11. Prompts Usados Durante o Desenvolvimento

Esta seção documenta os prompts e conversas-chave que guiaram a construção do projeto, úteis para quem quiser entender o processo ou repetir a experiência.

### Fase 1 — Estruturação do Projeto

> **Prompt (paráfrase):**  
> *"Quero criar um projeto que usa IBM Bob para explorar trilhas de formação da DIO. Preciso de slash commands para /trilha, /desafio e /certificado, com dados em um arquivo JSON."*

**O que o Bob fez:**
- Criou a estrutura de pastas do projeto
- Definiu o schema do `trilhas_dio.json`
- Criou os arquivos `.bob/commands/trilha.md`, `desafio.md` e `certificado.md`

---

### Fase 2 — Dados das Trilhas

> **Prompt (paráfrase):**  
> *"Crie o arquivo trilhas_dio.json com 10 trilhas de tecnologia, incluindo badges, promoções, lives ao vivo e planos de acesso."*

**O que o Bob fez:**
- Gerou um JSON rico com 10 trilhas cobrindo tecnologias relevantes do mercado
- Incluiu campos como `badges_disponiveis`, `lives_ao_vivo`, `vitalicio` e `promocoes`
- Adicionou um bloco `resumo` com estatísticas agregadas

---

### Fase 3 — Módulo Python com Testes

> **Prompt (paráfrase):**  
> *"Implemente o módulo Python `dio_commands.py` com funções puras para trilha, desafio e certificado. Precisa ser testável e retornar Markdown."*

**O que o Bob fez:**
- Criou `dio_commands.py` com funções `cmd_trilha`, `cmd_desafio` e `cmd_certificado`
- Implementou templates de desafio por tecnologia e nível
- Fez `cmd_desafio` retornar uma tupla `(output, effective_level)` para facilitar os testes

> **Prompt (paráfrase):**  
> *"Crie uma suite completa de testes pytest para o módulo Python, cobrindo casos de borda e testes com o arquivo real."*

**O que o Bob fez:**
- Criou `test_dio_commands.py` com 8 classes de teste e mais de 160 casos
- Usou `pytest.fixture` para criar arquivo de dados temporário nos testes
- Adicionou testes de integração com `test_real_file_*` que usam o JSON real

---

### Fase 4 — Servidor MCP

> **Prompt (paráfrase):**  
> *"Crie um servidor MCP em TypeScript que exponha as mesmas funções do Python via stdio, para que o Bob possa chamar automaticamente sem slash commands."*

**O que o Bob fez:**
- Criou `dio.ts` como mirror TypeScript do `dio_commands.py`
- Criou `index.ts` com transporte stdio usando `@modelcontextprotocol/sdk`
- Registrou as 4 tools: `list_trilhas`, `trilha`, `desafio`, `certificado`
- Configurou `.bob/mcp.json` para registrar o servidor no Bob

> **Prompt (paráfrase):**  
> *"Adicione também um modo HTTP para que o servidor possa ser consumido como API REST com autenticação por API Key."*

**O que o Bob fez:**
- Criou `http.ts` com Express + `StreamableHTTPServerTransport`
- Implementou gerenciamento de sessões por `mcp-session-id`
- Adicionou middleware de autenticação por Bearer token
- Documentou o modo HTTP no `README.md`

---

### Fase 5 — Documentação

> **Prompt:**  
> *"Bob, gostaria que você documentasse em markdown todo o projeto feito até o momento, com todos prompts usados, modos de uso, dica de uso para futuros profissionais que vão aprender com nosso projeto."*

**Resultado:** Este arquivo `DOCUMENTACAO.md`.

---

## 12. Modos de Uso

### Modo 1 — Slash Commands (uso interativo)

Ideal para uso direto no chat do Bob. Digita o comando e o Bob executa a lógica completa.

```
/trilha Python
/desafio Java avançado
/certificado "Seu Nome" React
```

**Quando usar:** Exploração interativa, geração de conteúdo one-off, demonstrações.

---

### Modo 2 — Linguagem Natural via MCP (uso assistido)

O Bob usa as tools MCP automaticamente quando você faz pedidos em linguagem natural. Não precisa saber os comandos.

```
"Quais trilhas estão disponíveis?"
"Me dá um desafio de Python para iniciantes"
"Gera meu certificado de conclusão da trilha de Java"
```

**Quando usar:** Onboarding de novos usuários, conversas exploratórias, quando não se lembra dos comandos.

---

### Modo 3 — API REST (integração externa)

Para sistemas que precisam consumir os dados programaticamente (CI/CD, apps web, dashboards).

```bash
# Listar trilhas
curl -X POST http://localhost:3000/mcp \
  -H "Authorization: Bearer sua-chave" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_trilhas","arguments":{}}}'
```

**Quando usar:** Integrações com sistemas externos, automação de pipelines, LMS custom.

---

### Modo 4 — Biblioteca Python (uso programático)

O módulo `dio_commands.py` pode ser importado diretamente em scripts Python.

```python
from dio_explorer.src.dio_commands import cmd_trilha, cmd_desafio, cmd_certificado

# Obter plano de estudos
print(cmd_trilha("Python"))

# Gerar desafio
output, level = cmd_desafio("Java", "avançado")
print(output)

# Emitir certificado
print(cmd_certificado("Ana Silva", "React"))
```

**Quando usar:** Scripts de automação, geração de conteúdo em lote, integração com outros sistemas Python.

---

## 13. Dicas para Futuros Profissionais

### 🏗️ Sobre a Arquitetura

**Separe lógica de transporte.** O projeto tem o `dio.ts` (lógica pura) separado do `index.ts` (stdio) e `http.ts` (HTTP). Isso permite testar a lógica de negócio sem depender do protocolo MCP. Aplique este princípio em todos os projetos.

**Python como camada de testes, TypeScript como camada de produção.** O `dio_commands.py` foi criado para ser facilmente testável com pytest, enquanto o `dio.ts` é o que realmente roda em produção. Ter os dois em sincronia é trabalhoso — considere ter apenas um se o projeto crescer.

---

### 🧪 Sobre os Testes

**Injete dependências ao invés de hardcodar caminhos.** Observe como `cmd_certificado` aceita `cert_id=None` — isso permite testes determinísticos sem mocks complexos. Faça o mesmo para datas, IDs e qualquer valor randômico.

**Use fixtures para compartilhar estado entre testes.** O `sample_data_file` fixture cria um arquivo JSON temporário e o injeta em vários testes. É mais limpo e rápido que criar o arquivo em cada teste.

**Teste o arquivo real, não só mocks.** Os testes `test_real_file_*` garantem que a integração com o JSON de produção está funcionando. Sempre tenha pelo menos um teste que usa dados reais.

---

### 🔌 Sobre MCP

**O MCP é o novo padrão para conectar IA com sistemas externos.** Aprender a criar servidores MCP hoje é como aprender REST APIs em 2010 — vai ser uma habilidade fundamental para desenvolvedores de IA.

**O padrão MCP usa JSON-RPC 2.0.** Se você já conhece JSON-RPC, entenderá rapidamente o protocolo. O SDK cuida do boilerplate — você só precisa registrar suas tools com `server.registerTool`.

**Valide os parâmetros com Zod.** O SDK MCP usa Zod para definir e validar o schema dos inputs das tools. Invista tempo aprendendo Zod — ele é amplamente usado no ecossistema TypeScript/Node.js.

---

### 💡 Sobre o IBM Bob

**Slash commands vs. MCP tools:** Use slash commands para fluxos bem definidos com prompts estruturados (o Bob "sabe" exatamente o que fazer). Use MCP tools para deixar o Bob raciocinar e decidir qual ferramenta usar baseado no contexto.

**Os arquivos `.md` em `.bob/commands/` são prompts.** Trate-os com o mesmo cuidado que trataria um prompt de sistema. A qualidade da saída do Bob depende diretamente da clareza das instruções nesses arquivos.

**Combine slash commands com MCP.** No projeto, o `/trilha Python` usa a lógica do Bob (lendo o JSON diretamente via instruções no `.md`), enquanto o MCP chama o código TypeScript compilado. Ambos coexistem bem.

---

### 🚀 Como Evoluir o Projeto

Algumas ideias para quem quiser ir além:

1. **Adicionar mais tecnologias ao JSON** — O JSON é facilmente extensível. Adicione trilhas de Cloud, DevOps, Data Science, etc.

2. **Integrar com a API real da DIO** — Substituir o JSON estático por chamadas à API real da DIO para dados sempre atualizados.

3. **Adicionar persistência** — Salvar progresso do usuário (módulos concluídos, desafios resolvidos) em um banco de dados local.

4. **Tool de busca semântica** — Usar embeddings para buscar trilhas por descrição ao invés de nome exato da tecnologia.

5. **Dashboard de progresso** — Criar uma tool MCP que retorna HTML com gráficos de progresso por tecnologia.

6. **Deploy na nuvem** — Hospedar o servidor HTTP em AWS Lambda, Azure Functions ou Railway e conectar ao Bob via MCP remoto.

---

## 14. Glossário

| Termo | Definição |
|---|---|
| **MCP** | Model Context Protocol — protocolo aberto para conectar modelos de IA com ferramentas e dados externos |
| **Tool (MCP)** | Função registrada no servidor MCP que o AI pode chamar com parâmetros estruturados |
| **Slash Command** | Atalho de texto que ativa um prompt/fluxo predefinido no Bob (ex: `/trilha Python`) |
| **stdio transport** | Modo de comunicação onde o servidor MCP roda como processo filho e troca mensagens via stdin/stdout |
| **Streamable HTTP transport** | Modo de comunicação onde o servidor MCP expõe um endpoint HTTP que suporta streaming |
| **JSON-RPC 2.0** | Protocolo de chamada de procedimento remoto baseado em JSON, usado internamente pelo MCP |
| **Zod** | Biblioteca TypeScript para validação de schemas em runtime |
| **pytest fixture** | Função auxiliar do pytest que provê dados ou objetos reutilizáveis para múltiplos testes |
| **IBM Bob** | Assistente de IA da IBM para desenvolvedores, com suporte nativo ao protocolo MCP |
| **DIO** | Digital Innovation One — plataforma brasileira de educação em tecnologia |

---

*Documentação gerada com IBM Bob · Projeto DIO Explorer · 2025*
