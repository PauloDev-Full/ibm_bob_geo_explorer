# ibm_bob_geo_explorer

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Node.js](https://img.shields.io/badge/Node.js-18%2B-green)
![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)
![Tests](https://img.shields.io/badge/tests-86%20passed-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)
![CI](https://github.com/PauloDev-Full/ibm_bob_geo_explorer/actions/workflows/ci.yml/badge.svg)

**ibm_bob_geo_explorer** integra o **IBM Bob** (assistente de IA para desenvolvedores) com a plataforma **DIO — Digital Innovation One** via um servidor **MCP (Model Context Protocol)**. Ele expõe trilhas de formação, desafios de código e certificados diretamente no chat do Bob, tanto por slash commands quanto por linguagem natural, e oferece uma API REST para integração externa.

---

## Arquitetura & Tecnologias

```
┌─────────────────────────────────────────────────────┐
│                    IBM Bob (Chat)                    │
│  ┌──────────────────┐    ┌───────────────────────┐  │
│  │  Slash Commands   │    │  MCP Tools (Chat)     │  │
│  │  /trilha          │    │  list_trilhas          │  │
│  │  /desafio         │    │  trilha                │  │
│  │  /certificado     │    │  desafio               │  │
│  └─────────┬─────────┘    │  certificado           │  │
│            │              └───────────┬────────────┘  │
└────────────┼─────────────────────────┼───────────────┘
             │                         │ stdio (MCP protocol)
             ▼                         ▼
┌──────────────────────────────────────────────────────┐
│              ibm_bob_geo_explorer MCP Server          │
│              (TypeScript / Node.js)                   │
│                                                       │
│  ibm_bob_geo_explorer/mcp/                           │
│  ├── src/index.ts   ← transporte stdio               │
│  ├── src/http.ts    ← transporte HTTP                │
│  └── src/dio.ts     ← lógica de negócio              │
└──────────────────────┬────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│           ibm_bob_geo_explorer/data/                  │
│           trilhas_dio.json                            │
│  (10 trilhas · Python, Java, React, Node.js …)       │
└──────────────────────────────────────────────────────┘
```

| Camada | Tecnologia | Versão | Função |
|--------|-----------|--------|--------|
| Lógica core (Python) | Python | 3.10+ | Módulo `dio_commands.py` — trilha, desafio, certificado |
| Testes | pytest + pytest-cov | 9.x / 7.x | Suíte de 86 testes, cobertura ≥ 99% |
| Servidor MCP | TypeScript + Node.js | 5.x / 18+ | Expõe ferramentas via stdio e HTTP |
| Framework MCP | `@modelcontextprotocol/sdk` | ^1.13.1 | Protocolo de comunicação com Bob |
| Validação de esquema | `zod` | ^3.24.4 | Tipagem e validação de inputs das tools |
| API HTTP | `express` | ^4.19.2 | Modo REST / API Gateway |
| Dados | JSON estático | — | `trilhas_dio.json` — 10 trilhas DIO |

---

## Pré-requisitos

| Ferramenta | Versão mínima | Para que serve |
|-----------|---------------|----------------|
| Python | 3.10+ | Lógica core e testes automatizados |
| pip | 23+ | Gerenciamento de pacotes Python |
| Node.js | 18+ | Executar o servidor MCP TypeScript |
| npm | 8+ | Instalar dependências JS/TS |
| IBM Bob | qualquer | Interface de chat com IA |

---

## Guia Rápido (Quickstart)

### 1 — Clonar o repositório

```bash
git clone https://github.com/PauloDev-Full/ibm_bob_geo_explorer.git
cd ibm_bob_geo_explorer
```

### 2 — Instalar dependências Python

```bash
pip install -r requirements.txt
```

Ou usando `pyproject.toml` (recomendado):

```bash
pip install -e ".[dev]"
```

### 3 — Instalar dependências e compilar o servidor MCP

```bash
cd ibm_bob_geo_explorer/mcp
npm install
npm run build
cd ../..
```

O diretório `ibm_bob_geo_explorer/mcp/build/` será criado com `index.js` (stdio) e `http.js` (HTTP).

### 4 — Registrar o servidor MCP no Bob

O arquivo `.bob/mcp.json` já está configurado. Ajuste o caminho absoluto se necessário:

```json
{
  "mcpServers": {
    "ibm-bob-geo-explorer": {
      "command": "node",
      "args": [
        "/caminho/absoluto/para/ibm_bob_geo_explorer/mcp/build/index.js"
      ],
      "env": {}
    }
  }
}
```

### 5 — Rodar os testes automatizados

```bash
# Testes unitários
pytest ibm_bob_geo_explorer/tests/ -v

# Testes com cobertura
pytest ibm_bob_geo_explorer/tests/ --cov=ibm_bob_geo_explorer.src.dio_commands --cov-report=term-missing
```

### 6 — (Opcional) Iniciar o servidor HTTP

```bash
# Copie e ajuste as variáveis de ambiente
cp .env.example .env

# Inicie com as variáveis configuradas
PORT=3000 API_KEY=sua-chave-secreta node ibm_bob_geo_explorer/mcp/build/http.js
```

---

## Variáveis de Ambiente

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

| Variável | Padrão | Obrigatória | Descrição |
|---------|--------|-------------|-----------|
| `PORT` | `3000` | Não | Porta TCP do servidor HTTP |
| `API_KEY` | *(vazio)* | Não | Chave Bearer exigida nos requests ao servidor HTTP. Sem valor = sem autenticação |
| `ALLOWED_ORIGIN` | `*` | Não | Header `Access-Control-Allow-Origin` para CORS |

> **Nota:** O transporte **stdio** (usado pelo Bob localmente) não requer nenhuma variável de ambiente.

---

## Slash Commands do Bob

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/trilha <tecnologia>` | Exibe o plano de estudos completo | `/trilha Python` |
| `/desafio <tecnologia> <nivel>` | Gera um desafio de código | `/desafio Java avançado` |
| `/certificado <nome> <tecnologia>` | Emite um certificado de conclusão | `/certificado Ana Silva React` |

---

## Ferramentas MCP

| Tool | Descrição | Parâmetros |
|------|-----------|-----------|
| `list_trilhas` | Lista todas as trilhas disponíveis | — |
| `trilha` | Overview completo de uma trilha (módulos, badges, promoções, lives) | `tecnologia` (string) |
| `desafio` | Gera um desafio de código | `tecnologia`, `nivel?` (iniciante / intermediário / avançado) |
| `certificado` | Emite certificado de conclusão | `nome`, `tecnologia` |

### Exemplos de Retorno das Ferramentas MCP

#### `list_trilhas`
```json
{
  "trilhas": [
    "Python", "Java", "React", "Node.js", "Angular",
    "Flutter", "Kotlin", "Spring Boot", "TypeScript", "AWS"
  ]
}
```

#### `trilha`
```json
{
  "tecnologia": "Python",
  "modulos": ["Fundamentos", "POO", "APIs com FastAPI", "Data Science"],
  "badges": ["Python Essentials", "Python Pro"],
  "promocoes": ["Bootcamp Python AI", "Santander Bootcamp"],
  "lives": ["Live Coding: Automação com Python", "Python para Data Science"]
}
```

#### `desafio`
```json
{
  "tecnologia": "Python",
  "nivel": "intermediario",
  "desafio": "Criar uma API RESTful com FastAPI para gerenciar trilhas de estudo.",
  "criterios_aceite": [
    "Endpoints CRUD completos",
    "Validação de schema via Pydantic"
  ]
}
```

#### `certificado`
```json
{
  "certificado": "Certificado de Conclusão",
  "nome": "Ana Silva",
  "tecnologia": "React",
  "id": "a3f8c1d2",
  "emitido_em": "2025-07-14"
}
```

---

## Estrutura de Arquivos

```
ibm_bob_geo_explorer/
├── .bob/
│   ├── mcp.json                         ← Registro do servidor MCP no Bob
│   └── commands/
│       ├── trilha.md                    ← Slash command /trilha
│       ├── desafio.md                   ← Slash command /desafio
│       └── certificado.md               ← Slash command /certificado
├── .github/
│   └── workflows/
│       └── ci.yml                       ← Pipeline CI/CD (GitHub Actions)
├── ibm_bob_geo_explorer/
│   ├── data/
│   │   └── trilhas_dio.json             ← Base de dados das trilhas DIO
│   ├── src/
│   │   ├── __init__.py
│   │   └── dio_commands.py              ← Lógica core em Python (testável)
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_dio_commands.py         ← Suíte de testes pytest (86 testes)
│   └── mcp/
│       ├── package.json
│       ├── tsconfig.json
│       ├── README.md
│       └── src/
│           ├── index.ts                 ← Servidor MCP — transporte stdio
│           ├── http.ts                  ← Servidor MCP — transporte HTTP
│           └── dio.ts                   ← Lógica core TypeScript
├── .env.example                         ← Exemplo de variáveis de ambiente
├── pyproject.toml                       ← Configuração do projeto Python
├── requirements.txt                     ← Dependências Python
└── README.md
```

---

## Testes Automatizados

```
86 testes · 99% de cobertura · 0 falhas
```

| Classe de Teste | Cobertura |
|----------------|-----------|
| `TestNormaliseLevel` | Normalização de níveis de dificuldade |
| `TestGenerateCertId` | Geração de IDs de certificados |
| `TestLoadData` | Carregamento de dados JSON |
| `TestFindTrilha` | Busca de trilhas por tecnologia |
| `TestListTecnologias` | Listagem de tecnologias |
| `TestCmdTrilha` | Comando `/trilha` end-to-end |
| `TestCmdDesafio` | Comando `/desafio` end-to-end |
| `TestCmdCertificado` | Comando `/certificado` end-to-end |
| `TestFullFlow` | Fluxo completo integrado |


---

## 🚀 Melhorias & Personalizações Realizadas

Estas são as contribuições extras que fui além do escopo mínimo do desafio:

| # | Melhoria | Descrição |
|---|----------|-----------|
| 1 | **Servidor MCP duplo (stdio + HTTP)** | Além do transporte `stdio` exigido pelo Bob, implementei um servidor HTTP com Express (`http.ts`), suportando autenticação Bearer via `API_KEY` e CORS configurável — ideal para integrações com n8n, Zapier ou qualquer API Gateway. |
| 2 | **Autenticação por API Key no servidor HTTP** | O endpoint `/mcp` valida um header `Authorization: Bearer <token>` quando `API_KEY` está definido. Sem configuração, o servidor funciona sem autenticação — seguro por padrão. |
| 3 | **Templates de desafio por tecnologia e nível** | Criei templates detalhados de desafios para Java (iniciante / intermediário / avançado) com título, descrição, exemplos de entrada/saída, dica e critérios de aceitação. As demais tecnologias usam um template genérico com problemas clássicos de algoritmo. |
| 4 | **Suíte de testes com 86 casos (99% de cobertura)** | Organizei os testes em 9 classes bem definidas cobrindo caminhos felizes, edge cases, inputs inválidos, case-insensitivity e fluxo de integração completo. O CI falha se a cobertura cair abaixo de 70%. |
| 5 | **Pipeline CI/CD com matriz de versões** | O GitHub Actions testa Python 3.10 / 3.11 / 3.12 e Node.js 18 / 20 / 22 em paralelo, garantindo compatibilidade ampla sem esforço manual. |
| 6 | **`pyproject.toml` com dependências opcionais** | O projeto é instalável como pacote Python (`pip install -e ".[dev]"`) com separação clara entre dependências de runtime (nenhuma!) e de desenvolvimento. |
| 7 | **Base de dados ficcionalmente rica** | O `trilhas_dio.json` contém 10 trilhas com campos completos: módulos, badges com XP, lives ao vivo, promoções com validade e opção de plano vitalício — tornando os outputs do MCP informativos e realistas. |
| 8 | **Função determinística para testes de certificado** | O parâmetro `cert_id` opcional em `cmd_certificado()` permite fixar o ID do certificado nos testes, eliminando a necessidade de mocks e tornando os asserts exatos. |

---

## 📖 O Que Aprendi Durante o Desafio

### 🤖 IBM Bob e o Model Context Protocol (MCP)
Aprendi na prática como o **Bob** funciona como interface de IA para desenvolvedores e como o **MCP** cria uma ponte entre o assistente e ferramentas externas. Entendi a diferença entre os transportes **stdio** (local, sem servidor) e **HTTP** (remoto, com autenticação) e quando usar cada um.

### 🔧 Construção de um servidor MCP real
Implementar o servidor MCP em TypeScript com o SDK `@modelcontextprotocol/sdk` me mostrou como registrar tools, validar inputs com `zod` e estruturar respostas. Aprendi que o protocolo é agnóstico à linguagem e que qualquer processo que converse via stdio pode ser um servidor MCP.

### 🧪 Cultura de testes como primeiro cidadão
Ao escrever 86 testes antes de refatorar o código, internalizei o valor de funções puras e inputs opcionais (`data_path`, `cert_id`). A separação entre lógica core (Python puro) e integração (servidor MCP) facilitou enormíssimo a testabilidade — não precisei de nenhum mock de I/O.

### 🔒 Boas práticas de segurança em projetos abertos
Aprendi a distinguir o que vai no `.gitignore` vs. o que fica como `.env.example`. O padrão de nunca commitar o `.env` real e documentar todas as variáveis no exemplo é fundamental para projetos open-source. Também reforcei que senhas e tokens jamais devem aparecer nos exemplos de README.

### ⚙️ CI/CD com GitHub Actions
Configurar pipelines com matriz de versões (Python 3.10–3.12, Node.js 18–22) me mostrou como garantir retrocompatibilidade de forma automatizada. Entendi o papel do `cache: pip` e `npm ci` para builds rápidos e reproducíveis.

### 📐 Arquitetura em camadas
O projeto me fez pensar em separação de responsabilidades: dados (JSON), lógica core (Python), interface de comando (slash commands), servidor de protocolo (TypeScript/MCP) e transporte (stdio/HTTP) são camadas independentes que podem evoluir sem quebrar as demais.

---
