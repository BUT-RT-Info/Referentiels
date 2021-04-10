import logging
import string
import pypandoc
import ruamel.yaml

from modeles import get_modele, TemplateLatex
from officiel import *
from ressourcedocx import remove_ligne_vide
from tools import caracteres_recalcitrants

__LOGGER = logging.getLogger(__name__)

class Ressource():
    """Modélise une ressource lorsqu'elle est extraite d'un yaml"""
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.ressource = yaml.load(fid.read())
            except:
                Ressource.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")

    def to_latex(self, modele="pn/modele_ressource.tex"):
        """Génère le code latex décrivant la ressource"""
        modlatex = get_modele(modele) #"pn/modele_ressource.tex")

        # if self.ressource["code"] == "R107":
        #    print("ici")

        # Préparation des coeffs
        ajoutcoeff = "\\ajoutRcoeff{%s}"
        coeffRT = []
        for comp in ['RT1', 'RT2', 'RT3']:
            if comp in self.ressource["coeffs"]:
                coeffRT.append(ajoutcoeff % (str(self.ressource["coeffs"][comp])))
            else:
                coeffRT.append("")

        # Préparation des ac
        ajoutac = "\\ajoutRac{%s}{%s}"
        compRT = []
        for accomp in ['RT1', 'RT2', 'RT3']:
            comps = []
            if accomp in self.ressource["acs"]:
                for no_ac in range(len(self.ressource["acs"][accomp])): # les ac de la comp
                    code_ac = self.ressource["acs"][accomp][no_ac]
                    comps.append( ajoutac % (code_ac, DATA_ACS[accomp][code_ac]) )
            compRT.append("\n".join(comps))

        # Préparation des sae
        ajoutsaes = "\\ajoutRsae{%s}{%s}" # nom, intitule, code_latex
        saesRT = []
        for (i, sae) in enumerate(self.ressource["sae"]): # in range(len(self.apprentissages)):
            code_latex = string.ascii_uppercase[int(sae[-2])-1] + string.ascii_uppercase[int(sae[-1])-1]
            saesRT.append(ajoutsaes % (sae, get_officiel_sae_name_by_code(sae))) # , code_latex))
        saes = "\n".join(saesRT)

        ajoutprerequis = "\\ajoutRprerequis{%s}{%s}"
        prerequis = ""
        if self.ressource["prerequis"] == "Aucun":
            prerequis = ""
        else:
            liste = []
            for (no, mod) in enumerate(self.ressource["prerequis"]):
                liste.append(ajoutprerequis % (mod, get_officiel_ressource_name_by_code(mod)))
            prerequis = "\n".join(liste)

        # préparation du contexte
        contexte = self.ressource["contexte"]
        if contexte == "Aucun":
            contexte = ""
            Ressource.__LOGGER.warning(f"{self.ressource['nom']} n'a pas de contexte")

        else:
            contexte = md_to_latex(contexte)

        # contexte = remove_ligne_vide(contexte)
        # préparation du contenu

        contenu = self.ressource["contenu"] #supprime les passages à la ligne

        if contenu:
            if self.ressource["code"] == "R112":
                print("ici")
            contenu = md_to_latex(contenu)


        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(code=self.ressource["code"],
                                                       nom=self.ressource["nom"],
                                                       heures_formation=self.ressource["heures_formation"],
                                                       heures_tp=self.ressource["heures_tp"],
                                                       coeffRT1=coeffRT[0],
                                                       coeffRT2=coeffRT[1],
                                                       coeffRT3=coeffRT[2],
                                                       compRT1=compRT[0],
                                                       compRT2=compRT[1],
                                                       compRT3=compRT[2],
                                                       saes=saes,
                                                       motscles=self.ressource["motscles"] + ".",
                                                       prerequis=prerequis,
                                                       contexte=contexte,
                                                       contenu=contenu,
                                                   )
        # chaine = chaine.replace("&", "\&")
        # Supprime les \\tighlist ajoutés par pypandoc
        chaine = chaine.replace("\\tightlist\n", "")
        chaine = ajoute_abbr_latex(chaine)

        # Insère les abbréviations
        return chaine


