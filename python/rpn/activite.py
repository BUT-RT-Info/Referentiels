import ruamel.yaml
import logging

import rofficiel.officiel
import rpn.latex

__LOGGER = logging.getLogger(__name__)

MODALITES = ["CM/TD", "TP", "Projet"]   # modalités de mise en oeuvre d'une ressource/SAE


class ActivitePedagogique():
    """Modélise les éléments de bases d'une activité pédagogique (ressource, SAE ou exemple
    de SAE) et stocke les données officielles.

    Une *activité pédagogique* est initialisée par lecture des données contenues dans fichier yaml (attribut yaml).
    Ses attributs sont :

    * ``yaml`` : le dictionnaire lu dans le fichier yaml décrivant l'activité
    * ``code`` : le code de l'activité (par ex: ``"R101"`` ou ``"SAE12"``)
    * ``nom_semestre`` : le nom du semestre où se tient l'activité (par ex: ``"S1"``)
    * ``numero_semestre`` : le numéro du semestre où se tient l'activité (1, 2, ..., 6)
    * ``officiel`` : les données officielles du templates (cf. module ``officiel``)
    """
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, pnofficiel):
        """
        Charge les données du ``fichieryaml``
        """
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.yaml = yaml.load(fid.read())
            except:
                ActivitePedagogique.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")
        # Rapatrie les infos communes (code/titre)
        self.code = self.yaml["code"]
        self.codeRT = self.yaml["codeRT"]
        self.numero_semestre = self.yaml["semestre"]
        self.nom_semestre = "S" + str(self.numero_semestre)
        self.annee = None # <- chargé plus tard
        self.adaptation_locale = None
        self.acs = None # <- chargé plus tard
        self.parcours = None

        # Heures
        self.heures_formation = None    # les heures de formation idéale
        self.heures_formation_pn = None
        self.details_heures_formation = {"cm": None, "tp": None, "td": None} # les heures de formation
        self.details_heures_formation_pn = {"cm": None, "tp": None, "td": None}  # les heures de formation moins les 30% d'adaption locale
        self.heures_projet = None
        self.heures_projet_pn = None

        # Charges les données officielles
        self.officiel = pnofficiel

    def est_tronc_commun(self):
        """
        Indique si l'activité est de tronc commun
        :return:
        """
        for p in self.parcours:
            if "Tronc" in p:
                return True
        if len(self.parcours) == len(rofficiel.officiel.PARCOURS):
            return True
        return False


    def est_ressource_from_code(self):
        """Indique si l'activité est une ressource d'après le code"""
        if "R" in self.code:
            return True
        else:
            return False

    def est_sae_from_code(self):
        """Indique si l'activité est une sae d'après le code"""
        if "SA" in self.code:
            return True
        else:
            return False


    def get_heures_encadrees(self):
        """Renvoie les heures de formation encadrees (incluant les TP)"""
        return self.heures_encadrees


    def get_heures_tp(self):
        """Renvoie les heures de TP"""
        return self.heures_tp

    def get_heures_projet(self):
        """Renvoie les heures de projet tuteurés"""
        return self.heures_projet

    def getInfo(self):
        """Renvoie les données du yaml (pour export to html)"""
        return self.yaml


    def prepare_nom(self):
        """Prépare le nom d'une activité"""
        return rpn.latex.nettoie_latex(self.nom.replace("&", "\\&"), self.officiel.DATA_ABBREVIATIONS)


    def prepare_cursus(self):
        """Prépare les informations sur le cursus"""
        # Prépare cursus
        latex_cursus = self.annee + " > " + self.nom_semestre
        if self.adaptation_locale == "oui":
            latex_cursus += " > " + "\\textit{Adaptation locale}"
        return latex_cursus

    def to_latex_liste_competences_et_acs(self):
        """Renvoie la description latex d'une liste de compétences et d'acs"""
        latex_comp = []
        # Nom compétence =>2 colonnes "\\begin{tabular}{UW}\n"
        # mapping ACs de la ressource -> compétences
        for comp in self.acs:
            details_competences = []
            # \hyperlink{comp:\compcode}{\textcolor{saeC}{\saecode}}
            # le nom de la comp
            type_niveau = "\\niveau" + {"BUT1": "A", "BUT2": "B", "BUT3": "C"}[self.yaml["annee"]]

            if "RT" in comp:
                couleur = "compC" + ["A", "B", "C"][int(comp[-1])-1]
            else:
                couleur = "compS" + ["A", "B"][int(comp[-1])-1] # la couleur pour les parcours
            nom_comp = self.officiel.DATA_COMPETENCES[comp].replace("&","\\&")
            details_competences.append("\\textcolor{%s}{%s} & %s" % (couleur, comp, nom_comp)) # le code de la comp
            # details_competences.append("\\tabularnewline")

            # Préparation du coeff (si existe)
            # ajoutcoeff = "\\ajoutRcoeff{%s}"
            # details_competences.append(ajoutcoeff % (str(self.ressource["coeffs"][comp])))

            # Préparation des ac
            details_acs = []
            for code_ac in self.acs[comp]:  # les acs de la ressource (triés théoriquement)
                if code_ac not in self.officiel.DATA_ACS[self.annee][comp]:
                    self.__LOGGER.warning(f"{self.code}/{self.codeRT}: to_latex: Pb {code_ac} non trouvé en {self.annee}")
                else:
                    nom_acs = " & " + "\\textcolor{%s}{%s}" % (couleur, code_ac)
                    nom_acs += " \\textit{%s}" % (self.officiel.DATA_ACS[self.annee][comp][code_ac].replace("&","\\&"))
                    details_acs.append(nom_acs)
            details_competences.append("\n\\tabularnewline\n".join(details_acs))

            # toutes les infos sur la comp
            latex_comp.append("\n\\tabularnewline\n".join(details_competences))

        # le latex final
        if latex_comp:
            chaine = "\\begin{tabular}[t]{UW}\n"
            chaine += "\n\\tabularnewline\n".join(latex_comp)
            chaine += "\n\\tabularnewline\n"
            chaine += "\\end{tabular}"
        else:
            chaine = ""


        return chaine

    def to_latex_champ_titre(self, titre, champ):
        """Convertit un champ en latex en lui ajoutant un titre"""
        latex_champ = ""
        if champ:
            champs = []
            champs.append("{\\bfseries " + titre + "}")
            champs.append(rpn.latex.md_to_latex(champ, self.officiel.DATA_MOTSCLES))
            latex_champ = "\n\n".join(champs)
        return latex_champ


    def to_latex_competences_et_acs(self):
        """Renvoie la description latex d'une liste de compétences et d'acs"""
        latex_comp = []

        # mapping ACs de la ressource -> compétences
        for comp in self.acs:
            details_competences = []
            # \hyperlink{comp:\compcode}{\textcolor{saeC}{\saecode}}
            # le nom de la comp
            type_niveau = "\\niveau" + {"BUT1": "A", "BUT2": "B", "BUT3": "C"}[self.yaml["annee"]]

            if "RT" in comp:
                couleur = "compC" + ["A", "B", "C"][int(comp[-1])-1]
            else:
                couleur = "compS" + ["A", "B"][int(comp[-1])-1] # la couleur pour les parcours
            nom_comp = self.officiel.DATA_COMPETENCES[comp].replace("&", "\\&")
            details_competences.append("\\textcolor{%s}{%s} %s" % (couleur, comp, nom_comp)) # le code de la comp
            # details_competences.append("\\tabularnewline")

            # Préparation du coeff (si existe)
            # ajoutcoeff = "\\ajoutRcoeff{%s}"
            # details_competences.append(ajoutcoeff % (str(self.ressource["coeffs"][comp])))

            # Préparation des ac
            details_acs = []
            for code_ac in self.acs[comp]:  # les acs de la ressource (triés théoriquement)
                if code_ac not in self.officiel.DATA_ACS[self.annee][comp]:
                    self.__LOGGER.warning(f"{self.code}/{self.codeRT}: to_latex: Pb {code_ac} non trouvé en {self.annee}")
                else:
                    nom_acs = "\\textcolor{%s}{$\\bullet$ %s}" % (couleur, code_ac)
                    intitule = self.officiel.DATA_ACS[self.annee][comp][code_ac].replace("&", "\\&")
                    nom_acs += " \\textit{%s}" % intitule
                    details_acs.append(nom_acs)
            details_competences.append("\n\\tabularnewline\n".join(details_acs))

            # toutes les infos sur la comp
            latex_comp.append("\n\\tabularnewline\n".join(details_competences))

        # le latex final
        if latex_comp:
            chaine = "\\begin{tabular}[t]{@{}T@{}}\n"
            chaine += "\n\\tabularnewline\n".join(latex_comp)
            chaine += "\n\\tabularnewline\n"
            chaine += "\\end{tabular}\n"
        else:
            chaine = ""
        return chaine


    def to_latex_liste_fiches(self, liste_fiches):
        """Prépare le latex d'une liste de fiches (fournis en paramètre) = ressources ou SAE indifféremment
        ex: liste_fiches = self.yaml["saes"]
        -> equivalent de \listeSAE"""
        latex_liste = []

        for elmt in liste_fiches:
            if elmt.startswith("S"):
                couleur = "saeC"
                intitule = self.officiel.get_sae_name_by_code(elmt)
            else:
                couleur = "ressourceC"
                intitule = self.officiel.get_ressource_name_by_code(elmt)
            if intitule:
                intitule = intitule.replace("&", "\\&") # échappement des &
            else:
                intitule = ""
            if False:
                nom = "\\hyperlink{%s}{\\textcolor{%s}{%s}} & %s" % (self.get_code_latex_hyperlink(elmt), couleur, elmt, intitule)
            else:
                nom = "\\hyperlink{%s}{\\textcolor{%s}{%s}} %s" % (self.get_code_latex_hyperlink(elmt), couleur, elmt, intitule)

            latex_liste.append(nom)

        if latex_liste:
            if False:
                chaine = "\\begin{tabular}[t]{@{}UW@{}}\n"
            else:
                chaine = "\\begin{tabular}[t]{@{}T@{}}\n"
            chaine += "\n\\tabularnewline\n".join(latex_liste)
            chaine += "\n\\tabularnewline\n"
            chaine += "\\end{tabular}"
        else:
            chaine = ""
        return chaine


    def to_latex_liste_fiches_old(self, liste_fiches):
        """Prépare le latex d'une liste de fiches (fournis en paramètre) = ressources ou SAE indifféremment
        ex: liste_fiches = self.yaml["saes"]
        -> equivalent de \listeSAE"""
        latex_liste = []

        for elmt in liste_fiches:
            if elmt.startswith("S"):
                couleur = "saeC"
                intitule = self.officiel.get_sae_name_by_code(elmt)
            else:
                couleur = "ressourceC"
                intitule = self.officiel.get_ressource_name_by_code(elmt)
            nom = "\\hyperlink{%s}{\\textcolor{%s}{%s}}~%s" % (self.get_code_latex_hyperlink(elmt), couleur, elmt, intitule)
            latex_liste.append(nom)

        if latex_liste:
            chaine = "\\begin{tabular}[t]{@{}T@{}}\n"
            chaine += "\n\\tabularnewline\n".join(latex_liste)
            chaine += "\n\\tabularnewline\n"
            chaine += "\\end{tabular}\n"
        else:
            chaine = ""
        return chaine

    def get_code_latex_hyperlink(self, contenu):
        return contenu.replace(".", "").replace("É", "E").replace(" ", "")