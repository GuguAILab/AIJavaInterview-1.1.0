"""Global Search query builder — pure function, easy to break, easy to test."""
import datetime

SITES = {
    "LinkedIn Jobs": "site:linkedin.com/jobs",
    "Naukri": "site:naukri.com",
}
ALIASES = {"bangalore": ["bangalore", "bengaluru"]}


def build_xray_query(role, city="", sites=None, skills=None,
                     exclude_senior=False, recent_days=7):
    parts = []
    ops = [SITES[s] for s in (sites or []) if s in SITES]
    if len(ops) == 1:
        parts.append(ops[0])
    elif ops:
        parts.append("(" + " OR ".join(ops) + ")")
    if role.strip():
        parts.append(f'"{role.strip()}"')
    if city.strip():
        v = ALIASES.get(city.strip().lower(), [city.strip().lower()])
        parts.append("(" + " OR ".join(v) + ")")
    for s in (skills or []):
        parts.append(f'"{s}"')
    if exclude_senior:
        parts.append("-senior -staff -principal -lead -director")
    if recent_days:
        since = datetime.date.today() - datetime.timedelta(days=int(recent_days))
        parts.append(f"after:{since.isoformat()}")
    return " ".join(parts)


def test_single_site_has_no_parens():
    q = build_xray_query("engineer", sites=["Naukri"], recent_days=0)
    assert q.startswith("site:naukri.com") and "(site:" not in q


def test_multiple_sites_are_or_grouped():
    q = build_xray_query("engineer", sites=["Naukri", "LinkedIn Jobs"], recent_days=0)
    assert q.startswith("(site:") and " OR " in q


def test_city_aliases_expand():
    q = build_xray_query("engineer", city="Bangalore", recent_days=0)
    assert "(bangalore OR bengaluru)" in q


def test_recency_produces_correct_date():
    q = build_xray_query("engineer", recent_days=7)
    expected = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    assert f"after:{expected}" in q


def test_any_time_has_no_date_filter():
    assert "after:" not in build_xray_query("engineer", recent_days=0)


def test_parens_balanced():
    q = build_xray_query("engineer", "Bangalore", ["Naukri", "LinkedIn Jobs"], ["Python"])
    assert q.count("(") == q.count(")")
