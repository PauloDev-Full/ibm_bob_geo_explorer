/**
 * dio.ts
 * ------
 * Pure TypeScript re-implementation of the ibm_bob_geo_explorer core logic,
 * mirroring the Python module at ../src/dio_commands.py.
 * All public functions return plain strings (Markdown-formatted).
 */

import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Badge {
  nome: string;
  descricao: string;
  xp_requerido: number;
}

interface Promocao {
  desconto_disponivel: boolean;
  percentual_desconto: number;
  descricao_promocao: string;
  validade_promocao: string | null;
}

interface Vitalicio {
  disponivel: boolean;
  preco_vitalicio_brl: number | null;
  descricao: string;
}

interface Live {
  titulo: string;
  frequencia: string;
  plataforma: string;
}

interface Trilha {
  id: number;
  nome: string;
  tecnologia: string;
  nivel: string;
  numero_de_modulos: number;
  xp_total: number;
  duracao_horas: number;
  descricao: string;
  badges_disponiveis: Badge[];
  promocoes: Promocao;
  vitalicio: Vitalicio;
  lives_ao_vivo: Live[];
  conteudos_modulos: string[];
  certificado: boolean;
  plano_requerido: string;
}

interface DioData {
  fonte: string;
  ultima_atualizacao: string;
  trilhas_formacao: Trilha[];
  resumo: {
    total_trilhas: number;
    tecnologias_cobertas: string[];
    xp_total_disponivel: number;
    total_badges: number;
    total_horas_conteudo: number;
  };
}

// ---------------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const DATA_PATH = join(__dirname, "../../data/trilhas_dio.json");

export function loadData(): DioData {
  const raw = readFileSync(DATA_PATH, "utf-8");
  return JSON.parse(raw) as DioData;
}

export function findTrilha(data: DioData, tecnologia: string): Trilha | undefined {
  const key = tecnologia.trim().toLowerCase();
  return data.trilhas_formacao.find((t) => t.tecnologia.toLowerCase() === key);
}

export function listTecnologias(data: DioData): string[] {
  return data.trilhas_formacao.map((t) => t.tecnologia);
}

// ---------------------------------------------------------------------------
// /trilha
// ---------------------------------------------------------------------------

