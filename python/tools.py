from officiel import supprime_accent_espace
import unicodedata
import re

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
    """Supprime les caractères récalcitrans (éâà) d'un ``contenu`` provenant d'un rdocx dont
    l'encodage dépend du système d'exploitation sur lequel a été rédigé
    le document
    """
    # contenu = contenu.replace("\'", "'")
    contenu = contenu.replace("è", "è")
    contenu = contenu.replace("é", "é")
    contenu = contenu.replace("â", "â").replace(b'a\xcc\x82'.decode("utf8"), "â")
    # contenu = unicodedata.normalize("NFKD", contenu)
    contenu = contenu.replace("’", "'") #.replace(b"\xe2\x80\x99".decode("utf8"), "'")
    contenu = contenu.replace('\xa0', ' ') # le nbsp


    # contenu = contenu.encode("utf8", "ignore").decode("utf8")

    return contenu


def check_espace(contenu):
    """Vérifie les pb d'espaces"""
    oublie_espace_avant_deux_points = re.findall(r"\w:", contenu)
    for val in oublie_espace_avant_deux_points:
        contenu = contenu.replace(val, val[0] + " :")
    oublie_espace_apres_deux_points = re.findall(r":[\w\[]", contenu)
    for val in oublie_espace_apres_deux_points:
        contenu = contenu.replace(val, ": " + val[1])

    espace_avant_point_virgule = re.findall(r"\w\s*;", contenu)
    for val in espace_avant_point_virgule:
        contenu = contenu.replace(val, val[0] + ";")
    return contenu