def contient_abbr(chaine):
    mots = []
    for lettre in DATA_ABBREVIATIONS:
        for mot in DATA_ABBREVIATIONS[lettre]:
            if mot in chaine:
                mots.append(mot)
    mots = sorted(mots, key=lambda m: len(m), reverse=True) # les mots triés par nbre de carac décroissant
    return mots

def ajoute_abbr_latex(chaine):
    """Parse la chaine latex pour ajouter les abbréviations"""
    mots = chaine.split(" ")
    for (i, mot) in enumerate(mots):
        abbrs = contient_abbr(mot)
        if abbrs:
            mots[i] = mots[i].replace(abbrs[0], "\\texttt{" + abbrs[0] + "}")
    chaine = " ".join(mots)
    if "/IP" in chaine:
        chaine = chaine.replace("/IP", "/\\texttt{IP}")
    return chaine


class SAE():
    """Modélise une saé (chapeau) lorsqu'elle est extraite d'un yaml"""
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.sae = yaml.load(fid.read())
            except:
                Ressource.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")



    def to_latex(self, modele="pn/modele_sae.tex"):
        """Génère le code latex décrivant la ressource"""
        modlatex = get_modele(modele) #"pn/modele_ressource.tex")

        # Préparation des coeffs
        ajoutcoeff = "\\ajoutScoeff{%s}"
        coeffRT = []
        for comp in ['RT1', 'RT2', 'RT3']:
            if comp in self.sae["coeffs"]:
                coeffRT.append(ajoutcoeff % (str(self.sae["coeffs"][comp])))
            else:
                coeffRT.append("")

        # Préparation des ac
        ajoutac = "\\ajoutSac{%s}{%s}" # nom, intitule, code latex
        compRT = []
        for accomp in ['RT1', 'RT2', 'RT3']:
            comps = []
            if accomp in self.sae["acs"]:
                for no_ac in range(len(self.sae["acs"][accomp])): # les ac de la comp
                    code_ac = self.sae["acs"][accomp][no_ac]
                    comps.append( ajoutac % (code_ac, DATA_ACS[accomp][code_ac]) )

            compRT.append("\n".join(comps))

        # Préparation des ressources
        ajoutressources = "\\ajoutSressources{%s}{%s}"
        resRT = []
        for (i, res) in enumerate(self.sae["ressources"]): # in range(len(self.apprentissages)):
            resRT.append(ajoutressources % (res, get_officiel_ressource_name_by_code(res)))
        ressources = "\n".join(resRT)


        # préparation du descriptif
        descriptif = self.sae["description"]
        if descriptif == "Aucun":
            descriptif = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de description")
        else:
            descriptif = md_to_latex(descriptif)

        # préparation des livrables
        livrables = self.sae["livrables"]
        if livrables == "Aucun":
            livrables = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de livrables")
        else:
            livrables = md_to_latex(livrables)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(code=self.sae["code"],
                                                    titre=self.sae["titre"],
                                                    heures_encadrees=self.sae["heures_encadrees"],
                                                    heures_tp=self.sae["tp"],
                                                    heures_projet=self.sae["projet"],
                                                    coeffRT1=coeffRT[0],
                                                    coeffRT2=coeffRT[1],
                                                    coeffRT3=coeffRT[2],
                                                    compRT1=compRT[0],
                                                    compRT2=compRT[1],
                                                    compRT3=compRT[2],
                                                    description=descriptif,
                                                    ressources=ressources,
                                                    livrables= livrables,
                                                    motscles = self.sae["motscles"] + ".",
                                                   )
        # chaine = chaine.replace("&", "\&")

        chaine = chaine.replace("\\tightlist\n", "")
        chaine = ajoute_abbr_latex(chaine)
        return chaine

