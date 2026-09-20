"""
dio_commands.py
---------------
Core logic for the ibm_bob_geo_explorer Bob commands:
  - trilha      : renders a learning-path overview from trilhas_dio.json
  - desafio     : generates a formatted coding challenge for a technology
  - certificado : emits a mock completion certificate

All public functions return a plain string (Markdown-formatted).
"""

from __future__ import annotations

import json
import os
import random
import re
import string
from datetime import date
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_DATA_PATH = Path(__file__).parent.parent / "data" / "trilhas_dio.json"

_VALID_LEVELS = {"iniciante", "intermediário", "avancado", "avançado"}

_CHALLENGE_TEMPLATES: dict[str, dict[str, dict]] = {
    "Java": {
        "iniciante": {
            "titulo": "Calculadora de Notas",
            "descricao": (
                "Crie um programa Java que leia as notas de 3 avaliações de um aluno "
                "(valores de 0 a 10) e calcule a média aritmética. "
                "Exiba se o aluno foi aprovado (média ≥ 6.0) ou reprovado."
            ),
            "entrada": "Três valores decimais separados por espaço: nota1 nota2 nota3",
            "saida": "A média calculada e o status: Aprovado ou Reprovado",
            "ex1_in": "7.0 8.0 9.0",
            "ex1_out": "Média: 8.0 — Aprovado",
            "ex2_in": "4.0 5.0 3.0",
            "ex2_out": "Média: 4.0 — Reprovado",
            "dica": "Utilize a classe Scanner para leitura, e operador ternário ou if/else para o status.",
            "criterio": "Tratar entradas fora do intervalo 0-10 com mensagem de erro",
            "tempo": "20",
        },
        "intermediário": {
            "titulo": "Gerenciador de Tarefas com POO",
            "descricao": (
                "Implemente uma mini aplicação de gerenciamento de tarefas em Java "
                "usando conceitos de POO. A classe `Task` deve ter: título, descrição, "
                "prioridade (HIGH/MEDIUM/LOW) e status (PENDING/DONE). "
                "Implemente um `TaskManager` que permita adicionar, listar e concluir tarefas."
            ),
            "entrada": "Comandos via console: ADD <titulo> <prioridade>, DONE <titulo>, LIST",
            "saida": "Listagem formatada das tarefas e confirmações de operação",
            "ex1_in": "ADD 'Estudar Java' HIGH",
            "ex1_out": "Tarefa 'Estudar Java' adicionada com prioridade HIGH",
            "ex2_in": "LIST",
            "ex2_out": "[PENDING] Estudar Java — HIGH",
            "dica": "Use um `ArrayList<Task>` no TaskManager e encapsule os campos com getters/setters.",
            "criterio": "Usar herança ou interface `Comparable` para ordenar tarefas por prioridade",
            "tempo": "45",
        },
        "avançado": {
            "titulo": "API REST de Inventário com Spring Boot",
            "descricao": (
                "Desenvolva uma API RESTful com Spring Boot para gerenciar um inventário de produtos. "
                "Implemente endpoints CRUD completos, validação de dados com Bean Validation, "
                "persistência com Spring Data JPA (H2 em memória), tratamento global de exceções "
                "com `@ControllerAdvice` e testes de integração com MockMvc."
            ),
            "entrada": "Requisições HTTP (JSON) nos endpoints: POST /products, GET /products, PUT /products/{id}, DELETE /products/{id}",
            "saida": "Respostas JSON com status HTTP adequados (200, 201, 404, 400)",
            "ex1_in": 'POST /products  Body: {"name":"Notebook","price":4500.0,"stock":10}',
            "ex1_out": '201 Created  Body: {"id":1,"name":"Notebook","price":4500.0,"stock":10}',
            "ex2_in": "GET /products/999",
            "ex2_out": '404 Not Found  Body: {"error":"Product not found"}',
            "dica": "Separe as camadas Controller → Service → Repository. Use `@Valid` nos DTOs de entrada.",
            "criterio": "Cobertura de testes ≥ 80% nas camadas Service e Controller",
            "tempo": "90",
        },
    }
}

