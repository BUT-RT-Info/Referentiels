from officiel import supprime_accent_espace


def get_indice(champ, entetes):
    """Récupère l'indice d'une entête"""
    for (i, entete) in enumerate(entetes):
        if entete in champ:
            return i
    return None


def get_indice_sans_accent_ni_espace(champ, entetes):
    """Récupère l'indice d'une entête en se débarrassant des majuscules/caractères spéciaux/espace"""
    champ_purge = supprime_accent_espace(champ).rstrip()
    for (i, entete) in enumerate(entetes):
        entete_purge = supprime_accent_espace(entete).rstrip()
        if entete_purge in champ_purge:
            return i
    return None


def caracteres_recalcitrants(contenu):
    contenu = contenu.replace("è", "è").replace(b"\xe2\x80\x99".decode("utf8"), "'").replace("é", "é")
    contenu = contenu.replace("’", "'")
    contenu = contenu.replace("â", "â").replace(b'a\xcc\x82'.decode("utf8"), "â")
    contenu = contenu.replace('\xa0', ' ') # le nbsp

    return contenu