import ruamel.yaml
import logging

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
        # Rappatrie les infos communes (code/titre)
        self.code = self.yaml["code"]
        if "codeRT" not in self.yaml:
            self.__LOGGER.warning(f"{self.code}: ActivitePedagogique: codeRT manquant")
        self.codeRT = self.yaml["codeRT"]
        self.numero_semestre = self.yaml["semestre"]
        self.nom_semestre = "S" + str(self.numero_semestre)
        self.annee = None # <- chargé plus tard
        self.acs = None # <- chargé plus tard

        # Charges les données officielles
        self.officiel = pnofficiel

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


    def to_latex_competences_et_acs(self, type="ressource"):
        """Renvoie la description latex d'une liste de compétences et d'acs"""
        competences = []

        # mapping ACs de la ressource -> compétences
        for comp in self.acs:
            details_competences = []
            # le nom de la comp
            type_niveau = "\\niveau" + {"BUT1": "A", "BUT2": "B", "BUT3": "C"}[self.yaml["annee"]]
            if type == "ressource":
                champ = "ajoutRcompetence"
            else:
                champ = "ajoutScompetence"
            details_competences.append("\\%s{%s}{%s}" % (champ, comp, type_niveau))

            # Préparation du coeff (si existe)
            # ajoutcoeff = "\\ajoutRcoeff{%s}"
            # details_competences.append(ajoutcoeff % (str(self.ressource["coeffs"][comp])))

            # Préparation des ac
            if type == "ressource":
                champ = "ajoutRac"
            else:
                champ = "ajoutSac"
            ajoutac = "\\ajoutRac{%s}{%s}"
            details_acs = []
            for code_ac in self.acs[comp]:  # les acs de la ressource (triés théoriquement)
                if code_ac not in self.officiel.DATA_ACS[self.annee][comp]:
                    self.__LOGGER.warning(f"{self.code}/{self.codeRT}: to_latex: Pb {code_ac} non trouvé en {self.annee}")
                else:
                    details_acs.append("\\%s{%s}{%s}" % (type, code_ac, self.officiel.DATA_ACS[self.annee][comp][code_ac]))
            details_competences.append("\n".join(details_acs))

            # toutes les infos sur la comp
            competences.append("\n".join(details_competences))

        return competences