_GENERIC_CHALLENGE: dict[str, dict] = {
    "iniciante": {
        "titulo": "Verificador de Palíndromo",
        "descricao": "Escreva uma função que receba uma string e retorne true se ela for um palíndromo (igual lida de trás para frente, ignorando espaços e maiúsculas).",
        "entrada": "Uma string s",
        "saida": "true ou false",
        "ex1_in": "racecar",
        "ex1_out": "true",
        "ex2_in": "hello",
        "ex2_out": "false",
        "dica": "Normalize a string removendo espaços e convertendo para minúsculas antes de comparar.",
        "criterio": "Tratar strings vazias retornando true",
        "tempo": "15",
    },
    "intermediário": {
        "titulo": "Anagramas em Grupos",
        "descricao": "Dado um array de strings, agrupe os anagramas. Dois strings são anagramas se contêm os mesmos caracteres com as mesmas frequências.",
        "entrada": "Um array de strings",
        "saida": "Lista de listas com grupos de anagramas",
        "ex1_in": '["eat","tea","tan","ate","nat","bat"]',
        "ex1_out": '[["eat","tea","ate"],["tan","nat"],["bat"]]',
        "ex2_in": '["a"]',
        "ex2_out": '[["a"]]',
        "dica": "Use a string ordenada de cada palavra como chave de um dicionário/mapa.",
        "criterio": "Solução deve ter complexidade O(n·k·log k), onde k é o tamanho máximo da string",
        "tempo": "40",
    },
    "avançado": {
        "titulo": "LRU Cache",
        "descricao": "Implemente uma estrutura de dados LRU Cache com complexidade O(1) para get e put. O cache tem capacidade fixa; ao atingi-la, o item menos recentemente usado deve ser removido.",
        "entrada": "Capacidade do cache; operações get(key) e put(key, value)",
        "saida": "Valor para get, ou -1 se não encontrado",
        "ex1_in": "LRUCache(2); put(1,1); put(2,2); get(1)",
        "ex1_out": "1",
        "ex2_in": "put(3,3); get(2)",
        "ex2_out": "-1  (chave 2 foi evicted)",
        "dica": "Combine um HashMap com uma Doubly Linked List para manter ordem de uso em O(1).",
        "criterio": "Implementar sem usar estruturas de cache prontas da biblioteca padrão",
        "tempo": "60",
    },
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(data_path: Optional[str | Path] = None) -> dict:
    """Load and return the trilhas JSON data."""
    path = Path(data_path) if data_path else _DEFAULT_DATA_PATH
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def find_trilha(data: dict, tecnologia: str) -> Optional[dict]:
    """Return the trilha dict whose *tecnologia* matches case-insensitively, or None."""
    key = tecnologia.strip().lower()
    for trilha in data.get("trilhas_formacao", []):
        if trilha.get("tecnologia", "").lower() == key:
            return trilha
    return None


def list_tecnologias(data: dict) -> list[str]:
    """Return all technology names present in the dataset."""
    return [t["tecnologia"] for t in data.get("trilhas_formacao", [])]


# ---------------------------------------------------------------------------
# /trilha command
# ---------------------------------------------------------------------------

def cmd_trilha(tecnologia: str, data_path: Optional[str | Path] = None) -> str:
    """
    Render the learning-path overview for *tecnologia*.

    Returns a Markdown string following the trilha.md command format.
    Raises ValueError if the technology is not found.
    """
    data = load_data(data_path)
    trilha = find_trilha(data, tecnologia)

    if trilha is None:
        available = ", ".join(list_tecnologias(data))
        raise ValueError(
            f"Trilha para '{tecnologia}' não encontrada. "
            f"Tecnologias disponíveis: {available}"
        )

    cert_str = "Sim" if trilha.get("certificado") else "Não"

    lines: list[str] = [
        f"# 🎯 Trilha: {trilha['nome']}",
        "",
        f"> {trilha['descricao']}",
        "",
        "| Campo             | Detalhe                  |",
        "|-------------------|--------------------------|",
        f"| 🏆 Nível          | {trilha['nivel']}         |",
        f"| 📦 Módulos        | {trilha['numero_de_modulos']}  |",
        f"| ⏱️ Duração        | {trilha['duracao_horas']}h |",
        f"| ✨ XP Total        | {trilha['xp_total']} XP   |",
        f"| 📜 Certificado    | {cert_str}               |",
        f"| 💳 Plano          | {trilha['plano_requerido']} |",
        "",
        "## 📚 Módulos do Plano de Estudos",
        "",
    ]

    for i, modulo in enumerate(trilha.get("conteudos_modulos", []), start=1):
        lines.append(f"📖 {i}. {modulo}")

    lines += ["", "## 🏅 Badges Disponíveis", ""]
    for badge in trilha.get("badges_disponiveis", []):
        lines.append(
            f"- **{badge['nome']}**: {badge['descricao']} *(XP necessário: {badge['xp_requerido']})*"
        )

    lines += ["", "## 🎥 Lives & Mentorias", ""]
    for live in trilha.get("lives_ao_vivo", []):
        lines.append(
            f"- **{live['titulo']}** — {live['frequencia']} | 📡 {live['plataforma']}"
        )

    lines += ["", "## 💰 Promoções & Planos", ""]
    promo = trilha.get("promocoes", {})
    if promo.get("desconto_disponivel"):
        lines.append(
            f"> 🔥 **Promoção ativa:** {promo['descricao_promocao']} "
            f"— válida até {promo['validade_promocao']}"
        )

    vit = trilha.get("vitalicio", {})
    if vit.get("disponivel"):
        lines.append(
            f"> 💎 **Plano Vitalício:** R$ {vit['preco_vitalicio_brl']:.2f} — {vit['descricao']}"
        )

    lines += [
        "",
        "> 💡 *Use `/desafio` para gerar um desafio de código dessa tecnologia "
        "ou `/certificado` para emitir seu certificado ao concluir a trilha!*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# /desafio command
# ---------------------------------------------------------------------------

def _normalise_level(nivel: str) -> str:
    """Normalise level string; falls back to 'intermediário' if unrecognised."""
    n = nivel.strip().lower()
    mapping = {
        "avancado": "avançado",
        "avançado": "avançado",
        "intermediario": "intermediário",
        "intermediário": "intermediário",
        "iniciante": "iniciante",
    }
    return mapping.get(n, "intermediário")


def cmd_desafio(
    tecnologia: str,
    nivel: str = "intermediário",
    data_path: Optional[str | Path] = None,
) -> tuple[str, str]:
    """
    Generate a coding challenge for *tecnologia* at *nivel*.

    Returns ``(markdown_output, effective_level)``.
    ``effective_level`` may differ from *nivel* when an invalid value was supplied.
    Raises ValueError if the technology is not found.
    """
    data = load_data(data_path)
    trilha = find_trilha(data, tecnologia)

    if trilha is None:
        available = ", ".join(list_tecnologias(data))
        raise ValueError(
            f"Tecnologia '{tecnologia}' não encontrada. "
            f"Disponíveis: {available}"
        )

    effective_level = _normalise_level(nivel)
    level_warning = ""
    if nivel.strip().lower() not in _VALID_LEVELS and nivel.strip().lower() not in {
        "avancado", "intermediario"
    }:
        level_warning = (
            f"> ⚠️ Nível '{nivel}' não reconhecido. Usando **intermediário** como padrão.\n\n"
        )
        effective_level = "intermediário"

    tec_key = tecnologia.strip().capitalize()
    templates = _CHALLENGE_TEMPLATES.get(tec_key, _GENERIC_CHALLENGE)
    tpl = templates.get(effective_level, templates.get("intermediário", {}))

    if not tpl:
        tpl = _GENERIC_CHALLENGE.get(effective_level, _GENERIC_CHALLENGE["intermediário"])

    lines = [
        f"# ⚡ Desafio de Código — {trilha['tecnologia']}",
        "",
        f"> 🎯 **Nível:** {effective_level} | ⏱️ **Tempo sugerido:** {tpl['tempo']} minutos",
        "",
        "## 📋 Descrição do Desafio",
        "",
        tpl["descricao"],
        "",
        "## 📥 Entrada Esperada",
        "",
        tpl["entrada"],
        "",
        "## 📤 Saída Esperada",
        "",
        tpl["saida"],
        "",
        "## 🧪 Exemplos",
        "",
        "**Exemplo 1:**",
        "```",
        f"Entrada: {tpl['ex1_in']}",
        f"Saída:   {tpl['ex1_out']}",
        "```",
        "",
        "**Exemplo 2:**",
        "```",
        f"Entrada: {tpl['ex2_in']}",
        f"Saída:   {tpl['ex2_out']}",
        "```",
        "",
        "## 💡 Dica",
        "",
        f"> {tpl['dica']}",
        "",
        "## ✅ Critérios de Aceitação",
        "",
        "- [ ] O código deve resolver todos os exemplos fornecidos",
        "- [ ] O código deve ser legível e bem comentado",
        f"- [ ] {tpl['criterio']}",
        "",
        "---",
        "",
        f"> 🏆 *Conseguiu resolver? Use `/certificado` para emitir seu certificado ao concluir a trilha completa de {trilha['tecnologia']}!*",
    ]

    return level_warning + "\n".join(lines), effective_level


# ---------------------------------------------------------------------------
# /certificado command
# ---------------------------------------------------------------------------

def _generate_cert_id(tecnologia: str) -> str:
    year = date.today().year
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    tec = re.sub(r"[^A-Z0-9]", "", tecnologia.upper())
    return f"DIO-{tec}-{year}-{suffix}"


def cmd_certificado(
    nome: str,
    tecnologia: str,
    data_path: Optional[str | Path] = None,
    cert_id: Optional[str] = None,
) -> str:
    """
    Emit a mock completion certificate for *nome* on *tecnologia*.

    *cert_id* can be supplied to make output deterministic (useful for tests).
    Raises ValueError if the technology is not found.
    """
    data = load_data(data_path)
    trilha = find_trilha(data, tecnologia)

    if trilha is None:
        available = ", ".join(list_tecnologias(data))
        raise ValueError(
            f"Tecnologia '{tecnologia}' não encontrada. "
            f"Disponíveis: {available}"
        )

    today = date.today().strftime("%d/%m/%Y")
    cid = cert_id or _generate_cert_id(trilha["tecnologia"])

    badges_lines = "\n".join(
        f"- 🥇 **{b['nome']}** — {b['descricao']}"
        for b in trilha.get("badges_disponiveis", [])
    )

    cert = (
        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║                                                                  ║\n"
        "║                    🎓  CERTIFICADO DE CONCLUSÃO                  ║\n"
        "║                                                                  ║\n"
        "║                     [ DIO — Digital Innovation One ]            ║\n"
        "║                                                                  ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n"
        "\n"
        "---\n"
        "\n"
        "## Certificamos que\n"
        "\n"
        f"# ✨ {nome} ✨\n"
        "\n"
        "concluiu com êxito a formação\n"
        "\n"
        f"## 🏆 {trilha['nome']}\n"
        "\n"
        "---\n"
        "\n"
        "### 📋 Detalhes da Formação\n"
        "\n"
        "| Campo              | Informação                        |\n"
        "|--------------------|-----------------------------------|\n"
        f"| 🎯 Tecnologia      | {trilha['tecnologia']}             |\n"
        f"| 📊 Nível           | {trilha['nivel']}                  |\n"
        f"| 📦 Módulos         | {trilha['numero_de_modulos']} módulos |\n"
        f"| ⏱️ Carga Horária   | {trilha['duracao_horas']} horas    |\n"
        f"| ✨ XP Conquistado   | {trilha['xp_total']} XP            |\n"
        "\n"
        "---\n"
        "\n"
        "### 🏅 Badges Conquistadas\n"
        "\n"
        f"{badges_lines}\n"
        "\n"
        "---\n"
        "\n"
        "> *Este certificado atesta que o(a) profissional demonstrou domínio dos*\n"
        "> *conhecimentos e habilidades práticas exigidos pela formação acima.*\n"
        "\n"
        "---\n"
        "\n"
        f"📅 **Data de Emissão:** {today}\n"
        f"🔑 **ID do Certificado:** {cid}\n"
        "🌐 **Verificar em:** https://www.dio.me/certificate\n"
        "\n"
        "---\n"
        "\n"
        "*Powered by DIO — Digital Innovation One*\n"
        "*\"Transformando talentos em profissionais de tecnologia.\"*"
    )

    footer = (
        f"\n\n> 💡 *Parabéns, **{nome}**! Agora compartilhe seu certificado no LinkedIn e no GitHub "
        f"para mostrar suas conquistas. Use `/trilha {tecnologia}` para revisar o plano de estudos "
        f"ou `/desafio {tecnologia} avançado` para um novo desafio!*"
    )

    return cert + footer
