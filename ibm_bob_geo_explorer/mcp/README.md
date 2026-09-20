# ibm_bob_geo_explorer — MCP Server

Servidor MCP (Model Context Protocol) que expõe os dados e comandos do **ibm_bob_geo_explorer** para que qualquer cliente MCP (Bob, Claude Desktop, etc.) ou sistema externo possa consumir as trilhas de formação via **stdio**, **HTTP/API** ou **SSO**.

---

## Arquitetura

```
ibm_bob_geo_explorer/mcp/
├── src/
│   ├── dio.ts       ← lógica de negócio (trilha, desafio, certificado)
│   ├── index.ts     ← servidor MCP — transporte stdio (Bob local)
│   └── http.ts      ← servidor MCP — transporte HTTP (API / SSO)
├── build/           ← artefatos compilados (gerado por `npm run build`)
├── package.json
└── tsconfig.json
```

---

## Pré-requisitos

- **Node.js ≥ 18** — https://nodejs.org
- npm (incluído com Node.js)

---

## Instalação e build

```bash
cd ibm_bob_geo_explorer/mcp
npm install
npm run build
```

O diretório `build/` será criado com `index.js` e `http.js`.

---

## Ferramentas expostas

| Tool | Descrição | Parâmetros |
|---|---|---|
| `list_trilhas` | Lista todas as trilhas disponíveis | — |
| `trilha` | Overview completo de uma trilha (módulos, badges, promoções, lives) | `tecnologia` (string) |
| `desafio` | Gera um desafio de código | `tecnologia`, `nivel?` (iniciante / intermediário / avançado) |
| `certificado` | Emite certificado de conclusão | `nome`, `tecnologia` |

---

## Modo 1 — Stdio (Bob local)

O arquivo `.bob/mcp.json` já registra o servidor automaticamente. Após o build, Bob conecta e você pode usar diretamente no chat:

```
liste todas as trilhas
mostre a trilha de Python
gere um desafio de Java nível avançado
emita o certificado de Ana Silva para React
```

---

## Modo 2 — HTTP / API REST

Ideal para integrações externas, pipelines CI/CD ou consumo via API Gateway.

### Iniciar

```bash
PORT=3000 API_KEY=minha-chave-secreta node build/http.js
```

### Endpoint MCP

```
POST http://localhost:3000/mcp
Content-Type: application/json
Authorization: Bearer minha-chave-secreta
```

### Health check

```
GET http://localhost:3000/health
```

### Exemplo de chamada com curl

```bash
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer minha-chave-secreta" \
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

---

## Modo 3 — HTTPS / SSO (produção)

O servidor HTTP não termina TLS diretamente — coloque-o atrás de um **reverse proxy** (nginx, AWS API Gateway, Azure APIM) que:

1. **Termina TLS** (certificado HTTPS).
2. **Valida o token SSO** (OIDC/OAuth2 — ex.: Azure AD, Okta, Auth0) e injeta os claims no header `Authorization`.
3. **Encaminha** para `http://localhost:3000/mcp` com o header `Authorization: Bearer <api-key-interna>`.

```
Client → [HTTPS + SSO provider] → nginx/API GW → [HTTP] → dio-explorer-mcp :3000
```

O campo `API_KEY` no processo Node serve como chave compartilhada interna entre o proxy e o servidor.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta TCP do servidor HTTP |
| `API_KEY` | *(vazio — sem autenticação)* | Chave Bearer exigida em todos os requests |
| `ALLOWED_ORIGIN` | `*` | Header `Access-Control-Allow-Origin` |

---

## Estrutura de sessões HTTP

O servidor HTTP gerencia sessões por `mcp-session-id`. Cada cliente novo recebe um ID de sessão na primeira resposta e deve reenviá-lo no header `mcp-session-id` em chamadas subsequentes para reutilizar o canal MCP.

---

## Tecnologias disponíveis (dados em `../data/trilhas_dio.json`)

Execute `list_trilhas` para ver a lista completa e atualizada.

---

*ibm_bob_geo_explorer MCP Server — parte do projeto ibm_bob_geo.*
