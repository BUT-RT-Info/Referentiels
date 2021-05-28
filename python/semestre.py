"""Classe modélisant un semestre (ensemble de SAés et de ressources)
"""
import os, glob
import activite
import officiel
import logging



class SemestrePN():
    """Modélise un semestre avec ses ressources et ses saés.

    Les ressources et les saes sont chargées d'après les fichiers yaml, stockés dans des répertoires spécifiques
    """
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, nom_semestre,
                 repertoire_ressources,
                 repertoire_saes):
        self.semestre = nom_semestre

        # Chargement des ressources et des saes
        self.ressources = self.get_activites_from_yaml(nom_semestre, "ressource", repertoire_ressources) # dictionnaire des ressources
        self.saes = self.get_activites_from_yaml(nom_semestre, "sae", repertoire_saes)
        self.activites = {**self.saes, **self.ressources}

        self.codes = self.get_codes_saes_tries() + self.get_codes_ressources_tries() # les codes SAE puis ressources triés

        self.nbre_ressources = len(self.ressources)
        self.nbre_saes = len(self.saes)

        self.DATA_RESSOURCES = officiel.get_DATA_RESSOURCES() # les ressources depuis le yaml
        self.DATA_SAES = officiel.get_DATA_SAES()

        # Check si tous les contenus sont présents
        if len(self.ressources) != len(self.DATA_RESSOURCES[self.semestre]):
            SemestrePN.__LOGGER.warning(f"Dans Semestre({self.semestre}), il manque des ressources")
        if len(self.saes) != len(self.DATA_SAES[self.semestre]):
            SemestrePN.__LOGGER.warning(f"Dans Semestre({self.semestre}), il manque des saes")

        # Injecte les tags
        self.tags = self.injecte_tags()
        print(self.tags)

    def injecte_tags(self):
        """Injecte les tags dans les infos sur les ressources"""
        ttags = [] # tous les tags
        for code in self.activites:
            if isinstance(self.activites[code], activite.Ressource):
                data = self.DATA_RESSOURCES
            else: # SAé
                data = self.DATA_SAES
            tags = data[self.semestre][code]["tags-thematiques"]
            self.activites[code].add_tags(tags)
            ttags += tags
        return sorted(list(set(ttags))) # suppression des doublons

    def get_activites_from_yaml(self, nom_semestre, type,
                                repertoire):
        """Charge les activités dont le type (ressources ou saes) est indiqué,
        rattachées au semestre `nom_semestre` dont les yaml sont dans le `repertoire`"""
        activites = {}
        fichiers = [os.path.split(x)[1] for x in glob.glob(repertoire + '/*.yml')]
        if type == "sae": # ne conserve pas les exemples
            fichiers = [f for f in fichiers if "exemple" not in f]
        fichiers = sorted(fichiers)  # tri par ordre alphabétique
        for fichieryaml in fichiers:
            if type == "ressource":
                a = activite.Ressource(repertoire + "/" + fichieryaml)  # lecture du fichier
            elif type == "sae":
                a = activite.SAE(repertoire + "/" + fichieryaml)

            sem = "S" + str(a.yaml["semestre"])
            if sem == nom_semestre:
                activites[a.yaml["code"]] = a
        return activites

    def get_codes_ressources_tries(self):
        """Renvoie les codes des ressources triés par code croissant"""
        ressources = list(self.ressources.keys())
        return sorted(ressources) # , key=lambda r: r.yaml["code"])

    def get_codes_saes_tries(self):
        """Renvoie les codes des saés triés"""
        saes = list(self.saes.keys())
        return sorted(saes) # key=lambda r: r.yaml["code"])

    def get_matrices_dependances(self):
        """Renvoie la matrice traduisant les dépendances entre les saés et les ressources d'un même semestre"""
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

    def get_volumes_horaires_par_tag(self, tag, cible=""):
        """Renvoie les volumes d'heures (formation encadrée) pour un tag donné,
        en ciblant tout si cible="", ou seulement les `"ressources"` ou les `"saes"`
        """
        heures_encadrees = 0
        for (code, act) in self.activites.items():
            if tag in act.tags:
                inclus = False
                if cible == "":
                    inclus = True
                elif cible == "ressources" and isinstance(act, activite.Ressource):
                    inclus = True
                elif cible == "saes" and isinstance(act, activite.SAE):
                    inclus = True
                if inclus:
                    heures_encadrees += act.get_heures_encadrees()
        return heures_encadrees

    def get_volumes_horaires_tous_tags(self, cible=""):
        """Renvoie un dictionnaire donnant les volumes horaires tag par tag,
        en ciblant tout si cible="", ou seulement les `"ressources"` ou les `"saes"`
        """
        dico = {}
        for tag in self.tags:
            dico[tag] = self.get_volumes_horaires_par_tag(tag, cible=cible)
        return dico

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

    def get_matrices_volumes(self):
        """Calcule la matrice des volumes horaires des sae & des ressource
        pour un sem donné et la renvoie
        """

        matrice = [[0] * (len(self.activites))
                   for i in range(self.nbre_saes + self.nbre_ressources)]

        for (i, s) in enumerate(self.saes):  # pour chaque SAE
            formation = (
                s.sae["heures_encadrees"]
                if not isinstance(s.sae["heures_encadrees"], str)
                else 0
            )
            tp = s.sae["tp"] if not isinstance(s.sae["tp"], str) else 0
            matrice[i][0] = formation - tp
            matrice[i][1] = tp
            matrice[i][2] = s.sae["projet"] if not isinstance(s.sae["projet"], str) else 0

        for (i, r) in enumerate(self.ressources):  # pour chaque ressource
            formation = (
                r.ressource["heures_formation"]
                if not isinstance(r.ressource["heures_formation"], str)
                else 0
            )
            tp = (
                r.ressource["heures_tp"]
                if not isinstance(r.ressource["heures_tp"], str)
                else 0
            )
            matrice[i + self.nbre_saes][0] = formation - tp
            matrice[i + self.nbre_saes][1] = tp

        return matrice
