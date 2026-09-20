/**
 * http.ts — DIO Explorer MCP Server (HTTP/SSO transport)
 * --------------------------------------------------------
 * Starts an Express HTTP server that exposes the same MCP tools
 * over a Streamable-HTTP transport (POST /mcp).
 *
 * Environment variables:
 *   PORT          - TCP port to listen on (default: 3000)
 *   API_KEY       - If set, all requests must include header  Authorization: Bearer <API_KEY>
 *   ALLOWED_ORIGIN- CORS origin allowed (default: *)
 *
 * Usage:
 *   node build/http.js
 *
 * Production (HTTPS / SSO):
 *   Place behind a reverse proxy (nginx / API Gateway) that terminates TLS
 *   and handles SSO token validation before forwarding to this process.
 *   The optional API_KEY guard provides a basic shared-secret layer.
 */

import express, { Request, Response, NextFunction } from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import { cmdTrilha, cmdDesafio, cmdCertificado, loadData } from "./dio.js";

const PORT = parseInt(process.env["PORT"] ?? "3000", 10);
const API_KEY = process.env["API_KEY"] ?? "";
const ALLOWED_ORIGIN = process.env["ALLOWED_ORIGIN"] ?? "*";

// ---------------------------------------------------------------------------
// Build MCP server (same tools as stdio transport)
// ---------------------------------------------------------------------------
function buildMcpServer(): McpServer {
  const server = new McpServer({ name: "dio-explorer", version: "0.1.0" });

  server.registerTool(
    "list_trilhas",
    {
      description: "Lista todas as trilhas de formação disponíveis na plataforma DIO.",
      inputSchema: z.object({}),
    },
    async () => {
      try {
        const data = loadData();
        const lines = [
          "# 📋 Trilhas de Formação DIO",
          "",
          `> Total: ${data.resumo.total_trilhas} trilhas | ${data.resumo.total_horas_conteudo}h de conteúdo | ${data.resumo.xp_total_disponivel} XP disponíveis`,
          "",
          "| # | Tecnologia | Nível | Módulos | Horas | XP | Plano |",
          "|---|-----------|-------|---------|-------|----|-------|",
        ];
        data.trilhas_formacao.forEach((t, i) => {
          lines.push(
            `| ${i + 1} | ${t.tecnologia} | ${t.nivel} | ${t.numero_de_modulos} | ${t.duracao_horas}h | ${t.xp_total} | ${t.plano_requerido} |`
          );
        });
        lines.push("", `*Última atualização: ${data.ultima_atualizacao}*`);
        return { content: [{ type: "text" as const, text: lines.join("\n") }] };
      } catch (err) {
        return {
          content: [{ type: "text" as const, text: `Erro: ${err instanceof Error ? err.message : String(err)}` }],
          isError: true,
        };
      }
    }
  );

  server.registerTool(
    "trilha",
    {
      description: "Retorna o overview completo de uma trilha de formação DIO.",
      inputSchema: z.object({
        tecnologia: z.string().describe("Nome da tecnologia (ex: Java, Python, React). Case-insensitive."),
      }),
    },
    async ({ tecnologia }) => {
      try {
        return { content: [{ type: "text" as const, text: cmdTrilha(tecnologia) }] };
      } catch (err) {
        return {
          content: [{ type: "text" as const, text: `Erro: ${err instanceof Error ? err.message : String(err)}` }],
          isError: true,
        };
      }
    }
  );

  server.registerTool(
    "desafio",
    {
      description: "Gera um desafio de código para a tecnologia e nível especificados.",
      inputSchema: z.object({
        tecnologia: z.string().describe("Nome da tecnologia (ex: Java, Python, React)."),
        nivel: z
          .enum(["iniciante", "intermediário", "avançado"])
          .optional()
          .describe("Nível de dificuldade. Padrão: intermediário."),
      }),
    },
    async ({ tecnologia, nivel }) => {
      try {
        return { content: [{ type: "text" as const, text: cmdDesafio(tecnologia, nivel ?? "intermediário") }] };
      } catch (err) {
        return {
          content: [{ type: "text" as const, text: `Erro: ${err instanceof Error ? err.message : String(err)}` }],
          isError: true,
        };
      }
    }
  );

  server.registerTool(
    "certificado",
    {
      description: "Emite um certificado de conclusão de trilha para o usuário informado.",
      inputSchema: z.object({
        nome: z.string().describe("Nome completo do(a) aluno(a)."),
        tecnologia: z.string().describe("Tecnologia da trilha concluída (ex: Java, Python)."),
      }),
    },
    async ({ nome, tecnologia }) => {
      try {
        return { content: [{ type: "text" as const, text: cmdCertificado(nome, tecnologia) }] };
      } catch (err) {
        return {
          content: [{ type: "text" as const, text: `Erro: ${err instanceof Error ? err.message : String(err)}` }],
          isError: true,
        };
      }
    }
  );

  return server;
}

// ---------------------------------------------------------------------------
// Express app
// ---------------------------------------------------------------------------
const app = express();
app.use(express.json());

// CORS
app.use((_req: Request, res: Response, next: NextFunction) => {
  res.setHeader("Access-Control-Allow-Origin", ALLOWED_ORIGIN);
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, mcp-session-id");
  next();
});

app.options("*", (_req: Request, res: Response) => {
  res.sendStatus(204);
});

// Optional API-key guard
function authMiddleware(req: Request, res: Response, next: NextFunction) {
  if (!API_KEY) return next();
  const auth = req.headers["authorization"] ?? "";
  if (auth === `Bearer ${API_KEY}`) return next();
  res.status(401).json({ error: "Unauthorized — invalid or missing API key" });
}

// Health check (no auth required)
app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "ok", server: "dio-explorer-mcp", version: "0.1.0" });
});

// MCP endpoint — one transport instance per session
const transports = new Map<string, StreamableHTTPServerTransport>();

app.all("/mcp", authMiddleware, async (req: Request, res: Response) => {
  try {
    // Session-based transport reuse
    const sessionId = req.headers["mcp-session-id"] as string | undefined;
    let transport = sessionId ? transports.get(sessionId) : undefined;

    if (!transport) {
      transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => crypto.randomUUID(),
        onsessioninitialized: (id) => {
          transports.set(id, transport!);
          console.error(`[dio-explorer] new session: ${id}`);
        },
      });
      transport.onclose = () => {
        if (transport!.sessionId) {
          transports.delete(transport!.sessionId);
          console.error(`[dio-explorer] session closed: ${transport!.sessionId}`);
        }
      };
      const mcpServer = buildMcpServer();
      await mcpServer.connect(transport);
    }

    await transport.handleRequest(req, res, req.body);
  } catch (err) {
    console.error("[dio-explorer] request error:", err);
    if (!res.headersSent) {
      res.status(500).json({ error: "Internal server error" });
    }
  }
});

app.listen(PORT, () => {
  console.error(
    `[dio-explorer] HTTP MCP server listening on http://0.0.0.0:${PORT}/mcp`
  );
  if (API_KEY) {
    console.error(`[dio-explorer] API key protection ENABLED`);
  } else {
    console.error(`[dio-explorer] WARNING: no API_KEY set — server is open`);
  }
});
