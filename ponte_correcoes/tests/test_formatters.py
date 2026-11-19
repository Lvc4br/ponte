from datetime import date, datetime

from app.formatters import fmt_celula, fmt_data, fmt_numero, fmt_percentual


def test_data_iso_meia_noite():
    assert fmt_data("2022-09-01T00:00:00") == "01/09/2022"

def test_data_com_hora():
    assert fmt_data("2022-09-01T14:30:00") == "01/09/2022 14:30"

def test_data_objetos_e_vazios():
    assert fmt_data(datetime(2001, 4, 1)) == "01/04/2001"
    assert fmt_data(date(2001, 4, 1)) == "01/04/2001"
    assert fmt_data(None) == "" and fmt_data("") == ""

def test_data_texto_invalido_nao_quebra():
    assert fmt_data("sem data") == "sem data"

def test_numero_ptbr():
    assert fmt_numero(1308.5) == "1.308,50"
    assert fmt_numero(2.6) == "2,60"
    assert fmt_numero(1234567.891, 1) == "1.234.567,9"
    assert fmt_numero(1257, 0) == "1.257"
    assert fmt_numero(float("nan")) == ""
    assert fmt_numero("12,5") == "12,50"

def test_percentual():
    assert fmt_percentual(97.4) == "97,4%"
    assert fmt_percentual(0.974, fracao=True) == "97,4%"
    assert fmt_percentual(100) == "100,0%"

def test_celula_por_tipo():
    assert fmt_celula("2023-09-01T00:00:00", "data") == "01/09/2023"
    assert fmt_celula(41.25, "decimal") == "41,25"
    assert fmt_celula(True, "booleano") == "Sim"
    assert fmt_celula(None, "texto") == ""
    assert fmt_celula(True) == "Sim"
