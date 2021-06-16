"""
Module semestre
"""
import glob, os
import ressource

class SemestrePN():
    """
    Classe modélisant un semestre (ensemble de SAés et de ressources)

    Les ressources et les SAé sont chargées d’après les fichiers yaml,
    stockés dans des répertoires spécifiques.
    """

    def __init__(self, nom_semestre,
                 repertoire_ressources,
                 repertoire_saes):
        """
        Modélise un semestre avec ses ressources et ses SAés.

        """
        self.nom_semestre = nom_semestre
        self.parcours = "TroncCommun"
        self.ressources = None
        self.saes = None
        self.exemples = {}

        # Chargement des ressources
        self.get_activites_from_yaml(type="ressource",
                                     repertoire=repertoire_ressources)
        # Chargement des SAés et des exemples
        self.get_activites_from_yaml(type="saé",
                                     repertoire=repertoire_saes)

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
                a = ressource.Ressource(fichieryaml)  # lecture du fichier
                sem = "S" + str(a.yaml["semestre"])
                if sem == self.nom_semestre:
                    self.ressources.append(a)
            else: # type = "saé"
                if "exemple" not in fichieryaml:
                    a = ressource.SAE(fichieryaml)
                    sem = "S" + str(a.yaml["semestre"])
                    if sem == self.nom_semestre:
                        self.saes.append(a)
                else: # un exemple de SAE
                    e = ressource.ExempleSAE(fichieryaml)
                    sem = "S" + str(e.yaml["semestre"])
                    sae = e.yaml["code"]
                    if sem == self.nom_semestre:
                        if sae not in self.exemples:
                            self.exemples[sae] = []
                        self.exemples[sae].append(e)

        # tri par code croissant
        if type == "ressources":
            self.ressources = sorted(self.ressources, key=lambda a: a.yaml["code"])
        else:
            self.saes = sorted(self.saes, key=lambda a: a.yaml["code"])


    def get_codes_ressources_tries(self):
        """
        Renvoie les codes des ressources triés par code croissant
        :return:
        """

    def get_codes_saes_tries(self):
        """
        Renvoie les codes des SAés triés

        :return:
        """

    def get_matrices_dependances(self):
        """
        Renvoie la matrice traduisant les dépendances entre les saés et les ressources d’un même semestre
        :return:
        """
