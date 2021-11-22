"""
Ensemble de fonctions utiles à l'export des ressources/SAé en latex.

Une partie des traitements s'appuient sur :

* ``DATA_ABBREVIATIONS`` provenant du fichier ``yaml\\abbreviations.yml``
* ``DATA_MOTSCLES`` provenant du fichier ``yaml\\motscles.yml`` qui liste notamment des
  noms de logiciels, des commandes...
"""

import re, pypandoc, string
from tools import remove_ligne_vide


def rotation_entete_colonne(contenu, pos="l"):
    """Renvoie le code latex permettant la rotation de 90° d'un ``contenu``
    """
    chaine = "\\rotatebox[origin=" + pos + "]{90}{"
    chaine += contenu + "}"
    return chaine


def to_latex_abbreviations(DATA_ABBREVIATIONS):
    """Renvoie le code latex d'un tableau listant l'ensemble des abréviations
     contenue dans le dictionnaire ``DATA_ABBREVIATIONS``.
     """
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


def nettoie_latex(chaine, DATA_ABBREVIATIONS):
    """Purge certains éléments de la ``chaine`` latex générée par ``pypandoc``
    et détecte les abréviations indiquées dans le dictionnaire
    ``DATA_ABBREVIATIONS``.
    """
    chaine = chaine.replace("\\tightlist\n", "")
    chaine = ajoute_abbr_latex(chaine, DATA_ABBREVIATIONS) # détecte les abréviations

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


def ajoute_abbr_latex(chaine, DATA_ABBREVIATIONS):
    """
    Parse la ``chaine`` latex pour ajouter les abréviations décrites dans le dictionnaire
    ``DATA_ABBREVIATIONS`` et les remplacer par
    le balisage latex ``\\textabbrv{abreviation}``
    """
    mots = chaine.split(" ")
    for (i, mot) in enumerate(mots):
        abbrs = contient_abbr(mot, DATA_ABBREVIATIONS)
        if abbrs:
            mots[i] = mots[i].replace(abbrs[0], "\\textabbrv{" + abbrs[0] + "}")
    chaine = " ".join(mots)
    if "/IP" in chaine:
        chaine = chaine.replace("/IP", "/\\textabbrv{IP}")
    return chaine


def contient_abbr(chaine, DATA_ABBREVIATIONS):
    """Détecte les abréviations présentes dans la ``chaine`` et présentes dans le dictionnaire
    ``DATA_ABBREVIATIONS`` et les renvoie sous forme d'une liste d'abréviations triée
    par nombre de caractères décroissants"""
    mots = []
    for lettre in DATA_ABBREVIATIONS:
        for mot in DATA_ABBREVIATIONS[lettre]:
            if mot in chaine:
                mots.append(mot)
    mots = sorted(
        mots, key=lambda m: len(m), reverse=True
    )  # les mots triés par nbre de carac décroissant
    return mots


def md_to_latex(contenu, DATA_MOTSCLES):
    """Réalise la conversion d'un ``contenu`` markdown en syntaxe latex avec pypandoc.

    Détecte les mots clés indiqués dans le dictionnaire ``DATA_MOTSCLES`` pour les mettre
    en évidence dans le code latex.
    """
    contenu = contenu.replace(
        "\n", "\n\n"
    )  # corrige les suppressions de ligne à la relecture du yaml

    contenu = pypandoc.convert_text(
        contenu, "tex", format="md", extra_args=["--atx-headers"]
    )
    contenu = contenu.replace("\r\n", "\n")
    lignes = contenu.split("\n\n")  # Détecte les sauts de ligne
    for (i, ligne) in enumerate(lignes):
        if i < len(lignes) - 1:
            if (
                lignes[i].strip().startswith("\\") == False
                and lignes[i].startswith(" ") == False
                and lignes[i + 1].strip().startswith("\\") == False
                and lignes[i + 1].startswith(" ") == False
                and lignes[i].strip().endswith("\\\\") == False
            ):
                lignes[i] = lignes[i] + "\\\\"  # ajoute un passage à la ligne latex
    contenu = "\n\n".join(lignes)

    # contenu = caracteres_recalcitrants(contenu)
    contenu = remove_ligne_vide(contenu)
    lignes = contenu.split("\n")  # pour debug

    if contenu.startswith("\\begin{itemize}"):
        contenu = (
            "\\vspace{-10pt}\n" + contenu
        )  # ajout d'un offset en cas de liste à puces
    contenu = contenu.replace("\\\\" * 2, "\\\\[25pt]")
    if not contenu.endswith("\\end{itemize}"):
        contenu += "\\\\[3pt]"

    contenu = ajoute_cmd_latex(contenu, DATA_MOTSCLES)  # détecte les commandes

    return contenu


def cesure_contenu(contenu, long_max=30):
    """Découpe un ``contenu`` pour le mettre en forme sur plusieurs lignes, chaque ligne
    ayant ``long_max`` caractères maximum.

    Le découpage se fait au mot près.
    """
    chaine = "\\rotatebox[origin=c]{90}{\n"
    chaine += "\\begin{tabular}{ll}\n"
    contenu_cesure = []
    while contenu:
        indice_espace = contenu.find(" ", long_max)
        if indice_espace < 0:
            contenu_cesure.append(contenu)
            contenu = ""
        else:
            contenu_cesure.append(contenu[:indice_espace])
            contenu = contenu[indice_espace + 1 :]
    chaine += " \\\\ ".join(contenu_cesure)
    chaine += "\\end{tabular} }"
    return chaine


def ajoute_cmd_latex(chaine, DATA_MOTSCLES):
    """
    Parse la ``chaine`` latex pour ajouter les abréviations et les mettre en forme
    avec le balisage ``\\textabbrv{abreviation}``
    """
    mots = chaine.split(" ")
    for (i, mot) in enumerate(mots):
        champs = mot.split("\n")
        for (j, champ) in enumerate(champs):
            cmd = contient_commandes(champ, DATA_MOTSCLES)
            if cmd:
                champs[j] = champs[j].replace(cmd, "\\texttt{" + cmd + "}")
        mots[i] = "\n".join(champs)
    chaine = " ".join(mots)
    return chaine

def contient_commandes(chaine, DATA_MOTSCLES):
    """
    Détecte si la ``chaine`` fait partie des commandes listées dans le dictionnaire ``DATA_MOTSCLES``.

    La détection prend en compte un éventuel caractère de ponctuation final.
    """
    chaine_texte = ""
    for car in chaine:
        if car in string.ascii_lowercase + "-":
            chaine_texte += car
    if "ipc" in chaine:
        print("ici")
    if chaine_texte in DATA_MOTSCLES["commandes"]:
        return chaine_texte
    return None
