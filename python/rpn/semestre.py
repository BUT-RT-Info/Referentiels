"""
Module semestre
"""
import glob, os, logging
import string

import rpn.exemple
import rpn.ressource
import rpn.sae
from config import Config
import rpn.latex
import rpn.activite

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
                 pnofficiel):
        """
        Modélise un semestre avec ses ressources et ses SAés, en utilisant les données
        officiels (yaml).

        """
        self.nom_semestre = nom_semestre
        self.numero_semestre = int(nom_semestre[1:])

        self.parcours = None # <- Mis à jour plus tard si besoin
        self.ressources = {}
        self.saes = {}
        self.exemples = {}

        # Charge les infos officielles
        self.officiel = pnofficiel
        self.annee = self.officiel.get_annee_from_semestre(self.nom_semestre[1])

        # Les ACS du semestre
        self.acs = self.officiel.DATA_ACS[self.annee]
        self.nbre_acs = len([self.acs[comp][a] for comp in self.acs for a in self.acs[comp]])

        # Les compétences du semestre
        self.niveaux = self.officiel.get_noms_niveaux()[self.annee]
        self.comp = self.officiel.DATA_COMPETENCES

        # Chargement des ressources
        self.get_activites_from_yaml(type="ressource",
                                     repertoire=repertoire_ressources + f"/{nom_semestre}")
        # Chargement des SAés et des exemples
        self.get_activites_from_yaml(type="saé",
                                     repertoire=repertoire_saes + f"/{nom_semestre}")

        # Les données numériques
        self.nbre_ressources = len(self.ressources)
        self.nbre_saes = len(self.saes)
        self.activites = {**self.saes, **self.ressources} # les saes et les ressources
        self.nbre_activites = len(self.activites)



        # Checks divers
        self.check_activites_vs_officiel()

    def get_activites_from_yaml(self,
                                type,
                                repertoire):
        """
        Charge les activités dont le type (ressources ou saes) est indiqué, rattachées au semestre nom_semestre dont
        les yaml sont dans le repertoire
        """
        fichiers_definitifs = [os.path.split(x)[1] for x in glob.glob(repertoire + '/*.yml')]
        fichiers = [repertoire + "/" + f for f in fichiers_definitifs]
        fichiers = sorted(fichiers)  # tri par ordre alphabétique
        # ne conserve que les fichiers du-dit semestre RN.XX ou N=numero du semestre

        for fichieryaml in fichiers:
            if "R3.05" in fichieryaml:
                print("ici")
            if type == "ressource":
                a = rpn.ressource.Ressource(fichieryaml, self.officiel)  # lecture du fichier
                if a.nom_semestre == self.nom_semestre:
                    self.ressources[a.code] = a
            else: # type = "saé"
                if "exemple" not in fichieryaml:
                    a = rpn.sae.SAE(fichieryaml, self.officiel)
                    if a.nom_semestre == self.nom_semestre:
                        self.saes[a.code] = a
                else: # un exemple de SAE
                    e = rpn.exemple.ExempleSAE(fichieryaml, self.officiel)
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
        nombre prévu dans les données officielles
        """
        nbre_saes_attendues = len(self.officiel.DATA_SAES[self.nom_semestre])
        nbre_ressources_attendues = len(self.officiel.DATA_RESSOURCES[self.nom_semestre])
        if len(self.saes) != nbre_saes_attendues:
            SemestrePN.__LOGGER.warning(f"Pb => il manque des saes au {self.nom_semestre}")
        if len(self.ressources) != nbre_ressources_attendues:
            SemestrePN.__LOGGER.warning(f"Pb => il manque des ressources au {self.nom_semestre}")


    def get_codes_competences_tries(self):
        """Trie les compétences avec le tronc commun d'abord (RT1, RT2, RT3) puis les parcours"""
        comps = [c for c in self.acs if not c.startswith("RT")]
        return ["RT{}".format(i) for i in range(1, 4)] + sorted(comps)


    def get_codes_acs_tries(self):
        """Renvoie le code des ACS triés par compétence"""
        competences_triees = self.get_codes_competences_tries()
        acs_du_semeste = [ac for comp in competences_triees for ac in self.acs[comp]]  # les acs prévus au semestre dans l'ordre des comp
        return acs_du_semeste


    def get_codes_ressources_tries(self, parcours=None):
        """
        Renvoie les codes des ressources triés par code croissant
        :return:
        """
        codes = self.ressources.keys()
        liste_codes = sorted(codes)
        if not parcours:
            return liste_codes
        else: # les ressources triées d'un parcours
            codes_du_parcours = []
            for r in liste_codes:
                parcours_ressources = ",".join(self.ressources[r].yaml["parcours"])
                if parcours in parcours_ressources or "Tronc" in parcours_ressources:
                    codes_du_parcours.append(r)
            return codes_du_parcours


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
        pass

    def get_matrice_ac_vs_saes(self, parcours=None):
        """Calcule la matrice AC vs sae pour un sem donné (tous parcours confondus)"""
        codes_activites = self.get_codes_saes_tries() # le codes de saes
        (matrice, acs_du_semestre) = self.get_matrice_ac(codes_activites)
        return (matrice, acs_du_semestre, codes_activites)


    def get_matrice_ac_vs_ressources(self, parcours=None):
        """Calcule la matrice AC vs sae pour un sem donné (tous parcours confondus)"""
        codes_activites = self.get_codes_ressources_tries()
        (matrice, acs_du_semestre) = self.get_matrice_ac(codes_activites)
        return (matrice, acs_du_semestre, codes_activites)


    def get_matrice_ac(self, codes_activites):
        """Renvoie la matrice d'AC pour une série de codes_activites fournis en paramètre"""
        matrice = [[False] * len(codes_activites) for i in range(self.nbre_acs)]
        acs_du_semestre = self.get_codes_acs_tries()  # les acs prévus au semestre dans l'ordre des comp
        for (i, code) in enumerate(codes_activites):  # pour chaque activité (saé & ressource)
            a = self.activites[code]
            for ac in acs_du_semestre:  # pour chaque ac prévu dans le semestre
                comp = self.officiel.get_comp_from_acs_code(ac)
                if comp in a.acs and ac in a.acs[comp]:  # si l'ac est prévue dans la saé
                    k = acs_du_semestre.index(ac)
                    matrice[k][i] = True
        return (matrice, acs_du_semestre)


    def get_matrice_ac_vs_activites(self):
        """Calcule la matrice AC vs sae + ressource pour un sem donné
        et la renvoie, en fusion les 2 matrices acs vs saes & acs vs ressources"""
        (matrice_saes, acs_du_semestre, codes_sae) = self.get_matrice_ac_vs_saes()
        (matrice_ressources, acs_du_semestre, codes_ressources) = self.get_matrice_ac_vs_ressources()

        # Fusionne les 2 matrices
        matrice = [ [False]*(len(codes_sae) + len(codes_ressources)) for i in range(self.nbre_acs)]
        for i in range(len(codes_sae)):
            for k in range(len(acs_du_semestre)):
                matrice[k][i] = matrice_saes[k][i]
        for i in range(len(codes_ressources)):
            for k in range(len(acs_du_semestre)):
                matrice[k][i + len(codes_sae)] = matrice_ressources[k][i]
        return (matrice, acs_du_semestre, codes_sae + codes_ressources)


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
        matrice = [[0] * (len(rpn.activite.MODALITES)) for i in range(self.nbre_activites)]

        codes_activites = self.get_codes_saes_tries() + self.get_codes_ressources_tries()
        for (i, code) in enumerate(codes_activites):  # pour chaque activité (SAE puis ressource)
            a = self.activites[code]
            if isinstance(a, rpn.sae.SAE):
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


    def str_matrice_vs_activites(self, matrice, lignes, colonnes):
        """Renvoie une chaine de caractère affichant la matrice
        croisant les lignes (acs) et les colonnes(activites)"""

        chaine = ""
        ligne = "{:20s} | " + "{:6s} | " * (len(colonnes))
        valeurs = ("" for i in range(len(colonnes) + 1))
        trait = "-" * len(ligne.format(*valeurs))

        valeurs = [""] + colonnes # avec (?)
        valeurs = tuple(valeurs)
        chaine += ligne.format(*valeurs) + "\n" + trait + "\n"
        for (j, ac) in enumerate(lignes):
            if isinstance(matrice[j][0], bool):
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
        ayant connaissances des ``saes`` et des ``ressources``
        du semestre
        """
        saes_du_semestre = self.get_codes_saes_tries()
        ressources_du_semestre = self.get_codes_ressources_tries()
        matrice, acs_du_semestre, codes_activites = self.get_matrice_ac_vs_activites()

        nbre_colonnes = len(codes_activites) + 2
        longueur = 4
        chaine = (
            "\\begin{tabular}[c]{|lp{%scm}|" % str(longueur)
            + "c|" * (len(codes_activites))
            + "}"
            + "\n"
        )
        chaine += "\\hline \n"  # % (nbre_saes + nbre_ressources+1)+ "\n"
        # l'entete
        chaine += " & & "
        chaine += (
            "\multicolumn{%d}{c|}{\\textcolor{saeC}{\\bfseries SAÉs}}" % (len(saes_du_semestre)) + "\n"
        )
        chaine += " & "
        chaine += (
            "\multicolumn{%d}{c|}{\\textcolor{ressourceC}{\\bfseries Ressources}}"
            % (len(ressources_du_semestre))
            + "\\\\ \n"
        )
        chaine += "\\cline{3-%d}" % (nbre_colonnes)
        chaine += " & & "
        # les noms des SAE et des ressources
        noms_saes = []
        for (i, code) in enumerate(saes_du_semestre):  # pour chaque SAE
            s = self.saes[code]
            # saecode = "Scode" + lettresem + string.ascii_uppercase[i]
            # contenu = "\\xdef\saecode{\csname " + saecode + "\endcsname}"
            # contenu += "\\tiny{\\hyperlink{sae:\\saecode}{" + s.sae["titre"] + "~}}"
            contenu = "\\tiny{" + s.yaml["titre"] + "~}"
            noms_saes.append(rpn.latex.rotation_entete_colonne(contenu) + "\n")
        chaine += " & ".join(noms_saes) + "\n"
        chaine += " & "

        noms_ressources = []
        for (i, code) in enumerate(ressources_du_semestre):  # pour chaque ressource
            r = self.ressources[code]
            # contenu = r.ressource["code"] + " | " + r.ressource["nom"]
            # noms_ressources.append(rpn.latex.rotation_entete_colonne(contenu) + "\n")
            contenu = "\\tiny{" + r.yaml["nom"] + "~}"
            noms_ressources.append(rpn.latex.rotation_entete_colonne(contenu) + "\n")
        chaine += " & ".join(noms_ressources) + "\n"
        chaine += "\\\\ \n"

        # les codes des SAE et des ressources
        noms_saes = []
        chaine += " & & \n"
        for (i, code) in enumerate(saes_du_semestre):  # pour chaque SAE
            s = self.saes[code]
            contenu = "~\\hyperlink{sae:" + s.yaml["code"] + "}{"
            contenu += "\\textcolor{saeC}{" + s.yaml["code"] + "}"
            contenu += "}"
            noms_saes.append(rpn.latex.rotation_entete_colonne(contenu, pos="r") + "\n")
        chaine += " & ".join(noms_saes) + "\n"
        chaine += " & "

        noms_ressources = []
        for (i, code) in enumerate(ressources_du_semestre):  # pour chaque ressource
            r = self.ressources[code]
            contenu = "~\\hyperlink{res:" + r.yaml["code"] + "}{"
            contenu += "\\textcolor{ressourceC}{" + r.yaml["code"] + "}"
            contenu += "}"
            noms_ressources.append(rpn.latex.rotation_entete_colonne(contenu, pos="r") + "\n")
        chaine += " & ".join(noms_ressources) + "\n"
        chaine += "\\\\ \n"
        chaine += "\\hline \n"

        # Les ACS et les croix
        for (noc, comp) in enumerate(self.officiel.DATA_ACS[self.annee]):
            nom_comp = self.officiel.DATA_COMPETENCES_DETAILLEES[comp]["nom"]
            niveau = list(self.officiel.DATA_COMPETENCES_DETAILLEES[comp]["niveaux"].keys())[0]
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
                indice_ac = acs_du_semestre.index(ac)
                for (i, code) in enumerate(saes_du_semestre):  # pour chaque SAE
                    s = self.saes[code]
                    croix.append("$\\times$" if matrice[indice_ac][i] == True else "")
                chaine += " & ".join(croix) + "\n"
                chaine += " & "
                croix = []
                for (j, code) in enumerate(ressources_du_semestre):  # pour chaque ressource
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
        chaine += rpn.latex.rotation_entete_colonne("\\bfseries Heures de formation encadrée") + " & "
        chaine += rpn.latex.rotation_entete_colonne("\\bfseries Heures de TPs") + " & "
        chaine += rpn.latex.rotation_entete_colonne("\\bfseries Heures de projets") + " & "
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
                + self.officiel.DATA_COMPETENCES_DETAILLEES[comp]["nom"].replace("&", "\&")
                + "\\\\ \n"
            )
            niveau = list(self.officiel.DATA_COMPETENCES_DETAILLEES[comp]["niveaux"].keys())[0]
            contenu += " \\small Niveau 1 - " + niveau.replace("&", "\&") + "\n"
            contenu += "\\end{tabular}\n"
            noms.append(rpn.latex.rotation_entete_colonne(contenu) + "\n")
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
        saes = self.get_codes_saes_tries()
        for (i, code) in enumerate(saes):  # pour chaque SAE
            s = self.saes[code]
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

        ressources = self.get_codes_ressources_tries()
        for (i, code) in enumerate(ressources):  # pour chaque SAE
            r = self.ressources[code]
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
        total_heures_activites = self.get_total_nbre_heures_par_modalite()
        total_heures_sae = self.get_total_nbre_heures_par_modalite(type="saés")
        total_heures_ressources = self.get_total_nbre_heures_par_modalite(type="ressources")
        total_coeffs_activites = self.get_total_coeffs_par_comp()
        total_coeffs_sae = self.get_total_coeffs_par_comp(type="saés")
        total_coeffs_ressources = self.get_total_coeffs_par_comp(type="ressources")

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
            chaine += " & {\\bfseries " + str(total_heures_activites[i]) + "h}"
        for i in range(3):
            chaine += " & {\\bfseries " + str(total_coeffs_activites[i]) + "}"
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


    def get_total_nbre_heures_par_modalite(self, type=""):
        """Calcule le nombre d'heures total d'après la matrice des volumes horaires,
        sur les 3 modalités (CM/TD, TP, projet).
        Par défaut, saés et ressources sont pris en compte.

        `type` permet de limiter le calcul soit aux `"saés"`, soit aux `"ressources"`.
        """
        matrice_heures = self.get_matrice_volumes_comp_vs_activites()

        plage = range(len(matrice_heures)) # plage sur les saés et les ressources
        if type == "saés":
            plage = range(self.nbre_saes)
        elif type == "ressources":
            plage = range(self.nbre_saes, len(matrice_heures))

        sommes = [
            sum(
                [
                    matrice_heures[i][j]
                    for i in plage
                    if matrice_heures[i][j]
                ]
            )
            for j in range(3)
        ]
        return sommes



    def get_total_coeffs_par_comp(self, type=""):
        """Calcule le total (somme) des coeffs de chaque compétence, en utilisant la matrice
        des coefficients.
        Par défaut, saés et ressources sont pris en compte.

        `type` permet de limiter le calcul soit aux `"saés"`, soit aux `"ressources"`.
        """
        matrice_coeffs = self.get_matrice_coeffs_comp_vs_activites()
        plage = range(len(matrice_coeffs))  # plage sur les saés et les ressources
        if type == "saés":
            plage = range(self.nbre_saes)
        elif type == "ressources":
            plage = range(self.nbre_saes, len(matrice_coeffs))
        sommes = [
            sum(
                [
                    matrice_coeffs[i][j]
                    for i in plage
                    if matrice_coeffs[i][j]
                ]
            )
            for j in range(3)
        ]
        return sommes


    def affiche_bilan_heures(self):
        """Renvoie une chaine décrivant un bilan des heures-ressources du semestre

        .. deprecated:: à revoir
        """
        ligne = "{:20s} | {:75s} | {:10s} | {:10s} |"
        trait = "-"*len(ligne.format("", "", "", ""))

        ressem = self.ressources # les ressources du semestre
        chaine = ""
        chaine += trait + "\n"
        chaine += ligne.format("Code", "Ressource", "Form.", "dont TP") + "\n"
        chaine += trait + "\n"
        for (code, r) in self.ressources.items():
            chaine += ligne.format(r.code if r.code else "MANQUANT",
                               # r.nom[:30] + ("..." if len(r.nom) > 30 else "") ,
                               r.nom,
                               str(r.heures_encadrees) if r.heures_encadrees else "MANQUANT",
                               str(r.tp) if r.tp else "MANQUANT") + "\n"
        heures_formation_total = sum([r.heures_encadrees for r in ressem if r.heures_encadrees != None])
        heures_tp_total = sum([r.tp for r in ressem if r.tp != None])
        chaine += trait + "\n"
        chaine += ligne.format("", "Total", str(heures_formation_total), str(heures_tp_total)) + "\n"
        chaine += trait + "\n"
        return chaine

    def get_matrice_prerequis(self):
        """Renvoie la matrice traduisant les dépendances entre les SAés et les
        ressources d'un même semestre (les activités hors semestres ne sont pas considérées).

        Une activité i dépend d'une activité j si l'activité j fait partie des pré-requis de l'activité i.
        """
        matrice = [[0] * (self.nbre_saes + self.nbre_ressources) for i in range(len(self.codes))]

        for (i, code) in enumerate(self.codes):  # pour chaque SAE ou ressources
            act = self.activites[code]
            prerequis = []
            if "prerequis" in act.yaml:
                prerequis = act.yaml["prerequis"]

            for (j, code_prerequis) in enumerate(self.codes):
                if code_prerequis in prerequis:
                    matrice[i][j] = 1
        return matrice

    def get_volumes_horaires_ressources(self):
        """Calcule le nombre d'heures total des ressources et
        renvoie une liste donnant [heures_encadrees (tp_inclus), heures_tp, heures_projet]"""
        heures = [0]*3
        for (code, r) in self.ressources.items():
            heures[0] += r.get_heures_encadrees()
            heures[1] += r.get_heures_tp()
            heures[2] += r.get_heures_projet()
        return heures

    def get_volumes_horaires_saes(self):
        """Calcule le nombre d'heures total des SAés et renvoie une liste donnant
        [heures_encadrees (tp_inclus), heures_tp, heures_projet]
        """
        heures = [0] * 3
        for (code, s) in self.saes.items():
            heures[0] += s.get_heures_encadrees()
            heures[1] += s.get_heures_tp()
            heures[2] += s.get_heures_projet()
        return heures
