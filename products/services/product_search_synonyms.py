"""Synonymes controles pour la recherche du catalogue produits.

Le but est d'elargir une intention de recherche sans rendre le moteur flou.
Chaque groupe represente des termes equivalents FR/EN.
"""

SYNONYM_GROUPS = (
    ("souris", "mouse"),
    ("clavier", "keyboard"),
    ("ordinateur", "pc", "laptop"),
    ("ecouteurs", "écouteurs", "oreillettes", "earbuds"),
    ("casque", "headset", "headphones"),
    ("rangement", "organisateur", "organizer"),
    ("sans fil", "wireless"),
)


def _normalized(value):
    return value.casefold().strip()


def _group_for(term):
    normalized_term = _normalized(term)
    for group in SYNONYM_GROUPS:
        if normalized_term in {_normalized(value) for value in group}:
            return group
    return (term,)


def build_search_groups(search_query):
    """Retourne les groupes a rechercher avec ET entre groupes et OU dedans.

    Les expressions multi-mots connues (ex. ``sans fil``) sont reconnues avant
    le decoupage mot a mot afin que ``wireless`` soit un vrai equivalent.
    """
    words = search_query.split()
    groups = []
    index = 0

    multiword_terms = sorted(
        {
            value
            for group in SYNONYM_GROUPS
            for value in group
            if " " in value
        },
        key=lambda value: len(value.split()),
        reverse=True,
    )

    while index < len(words):
        matched = None
        matched_size = 0

        for phrase in multiword_terms:
            phrase_words = phrase.split()
            size = len(phrase_words)
            candidate = " ".join(words[index:index + size])
            if _normalized(candidate) == _normalized(phrase):
                matched = phrase
                matched_size = size
                break

        if matched is not None:
            groups.append(_group_for(matched))
            index += matched_size
        else:
            groups.append(_group_for(words[index]))
            index += 1

    return groups
