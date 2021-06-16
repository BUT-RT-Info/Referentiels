"""
Module semestre
"""
import glob, os, logging
import string

import officiel
import ressource
from config import Config
from latex import rotation_entete_colonne
from ressource import __LOGGER, MODALITES, get_total_nbre_heures, get_total_nbre_heures_saes, \
    get_total_nbre_heures_ressources, get_total_coeffs, get_total_coeffs_saes, get_total_coeffs_ressources


class SemestrePN():
    """
    Classe modélisant un semestre (ensemble de SAés et de ressources)

    Les ressources et les SAé sont chargées d’après les fichiers yaml,
    stockés dans des répertoires spécifiques.
    """
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, nom_semestre,
                 repertoire_ressources,
                 repertoire_saes,
                 officiel):
        """
        Modélise un semestre avec ses ressources et ses SAés, en utilisant les données
        officiels (yaml).

        """
        self.nom_semestre = nom_semestre
        self.numero_semestre = int(nom_semestre[1:])
        self.parcours = "TroncCommun"
        self.ressources = {}
        self.saes = {}
        self.exemples = {}

        # Chargement des ressources
        self.get_activites_from_yaml(type="ressource",
                                     repertoire=repertoire_ressources)
        # Chargement des SAés et des exemples
        self.get_activites_from_yaml(type="saé",
                                     repertoire=repertoire_saes)
        self.nbre_ressources = len(self.ressources)
        self.nbre_saes = len(self.saes)
        self.activites = {**self.saes, **self.ressources} # les saes et les ressources
        self.nbre_activites = len(self.activites)

        # Charge les infos officielles
        self.officiel = officiel
        self.code_acs = [code for comp in self.officiel.DATA_ACS
                            for code in self.officiel.DATA_ACS[comp]]
        self.nbre_acs = len(self.code_acs)

        # Checks divers
        self.check_activites_vs_officiel()

    def get_activites_from_yaml(self,
                                type,
                                repertoire):
        """
        Charge les activités dont le type (ressources ou saes) est indiqué, rattachées au semestre nom_semestre dont les yaml sont dans le repertoire

        :param type:
        :param repertoire:
        :return:
        """
        fichiers_definitifs = [os.path.split(x)[1] for x in glob.glob(repertoire + '/*.yml')]
        fichiers_ressources = [repertoire + "/" + f for f in fichiers_definitifs]
        fichiers_ressources = sorted(fichiers_ressources)  # tri par ordre alphabétique


        for fichieryaml in fichiers_ressources:
            if type == "ressource":
                a = ressource.Ressource(fichieryaml, officiel)  # lecture du fichier
                if a.nom_semestre == self.nom_semestre:
                    self.ressources[a.code] = a
            else: # type = "saé"
                if "exemple" not in fichieryaml:
                    a = ressource.SAE(fichieryaml, officiel)
                    if a.nom_semestre == self.nom_semestre:
                        self.saes[a.code] = a
                else: # un exemple de SAE
                    e = ressource.ExempleSAE(fichieryaml, officiel)
                    sae = e.yaml["code"]
                    if e.nom_semestre == self.nom_semestre:
                        if sae not in self.exemples:
                            self.exemples[sae] = []
                        self.exemples[sae].append(e)

        if type == "ressources":
            SemestrePN.__LOGGER.info("Semestre {} : {} ressources chargées".format(self.nom_semestre,
                          len(self.ressources)))
        else:
            SemestrePN.__LOGGER.info("Semestre {} : {} saés chargées et {} exemples".format(self.nom_semestre,
                                                                                            len(self.saes),
                                                                                            sum([len(self.exemples[s]) for s in self.exemples])))


    def check_activites_vs_officiel(self):
        """Check si le nombre de ressources & de saés chargés correspond au
        nombre prévu dans les données officielles"""
        nbre_saes_attendues = len(self.officiel.DATA_SAES[self.nom_semestre])
        nbre_ressources_attendues = len(self.officiel.DATA_RESSOURCES[self.nom_semestre])
        if len(self.saes) != nbre_saes_attendues:
            SemestrePN.__LOGGER.warning(f"Pb => il manque des saes au {self.nom_semestre}")
        if len(self.ressources) != nbre_ressources_attendues:
            SemestrePN.__LOGGER.warning(f"Pb => il manque des ressources au {self.nom_semestre}")

    def get_codes_ressources_tries(self):
        """
        Renvoie les codes des ressources triés par code croissant
        :return:
        """
        codes = self.ressources.keys()
        return sorted(codes)

    def get_codes_saes_tries(self):
        """
        Renvoie les codes des SAés triés
        :return:
        """
        codes = self.saes.keys()
        return sorted(codes)

    def get_matrices_dependances(self):
        """
        Renvoie la matrice traduisant les dépendances entre les saés et les
        ressources d’un même semestre
        :return:
        """

    def get_matrice_ac_vs_activites(self):
        """Calcule la matrice AC vs sae + ressource pour un sem donné
        et la renvoie"""
        matrice = [[False] * self.nbre_activites for i in range(self.nbre_acs)]

        # AC vs SAés
        codes_activites = self.get_codes_saes_tries() + self.get_codes_ressources_tries()
        for (i, code) in enumerate(codes_activites):  # pour chaque activité (saé & ressource)
            a = self.activites[code]
            for comp in a.yaml["acs"]:  # pour chaque comp prévue dans l'a SAé'
                for (j, ac) in enumerate(self.officiel.DATA_ACS[comp]):  # pour chaque ac prévu dans la compétence
                    if ac in a.yaml["acs"][comp]:  # si l'ac est prévue dans la saé
                        if ac not in self.code_acs:
                            SemestrePN.__LOGGER.error(f"{ac} non trouvé dans la liste des code_acs")
                        k = self.code_acs.index(ac)
                        matrice[k][i] = True

        return matrice


    def get_matrice_coeffs_comp_vs_activites(self):
        """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
        comps = ["RT1", "RT2", "RT3"]

        matrice = [[None] * (len(comps)) for i in range(self.nbre_activites)]

        codes_activites = self.get_codes_saes_tries() + self.get_codes_ressources_tries()
        for (i, code) in enumerate(codes_activites):  # pour chaque activité (saé & ressources)
            a = self.activites[code]
            for (j, comp) in enumerate(comps):  # pour chaque comp
                if comp in a.yaml["coeffs"]:
                    matrice[i][j] = a.yaml["coeffs"][comp]
        return matrice


    def get_matrice_volumes_comp_vs_activites(self):
        """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
        matrice = [[0] * (len(MODALITES)) for i in range(self.nbre_activites)]

        codes_activites = self.get_codes_saes_tries() + self.get_codes_ressources_tries()
        for (i, code) in enumerate(codes_activites):  # pour chaque activité (SAE puis ressource)
            a = self.activites[code]
            if isinstance(a, ressource.SAE):
                formation = (
                    a.yaml["heures_encadrees"]
                    if not isinstance(a.yaml["heures_encadrees"], str)
                    else 0
                )
                tp = a.yaml["tp"] if not isinstance(a.yaml["tp"], str) else 0
                matrice[i][0] = formation - tp
                matrice[i][1] = tp
                matrice[i][2] = a.yaml["projet"] if not isinstance(a.yaml["projet"], str) else 0
            else: # isinstance(s, ressource.Ressource)

                formation = (
                    a.yaml["heures_formation"]
                    if not isinstance(a.yaml["heures_formation"], str)
                    else 0
                )
                tp = (
                    a.yaml["heures_tp"]
                    if not isinstance(a.yaml["heures_tp"], str)
                    else 0
                )
                matrice[i][0] = formation - tp
                matrice[i][1] = tp

        return matrice


    def str_matrice_ac_vs_activites(self):
        """Renvoie une chaine de caractère affichant la matrice
        croisant les acs et les activites"""
        matrice = self.get_matrice_ac_vs_activites()

        chaine = ""
        ligne = "{:20s} | " + "{:5s} | " * (self.nbre_activites)
        valeurs = ("" for i in range(self.nbre_activites + 1))
        trait = "-" * len(ligne.format(*valeurs))

        valeurs = (
            [""]
            + self.get_codes_saes_tries()
            + self.get_codes_ressources_tries()
        )
        valeurs = tuple(valeurs)
        chaine += ligne.format(*valeurs) + "\n" + trait + "\n"
        for (j, ac) in enumerate(self.code_acs):
            valeurs = [ac] + [
                ("X" if matrice[j][i] == True else "")
                for i in range(self.nbre_activites)
            ]
            valeurs = tuple(valeurs)
            chaine += ligne.format(*valeurs) + "\n"
        chaine += trait + "\n"
        return chaine


    def to_latex_matrice_ac_vs_activites(self):
        """Renvoie le tableau latex affichant la matrice des apprentissages critiques
        ayant connaissances des ``saes`` et des ``ressources `` (triées dans un dictionnaire par semestre)
        pour un ``sem``estre donné
        """
        matrice = self.get_matrice_ac_vs_activites()

        nbre_colonnes = self.nbre_saes + self.nbre_ressources + 2
        longueur = 4
        chaine = (
            "\\begin{tabular}[c]{|lp{%scm}|" % str(longueur)
            + "c|" * (self.nbre_activites)
            + "}"
            + "\n"
        )
        chaine += "\\hline \n"  # % (nbre_saes + nbre_ressources+1)+ "\n"
        # l'entete
        chaine += " & & "
        chaine += (
            "\multicolumn{%d}{c|}{\\textcolor{saeC}{\\bfseries SAÉs}}" % (self.nbre_saes) + "\n"
        )
        chaine += " & "
        chaine += (
            "\multicolumn{%d}{c|}{\\textcolor{ressourceC}{\\bfseries Ressources}}"
            % (self.nbre_ressources)
            + "\\\\ \n"
        )
        chaine += "\\cline{3-%d}" % (nbre_colonnes)
        chaine += " & & "
        # les noms des SAE et des ressources
        noms_saes = []
        saes = self.get_codes_saes_tries()
        for (i, code) in enumerate(saes):  # pour chaque SAE
            s = self.saes[code]
            # saecode = "Scode" + lettresem + string.ascii_uppercase[i]
            # contenu = "\\xdef\saecode{\csname " + saecode + "\endcsname}"
            # contenu += "\\tiny{\\hyperlink{sae:\\saecode}{" + s.sae["titre"] + "~}}"
            contenu = "\\tiny{" + s.yaml["titre"] + "~}"
            noms_saes.append(rotation_entete_colonne(contenu) + "\n")
        chaine += " & ".join(noms_saes) + "\n"
        chaine += " & "
        noms_ressources = []
        ressources = self.get_codes_ressources_tries()
        for (i, code) in enumerate(ressources):  # pour chaque ressource
            r = self.ressources[code]
            # contenu = r.ressource["code"] + " | " + r.ressource["nom"]
            # noms_ressources.append(rotation_entete_colonne(contenu) + "\n")
            contenu = "\\tiny{" + r.yaml["nom"] + "~}"
            noms_ressources.append(rotation_entete_colonne(contenu) + "\n")
        chaine += " & ".join(noms_ressources) + "\n"
        chaine += "\\\\ \n"

        # les codes des SAE et des ressources
        noms_saes = []
        chaine += " & & \n"
        saes = self.get_codes_saes_tries()
        for (i, code) in enumerate(saes):  # pour chaque SAE
            s = self.saes[code]
            contenu = "~\\hyperlink{sae:" + s.yaml["code"] + "}{"
            contenu += "\\textcolor{saeC}{" + s.yaml["code"] + "}"
            contenu += "}"
            noms_saes.append(rotation_entete_colonne(contenu, pos="r") + "\n")
        chaine += " & ".join(noms_saes) + "\n"
        chaine += " & "
        noms_ressources = []
        ressources = self.get_codes_ressources_tries()
        for (i, code) in enumerate(ressources):  # pour chaque ressource
            r = self.ressources[code]
            contenu = "~\\hyperlink{res:" + r.yaml["code"] + "}{"
            contenu += "\\textcolor{ressourceC}{" + r.yaml["code"] + "}"
            contenu += "}"
            noms_ressources.append(rotation_entete_colonne(contenu, pos="r") + "\n")
        chaine += " & ".join(noms_ressources) + "\n"
        chaine += "\\\\ \n"
        chaine += "\\hline \n"

        # Les ACS et les croix
        for (noc, comp) in enumerate(self.officiel.DATA_ACS):
            nom_comp = self.officiel.DATA_COMPETENCES[comp]["nom"]
            niveau = list(self.officiel.DATA_COMPETENCES[comp]["niveaux"].keys())[0]
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
            for (k, ac) in enumerate(self.officiel.DATA_ACS[comp]):
                chaine += couleur + "{" + ac + "}" + " & " + "\n"
                chaine += "\\begin{tabular}{p{%scm}} " % (str(longueur - 0.2))
                chaine += "\\tiny{" + self.officiel.DATA_ACS[comp][ac] + "}"
                chaine += "\\end{tabular} & \n"

                croix = []
                indice_ac = self.code_acs.index(ac)
                saes = self.get_codes_saes_tries()
                for (i, code) in enumerate(saes):  # pour chaque SAE
                    s = self.saes[code]
                    croix.append("$\\times$" if matrice[indice_ac][i] == True else "")
                chaine += " & ".join(croix) + "\n"
                chaine += " & "
                croix = []
                ressources = self.get_codes_ressources_tries()
                for (j, code) in enumerate(ressources):  # pour chaque ressource
                    r = self.ressources[code]
                    croix.append(
                        "$\\times$" if matrice[indice_ac][self.nbre_saes + j] == True else ""
                    )
                chaine += " & ".join(croix) + "\\\\ \n"
                # if k < len(DATA_ACS[comp]) -1:
                #    chaine += "\\cline{2-%d}" % (nbre_saes+ nbre_ressources+3)
                chaine += "\\hline \n"
            chaine += "\\hline \n"

        chaine += "\\end{tabular}"
        return chaine


    def to_latex_matrice_coeffs_et_volumes_comp_vs_activites(self):
        """Renvoie le tableau latex affichant la matrice"""
        matrice_coeffs = self.get_matrice_coeffs_comp_vs_activites()
        matrice_vols = self.get_matrice_volumes_comp_vs_activites()

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

        lettresem = "A" if self.nom_semestre == "S1" else "B" # lettre dans le code latex pour décrire le semestre

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
                + self.officiel.DATA_COMPETENCES[comp]["nom"].replace("&", "\&")
                + "\\\\ \n"
            )
            niveau = list(self.officiel.DATA_COMPETENCES[comp]["niveaux"].keys())[0]
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
        for (i, s) in enumerate(self.saes):  # pour chaque SAE
            chaine += "\\hyperlink{sae:" + s.yaml["code"] + "}{"
            chaine += "\\textcolor{saeC}{" + s.yaml["code"] + "}"
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

        for (i, r) in enumerate(self.ressources):  # pour chaque SAE
            chaine += "\hyperlink{res:" + r.yaml["code"] + "}{"
            chaine += "\\textcolor{ressourceC}{" + r.yaml["code"] + "}"
            chaine += "}"
            chaine += " & " + "\n"

            chaine += "\\begin{tabular}{p{5.7cm}}"
            chaine += "\\tiny{" + r.ressource["nom"] + "}"
            chaine += " \\end{tabular} & \n"
            chaine += str_volume(matrice_vols[i + self.nbre_saes][0]) + " & "
            chaine += str_volume(matrice_vols[i + self.nbre_saes][1]) + " & "
            chaine += " & "
            chaine += " & ".join(
                [str_coeff(matrice_coeffs[i + self.nbre_saes][j]) for j in range(len(comp))]
            )
            chaine += "\\\\ \n"
            chaine += "\\hline "

        # Total
        total_heures = get_total_nbre_heures(matrice_vols)
        total_heures_sae = get_total_nbre_heures_saes(matrice_vols, self.nom_semestre)
        total_heures_ressources = get_total_nbre_heures_ressources(matrice_vols, self.nom_semestre)
        total_coeffs = get_total_coeffs(matrice_coeffs)
        total_coeffs_sae = get_total_coeffs_saes(matrice_coeffs, self.nom_semestre)
        total_coeffs_ressources = get_total_coeffs_ressources(matrice_coeffs, self.nom_semestre)

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
        """ % tuple(Config.ECTS[self.numero_semestre][ue] for ue in Config.ECTS[self.numero_semestre])
        chaine += "\\end{tabular}"
        return chaine