export function cmdTrilha(tecnologia: string): string {
  const data = loadData();
  const trilha = findTrilha(data, tecnologia);

  if (!trilha) {
    const available = listTecnologias(data).join(", ");
    throw new Error(
      `Trilha para '${tecnologia}' não encontrada. Tecnologias disponíveis: ${available}`
    );
  }

  const certStr = trilha.certificado ? "Sim" : "Não";
  const lines: string[] = [
    `# 🎯 Trilha: ${trilha.nome}`,
    "",
    `> ${trilha.descricao}`,
    "",
    "| Campo             | Detalhe                  |",
    "|-------------------|--------------------------|",
    `| 🏆 Nível          | ${trilha.nivel}           |`,
    `| 📦 Módulos        | ${trilha.numero_de_modulos}  |`,
    `| ⏱️ Duração        | ${trilha.duracao_horas}h  |`,
    `| ✨ XP Total        | ${trilha.xp_total} XP     |`,
    `| 📜 Certificado    | ${certStr}               |`,
    `| 💳 Plano          | ${trilha.plano_requerido} |`,
    "",
    "## 📚 Módulos do Plano de Estudos",
    "",
  ];

  trilha.conteudos_modulos.forEach((modulo, i) => {
    lines.push(`📖 ${i + 1}. ${modulo}`);
  });

  lines.push("", "## 🏅 Badges Disponíveis", "");
  trilha.badges_disponiveis.forEach((badge) => {
    lines.push(
      `- **${badge.nome}**: ${badge.descricao} *(XP necessário: ${badge.xp_requerido})*`
    );
  });

  lines.push("", "## 🎥 Lives & Mentorias", "");
  trilha.lives_ao_vivo.forEach((live) => {
    lines.push(`- **${live.titulo}** — ${live.frequencia} | 📡 ${live.plataforma}`);
  });

  lines.push("", "## 💰 Promoções & Planos", "");
  if (trilha.promocoes.desconto_disponivel) {
    lines.push(
      `> 🔥 **Promoção ativa:** ${trilha.promocoes.descricao_promocao} — válida até ${trilha.promocoes.validade_promocao}`
    );
  }
  if (trilha.vitalicio.disponivel && trilha.vitalicio.preco_vitalicio_brl) {
    lines.push(
      `> 💎 **Plano Vitalício:** R$ ${trilha.vitalicio.preco_vitalicio_brl.toFixed(2)} — ${trilha.vitalicio.descricao}`
    );
  }

  lines.push(
    "",
    "> 💡 *Use `/desafio` para gerar um desafio de código dessa tecnologia ou `/certificado` para emitir seu certificado ao concluir a trilha!*"
  );

  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// /desafio
// ---------------------------------------------------------------------------

type Level = "iniciante" | "intermediário" | "avançado";

function normaliseLevel(nivel: string): Level {
  const n = nivel.trim().toLowerCase();
  const map: Record<string, Level> = {
    avancado: "avançado",
    "avançado": "avançado",
    intermediario: "intermediário",
    "intermediário": "intermediário",
    iniciante: "iniciante",
  };
  return map[n] ?? "intermediário";
}

const GENERIC_CHALLENGE: Record<Level, Record<string, string>> = {
  iniciante: {
    titulo: "Verificador de Palíndromo",
    descricao:
      "Escreva uma função que receba uma string e retorne true se ela for um palíndromo (igual lida de trás para frente, ignorando espaços e maiúsculas).",
    entrada: "Uma string s",
    saida: "true ou false",
    ex1_in: "racecar",
    ex1_out: "true",
    ex2_in: "hello",
    ex2_out: "false",
    dica: "Normalize a string removendo espaços e convertendo para minúsculas antes de comparar.",
    criterio: "Tratar strings vazias retornando true",
    tempo: "15",
  },
  "intermediário": {
    titulo: "Anagramas em Grupos",
    descricao:
      'Dado um array de strings, agrupe os anagramas. Dois strings são anagramas se contêm os mesmos caracteres com as mesmas frequências.',
    entrada: "Um array de strings",
    saida: "Lista de listas com grupos de anagramas",
    ex1_in: '["eat","tea","tan","ate","nat","bat"]',
    ex1_out: '[["eat","tea","ate"],["tan","nat"],["bat"]]',
    ex2_in: '["a"]',
    ex2_out: '[["a"]]',
    dica: "Use a string ordenada de cada palavra como chave de um dicionário/mapa.",
    criterio: "Solução deve ter complexidade O(n·k·log k), onde k é o tamanho máximo da string",
    tempo: "40",
  },
  "avançado": {
    titulo: "LRU Cache",
    descricao:
      "Implemente uma estrutura de dados LRU Cache com complexidade O(1) para get e put. O cache tem capacidade fixa; ao atingi-la, o item menos recentemente usado deve ser removido.",
    entrada: "Capacidade do cache; operações get(key) e put(key, value)",
    saida: "Valor para get, ou -1 se não encontrado",
    ex1_in: "LRUCache(2); put(1,1); put(2,2); get(1)",
    ex1_out: "1",
    ex2_in: "put(3,3); get(2)",
    ex2_out: "-1  (chave 2 foi evicted)",
    dica: "Combine um HashMap com uma Doubly Linked List para manter ordem de uso em O(1).",
    criterio: "Implementar sem usar estruturas de cache prontas da biblioteca padrão",
    tempo: "60",
  },
};

export function cmdDesafio(tecnologia: string, nivel = "intermediário"): string {
  const data = loadData();
  const trilha = findTrilha(data, tecnologia);

  if (!trilha) {
    const available = listTecnologias(data).join(", ");
    throw new Error(`Tecnologia '${tecnologia}' não encontrada. Disponíveis: ${available}`);
  }

  const effectiveLevel = normaliseLevel(nivel);
  const tpl = GENERIC_CHALLENGE[effectiveLevel];

  const lines = [
    `# ⚡ Desafio de Código — ${trilha.tecnologia}`,
    "",
    `> 🎯 **Nível:** ${effectiveLevel} | ⏱️ **Tempo sugerido:** ${tpl.tempo} minutos`,
    "",
    "## 📋 Descrição do Desafio",
    "",
    tpl.descricao,
    "",
    "## 📥 Entrada Esperada",
    "",
    tpl.entrada,
    "",
    "## 📤 Saída Esperada",
    "",
    tpl.saida,
    "",
    "## 🧪 Exemplos",
    "",
    "**Exemplo 1:**",
    "```",
    `Entrada: ${tpl.ex1_in}`,
    `Saída:   ${tpl.ex1_out}`,
    "```",
    "",
    "**Exemplo 2:**",
    "```",
    `Entrada: ${tpl.ex2_in}`,
    `Saída:   ${tpl.ex2_out}`,
    "```",
    "",
    "## 💡 Dica",
    "",
    `> ${tpl.dica}`,
    "",
    "## ✅ Critérios de Aceitação",
    "",
    "- [ ] O código deve resolver todos os exemplos fornecidos",
    "- [ ] O código deve ser legível e bem comentado",
    `- [ ] ${tpl.criterio}`,
    "",
    "---",
    "",
    `> 🏆 *Conseguiu resolver? Use \`/certificado\` para emitir seu certificado ao concluir a trilha completa de ${trilha.tecnologia}!*`,
  ];

  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// /certificado
// ---------------------------------------------------------------------------

function generateCertId(tecnologia: string): string {
  const year = new Date().getFullYear();
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  const suffix = Array.from({ length: 6 }, () =>
    chars[Math.floor(Math.random() * chars.length)]
  ).join("");
  const tec = tecnologia.toUpperCase().replace(/[^A-Z0-9]/g, "");
  return `DIO-${tec}-${year}-${suffix}`;
}

export function cmdCertificado(nome: string, tecnologia: string): string {
  const data = loadData();
  const trilha = findTrilha(data, tecnologia);

  if (!trilha) {
    const available = listTecnologias(data).join(", ");
    throw new Error(`Tecnologia '${tecnologia}' não encontrada. Disponíveis: ${available}`);
  }

  const today = new Date().toLocaleDateString("pt-BR");
  const cid = generateCertId(trilha.tecnologia);
  const badgesLines = trilha.badges_disponiveis
    .map((b) => `- 🥇 **${b.nome}** — ${b.descricao}`)
    .join("\n");

  return [
    "╔══════════════════════════════════════════════════════════════════╗",
    "║                                                                  ║",
    "║                    🎓  CERTIFICADO DE CONCLUSÃO                  ║",
    "║                                                                  ║",
    "║                     [ DIO — Digital Innovation One ]            ║",
    "║                                                                  ║",
    "╚══════════════════════════════════════════════════════════════════╝",
    "",
    "---",
    "",
    "## Certificamos que",
    "",
    `# ✨ ${nome} ✨`,
    "",
    "concluiu com êxito a formação",
    "",
    `## 🏆 ${trilha.nome}`,
    "",
    "---",
    "",
    "### 📋 Detalhes da Formação",
    "",
    "| Campo              | Informação                        |",
    "|--------------------|-----------------------------------|",
    `| 🎯 Tecnologia      | ${trilha.tecnologia}               |`,
    `| 📊 Nível           | ${trilha.nivel}                    |`,
    `| 📦 Módulos         | ${trilha.numero_de_modulos} módulos |`,
    `| ⏱️ Carga Horária   | ${trilha.duracao_horas} horas      |`,
    `| ✨ XP Conquistado   | ${trilha.xp_total} XP              |`,
    "",
    "---",
    "",
    "### 🏅 Badges Conquistadas",
    "",
    badgesLines,
    "",
    "---",
    "",
    "> *Este certificado atesta que o(a) profissional demonstrou domínio dos*",
    "> *conhecimentos e habilidades práticas exigidos pela formação acima.*",
    "",
    "---",
    "",
    `📅 **Data de Emissão:** ${today}`,
    `🔑 **ID do Certificado:** ${cid}`,
    "🌐 **Verificar em:** https://www.dio.me/certificate",
    "",
    "---",
    "",
    "*Powered by DIO — Digital Innovation One*",
    "*\"Transformando talentos em profissionais de tecnologia.\"*",
    "",
    `> 💡 *Parabéns, **${nome}**! Agora compartilhe seu certificado no LinkedIn e no GitHub para mostrar suas conquistas.*`,
  ].join("\n");
}
