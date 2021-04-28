"""
Ensemble de fonctions utiles à l'export des ressources/SAé en latex
"""
import re
import string

from config import Config
from officiel import DATA_ACS, DATA_SAES, DATA_RESSOURCES, DATA_COMPETENCES, DATA_ABBREVIATIONS
from activite import *


def rotation_entete_colonne(contenu, pos="l"):
    """Renvoie le code latex permettant la rotation de 90° d'un ``contenu``"""
    chaine = "\\rotatebox[origin=" + pos + "]{90}{"
    chaine += contenu + "}"
    return chaine


def to_latex_matrice_acs(matrice, saes, ressources, sem):
    """Renvoie le tableau latex affichant la ``matrice`` des apprentissages critiques
    ayant connaissances des ``saes`` et des ``ressources `` (triées dans un dictionnaire par semestre)
    pour un ``sem``estre donné
    """

    les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]

    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])
    nbre_colonnes = nbre_saes + nbre_ressources + 2
    longueur = 4
    chaine = (
        "\\begin{tabular}[c]{|lp{%scm}|" % str(longueur)
        + "c|" * (nbre_saes)
        + "c|" * (nbre_ressources)
        + "}"
        + "\n"
    )
    chaine += "\\hline \n"  # % (nbre_saes + nbre_ressources+1)+ "\n"
    # l'entete
    chaine += " & & "
    chaine += (
        "\multicolumn{%d}{c|}{\\textcolor{saeC}{\\bfseries SAÉs}}" % (nbre_saes) + "\n"
    )
    chaine += " & "
    chaine += (
        "\multicolumn{%d}{c|}{\\textcolor{ressourceC}{\\bfseries Ressources}}"
        % (nbre_ressources)
        + "\\\\ \n"
    )
    chaine += "\\cline{3-%d}" % (nbre_colonnes)
    chaine += " & & "
    # les noms des SAE et des ressources
    noms_saes = []
    for (i, s) in enumerate(saesem):  # pour chaque SAE
        # saecode = "Scode" + lettresem + string.ascii_uppercase[i]
        # contenu = "\\xdef\saecode{\csname " + saecode + "\endcsname}"
        # contenu += "\\tiny{\\hyperlink{sae:\\saecode}{" + s.sae["titre"] + "~}}"
        contenu = "\\tiny{" + s.sae["titre"] + "~}"
        noms_saes.append(rotation_entete_colonne(contenu) + "\n")
    chaine += " & ".join(noms_saes) + "\n"
    chaine += " & "
    noms_ressources = []
    for (i, r) in enumerate(ressem):  # pour chaque SAE
        # contenu = r.ressource["code"] + " | " + r.ressource["nom"]
        # noms_ressources.append(rotation_entete_colonne(contenu) + "\n")
        contenu = "\\tiny{" + r.ressource["nom"] + "~}"
        noms_ressources.append(rotation_entete_colonne(contenu) + "\n")
    chaine += " & ".join(noms_ressources) + "\n"
    chaine += "\\\\ \n"

    # les codes des SAE et des ressources
    noms_saes = []
    chaine += " & & \n"
    for (i, s) in enumerate(saesem):  # pour chaque SAE
        contenu = "~\\hyperlink{sae:" + s.sae["code"] + "}{"
        contenu += "\\textcolor{saeC}{" + s.sae["code"] + "}"
        contenu += "}"
        noms_saes.append(rotation_entete_colonne(contenu, pos="r") + "\n")
    chaine += " & ".join(noms_saes) + "\n"
    chaine += " & "
    noms_ressources = []
    for (i, r) in enumerate(ressem):  # pour chaque SAE
        contenu = "~\\hyperlink{res:" + r.ressource["code"] + "}{"
        contenu += "\\textcolor{ressourceC}{" + r.ressource["code"] + "}"
        contenu += "}"
        noms_ressources.append(rotation_entete_colonne(contenu, pos="r") + "\n")
    chaine += " & ".join(noms_ressources) + "\n"
    chaine += "\\\\ \n"
    chaine += "\\hline \n"

    # Les ACS et les croix
    for (noc, comp) in enumerate(DATA_ACS):
        nom_comp = DATA_COMPETENCES[comp]["nom"]
        niveau = list(DATA_COMPETENCES[comp]["niveaux"].keys())[0]
        couleur = "\\textcolor{compC" + string.ascii_uppercase[noc] + "}"
        chaine += (
            "\\multicolumn{%d}{|l|}{\hyperlink{comp:%s}{%s{\\bfseries %s - %s }}} \\\\"
            % (nbre_colonnes, comp, couleur, comp, nom_comp.replace("&", "\&"))
        )
        chaine += "\\multicolumn{%d}{|l|}{\small Niveau 1 - %s} \\\\" % (
            nbre_colonnes,
            niveau.replace("&", "\&"),
        )
        chaine += "\\hline \n"
        for (k, ac) in enumerate(DATA_ACS[comp]):
            chaine += couleur + "{" + ac + "}" + " & " + "\n"
            chaine += "\\begin{tabular}{p{%scm}} " % (str(longueur - 0.2))
            chaine += "\\tiny{" + DATA_ACS[comp][ac] + "}"
            chaine += "\\end{tabular} & \n"

            croix = []
            indice_ac = les_codes_acs.index(ac)
            for (i, s) in enumerate(saesem):  # pour chaque SAE
                croix.append("$\\times$" if matrice[indice_ac][i] == True else "")
            chaine += " & ".join(croix) + "\n"
            chaine += " & "
            croix = []
            for (j, r) in enumerate(ressem):  # pour chaque SAE
                croix.append(
                    "$\\times$" if matrice[indice_ac][nbre_saes + j] == True else ""
                )
            chaine += " & ".join(croix) + "\\\\ \n"
            # if k < len(DATA_ACS[comp]) -1:
            #    chaine += "\\cline{2-%d}" % (nbre_saes+ nbre_ressources+3)
            chaine += "\\hline \n"
        chaine += "\\hline \n"

    chaine += "\\end{tabular}"
    return chaine


