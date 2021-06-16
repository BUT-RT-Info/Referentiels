"""
Ensemble de fonctions utiles à l'export des ressources/SAé en latex
"""

from ressource import *


def rotation_entete_colonne(contenu, pos="l"):
    """Renvoie le code latex permettant la rotation de 90° d'un ``contenu``"""
    chaine = "\\rotatebox[origin=" + pos + "]{90}{"
    chaine += contenu + "}"
    return chaine


def str_latex_abbreviations(DATA_ABBREVIATIONS):
    """Renvoie le code latex d'un tableau pour les abbréviations"""
    liste = [
        [cle, DATA_ABBREVIATIONS[lettre][cle]]
        for lettre in DATA_ABBREVIATIONS
        for cle in DATA_ABBREVIATIONS[lettre]
    ]
    nbre_abbreviations = len(liste)
    chaine = ""
    for i in range(nbre_abbreviations):
        chaine += "\\begin{tabular}{rp{6.5cm}} \n"
        chaine += (
            "\makebox[1.5cm][r]{\\textabbrv{"
            + liste[i][0]
            + "}} & "
            + liste[i][1]
            + "\\\\ \n"
        )
        chaine += "\\end{tabular}\n\n"
    return chaine


def nettoie_latex(chaine):
    """Purge certains éléments de la `chaine` latex générée par pypandoc"""
    chaine = chaine.replace("\\tightlist\n", "")
    chaine = ajoute_abbr_latex(chaine) # détecte les abréviations

    # detecte les espaces insécables
    chaine = chaine.replace(" :", "~:")
    m = re.findall(r"(\w\w:)", chaine)
    m += re.findall(r"(\w}:)", chaine)
    for marq in m:
        if marq != "ex:" and marq != "ps:" and marq != "tp:": # les ex et les liens
            chaine = chaine.replace(marq, marq[0:2] + "~:")
    m = re.findall(r"(:\w)", chaine) # les : suivis d'une lettre
    m += re.findall(r"(:\\)", chaine)
    for marq in m:
        chaine = chaine.replace(marq, ": " + marq[-1])
    chaine = chaine.replace(" ;", "\,;")
    m = re.findall(r"(\w;)", chaine)
    m += re.findall(r"(\);)", chaine)
    for marq in m:
        chaine = chaine.replace(marq, marq[0] + "\,;")

    # Ajoute les topsep
    lignes = chaine.split("\n")
    nbre_itemize = 0
    for (i, ligne) in enumerate(lignes):
        if "\\begin{itemize}" in ligne:  # on rencontre un itemize
            nbre_itemize += 1
            if nbre_itemize == 1 and i != 0: # si c'est le 1er itemize et que ce n'est pas la 1ère ligne
                lignes[i] = lignes[i].replace("\\begin{itemize}", "\\begin{itemize}[topsep=5pt]")
        elif "\\end{itemize}" in ligne:
            nbre_itemize -= 1
    chaine = "\n".join(lignes)

    return chaine


