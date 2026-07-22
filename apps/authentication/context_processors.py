"""Context processors for sidebar and global context."""

from apps.users.models import Role

# Sidebar menu structure per role
SIDEBAR_MENUS = {
    Role.SUPER_ADMIN: [
        {'icon': 'bi-speedometer2', 'label': 'Tableau de bord', 'url': 'dashboard:index', 'args': []},
        {'icon': 'bi-building', 'label': 'Écoles', 'url': 'schools:list', 'args': []},
        {'icon': 'bi-people', 'label': 'Utilisateurs', 'url': 'users:list', 'args': []},
        {'icon': 'bi-shield-check', 'label': 'Journal d\'audit', 'url': 'audit:list', 'args': []},
        {'icon': 'bi-bar-chart', 'label': 'Rapports & Stats', 'url': 'analytics:index', 'args': []},
        {'icon': 'bi-database', 'label': 'Sauvegarde', 'url': 'backup:index', 'args': []},
    ],
    Role.ADMIN_ECOLE: [
        {'icon': 'bi-speedometer2', 'label': 'Tableau de bord', 'url': 'dashboard:index', 'args': []},
        {'icon': 'bi-people', 'label': 'Utilisateurs', 'url': 'users:list', 'args': []},
        {'icon': 'bi-calendar3', 'label': 'Années scolaires', 'url': 'academic:years', 'args': []},
        {'icon': 'bi-diagram-3', 'label': 'Organisation', 'url': 'academic:index', 'args': []},
        {'icon': 'bi-person-vcard', 'label': 'Élèves', 'url': 'students:list', 'args': []},
        {'icon': 'bi-people-fill', 'label': 'Parents', 'url': 'parents:list', 'args': []},
        {'icon': 'bi-person-badge', 'label': 'Personnel', 'url': 'staff:list', 'args': []},
        {'icon': 'bi-clipboard-check', 'label': 'Inscriptions', 'url': 'enrollment:index', 'args': []},
        {'icon': 'bi-calendar-week', 'label': 'Emplois du temps', 'url': 'timetable:index', 'args': []},
        {'icon': 'bi-pencil-square', 'label': 'Évaluations', 'url': 'assessments:index', 'args': []},
        {'icon': 'bi-file-text', 'label': 'Bulletins', 'url': 'reports:index', 'args': []},
        {'icon': 'bi-cash-coin', 'label': 'Finance', 'url': 'finance:index', 'args': []},
        {'icon': 'bi-bus-front', 'label': 'Transport', 'url': 'transport:index', 'args': []},
        {'icon': 'bi-chat-dots', 'label': 'Communication', 'url': 'communication:index', 'args': []},
        {'icon': 'bi-folder', 'label': 'Documents', 'url': 'documents:index', 'args': []},
        {'icon': 'bi-bar-chart', 'label': 'Rapports & Stats', 'url': 'analytics:index', 'args': []},
        {'icon': 'bi-shield-check', 'label': 'Journal d\'audit', 'url': 'audit:list', 'args': []},
    ],
    Role.SECRETAIRE: [
        {'icon': 'bi-speedometer2', 'label': 'Tableau de bord', 'url': 'dashboard:index', 'args': []},
        {'icon': 'bi-person-vcard', 'label': 'Élèves', 'url': 'students:list', 'args': []},
        {'icon': 'bi-people-fill', 'label': 'Parents', 'url': 'parents:list', 'args': []},
        {'icon': 'bi-clipboard-check', 'label': 'Inscriptions', 'url': 'enrollment:index', 'args': []},
        {'icon': 'bi-calendar-week', 'label': 'Emplois du temps', 'url': 'timetable:index', 'args': []},
        {'icon': 'bi-chat-dots', 'label': 'Communication', 'url': 'communication:index', 'args': []},
        {'icon': 'bi-folder', 'label': 'Documents', 'url': 'documents:index', 'args': []},
    ],
    Role.ENSEIGNANT: [
        {'icon': 'bi-speedometer2', 'label': 'Tableau de bord', 'url': 'dashboard:index', 'args': []},
        {'icon': 'bi-calendar-week', 'label': 'Emploi du temps', 'url': 'timetable:index', 'args': []},
        {'icon': 'bi-pencil-square', 'label': 'Évaluations', 'url': 'assessments:index', 'args': []},
        {'icon': 'bi-file-text', 'label': 'Bulletins', 'url': 'reports:index', 'args': []},
        {'icon': 'bi-chat-dots', 'label': 'Communication', 'url': 'communication:index', 'args': []},
    ],
    Role.COMPTABLE: [
        {'icon': 'bi-speedometer2', 'label': 'Tableau de bord', 'url': 'dashboard:index', 'args': []},
        {'icon': 'bi-cash-coin', 'label': 'Finance', 'url': 'finance:index', 'args': []},
        {'icon': 'bi-person-vcard', 'label': 'Élèves', 'url': 'students:list', 'args': []},
        {'icon': 'bi-bar-chart', 'label': 'Rapports financiers', 'url': 'analytics:index', 'args': []},
    ],
}


def sidebar_context(request):
    """Inject sidebar menu items and school info into every template."""
    if not request.user.is_authenticated:
        return {}
    menu = SIDEBAR_MENUS.get(request.user.role, [])
    return {
        'sidebar_menu': menu,
        'current_school': getattr(request.user, 'school', None),
    }
