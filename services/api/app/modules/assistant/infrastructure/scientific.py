from __future__ import annotations

import re
import sympy as sp

_ALLOWED = re.compile(r"^[0-9a-zA-Z_+\-*/^=().,\s]+$")


class SympyScientificSolver:
    """Small deterministic first line for symbolic expressions/equations.

    It intentionally declines word problems and unfamiliar syntax so the request can
    fall back to the AI reasoning route instead of guessing.
    """
    def solve(self, expression: str) -> str | None:
        raw = expression.strip()
        lowered = raw.casefold()
        for prefix in ("résous", "resous", "solve", "calculer", "calcule"):
            if lowered.startswith(prefix):
                raw = raw[len(prefix):].lstrip(" :")
                break
        raw = raw.replace("^", "**")
        if not raw or len(raw) > 240 or not _ALLOWED.match(raw):
            return None
        symbols = {name: sp.Symbol(name) for name in ("x","y","z","t","n")}
        safe = {**symbols, "sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "log": sp.log, "exp": sp.exp, "pi": sp.pi, "E": sp.E}
        try:
            if "=" in raw:
                left, right = raw.split("=", 1)
                lhs = sp.sympify(left, locals=safe)
                rhs = sp.sympify(right, locals=safe)
                present = sorted((lhs-rhs).free_symbols, key=lambda s: s.name)
                if not present:
                    return f"Vérification déterministe : {sp.simplify(lhs-rhs) == 0}."
                solutions = sp.solve(sp.Eq(lhs, rhs), present[0])
                return f"Équation : {sp.sstr(lhs)} = {sp.sstr(rhs)}\nVariable : {present[0]}\nSolution(s) : {', '.join(sp.sstr(v) for v in solutions) if solutions else 'aucune solution trouvée'}"
            expr = sp.sympify(raw, locals=safe)
            simplified = sp.simplify(expr)
            return f"Expression : {sp.sstr(expr)}\nRésultat simplifié : {sp.sstr(simplified)}"
        except Exception:
            return None