class ExempleSAE():
    """Modélise un exemple de SAE lorsqu'elle est extraite d'un yaml"""
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.exemple = yaml.load(fid.read())
            except:
                Ressource.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")

    def to_latex(self, modele="pn/modele_exemple_sae.tex"):
        """Génère le code latex décrivant la ressource"""
        modlatex = get_modele(modele) #"pn/modele_ressource.tex")

        # préparation du descriptif
        description = self.exemple["description"]
        if not description:
            description = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de description")
        else:
            description = md_to_latex(description)

        # préparation de la forme
        formes = self.exemple["formes"]
        if not formes:
            formes = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de formes")
        else:
            formes = md_to_latex(formes)

        # préparation de la problématique
        problematique = self.exemple["problematique"]
        if not problematique:
            problematique = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de problematique")
        else:
            problematique = md_to_latex(problematique)

        # préparation des modalites
        modalite = self.exemple["modalite"]
        if not modalite:
            modalite = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de modalite")
        else:
            modalite = md_to_latex(modalite)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(titre=self.exemple["titre"],
                                                    description=description,
                                                    formes=formes,
                                                    problematique = problematique,
                                                    modalite=modalite
                                                    )
        # chaine = chaine.replace("&", "\&")

        chaine = chaine.replace("\\tightlist\n", "")
        chaine = ajoute_abbr_latex(chaine)
        return chaine

def md_to_latex(contenu):
    """Réalise la conversion markdown to latex avec pypandoc"""
    contenu = contenu.replace("\n", "\n\n")  # corrige les suppressions de ligne à la relecture du yaml

    contenu = pypandoc.convert_text(contenu, 'tex', format='md',
                                   extra_args=['--atx-headers'])
    contenu = contenu.replace("\r\n", "\n")
    lignes = contenu.split("\n\n") # Détecte les sauts de ligne
    for (i, ligne) in enumerate(lignes):
        if i < len(lignes)-1:
            if lignes[i].strip().startswith("\\") == False and \
                lignes[i].startswith(" ") == False and \
                lignes[i+1].strip().startswith("\\") == False and \
                lignes[i+1].startswith(" ") == False and \
                lignes[i].strip().endswith("\\\\") == False:
                lignes[i] = lignes[i] + "\\\\" # ajoute un passage à la ligne latex
    contenu = "\n\n".join(lignes)

    # contenu = caracteres_recalcitrants(contenu)
    contenu = remove_ligne_vide(contenu)
    lignes = contenu.split("\n") # pour debug

    if contenu.startswith("\\begin{itemize}"):
        contenu = "\\vspace{-5pt}\n" + contenu # ajout d'un offset en cas de liste à puces
    contenu = contenu.replace("\\\\"*2, "\\\\")
    return contenu


def get_matrices_ac_ressource(saes, ressources, sem):
    """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
    les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]
    nbre_acs = len(les_codes_acs)

    saesem = saes[sem] # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])
    if len(saesem)!= nbre_saes or len(ressem) != nbre_ressources:
        __LOGGER.warning(f"Pb => il manque des saes/ressources au {sem}")

    matrice = [[False] * (nbre_saes + nbre_ressources) for i in range(nbre_acs)]

    for (i, s) in enumerate(saesem): # pour chaque SAE
        for comp in s.sae["acs"]: # pour chaque comp
            for (j, ac) in enumerate(DATA_ACS[comp]):  # pour chaque ac
                if ac in s.sae["acs"][comp]:  # si l'ac est prévue dans la ressource
                    k = les_codes_acs.index(ac)
                    matrice[k][i] = True

    for (i, r) in enumerate(ressem):  # pour chaque ressource
        for comp in r.ressource["acs"]:  # pour chaque comp
            for (j, ac) in enumerate(DATA_ACS[comp]):  # pour chaque ac
                if ac in r.ressource["acs"][comp]:  # si l'ac est prévue dans la ressource
                    k = les_codes_acs.index(ac)
                    matrice[k][i+nbre_saes] = True
    return matrice

def get_matrices_coeffs(saes, ressources, sem):
    """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
    comps = ['RT1', 'RT2', 'RT3']

    saesem = saes[sem] # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])
    if len(saesem)!= nbre_saes or len(ressem) != nbre_ressources:
        __LOGGER.warning(f"Pb => il manque des saes/ressources au {sem}")

    matrice = [[None] * (len(comps)) for i in range(nbre_saes + nbre_ressources)]

    for (i, s) in enumerate(saesem): # pour chaque SAE
        for (j, comp) in enumerate(comps): # pour chaque comp
            if comp in s.sae["coeffs"]:
                matrice[i][j] = s.sae["coeffs"][comp]

    for (i, r) in enumerate(ressem):  # pour chaque ressource
        for (j, comp) in enumerate(comps): # pour chaque comp
            if comp in r.ressource["coeffs"]:  # pour chaque ac
                matrice[i+nbre_saes][j] = r.ressource["coeffs"][comp]
    return matrice

