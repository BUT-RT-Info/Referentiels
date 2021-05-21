"""Classe modélisant un semestre (ensemble de SAés et de ressources)
"""
import os, glob
import activite


class SemestrePN():
    """Modélise un semestre avec ses ressources et ses saés.

    Les ressources et les saes sont chargées d'après les fichiers yaml, stockés dans des répertoires spécifiques
    """
    def __init__(self, nom_semestre,
                 repertoire_ressources,
                 repertoire_saes):
        self.nom = nom_semestre

        # Chargement des ressources et des saes
        self.ressources = self.get_activites_from_yaml(nom_semestre, "ressource", repertoire_ressources) # dictionnaire des ressources
        self.saes = self.get_activites_from_yaml(nom_semestre, "sae", repertoire_saes)
        self.activites = {**self.saes, **self.ressources}

        self.codes = self.get_codes_saes_tries() + self.get_codes_ressources_tries() # les codes SAE puis ressources triés

        self.nbre_ressources = len(self.ressources)
        self.nbre_saes = len(self.saes)


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