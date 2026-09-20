"""
test_dio_commands.py
---------------------
Testes unitários para os comandos ibm_bob_geo_explorer:
  - /trilha      → cmd_trilha()
  - /desafio     → cmd_desafio()
  - /certificado → cmd_certificado()

Cobertura alvo: ≥ 70 %
Execute com:
    pytest ibm_bob_geo_explorer/tests/test_dio_commands.py -v --tb=short
    pytest ibm_bob_geo_explorer/tests/test_dio_commands.py --cov=ibm_bob_geo_explorer.src.dio_commands --cov-report=term-missing
"""

import json
import os
import sys
import re
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

# Garante que o pacote é encontrável independentemente de onde pytest é invocado
_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ibm_bob_geo_explorer.src.dio_commands import (
    load_data,
    find_trilha,
    list_tecnologias,
    cmd_trilha,
    cmd_desafio,
    cmd_certificado,
    _normalise_level,
    _generate_cert_id,
    _DEFAULT_DATA_PATH,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REAL_DATA_PATH = Path(__file__).parent.parent / "data" / "trilhas_dio.json"

# Minimal in-memory dataset used by most tests (isolates tests from filesystem)
_SAMPLE_TRILHA_JAVA = {
    "id": 2,
    "nome": "Formação Java Developer",
    "tecnologia": "Java",
    "nivel": "Básico ao Avançado",
    "numero_de_modulos": 10,
    "xp_total": 22000,
    "duracao_horas": 76,
    "descricao": "Formação completa em Java.",
    "badges_disponiveis": [
        {"nome": "Java Fundamentals", "descricao": "Complete os fundamentos", "xp_requerido": 4000},
        {"nome": "Spring Boot Expert", "descricao": "Domine Spring Boot", "xp_requerido": 12000},
        {"nome": "Java Developer", "descricao": "Conclusão da trilha", "xp_requerido": 22000},
    ],
    "promocoes": {
        "desconto_disponivel": True,
        "percentual_desconto": 30,
        "descricao_promocao": "30% off no primeiro mês",
        "validade_promocao": "2025-12-31",
    },
    "vitalicio": {
        "disponivel": True,
        "preco_vitalicio_brl": 1797.00,
        "descricao": "Acesso vitalício",
    },
    "lives_ao_vivo": [
        {"titulo": "Mentoria Java", "frequencia": "Semanal", "plataforma": "YouTube"},
        {"titulo": "Desafio Java ao Vivo", "frequencia": "Mensal", "plataforma": "Twitch DIO"},
    ],
    "conteudos_modulos": [
        "Introdução ao Java e JDK",
        "Estruturas de Dados em Java",
        "POO com Java",
        "Coleções e Generics",
        "Tratamento de Exceções",
        "Spring Framework e Spring Boot",
        "JPA e Hibernate",
        "APIs RESTful",
        "Microsserviços com Spring Cloud",
        "Testes e Deploy em Cloud",
    ],
    "certificado": True,
    "plano_requerido": "Pro",
}

_SAMPLE_TRILHA_NO_PROMO = {
    "id": 3,
    "nome": "Formação Angular Developer",
    "tecnologia": "Angular",
    "nivel": "Intermediário ao Avançado",
    "numero_de_modulos": 7,
    "xp_total": 16500,
    "duracao_horas": 54,
    "descricao": "Angular moderno.",
    "badges_disponiveis": [
        {"nome": "Angular Basics", "descricao": "Fundamentos do Angular", "xp_requerido": 3500},
    ],
    "promocoes": {
        "desconto_disponivel": False,
        "percentual_desconto": 0,
        "descricao_promocao": "Sem promoção",
        "validade_promocao": None,
    },
    "vitalicio": {"disponivel": False, "preco_vitalicio_brl": None, "descricao": "N/A"},
    "lives_ao_vivo": [
        {"titulo": "Angular ao Vivo", "frequencia": "Quinzenal", "plataforma": "YouTube DIO"},
    ],
    "conteudos_modulos": ["TypeScript", "Angular CLI", "Componentes"],
    "certificado": False,
    "plano_requerido": "Free",
}

_SAMPLE_DATA = {
    "fonte": "https://dio.me",
    "ultima_atualizacao": "2025-01-01",
    "trilhas_formacao": [_SAMPLE_TRILHA_JAVA, _SAMPLE_TRILHA_NO_PROMO],
    "resumo": {
        "total_trilhas": 2,
        "tecnologias_cobertas": ["Java", "Angular"],
        "xp_total_disponivel": 38500,
        "total_badges": 4,
        "total_horas_conteudo": 130,
        "planos_disponiveis": {
            "free": "Acesso limitado",
            "pro_mensal": "Acesso completo",
            "pro_anual": "Melhor custo",
            "vitalicio": "Acesso permanente",
        },
    },
}


@pytest.fixture
def sample_data_file(tmp_path: Path) -> Path:
    """Write _SAMPLE_DATA to a temp JSON file and return its path."""
    p = tmp_path / "trilhas_dio.json"
    p.write_text(json.dumps(_SAMPLE_DATA), encoding="utf-8")
    return p


# ===========================================================================
# 1. Helpers / utilities
# ===========================================================================


class TestNormaliseLevel:
    def test_iniciante(self):
        assert _normalise_level("iniciante") == "iniciante"

    def test_intermediario_sem_acento(self):
        assert _normalise_level("intermediario") == "intermediário"

    def test_intermediario_com_acento(self):
        assert _normalise_level("intermediário") == "intermediário"

    def test_avancado_sem_acento(self):
        assert _normalise_level("avancado") == "avançado"

    def test_avancado_com_acento(self):
        assert _normalise_level("avançado") == "avançado"

    def test_uppercase_input(self):
        assert _normalise_level("INICIANTE") == "iniciante"

    def test_unknown_falls_back(self):
        assert _normalise_level("expert") == "intermediário"

    def test_empty_string_falls_back(self):
        assert _normalise_level("") == "intermediário"


class TestGenerateCertId:
    def test_format(self):
        cid = _generate_cert_id("Java")
        # Expected: DIO-JAVA-<year>-<6 chars>
        assert re.match(r"^DIO-JAVA-\d{4}-[A-Z0-9]{6}$", cid), f"Unexpected format: {cid}"

    def test_special_chars_stripped(self):
        cid = _generate_cert_id(".NET/C#")
        assert "/" not in cid
        assert "." not in cid
        assert "#" not in cid

    def test_uniqueness(self):
        ids = {_generate_cert_id("Java") for _ in range(50)}
        # Very unlikely to get fewer than 40 unique values out of 50
        assert len(ids) > 40


# ===========================================================================
# 2. load_data / find_trilha / list_tecnologias
# ===========================================================================


class TestLoadData:
    def test_loads_real_file(self):
        data = load_data(REAL_DATA_PATH)
        assert "trilhas_formacao" in data
        assert len(data["trilhas_formacao"]) > 0

    def test_loads_sample_file(self, sample_data_file):
        data = load_data(sample_data_file)
        assert data["fonte"] == "https://dio.me"
        assert len(data["trilhas_formacao"]) == 2

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_data(tmp_path / "nonexistent.json")


class TestFindTrilha:
    def test_finds_java_exact_case(self):
        t = find_trilha(_SAMPLE_DATA, "Java")
        assert t is not None
        assert t["tecnologia"] == "Java"

    def test_finds_java_lowercase(self):
        t = find_trilha(_SAMPLE_DATA, "java")
        assert t is not None
        assert t["nome"] == "Formação Java Developer"

    def test_finds_java_uppercase(self):
        t = find_trilha(_SAMPLE_DATA, "JAVA")
        assert t is not None

    def test_returns_none_for_unknown(self):
        assert find_trilha(_SAMPLE_DATA, "Rust") is None

    def test_finds_angular(self):
        t = find_trilha(_SAMPLE_DATA, "angular")
        assert t is not None
        assert t["tecnologia"] == "Angular"

    def test_empty_string_returns_none(self):
        assert find_trilha(_SAMPLE_DATA, "") is None


class TestListTecnologias:
    def test_returns_list(self):
        techs = list_tecnologias(_SAMPLE_DATA)
        assert isinstance(techs, list)

    def test_contains_java_and_angular(self):
        techs = list_tecnologias(_SAMPLE_DATA)
        assert "Java" in techs
        assert "Angular" in techs

    def test_count_matches_trilhas(self):
        techs = list_tecnologias(_SAMPLE_DATA)
        assert len(techs) == len(_SAMPLE_DATA["trilhas_formacao"])

    def test_empty_data(self):
        assert list_tecnologias({"trilhas_formacao": []}) == []


# ===========================================================================
# 3. /trilha command
# ===========================================================================


class TestCmdTrilha:
    """Tests for the /trilha command — uses the real JSON file."""

    # --- Happy path: Java ---------------------------------------------------

    def test_returns_string(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_title_present(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "Formação Java Developer" in result

    def test_nivel_present(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "Básico ao Avançado" in result

    def test_duracao_present(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "76h" in result

    def test_xp_present(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "22000 XP" in result

    def test_certificado_sim(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "Sim" in result

    def test_modulos_listed(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "📖 1." in result
        assert "Introdução ao Java e JDK" in result

    def test_badges_listed(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "Java Fundamentals" in result
        assert "Spring Boot Expert" in result

    def test_lives_listed(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "Mentoria Java" in result

    def test_promocao_active_shown(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "Promoção ativa" in result
        assert "30% off no primeiro mês" in result

    def test_vitalicio_shown(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "Plano Vitalício" in result
        assert "1797" in result

    def test_footer_tip_present(self, sample_data_file):
        result = cmd_trilha("Java", sample_data_file)
        assert "/desafio" in result
        assert "/certificado" in result

    # --- Case insensitivity -------------------------------------------------

    def test_java_lowercase(self, sample_data_file):
        result = cmd_trilha("java", sample_data_file)
        assert "Formação Java Developer" in result

    def test_java_mixed_case(self, sample_data_file):
        result = cmd_trilha("JAVA", sample_data_file)
        assert "Formação Java Developer" in result

    # --- Angular (no promo / no vitalicio) ----------------------------------

    def test_angular_certificado_nao(self, sample_data_file):
        result = cmd_trilha("Angular", sample_data_file)
        assert "Não" in result

    def test_angular_no_promo_block(self, sample_data_file):
        result = cmd_trilha("Angular", sample_data_file)
        assert "Promoção ativa" not in result

    def test_angular_no_vitalicio_block(self, sample_data_file):
        result = cmd_trilha("Angular", sample_data_file)
        assert "Plano Vitalício" not in result

    # --- Real file: Java trilha ---------------------------------------------

    def test_real_file_java_trilha(self):
        result = cmd_trilha("Java", REAL_DATA_PATH)
        assert "Formação Java Developer" in result
        assert "Spring Boot" in result

    # --- Error path ---------------------------------------------------------

    def test_unknown_technology_raises(self, sample_data_file):
        with pytest.raises(ValueError) as exc_info:
            cmd_trilha("Rust", sample_data_file)
        assert "Rust" in str(exc_info.value)
        assert "Java" in str(exc_info.value)  # lists available technologies

    def test_error_message_contains_available_techs(self, sample_data_file):
        with pytest.raises(ValueError) as exc_info:
            cmd_trilha("Cobol", sample_data_file)
        msg = str(exc_info.value)
        assert "Angular" in msg


# ===========================================================================
# 4. /desafio command
# ===========================================================================


class TestCmdDesafio:
    """Tests for the /desafio command."""

    # --- Java desafios ------------------------------------------------------

    def test_java_iniciante_returns_tuple(self, sample_data_file):
        md, level = cmd_desafio("Java", "iniciante", sample_data_file)
        assert isinstance(md, str)
        assert level == "iniciante"

    def test_java_intermediario_output(self, sample_data_file):
        md, level = cmd_desafio("Java", "intermediário", sample_data_file)
        assert "Java" in md
        assert level == "intermediário"

    def test_java_avancado_output(self, sample_data_file):
        md, level = cmd_desafio("Java", "avançado", sample_data_file)
        assert "Java" in md
        assert level == "avançado"

    def test_challenge_header_present(self, sample_data_file):
        md, _ = cmd_desafio("Java", "iniciante", sample_data_file)
        assert "⚡ Desafio de Código" in md
        assert "Java" in md

    def test_sections_present(self, sample_data_file):
        md, _ = cmd_desafio("Java", "intermediário", sample_data_file)
        assert "## 📋 Descrição do Desafio" in md
        assert "## 📥 Entrada Esperada" in md
        assert "## 📤 Saída Esperada" in md
        assert "## 🧪 Exemplos" in md
        assert "## 💡 Dica" in md
        assert "## ✅ Critérios de Aceitação" in md

    def test_footer_certificado_tip(self, sample_data_file):
        md, _ = cmd_desafio("Java", "iniciante", sample_data_file)
        assert "/certificado" in md

    def test_nivel_shown_in_output(self, sample_data_file):
        md, _ = cmd_desafio("Java", "avançado", sample_data_file)
        assert "avançado" in md

    # --- Level normalisation / fallback ------------------------------------

    def test_invalid_level_falls_back_to_intermediario(self, sample_data_file):
        md, level = cmd_desafio("Java", "expert", sample_data_file)
        assert level == "intermediário"

    def test_invalid_level_warning_in_output(self, sample_data_file):
        md, _ = cmd_desafio("Java", "expert", sample_data_file)
        assert "expert" in md or "intermediário" in md  # warning or fallback notice

    def test_avancado_without_accent_normalised(self, sample_data_file):
        md, level = cmd_desafio("Java", "avancado", sample_data_file)
        assert level == "avançado"

    def test_intermediario_without_accent_normalised(self, sample_data_file):
        _, level = cmd_desafio("Java", "intermediario", sample_data_file)
        assert level == "intermediário"

    # --- Generic challenge for Angular (no specific template) ---------------

    def test_angular_desafio_generates_output(self, sample_data_file):
        md, level = cmd_desafio("Angular", "iniciante", sample_data_file)
        assert "Angular" in md
        assert len(md) > 100

    def test_angular_intermediario(self, sample_data_file):
        md, level = cmd_desafio("Angular", "intermediário", sample_data_file)
        assert level == "intermediário"
        assert "⚡ Desafio de Código" in md

    # --- Real file: Java ---------------------------------------------------

    def test_real_file_java_desafio(self):
        md, level = cmd_desafio("Java", "intermediário", REAL_DATA_PATH)
        assert "Java" in md
        assert level == "intermediário"

    # --- Error path --------------------------------------------------------

    def test_unknown_technology_raises(self, sample_data_file):
        with pytest.raises(ValueError) as exc_info:
            cmd_desafio("Rust", "iniciante", sample_data_file)
        assert "Rust" in str(exc_info.value)

    def test_error_lists_available_techs(self, sample_data_file):
        with pytest.raises(ValueError) as exc_info:
            cmd_desafio("PHP", "avançado", sample_data_file)
        assert "Java" in str(exc_info.value)


# ===========================================================================
# 5. /certificado command
# ===========================================================================


class TestCmdCertificado:
    """Tests for the /certificado command."""

    _FIXED_ID = "DIO-JAVA-2025-ABCDEF"

    # --- Structure checks ---------------------------------------------------

    def test_returns_string(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert isinstance(result, str)

    def test_header_present(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "CERTIFICADO DE CONCLUSÃO" in result

    def test_user_name_in_output(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "Alice" in result

    def test_trilha_name_in_output(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "Formação Java Developer" in result

    def test_tecnologia_in_output(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "Java" in result

    def test_nivel_in_output(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "Básico ao Avançado" in result

    def test_modules_count_in_output(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "10 módulos" in result

    def test_duracao_in_output(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "76 horas" in result

    def test_xp_in_output(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "22000 XP" in result

    def test_badges_listed(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "Java Fundamentals" in result
        assert "Spring Boot Expert" in result
        assert "Java Developer" in result

    def test_cert_id_present(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert self._FIXED_ID in result

    def test_date_present(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "Data de Emissão" in result

    def test_verification_url(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "https://www.dio.me/certificate" in result

    def test_footer_tip_present(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "LinkedIn" in result
        assert "/trilha" in result

    # --- Case insensitivity -------------------------------------------------

    def test_java_lowercase(self, sample_data_file):
        result = cmd_certificado("Bob", "java", sample_data_file, cert_id=self._FIXED_ID)
        assert "Formação Java Developer" in result

    def test_java_uppercase(self, sample_data_file):
        result = cmd_certificado("Bob", "JAVA", sample_data_file, cert_id=self._FIXED_ID)
        assert "Formação Java Developer" in result

    # --- Different student name ---------------------------------------------

    def test_different_student_name(self, sample_data_file):
        result = cmd_certificado("Carlos Eduardo", "Java", sample_data_file, cert_id=self._FIXED_ID)
        assert "Carlos Eduardo" in result

    # --- Auto-generated cert_id (no fixture) --------------------------------

    def test_auto_cert_id_format(self, sample_data_file):
        result = cmd_certificado("Alice", "Java", sample_data_file)
        assert re.search(r"DIO-JAVA-\d{4}-[A-Z0-9]{6}", result)

    # --- Real file ----------------------------------------------------------

    def test_real_file_java_certificado(self):
        result = cmd_certificado("João Silva", "Java", REAL_DATA_PATH, cert_id="DIO-JAVA-2025-TSTXXX")
        assert "João Silva" in result
        assert "Formação Java Developer" in result
        assert "Spring Boot" in result

    # --- Error path ---------------------------------------------------------

    def test_unknown_technology_raises(self, sample_data_file):
        with pytest.raises(ValueError) as exc_info:
            cmd_certificado("Alice", "Rust", sample_data_file)
        assert "Rust" in str(exc_info.value)

    def test_error_lists_available_techs(self, sample_data_file):
        with pytest.raises(ValueError) as exc_info:
            cmd_certificado("Alice", "COBOL", sample_data_file)
        assert "Java" in str(exc_info.value)


# ===========================================================================
# 6. Integration / end-to-end flow (trilha → desafio → certificado)
# ===========================================================================


class TestFullFlow:
    """
    End-to-end scenario:
    1. User queries /trilha Java
    2. User requests /desafio Java intermediário
    3. User emits /certificado Alice Java
    All against the real JSON data file.
    """

    def test_full_flow_java(self):
        # Step 1 — trilha
        trilha_output = cmd_trilha("Java", REAL_DATA_PATH)
        assert "Formação Java Developer" in trilha_output
        assert "📖" in trilha_output

        # Step 2 — desafio
        desafio_output, level = cmd_desafio("Java", "intermediário", REAL_DATA_PATH)
        assert "⚡ Desafio de Código" in desafio_output
        assert level == "intermediário"

        # Step 3 — certificado
        cert_output = cmd_certificado(
            "Alice", "Java", REAL_DATA_PATH, cert_id="DIO-JAVA-2025-FLOW01"
        )
        assert "Alice" in cert_output
        assert "DIO-JAVA-2025-FLOW01" in cert_output

    def test_full_flow_all_levels(self):
        for nivel in ("iniciante", "intermediário", "avançado"):
            md, level = cmd_desafio("Java", nivel, REAL_DATA_PATH)
            assert "⚡ Desafio de Código" in md, f"Header missing for level: {nivel}"
            assert level == nivel

    def test_trilha_to_desafio_consistency(self):
        """Technology returned by trilha is usable in desafio."""
        data = load_data(REAL_DATA_PATH)
        for trilha in data["trilhas_formacao"]:
            tec = trilha["tecnologia"]
            try:
                md, _ = cmd_desafio(tec, "intermediário", REAL_DATA_PATH)
                assert "⚡ Desafio de Código" in md
            except ValueError:
                pytest.fail(f"cmd_desafio raised ValueError for existing technology: {tec}")

    def test_all_technologies_have_valid_trilha(self):
        """Every technology in the dataset can be queried via cmd_trilha."""
        data = load_data(REAL_DATA_PATH)
        for trilha in data["trilhas_formacao"]:
            tec = trilha["tecnologia"]
            result = cmd_trilha(tec, REAL_DATA_PATH)
            assert trilha["nome"] in result, f"Nome da trilha ausente para {tec}"

    def test_all_technologies_certificate_generation(self):
        """Every technology in the dataset can emit a certificate."""
        data = load_data(REAL_DATA_PATH)
        for trilha in data["trilhas_formacao"]:
            tec = trilha["tecnologia"]
            result = cmd_certificado("Estudante Teste", tec, REAL_DATA_PATH)
            assert "Estudante Teste" in result
            assert "CERTIFICADO DE CONCLUSÃO" in result