def get_matrices_volumes(saes, ressources, sem):
    """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
    format = ['CM/TD', 'TP', 'Projet']

    saesem = saes[sem] # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])
    if len(saesem)!= nbre_saes or len(ressem) != nbre_ressources:
        __LOGGER.warning(f"Pb => il manque des saes/ressources au {sem}")

    matrice = [[0] * (len(format)) for i in range(nbre_saes + nbre_ressources)]

    for (i, s) in enumerate(saesem): # pour chaque SAE
        formation = s.sae["heures_encadrees"] if not isinstance(s.sae["heures_encadrees"], str) else 0
        tp = s.sae["tp"] if not isinstance(s.sae["tp"], str) else 0
        matrice[i][0] = formation - tp
        matrice[i][1] = tp
        matrice[i][2] = s.sae["projet"] if not isinstance(s.sae["projet"], str) else 0

    for (i, r) in enumerate(ressem):  # pour chaque ressource
        formation = r.ressource["heures_formation"] if not isinstance(r.ressource["heures_formation"], str) else 0
        tp = r.ressource["heures_tp"] if not isinstance(r.ressource["heures_tp"], str) else 0
        matrice[i + nbre_saes][0] = formation - tp
        matrice[i + nbre_saes][1] = tp

    return matrice

def str_matrice(matrice, saes, ressources, sem):
    """Renvoie une chaine de caractère affichant la matrice"""
    les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]
    nbre_acs = len(les_codes_acs)

    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])

    chaine = ""
    ligne = "{:20s} | " + "{:5s} | " * (nbre_saes + nbre_ressources)
    valeurs = ("" for i in range(nbre_saes + nbre_ressources + 1))
    trait = "-" * len(ligne.format(*valeurs))

    valeurs = [""] + [s.sae["code"] if s.sae["code"] else "????" for s in saesem] +\
              [r.ressource["code"] if r.ressource["code"] else "????" for r in ressem] + [""] * (nbre_saes - len(saesem) + nbre_ressources - len(ressem))
    valeurs = tuple(valeurs)
    chaine += ligne.format(*valeurs) + "\n" + trait + "\n"
    for (j, ac) in enumerate(les_codes_acs):
        valeurs = [ac] + [("X" if matrice[j][i] == True else "") for i in range(nbre_saes + nbre_ressources )]
        valeurs = tuple(valeurs)
        chaine += ligne.format(*valeurs) + "\n"
    chaine += trait + "\n"
    return chaine

def cesure_contenu(contenu, long_max = 30):
    chaine = "\\rotatebox[origin=c]{90}{\n"
    chaine += "\\begin{tabular}{ll}\n"
    contenu_cesure = []
    while contenu:
        indice_espace = contenu.find(" ", long_max)
        if indice_espace<0:
            contenu_cesure.append(contenu)
            contenu = ""
        else:
            contenu_cesure.append(contenu[:indice_espace])
            contenu = contenu[indice_espace+1:]
    chaine += " \\\\ ".join(contenu_cesure)
    chaine += "\\end{tabular} }"
    return chaine

def rotation_entete_colonne(contenu, pos="l"):
    chaine = "\\rotatebox[origin=" + pos + "]{90}{"
    chaine += contenu + "}"
    return chaine

def to_latex_matrice_acs(matrice, saes, ressources, sem):
    """Renvoie le tableau latex affichant la matrice"""

    les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]
    nbre_acs = len(les_codes_acs)

    lettresem = "A" if sem=="S1" else "B"

    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre


    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])
    nbre_colonnes = nbre_saes + nbre_ressources + 2
    longueur = 4
    chaine = "\\begin{tabular}[c]{|lp{%scm}|" % str(longueur) + "c|"*(nbre_saes) + "c|"*(nbre_ressources) + "}" + "\n"
    chaine += "\\hline \n" # % (nbre_saes + nbre_ressources+1)+ "\n"
    # l'entete
    chaine += " & & "
    chaine += "\multicolumn{%d}{c|}{\\textcolor{saeC}{\\bfseries SAÉs}}" % (nbre_saes) + "\n"
    chaine += " & "
    chaine += "\multicolumn{%d}{c|}{\\textcolor{ressourceC}{\\bfseries Ressources}}" % (nbre_ressources) + "\\\\ \n"
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
        contenu = "~\\textcolor{saeC}{" + s.sae["code"] + "}"
        noms_saes.append(rotation_entete_colonne(contenu, pos="r") + "\n")
    chaine += " & ".join(noms_saes) + "\n"
    chaine += " & "
    noms_ressources = []
    for (i, r) in enumerate(ressem):  # pour chaque SAE
        contenu = "~\\textcolor{ressourceC}{" + r.ressource["code"] + "}"
        noms_ressources.append(rotation_entete_colonne(contenu, pos="r") + "\n")
    chaine += " & ".join(noms_ressources) + "\n"
    chaine += "\\\\ \n"
    chaine += "\\hline \n"

    # Les ACS et les croix
    for (noc, comp) in enumerate(DATA_ACS):
        nom_comp = DATA_COMPETENCES[comp]["nom"]
        niveau = list(DATA_COMPETENCES[comp]["niveaux"].keys())[0]
        couleur = "\\textcolor{compC" + string.ascii_uppercase[noc] + "}"
        chaine += "\\multicolumn{%d}{|l|}{\hyperlink{comp:%s}{%s{\\bfseries %s - %s }}} \\\\" % (nbre_colonnes, comp, couleur, comp, nom_comp.replace("&", "\&"))
        chaine += "\\multicolumn{%d}{|l|}{\small Niveau 1 - %s} \\\\" % (nbre_colonnes, niveau.replace("&", "\&"))
        chaine += "\\hline \n"
        for (k, ac) in enumerate(DATA_ACS[comp]):
            chaine += couleur + "{" + ac + "}" + " & " + "\n"
            chaine += "\\begin{tabular}{p{%scm}} " % (str(longueur-0.2))
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
                croix.append("$\\times$" if matrice[indice_ac][nbre_saes + j] == True else "")
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

    comps = ['RT1', 'RT2', 'RT3']
    lettresem = "A" if sem == "S1" else "B"

    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre
    
    nbre_saes = len(saesem)
    nbre_colonnes = len(comps) + 2


    chaine = "\\begin{tabular}[c]{|rp{6cm}|" + "c|" * 2 + "c|" + "c|"*(len(comps)) + "}" + "\n"
    chaine += "\\hline \n" # % (nbre_saes + nbre_ressources+1)+ "\n"
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
    for (i, comp) in enumerate(comps):  # pour chaque SAE
        contenu = "\\begin{tabular}{p{5cm}}\n"
        couleur = "\\textcolor{compC" + string.ascii_uppercase[i] + "}"
        contenu += couleur + "{\\bfseries " + comp + "} - " + DATA_COMPETENCES[comp]["nom"].replace("&", "\&") + "\\\\ \n"
        niveau = list(DATA_COMPETENCES[comp]["niveaux"].keys())[0]
        contenu += " \\small Niveau 1 - " + niveau.replace("&", "\&") + "\n"
        contenu += "\\end{tabular}\n"
        noms.append(rotation_entete_colonne(contenu) + "\n")
    chaine += " & ".join(noms) + "\n"
    chaine += "\\\\ \n"

    chaine += "\\hline"
    chaine += "\\hline"

    chaine += "\multicolumn{%d}{|l}{\\textcolor{saeC}{\\bfseries SAÉs}}" % (nbre_colonnes) + "\n"
    chaine += "\\\\ \n"
    chaine += "\\hline "
    # le nom des SAE
    for (i, s) in enumerate(saesem):  # pour chaque SAE
        chaine += "\\textcolor{saeC}{" + s.sae["code"] + "} & " + "\n"
        chaine += "\\begin{tabular}{p{5.7cm}} \\tiny{" + s.sae["titre"] + "} \\end{tabular} & \n"
        chaine += str_volume(matrice_vols[i][0]) + " & "
        chaine += str_volume(matrice_vols[i][1]) + " & "
        chaine += str_volume(matrice_vols[i][2]) + " & "
        chaine += " & ".join([str_coeff(matrice_coeffs[i][j]) for j in range(len(comp))])
        chaine += "\\\\ \n"
        chaine += "\\hline "
    # Les ressources et les coeff
    chaine += "\multicolumn{%d}{|l}{\\textcolor{ressourceC}{\\bfseries Ressources}}" % (nbre_colonnes) + "\n"
    chaine += "\\\\ \n"
    chaine += "\\hline "

    for (i, r) in enumerate(ressem):  # pour chaque SAE
        chaine += "\\textcolor{ressourceC}{" + r.ressource["code"] + "} & " + "\n"
        chaine += "\\begin{tabular}{p{5.7cm}}"
        chaine += "\\tiny{" + r.ressource["nom"] + "} \\end{tabular} & \n"
        chaine += str_volume(matrice_vols[i + nbre_saes][0]) + " & "
        chaine += str_volume(matrice_vols[i + nbre_saes][1]) + " & "
        chaine += " & "
        chaine += " & ".join([str_coeff(matrice_coeffs[i + nbre_saes][j]) for j in range(len(comp))])
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
    chaine += "\multicolumn{%d}{|l}{\\bfseries Total}" % (nbre_colonnes) + "\n"
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
        chaine += " & {\\bfseries "  + str(total_heures[i]) + "h}"
    for i in range(3):
        chaine += " & {\\bfseries " + str(total_coeffs[i]) + "}"
    chaine += "\\\\ \\hline"
    chaine += "\\end{tabular}"
    return chaine


def get_total_nbre_heures(matrice_heures):
    """Calcul le nombre d'heures total des SAé d'après la matrice"""
    sommes = [sum([matrice_heures[i][j] for i in range(len(matrice_heures)) if matrice_heures[i][j]]) for j in range(3)]
    return sommes

def get_total_nbre_heures_saes(matrice_heures, sem):
    """Calcul le nombre d'heures total des SAé d'après la matrice"""
    nbre_sae = len(DATA_SAES[sem])
    sommes = [sum([matrice_heures[i][j] for i in range(nbre_sae) if matrice_heures[i][j]]) for j in range(3)]
    return sommes

def get_total_nbre_heures_ressources(matrice_heures, sem):
    """Calcul le nombre d'heures total des SAé d'après la matrice"""
    nbre_sae = len(DATA_SAES[sem])
    sommes = [sum([matrice_heures[i][j] for i in range(nbre_sae, len(matrice_heures)) if matrice_heures[i][j]]) for j in range(3)]
    return sommes

def get_total_coeffs(matrice_coeffs):
    sommes = [sum([matrice_coeffs[i][j] for i in range(len(matrice_coeffs)) if matrice_coeffs[i][j]]) for j in range(3)]
    return sommes

def get_total_coeffs_saes(matrice_coeffs, sem):
    nbre_sae = len(DATA_SAES[sem])
    sommes = [sum([matrice_coeffs[i][j] for i in range(nbre_sae) if matrice_coeffs[i][j]]) for j in range(3)]
    return sommes

def get_total_coeffs_ressources(matrice_coeffs, sem):
    nbre_sae = len(DATA_SAES[sem])
    sommes = [sum([matrice_coeffs[i][j] for i in range(nbre_sae, len(matrice_coeffs)) if matrice_coeffs[i][j]]) for j in range(3)]
    return sommes

def str_latex_abbreviations():
    """Renvoie le code latex d'un tableau pour les abbréviations"""
    liste = [ [cle, DATA_ABBREVIATIONS[lettre][cle]] for lettre in DATA_ABBREVIATIONS for cle in DATA_ABBREVIATIONS[lettre]]
    nbre_abbreviations = len(liste)
    chaine = ""
    for i in range(nbre_abbreviations):
        chaine += "\\begin{tabular}{rp{6.5cm}} \n"
        chaine += "\makebox[1.5cm][r]{\\texttt{" + liste[i][0] + "}} & " + liste[i][1] + "\\\\ \n"
        chaine += "\\end{tabular}\n\n"
    return chaine