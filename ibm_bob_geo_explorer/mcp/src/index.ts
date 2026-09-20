#!/usr/bin/env node
/**
 * index.ts — ibm_bob_geo_explorer MCP Server (stdio transport)
 * -------------------------------------------------------
 * Runs as a child process spawned by Bob via stdio.
 * Exposes four tools:
 *   - list_trilhas   : list all available learning paths
 *   - trilha         : get a full learning-path overview
 *   - desafio        : generate a coding challenge
 *   - certificado    : emit a mock completion certificate
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { cmdTrilha, cmdDesafio, cmdCertificado, loadData, listTecnologias } from "./dio.js";

const server = new McpServer({ name: "ibm-bob-geo-explorer", version: "0.1.0" });

// ---------------------------------------------------------------------------
// Tool: list_trilhas
// ---------------------------------------------------------------------------
server.registerTool(
  "list_trilhas",
  {
    description:
      "Lista todas as trilhas de formação disponíveis na plataforma DIO com seus metadados principais.",
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

// ---------------------------------------------------------------------------
// Tool: trilha
// ---------------------------------------------------------------------------
server.registerTool(
  "trilha",
  {
    description:
      "Retorna o overview completo de uma trilha de formação DIO incluindo módulos, badges, lives e promoções.",
    inputSchema: z.object({
      tecnologia: z
        .string()
        .describe("Nome da tecnologia (ex: Java, Python, React, Node.js). Case-insensitive."),
    }),
  },
  async ({ tecnologia }) => {
    try {
      const result = cmdTrilha(tecnologia);
      return { content: [{ type: "text" as const, text: result }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Erro: ${err instanceof Error ? err.message : String(err)}` }],
        isError: true,
      };
    }
  }
);

// ---------------------------------------------------------------------------
// Tool: desafio
// ---------------------------------------------------------------------------
server.registerTool(
  "desafio",
  {
    description:
      "Gera um desafio de código para a tecnologia e nível especificados.",
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
      const result = cmdDesafio(tecnologia, nivel ?? "intermediário");
      return { content: [{ type: "text" as const, text: result }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Erro: ${err instanceof Error ? err.message : String(err)}` }],
        isError: true,
      };
    }
  }
);

// ---------------------------------------------------------------------------
// Tool: certificado
// ---------------------------------------------------------------------------
server.registerTool(
  "certificado",
  {
    description:
      "Emite um certificado de conclusão de trilha para o usuário informado.",
    inputSchema: z.object({
      nome: z.string().describe("Nome completo do(a) aluno(a)."),
      tecnologia: z.string().describe("Tecnologia da trilha concluída (ex: Java, Python)."),
    }),
  },
  async ({ nome, tecnologia }) => {
    try {
      const result = cmdCertificado(nome, tecnologia);
      return { content: [{ type: "text" as const, text: result }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Erro: ${err instanceof Error ? err.message : String(err)}` }],
        isError: true,
      };
    }
  }
);

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ibm-bob-geo-explorer MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
