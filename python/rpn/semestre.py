"""
Module semestre
"""
import glob, os, logging
import string

import rofficiel.officiel
import rpn.exemple
import rpn.ressource
import rpn.sae
from config import Config
import rpn.latex
import rpn.activite, modeles

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
        self.comp_et_acs = self.officiel.DATA_ACS[self.annee] #
        self.nbre_acs = len([self.comp_et_acs[comp][a] for comp in self.comp_et_acs for a in self.comp_et_acs[comp]])

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

        # Trie des fiches par parcours
        self.saes_par_parcours = self.tri_activites_par_parcours(self.saes)
        self.ressources_par_parcours = self.tri_activites_par_parcours(self.ressources)


    def tri_activites_par_parcours(self, dico):
        """Tri une liste d'activité par parcours (soit des ressources, soit des saes, donc les codes sont fournis dans un dictionnaire)"""
        tri = {p: {} for p in ["Tronc commun"] + rofficiel.officiel.PARCOURS} # + ["Fiches complémentaires"]}
        for code in dico:
            ajout = False
            a = dico[code]
            if a.est_tronc_commun():
                tri["Tronc commun"][code] = a
                ajout = True
            else:
                for p in rofficiel.officiel.PARCOURS:
                    if p in dico[code].yaml["parcours"]:
                        tri[p][code] = a
                        ajout = True
            if not ajout:
                self.__LOGGER.warning(f"{self.nom_semestre}: tri_activites_par_parcours: {code} n'a pas pu être ajouté à un parcours")
        return tri


    def get_niveau_from_comp(self, comp):
        """Renvoie le niveau (numéro) d'une comp en fonction de l'année => à déplacer"""
        if "RT" in comp:
            niveau = int(self.annee[-1]) # le niveau = l'année
        else:
            niveau = int(self.annee[-1]) - 1 # le niveau est décrémenté
        return niveau


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


        # injecte les exemples dans les sae
        for s in self.exemples:
            if s not in self.saes:
                self.__LOGGER.warning(f"{self.nom_semestre}: la SAE {s} n'existe pas et ne peut être chargé avec ses exemples")
            else:
                for e in self.exemples[s]:
                    self.saes[s].charge_exemple(e)

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


    def tri_codes_competences(self, parcours=None):
        """Trie les compétences avec le tronc commun d'abord (RT1, RT2, RT3) puis les parcours.
        Si parcours=`None`, tous les parcours sont considérés ;
        Sinon seul le parcours mentionné est considéré"""
        if not parcours:
            comps = [c for c in self.comp_et_acs if not c.startswith("RT")] # les comps de parcours (tous parcours confondus)
        else:
            comps = [c for c in self.comp_et_acs if not c.startswith("RT") and parcours in c]
        return ["RT{}".format(i) for i in range(1, 4)] + sorted(comps)


    def tri_comp_et_acs(self, parcours=None):
        """Renvoie les codes des ACS triés par compétence (dictionnaire {competence: [acs]},
        tous parcours confondus
        si ``parcours=None`` et pour un parcours donné s'il est mentionné"""
        competences_triees = self.tri_codes_competences(parcours=parcours)
        comp_et_acs_du_parcours = {}
        for comp in competences_triees:
            comp_et_acs_du_parcours[comp] = sorted([ac for ac in self.comp_et_acs[comp]])
        return comp_et_acs_du_parcours

    def tri_liste_codes_acs(self, parcours=None):
        """La même mais pour une liste"""
        competences_triees = self.tri_codes_competences(parcours=parcours)
        acs_du_parcours = self.tri_comp_et_acs()
        return [ac for comp in competences_triees for ac in acs_du_parcours[comp]]


    def tri_codes_activites(self, codes_a_trier, parcours=None):
        """
        Renvoie les codes_a_trier triés par code croissant.
        Si parcours = None, tous les parcours sont considérés
        Si parcours mentionné, seul le parcours indiqué est pris en compte
        """
        liste_codes = sorted(codes_a_trier)
        if not parcours:
            return liste_codes
        else: # les ressources triées d'un parcours
            codes_du_parcours = []
            for c in liste_codes:
                a = self.activites[c]
                if a.est_tronc_commun():
                    codes_du_parcours.append(c)
                elif parcours in a.parcours:
                    codes_du_parcours.append(c)
            return codes_du_parcours


    def tri_codes_ressources(self, parcours=None):
        """
        Renvoie les codes des ressources triés par code croissant.
        Si parcours = None, tous les parcours sont considérés
        Si parcours mentionné, seul le parcours indiqué est pris en compte
        """
        return self.tri_codes_activites(self.ressources, parcours=parcours)


    def tri_codes_saes(self, parcours=None):
        """
        Renvoie les codes des SAés triés
        Si parcours = None, tous les parcours sont considérés
        Si parcours mentionné, seul le parcours indiqué est pris en compte
        :return:
        """
        return self.tri_codes_activites(self.saes, parcours=parcours)


    def get_matrices_dependances(self):
        """
        Renvoie la matrice traduisant les dépendances entre les saés et les
        ressources d’un même semestre
        La matrice contient None si aucune dépendance n'est trouvée, -1 si la sae s'appuie sur une ressource,
        1 si la ressource se prolonge sur la sae => 0 si les saes et les ressources sont bien synchrone
        """
        saes = self.tri_codes_saes() # les saes tries
        ressources = self.tri_codes_ressources() # les ressources tries
        matrice = {s: {} for s in saes}
        for s in matrice:
            matrice[s] = {r: None for r in ressources}

        # Les ressources sur lesquelles s'appuient les sae
        for s in saes:
            a = self.activites[s] # la sae
            for r in a.yaml["ressources"]:
                matrice[s][r] = -1

        # les saes qui mobilisent les ressources
        for r in ressources:
            a = self.activites[r]
            for s in a.yaml["sae"]:
                if s in matrice:
                    if not matrice[s][r]:
                        matrice[s][r] = 1
                    else:
                        matrice[s][r] += 1
                else:
                    self.__LOGGER.error(f"Dans {self.nom_semestre}, {s} (venant de {r}) n'existe pas dans les sae du semestre")
        return matrice



    def get_matrice_ac(self):
        """Renvoie la matrice d'AC (trié par compétence) vs SAE et ressources sous la forme d'un dictionnaire :
        { comp : {acs: { activite: }}
        """
        # Initialisation de la matrice
        matrice = {comp: {} for comp in self.comp_et_acs}
        for comp in self.comp_et_acs:
            for acs in self.comp_et_acs[comp]:
                matrice[comp][acs] = {}
                for a in self.activites:
                    matrice[comp][acs][a] = False

        for (i, code) in enumerate(self.activites):  # pour chaque activité (saé & ressource)
            a = self.activites[code]
            for comp in self.comp_et_acs:
                if comp in a.acs: # si la comp fait partie des acs de l'activité
                    for ac in a.acs[comp]:  # pour les acs de l'activité dans la comp
                        if ac in matrice[comp]:
                            matrice[comp][ac][code] = True
                        else:
                            self.__LOGGER.error(f"{ac} n'existe pas dans sem {self.nom_semestre}")
        return matrice


    def get_matrice_coeffs_comp_vs_activites(self):
        """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
        comps = ["RT1", "RT2", "RT3"]

        matrice = [[None] * (len(comps)) for i in range(self.nbre_activites)]

        codes_activites = self.tri_codes_saes() + self.tri_codes_ressources()
        for (i, code) in enumerate(codes_activites):  # pour chaque activité (saé & ressources)
            a = self.activites[code]
            for (j, comp) in enumerate(comps):  # pour chaque comp
                if comp in a.yaml["coeffs"]:
                    matrice[i][j] = a.yaml["coeffs"][comp]
        return matrice


    def get_matrice_volumes_comp_vs_activites(self):
        """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
        matrice = [[0] * (len(rpn.activite.MODALITES)) for i in range(self.nbre_activites)]

        codes_activites = self.tri_codes_saes() + self.tri_codes_ressources()
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


    def prepare_inclusion_fiches(self, codes_par_parcours):
        """Prépare une liste de fiches à inclure sur la base de leur code"""
        chaine = ""
        for p in codes_par_parcours:
            if codes_par_parcours[p]: # s'il y a des fiches
                # chaine += "\\subsubsection{%s}\n\n" % (p)
                chaine += "\\phantomsection \\label{subsubsec:FichesSAE%s%s}\n" % (self.nom_semestre, p.split(" ")[0])
                chaine += "\\addtocounter{subsubsection}{1}\n"
                chaine += "\\addcontentsline{toc}{subsubsection}{%s}" % (p)
                liste = []
                for code in codes_par_parcours[p]:
                    if "S" in code:
                        type = "saes"
                    else:
                        type = "ressources"
                    a = codes_par_parcours[p][code]
                    liste.append("\\input{%s/%s/%s.tex}" % (type, self.nom_semestre, a.code.replace("É", "E")))
                chaine += "\\newpage\n".join(liste)
                chaine += "\\newpage\n"
                chaine += "\n"
        return chaine


    def prepare_inclusion_matrices(self):
        """Ajoute les matrices"""

        if self.nom_semestre == "S1" or self.nom_semestre == "S2":
            champs = ["\\scalebox{0.95}{\\input{synthese/%s_acs_vs_saes_ressources.tex}}" % (self.nom_semestre)]
        else:
            champs = []
            for p in rofficiel.officiel.PARCOURS:
                champs.append("\\subsubsection*{Parcours %s}" % (p))
                champs.append("\\scalebox{0.75}{\\input{synthese/%s_%s_acs_vs_saes_ressources.tex}}" % (self.nom_semestre, p))
                champs.append("\\newpage" )

        return "\n".join(champs) + "\n"

    def to_latex_description_semestres(self, modele=Config.ROOT + "/python/templates/modele_semestre.tex"):
        """Génère le code latex décrivant un semestre (ses SAE, ses ressources, ...)
        """
        modlatex = modeles.get_modele(modele)
        latex_inclusion_fiches_saes = self.prepare_inclusion_fiches(self.saes_par_parcours)
        latex_inclusion_fiches_ressources = self.prepare_inclusion_fiches(self.ressources_par_parcours)

        latex_matrices = self.prepare_inclusion_matrices()

        # Injection dans le template
        chaine = modeles.TemplateLatex(modlatex).substitute(
            numero=self.numero_semestre,
            fichierListeSAEs="liste_saes_%s.tex" % (self.nom_semestre),
            fichierListeRessources="liste_ressources_%s.tex" % (self.nom_semestre),
            fichierDependance="%s_dependances_saes_vs_ressources.tex" % (self.nom_semestre),
            # fichierMatriceACs="%s_acs_vs_saes_ressources.tex" % (self.nom_semestre),
            fichiersMatriceACs=latex_matrices,
            inclusion_fiches_saes=latex_inclusion_fiches_saes,
            inclusion_fiches_ressources=latex_inclusion_fiches_ressources,
        )
        return chaine


    def to_latex_matrice_ac_vs_activites(self, parcours=None):
        """Renvoie le tableau latex affichant la matrice des apprentissages critiques
        ayant connaissances des ``saes`` et des ``ressources``
        du semestre
        """
        # Les activités du parcours
        saes_du_parcours = self.tri_codes_saes(parcours=parcours)
        ressources_du_parcours = self.tri_codes_ressources(parcours=parcours)
        codes_activites = saes_du_parcours + ressources_du_parcours

        matrice = self.get_matrice_ac()

        comp_et_acs_du_parcours = self.tri_comp_et_acs(parcours=parcours) # dico : comp => acs

        nbre_colonnes = len(codes_activites) + 2
        longueur = 5
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
            "\multicolumn{%d}{c|}{\\textcolor{saeC}{\\bfseries SAÉs}}" % (len(saes_du_parcours)) + "\n"
        )
        chaine += " & "
        chaine += (
            "\multicolumn{%d}{c|}{\\textcolor{ressourceC}{\\bfseries Ressources}}"
            % (len(ressources_du_parcours))
            + "\\\\ \n"
        )
        chaine += "\\cline{3-%d}" % (nbre_colonnes)
        chaine += " & & "
        # les noms des SAE et des ressources
        noms_saes = []
        noms_ressources = []
        for (i, code) in enumerate(saes_du_parcours + ressources_du_parcours):  # pour chaque SAE
            a = self.activites[code]
            contenu = "\\tiny{%s}" % (a.nom.replace("&", "\&"))
            rotation = rpn.latex.rotation_entete_colonne(contenu) + "\n"
            if code in saes_du_parcours:
                noms_saes.append(rotation)
            else:
                noms_ressources.append(rotation)
        chaine += " & ".join(noms_saes) + "\n"
        chaine += " & "
        chaine += " & ".join(noms_ressources) + "\n"
        chaine += "\\\\ \n"

        # les codes des SAE et des ressources
        noms_saes = []
        noms_ressources = []
        chaine += " & & \n"
        for (i, code) in enumerate(saes_du_parcours + ressources_du_parcours):  # pour chaque SAE
            a = self.activites[code]
            if code in saes_du_parcours:
                couleur = "saeC"
            else:
                couleur = "ressourceC"
            contenu = "~\\hyperlink{%s}{\\textcolor{%s}{%s}}" % (a.get_code_latex_hyperlink(a.code),
                                                                 couleur,
                                                                 a.code)
            rotation = rpn.latex.rotation_entete_colonne(contenu, pos="r") + "\n"
            if code in saes_du_parcours:
                noms_saes.append(rotation)
            else:
                noms_ressources.append(rotation)
        chaine += " & ".join(noms_saes) + "\n"
        chaine += " & "
        chaine += " & ".join(noms_ressources) + "\n"
        chaine += "\\\\ \n"
        chaine += "\\hline \n"

        # Les ACS et les croix self.acs

        for (noc, comp) in enumerate(comp_et_acs_du_parcours): # les comp & les acs du semestre
            nom_comp = self.officiel.DATA_COMPETENCES_DETAILLEES[comp]["nom"]
            numero_niveau = self.get_niveau_from_comp(comp) # le numero du niveau de 1 à 3
            niveau = list(self.officiel.DATA_COMPETENCES_DETAILLEES[comp]["niveaux"].keys())[numero_niveau-1]

            couleur = rpn.latex.get_couleur_comp(comp)
            chaine += (
                    "\\multicolumn{%d}{|l|}{\hyperlink{%s}{\\textcolor{%s}{\\bfseries %s - %s }}} \\\\ \n"
                    % (nbre_colonnes, comp, couleur, comp,
                       nom_comp.replace("&", "\&"))
                )
            chaine += "\\multicolumn{%d}{|l|}{\small Niveau %d - %s} \\\\ \n" % (
                    nbre_colonnes,
                    numero_niveau,
                    niveau.replace("&", "\&"),
                )
            chaine += "\\hline \n"
            for ac in comp_et_acs_du_parcours[comp]:
                chaine += "\\textcolor{%s}{%s} & \n" % (couleur, ac)
                chaine += "\\begin{tabular}{p{%scm}} " % (str(longueur - 0.2))
                nom_ac = self.comp_et_acs[comp][ac].replace("&", "\&")
                chaine += "\\tiny{\\textit{" + nom_ac + "}}"
                chaine += "\\end{tabular} & \n"

                croix_saes = []
                croix_ressources = []
                for (i, code) in enumerate(saes_du_parcours + ressources_du_parcours):  # pour chaque SAE
                    a = self.activites[code]
                    if matrice[comp][ac][code] == True:
                        valeur = "$\\times$"
                    else:
                        valeur = ""
                    if code in saes_du_parcours:
                        croix_saes.append(valeur)
                    else:
                        croix_ressources.append(valeur)

                chaine += " & ".join(croix_saes) + "\n"
                chaine += " & "
                chaine += " & ".join(croix_ressources) + "\\\\ \n"
                chaine += "\\hline \n"
            if noc < len(comp_et_acs_du_parcours) - 1: # si pas la dernière comp
                chaine += "\\hline \n"

        chaine += "\\end{tabular}"
        return chaine


    def to_latex_matrice_dependance(self):
        """Renvoie le tableau latex affichant la matrice des dépendances SAEs, ressources
        """

        # Les activités du parcours
        saes = self.tri_codes_saes()
        ressources = self.tri_codes_ressources()

        matrice = self.get_matrices_dependances()

        nbre_colonnes = len(ressources) + 2
        longueur = 4
        chaine = (
                "\\begin{tabular}[c]{|l|p{%scm}|" % str(longueur)
                + "c|" * (len(ressources))
                + "}"
                + "\n"
        )
        chaine += "\\hline \n"  # % (nbre_saes + nbre_ressources+1)+ "\n"
        # l'entete
        chaine += " & & "
        # les noms des SAE et des ressources
        noms_ressources = []
        for (i, code) in enumerate(ressources):  # pour chaque SAE
            a = self.activites[code]
            contenu = "\\tiny{%s}" % (a.nom.replace("&", "\&"))
            rotation = rpn.latex.rotation_entete_colonne(contenu) + "\n"
            noms_ressources.append(rotation)
        chaine += " & ".join(noms_ressources) + "\n"
        chaine += "\\\\ \n"

        # les codes des SAE et des ressources
        noms_ressources = []
        chaine += " & & \n"
        for (i, code) in enumerate(ressources):  # pour chaque ressource
            a = self.activites[code]
            couleur = "ressourceC"
            contenu = "~\\hyperlink{%s}{\\textcolor{%s}{%s}}" % (a.get_code_latex_hyperlink(a.code),
                                                                 couleur,
                                                                 a.code)
            rotation = rpn.latex.rotation_entete_colonne(contenu, pos="r") + "\n"
            noms_ressources.append(rotation)
        chaine += " & ".join(noms_ressources) + "\n"
        chaine += "\\\\ \n"
        chaine += "\\hline \n"

        # Les dépendances
        for s in saes:  # les comp & les acs du semestre
            asae = self.activites[s]

            couleur = "saeC"
            chaine += "~\\hyperlink{%s}{\\textcolor{%s}{%s}}" % (asae.get_code_latex_hyperlink(asae.code),
                                                                 couleur,
                                                                 asae.code)
            chaine += " & "
            chaine += "\\begin{tabular}{p{%scm}} " % (str(longueur - 0.2))
            nom_sae = asae.nom.replace("&", "\&")
            chaine += "\\tiny{\\textit{" + nom_sae + "}}"
            chaine += "\\end{tabular} & \n"

            croix_saes = []
            for r in ressources:  # pour chaque SAE
                aressource = self.activites[r]
                valeur = ""
                if matrice[s][r] == -1:
                    valeur = "$\\uparrow$"
                elif matrice[s][r] == 1:
                    valeur = "$\\leftarrow$"
                elif matrice[s][r] == 0:
                    valeur = "$\\times$"
                croix_saes.append(valeur)
            chaine += " & ".join(croix_saes) + "\n"
            chaine += "\\\\ \n \\hline \n"

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
        saes = self.tri_codes_saes()
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

        ressources = self.tri_codes_ressources()
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
                                   str(r.heures_formation) if r.heures_formation else "MANQUANT",
                                   str(r.tp) if r.tp else "MANQUANT") + "\n"
        heures_formation_total = sum([r.heures_formation for r in ressem if r.heures_formation != None])
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


    def to_latex_liste_activites(self, activites_par_parcours,
                                 modele=Config.ROOT + "/python/templates/modele_liste_sae_par_semestre.tex"):
        """Prépare les codes latex d'une liste d'activité triée par parcours"""

        modlatex = modeles.get_modele(modele)

        liste_saes_et_exemples = []
        for p in activites_par_parcours:
            if len(activites_par_parcours[p]) > 0:
                titre = "\\multicolumn{3}{|l|}{\\bfseries %s}" % ("Tronc commun" if "Tronc" in p else "Parcours %s" % p)
                liste_saes_et_exemples.append(titre)
            for sae in activites_par_parcours[p]: # les saes du semestre et du parcours
                a = activites_par_parcours[p][sae] # l'activite
                info_sae = []
                hyperlink = a.get_code_latex_hyperlink(a.code)
                couleur = "saeC" if a.est_sae_from_code() else "ressourceC"
                code = "\\bfseries \\hyperlink{%s}{\\textcolor{%s}{%s}}" % (hyperlink, couleur, a.code)
                titre = "%s : " % (a.codeRT)
                titre += a.nom.replace("&", "\&")
                page = "\\pageref{subsubsec:%s}" % (hyperlink)
                info_sae.append( " & ".join([code, titre, page]))

                for exemple in []: # self.exemples[sae]:
                    code = ""
                    titre = "Exemple 1:"
                    # page = "\"
                    info_sae.append( " & ".join([code, titre, page]) )

                liste_saes_et_exemples.append("\n\\tabularnewline\n".join(info_sae))

            tableau = "\n \\tabularnewline \\hline \n".join(liste_saes_et_exemples) + "\n\\tabularnewline\n"

        chaine = modeles.TemplateLatex(modlatex).substitute(
            liste_sae_par_semestre=tableau
            # listeExemples = A FAIRE
        )
        # chaine = chaine.replace("&", "\&")
        return chaine


