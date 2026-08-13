"""
Gamificação — pontos, níveis, medalhas e ranking por trilha/grupo.

Os pontos são DERIVADOS do progresso já registrado (class_progress + test_sessions),
sem tabela extra: cada aula concluída, cada simulado feito e cada certificação-alvo
aprovada valem pontos. Assim o ranking reflete o engajamento real na capacitação.
"""
from __future__ import annotations

from typing import Optional

from app.config import get_settings

# ── Regras de pontuação ───────────────────────────────────────────────────────
PTS_CLASS = 10        # por aula concluída (class_progress)
PTS_ATTEMPT = 15      # por simulado realizado (test_sessions)
PTS_PASS = 40         # por simulado aprovado (bônus, por tentativa aprovada)

LEVELS = [            # (mín. de pontos, rótulo)
    (0, "Iniciante"), (60, "Explorador"), (150, "Praticante"),
    (300, "Avançado"), (500, "Especialista"), (800, "Mestre Databricks"),
]


def level_for(points: int) -> dict:
    label, floor, nxt = LEVELS[0][1], 0, None
    for i, (thr, lbl) in enumerate(LEVELS):
        if points >= thr:
            label, floor = lbl, thr
            nxt = LEVELS[i + 1][0] if i + 1 < len(LEVELS) else None
    return {"label": label, "floor": floor, "next_at": nxt}


def _badges(classes_done: int, attempts: int, passed: int, points: int) -> list[dict]:
    b = []
    def add(cond, key, name, icon):
        if cond:
            b.append({"key": key, "name": name, "icon": icon})
    add(classes_done >= 1, "first_class", "Primeira aula", "PlayCircle")
    add(classes_done >= 5, "five_classes", "5 aulas concluídas", "BookOpen")
    add(classes_done >= 15, "fifteen_classes", "15 aulas concluídas", "GraduationCap")
    add(attempts >= 1, "first_sim", "Primeiro simulado", "ClipboardCheck")
    add(attempts >= 10, "ten_sims", "10 simulados", "Target")
    add(passed >= 1, "first_pass", "Simulado aprovado", "Award")
    add(passed >= 3, "three_pass", "3 aprovações", "Medal")
    add(points >= 300, "advanced", "Nível Avançado", "Flame")
    add(points >= 800, "master", "Mestre Databricks", "Crown")
    return b


def _compute(classes_done: int, attempts: int, passed: int) -> dict:
    points = classes_done * PTS_CLASS + attempts * PTS_ATTEMPT + passed * PTS_PASS
    lvl = level_for(points)
    return {
        "points": points, "level": lvl["label"], "level_floor": lvl["floor"],
        "next_level_at": lvl["next_at"], "classes_done": classes_done,
        "attempts": attempts, "passed": passed,
        "badges": _badges(classes_done, attempts, passed, points),
    }


def user_stats(tenant_id: str, email: str) -> dict:
    """Pontos/nível/medalhas de um usuário."""
    email = email.lower()
    if get_settings().MOCK_MODE:
        return _compute(0, 0, 0)
    from app.db import get_conn
    with get_conn() as conn:
        cd = conn.execute("SELECT COUNT(*) FROM class_progress WHERE tenant_id=%s AND user_email=%s",
                          (tenant_id, email)).fetchone()[0]
        at = conn.execute("SELECT COUNT(*) FROM test_sessions WHERE tenant_id=%s AND user_email=%s",
                          (tenant_id, email)).fetchone()[0]
        pa = conn.execute("SELECT COUNT(*) FROM test_sessions WHERE tenant_id=%s AND user_email=%s "
                          "AND passed=TRUE", (tenant_id, email)).fetchone()[0]
    return _compute(int(cd), int(at), int(pa))


def leaderboard(tenant_id: str, group_key: Optional[str] = None, limit: int = 100) -> list[dict]:
    """Ranking por pontos. Filtra por grupo se informado; inclui nome/área/grupo."""
    if get_settings().MOCK_MODE:
        return []
    from app.db import get_conn
    params = [tenant_id, tenant_id, tenant_id]
    where_group = ""
    if group_key:
        where_group = "AND u.group_key=%s"
        params.append(group_key)
    sql = f"""
        SELECT u.email, u.name, u.area, u.group_key,
               COALESCE(c.cd,0) AS cd, COALESCE(s.at,0) AS at, COALESCE(s.pa,0) AS pa
        FROM users u
        LEFT JOIN (SELECT user_email, COUNT(*) cd FROM class_progress
                   WHERE tenant_id=%s GROUP BY user_email) c ON c.user_email=u.email
        LEFT JOIN (SELECT user_email, COUNT(*) at, COUNT(*) FILTER (WHERE passed) pa
                   FROM test_sessions WHERE tenant_id=%s GROUP BY user_email) s ON s.user_email=u.email
        WHERE u.tenant_id=%s AND COALESCE(u.status,'active')<>'suspended' {where_group}
    """
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        st = _compute(int(r[4]), int(r[5]), int(r[6]))
        out.append({"email": r[0], "name": r[1], "area": r[2], "group_key": r[3], **st})
    out.sort(key=lambda x: (-x["points"], x["name"] or ""))
    for i, row in enumerate(out[:limit]):
        row["rank"] = i + 1
    return out[:limit]
