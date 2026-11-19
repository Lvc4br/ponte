import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from checar_acentos import corrigir_texto  # noqa: E402


def test_corrige_textos_da_interface():
    assert corrigir_texto("RESUMO ESTAT?STICO") == "RESUMO ESTATÍSTICO"
    assert corrigir_texto("GEST?O T?CNICA DE OBRAS") == "GESTÃO TÉCNICA DE OBRAS"
    assert corrigir_texto("V?o (m)") == "Vão (m)"
    assert corrigir_texto("M?nimo") == "Mínimo"
    assert corrigir_texto("Conte?do da c?lula selecionada") == "Conteúdo da célula selecionada"
    assert corrigir_texto("filtros s?o aplicados ? planilha") == "filtros são aplicados à planilha"
    assert corrigir_texto("n?o num?ricos s?o ignorados") == "não numéricos são ignorados"

def test_botoes():
    assert corrigir_texto('QPushButton("? Novo projeto")') == 'QPushButton("+ Novo projeto")'
    assert corrigir_texto('"? Registro"') == '"+ Registro"'
    assert corrigir_texto('"? P?gina"') == '"< Página"'
    assert corrigir_texto('"P?gina ?"') == '"Página >"'

def test_nao_mexe_em_placeholders_sql():
    sql = 'cur.execute("SELECT * FROM t WHERE id = ?", (1,))'
    assert corrigir_texto(sql) == sql
