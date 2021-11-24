import string

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


def remove_ligne_vide(contenus):
    """Supprime les lignes vides"""
    if isinstance(contenus, list):
        return [c for c in contenus if c.rstrip()]
    else: # contenu = chaine
        if get_marqueurs(contenus):
            temp = contenus.split("\n")
            temp = [t for t in temp if t.replace("\t", "").rstrip()]
            return "\n".join(temp)
        else: # pas de marqueur => respect des paragraphes
            contenus = contenus.replace("\n\n", "\\\\\n")
            temp = contenus.split("\n")
            temp = [t for t in temp if t.replace("\t", "").rstrip()]
            return "\n".join(temp)


def get_marqueurs(contenu):
    """Renvoie la liste des marqueurs (à 1 caractère) partant d'un contenu - splitable en plusieurs lignes
    (éventuellement vide)"""
    contenus = [ligne.rstrip()[indice_premier_caractere(ligne):] for ligne in contenu.split("\n")]  # les contenus avec suppression des espaces initiaux

    marqueurs = []
    for ligne in contenus:
        m = re.search(r"(\t)*", ligne) # y a-t-il des tabulations ?
        if m.group() != "":
            ajout = m.group()
        else:
            ajout = ""
        ligne = ligne.replace("\t"," ") # supprime les tabulations pour rapatrier le marqueur en début de ligne
        ligne = ligne[indice_premier_caractere(ligne):] # supprime les espaces en début de ligne
        ligne = supprime_accent_espace(ligne) # supprime les accents
        if ligne: # si la ligne n'est pas vide, cherche le marqueur en début de ligne (si 1 caractère)
            if ligne[0] not in string.ascii_letters and ligne[0] != "/":
                i = 0
                while i<len(ligne) and ligne[i].lower() not in string.ascii_lowercase + string.digits:
                    i = i+1
                marqueur = ligne[0:i]
                marqueurs += [ajout + marqueur] # tous les symboles

    marqueurs_finaux = [] # tri les marqueurs en supprimant les doublons et en gardant un ordre (pour détecter les sous listes)
    for m in marqueurs:
        if m not in marqueurs_finaux:
            marqueurs_finaux.append(m)
    return marqueurs_finaux


def get_marqueur_from_liste(ligne, marqueurs):
    """Renvoie le marqueur qui marque le début d'une ligne parmi une liste de marqueurs recherchés"""
    match = []
    for m in marqueurs: # à l'envers pour éviter les marqueurs emboités
        if ligne.startswith(m):
            match.append(m)
    if match:
        # Prend le marqueur qui match le mieux (le plus long à priori)
        longueur = [len(m) for m in match]
        max_longueur = max(longueur)
        return match[longueur.index(max_longueur)]


def remplace_marqueur_numerique_with_caracteres(contenu):
    """Remplace les marqueurs numériques par des marqueurs > lorsque présents dans un contenu"""
    marqueurs_numeriques = get_marqueur_numerique(contenu)
    for m in marqueurs_numeriques: # remplace les marqueurs numériques
        contenu = contenu.replace(m, ">")
    return contenu


def indice_premier_caractere(contenu):
    """Renvoie l'indice du premier caractère (non espace) pour suppression espace"""
    i = 0
    while i < len(contenu) and contenu[i] == " ":
        i = i+1
    if i == len(contenu):
        return 0
    else:
        return i


def get_marqueur_numerique(contenu):
    """Revoie la liste des marqueurs numériques"""
    m = re.findall(r"(\d/|\d\s/)", contenu)
    #m += re.findall(r"(\d\s\)|\d\))", contenu) # les marqueurs de la forme 1)
    m += re.findall(r"(\d\s\))", contenu)
    # m = re.findall(r"\d\s{0,1}[/\)]", contenu)
    # tirets = re.findall(r"(--)(\s|\t)", contenu) # <-- pourquoi ?
    # m += ["".join(t) for t in tirets]
    return m