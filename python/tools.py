import string


import unicodedata
import re

import openpyxl

from export_fiches import REPERTOIRE


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
    contenu = contenu.replace("\\", "") # les slashs ?


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
            marqueurs_ligne = re.findall("\n{2}\n*", contenus)
            for m in marqueurs_ligne[::-1]:
                contenus = contenus.replace(m, "\n")
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
        ligne = ligne.replace(" ", "")  # retire les espaces
        # ligne = supprime_accent_espace(ligne) # supprime les accents
        if ligne: # si la ligne n'est pas vide, cherche le marqueur en début de ligne (si 1 caractère)
            attendus = string.ascii_lowercase + string.digits + "é/"
            if ligne[0].lower() not in attendus:
                i = 0
                while i<len(ligne) and ligne[i].lower() not in attendus:
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
    m += re.findall(r"(\d-)", contenu)
    # m = re.findall(r"\d\s{0,1}[/\)]", contenu)
    # tirets = re.findall(r"(--)(\s|\t)", contenu) # <-- pourquoi ?
    # m += ["".join(t) for t in tirets]
    return m


def supprime_accent_espace(chaine):
    """Met une chaine en minuscule, supprime les accents, les ponctuations et les espaces"""
    purge = chaine.lower().replace("'", "").replace("’", "")
    purge = unicodedata.normalize('NFD', purge).encode('ascii', 'ignore').decode('ascii')
    purge = purge.replace(" ", "")
    return purge


def get_download_information(fichier = "BUT-RT-S1-S6.xlsx"):
    """Récupère les info sur les fiches à télécharger par lecture de la feuille "Ressources et SAE S1-S6" du
    tableur"""

    wb_obj = openpyxl.load_workbook(REPERTOIRE + fichier)

    # Read the active sheet:
    sheet = wb_obj["Ressources et SAE S1-S6"]

    modele = {"url": "", # l'url
              "idf": "", # l'idf
              "tableur_heures_formation" : {}, #"cm/td": None, "tp": None, "projet": None},
              "tableur_heures_formation_pn" : {}, #"cm/td": None, "tp": None}
    }
    fiches = {}
    for (i, row) in enumerate(sheet.iter_rows(max_row=500)): #lecture ligne à ligne
        code = sheet["A" + str(i+1)].value
        url = sheet["U" + str(i+1)].value
        if code:
            m = re.match("^[RS].+\d$", code) # commence par un R ou un S et se finit par un chiffre
            if m:
                idf = url.split("/")[-2] # l'id de la fiche sur Google Drive
                # print(code, idf)
                if m in fiches:
                    print(f"Pb : {m} déjà dans les fiches")
                fiches[code] = {**modele}
                fiches[code]["idf"] = idf
                fiches[code]["url"] = url

                # Lecture des heures
                fiches[code]["tableur_heures_formation"] = {}
                fiches[code]["tableur_heures_formation"]["cm/td"] = sheet["C" + str(i+1)].value
                fiches[code]["tableur_heures_formation"]["tp"] = sheet["D" + str(i + 1)].value
                fiches[code]["tableur_heures_formation"]["projet"] = sheet["E" + str(i + 1)].value

                fiches[code]["tableur_heures_formation_pn"] = {}
                fiches[code]["tableur_heures_formation_pn"]["cm/td"] = sheet["F" + str(i + 1)].value
                fiches[code]["tableur_heures_formation_pn"]["tp"] = sheet["G" + str(i + 1)].value

    return fiches