def to_latex_matrice_coeffs(matrice_vols, matrice_coeffs, saes, ressources, sem):
    """Renvoie le tableau latex affichant la matrice"""

    def str_coeff(val):
        if val == None:
            return ""
        else:
            return str(val)

    def str_volume(val):
        if val:
            return str(val) + "h"
        else:
            return " "

    comps = ["RT1", "RT2", "RT3"]
    lettresem = "A" if sem == "S1" else "B"
    sem_id = int(sem[1:])
    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    nbre_saes = len(saesem)
    nbre_colonnes = len(comps) + 2

    chaine = (
        "\\begin{tabular}[c]{|rp{6cm}|"
        + "c|" * 2
        + "c|"
        + "c|" * (len(comps))
        + "}"
        + "\n"
    )
    chaine += "\\hline \n"  # % (nbre_saes + nbre_ressources+1)+ "\n"
    # le début
    chaine += " & & " + "\\multicolumn{3}{c|}{\\bfseries Volumes} \n"
    chaine += " & " + "\\multicolumn{3}{c|}{\\bfseries Coefficients} \n"
    chaine += " \\\\ \\hline \n"
    # l'entete
    chaine += " & & "
    # Volume
    chaine += rotation_entete_colonne("\\bfseries Heures de formation encadrée") + " & "
    chaine += rotation_entete_colonne("\\bfseries Heures de TPs") + " & "
    chaine += rotation_entete_colonne("\\bfseries Heures de projets") + " & "
    # les noms des comps
    noms = []
    for (i, comp) in enumerate(comps):  # pour chaque compétence
        contenu = "\\begin{tabular}{p{5cm}}\n"
        couleur = "\\textcolor{compC" + string.ascii_uppercase[i] + "}"
        contenu += (
            "\\hyperlink{comp:" + comp + "}{"
            + couleur
            + "{\\bfseries "
            + comp
            + "}} - "
            + DATA_COMPETENCES[comp]["nom"].replace("&", "\&")
            + "\\\\ \n"
        )
        niveau = list(DATA_COMPETENCES[comp]["niveaux"].keys())[0]
        contenu += " \\small Niveau 1 - " + niveau.replace("&", "\&") + "\n"
        contenu += "\\end{tabular}\n"
        noms.append(rotation_entete_colonne(contenu) + "\n")
    chaine += " & ".join(noms) + "\n"
    chaine += "\\\\ \n"

    chaine += "\\hline"
    chaine += "\\hline"

    chaine += (
        "\multicolumn{%d}{|l}{\\textcolor{saeC}{\\bfseries SAÉs}}" % (nbre_colonnes)
        + "\n"
    )
    chaine += "\\\\ \n"
    chaine += "\\hline "
    # le nom des SAE
    for (i, s) in enumerate(saesem):  # pour chaque SAE
        chaine += "\\hyperlink{sae:" + s.sae["code"] + "}{"
        chaine += "\\textcolor{saeC}{" + s.sae["code"] + "}"
        chaine += "}"
        chaine += " & " + "\n"
        chaine += (
            "\\begin{tabular}{p{5.7cm}} \\tiny{"
            + s.sae["titre"]
            + "} \\end{tabular} & \n"
        )
        chaine += str_volume(matrice_vols[i][0]) + " & "
        chaine += str_volume(matrice_vols[i][1]) + " & "
        chaine += str_volume(matrice_vols[i][2]) + " & "
        chaine += " & ".join(
            [str_coeff(matrice_coeffs[i][j]) for j in range(len(comp))]
        )
        chaine += "\\\\ \n"
        chaine += "\\hline "
    # Les ressources et les coeff
    chaine += (
        "\multicolumn{%d}{|l}{\\textcolor{ressourceC}{\\bfseries Ressources}}"
        % (nbre_colonnes)
        + "\n"
    )
    chaine += "\\\\ \n"
    chaine += "\\hline "

    for (i, r) in enumerate(ressem):  # pour chaque SAE
        chaine += "\hyperlink{res:" + r.ressource["code"] + "}{"
        chaine += "\\textcolor{ressourceC}{" + r.ressource["code"] + "}"
        chaine += "}"
        chaine += " & " + "\n"

        chaine += "\\begin{tabular}{p{5.7cm}}"
        chaine += "\\tiny{" + r.ressource["nom"] + "}"
        chaine += " \\end{tabular} & \n"
        chaine += str_volume(matrice_vols[i + nbre_saes][0]) + " & "
        chaine += str_volume(matrice_vols[i + nbre_saes][1]) + " & "
        chaine += " & "
        chaine += " & ".join(
            [str_coeff(matrice_coeffs[i + nbre_saes][j]) for j in range(len(comp))]
        )
        chaine += "\\\\ \n"
        chaine += "\\hline "

    # Total
    total_heures = get_total_nbre_heures(matrice_vols)
    total_heures_sae = get_total_nbre_heures_saes(matrice_vols, sem)
    total_heures_ressources = get_total_nbre_heures_ressources(matrice_vols, sem)
    total_coeffs = get_total_coeffs(matrice_coeffs)
    total_coeffs_sae = get_total_coeffs_saes(matrice_coeffs, sem)
    total_coeffs_ressources = get_total_coeffs_ressources(matrice_coeffs, sem)

    chaine += "\\hline "
    chaine += "\multicolumn{%d}{|l|}{\\bfseries Total}" % (nbre_colonnes) + "\n"
    chaine += "\\\\ \n"
    chaine += "\\hline "
    # sous-total SAE
    chaine += "\multicolumn{2}{|r|}{\\textit{SAÉs}} "
    for i in range(3):
        chaine += " & \\textit{" + str(total_heures_sae[i]) + "h}"
    for i in range(3):
        chaine += " & \\textit{" + str(total_coeffs_sae[i]) + "}"
    chaine += "\\\\ \hline "
    chaine += "\multicolumn{2}{|r|}{\\textit{Ressources}} "
    for i in range(3):
        chaine += " & \\textit{" + str(total_heures_ressources[i]) + "h}"
    for i in range(3):
        chaine += " & \\textit{" + str(total_coeffs_ressources[i]) + "}"
    chaine += "\\\\ \hline "
    chaine += "\multicolumn{2}{|r|}{\\bfseries SAÉs + Ressources}"
    for i in range(3):
        chaine += " & {\\bfseries " + str(total_heures[i]) + "h}"
    for i in range(3):
        chaine += " & {\\bfseries " + str(total_coeffs[i]) + "}"
    chaine += "\\\\ \\hline"

    # ECTS
    chaine += r"""\multicolumn{5}{l}{~}\\
\multicolumn{5}{l}{\bfseries Crédits ECTS}\\
\hline
\multicolumn{5}{|l|}{} & RT1 & RT2 & \multicolumn{1}{c|}{RT3} \\
    \hline
\multicolumn{5}{|l|}{} & %d & %d & %d \\
    \hline
    """ % tuple(Config.ECTS[sem_id][ue] for ue in Config.ECTS[sem_id])
    chaine += "\\end{tabular}"
    return chaine


def str_latex_abbreviations():
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