"""Formatação de valores para exibição em pt-BR (tabela e indicadores).

Só formata para mostrar na tela: não altera o dado guardado no banco.
"""
from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any


def _vazio(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    return isinstance(v, float) and math.isnan(v)


def fmt_numero(v: Any, casas: int = 2) -> str:
    """1308.5 -> '1.308,50'. Vazio/None/NaN -> ''."""
    if _vazio(v):
        return ""
    if isinstance(v, bool):
        return "Sim" if v else "Não"
    if isinstance(v, str):
        try:
            v = float(v.replace(",", "."))
        except ValueError:
            return v
    texto = f"{v:,.{casas}f}"
    return texto.replace(",", "\0").replace(".", ",").replace("\0", ".")


def fmt_percentual(v: Any, casas: int = 1, fracao: bool = False) -> str:
    """97.4 -> '97,4%'. Com fracao=True, 0.974 -> '97,4%'."""
    if _vazio(v):
        return ""
    valor = float(v) * 100 if fracao else float(v)
    return fmt_numero(valor, casas) + "%"


def fmt_data(v: Any) -> str:
    """'2022-09-01T00:00:00' -> '01/09/2022'. Com hora real: '01/09/2022 14:30'."""
    if _vazio(v):
        return ""
    if isinstance(v, datetime):
        dt = v
    elif isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    else:
        try:
            dt = datetime.fromisoformat(str(v).strip().replace("Z", ""))
        except ValueError:
            return str(v)
    if dt.hour == dt.minute == dt.second == 0:
        return dt.strftime("%d/%m/%Y")
    return dt.strftime("%d/%m/%Y %H:%M")


def fmt_celula(v: Any, tipo: str | None = None) -> str:
    """Escolhe o formatador pelo tipo da coluna (texto, inteiro, decimal, data...)."""
    if _vazio(v):
        return ""
    t = (tipo or "").lower()
    if t in {"data", "date", "data/hora", "datetime"}:
        return fmt_data(v)
    if t in {"decimal", "float", "numero", "número"}:
        return fmt_numero(v, 2)
    if t in {"inteiro", "int", "integer"}:
        return fmt_numero(v, 0)
    if t in {"booleano", "bool", "boolean"}:
        return "Sim" if v else "Não"
    if isinstance(v, (datetime, date)):
        return fmt_data(v)
    if isinstance(v, bool):
        return "Sim" if v else "Não"
    if isinstance(v, float):
        return fmt_numero(v, 2)
    if isinstance(v, int):
        return fmt_numero(v, 0)
    return str(v)
