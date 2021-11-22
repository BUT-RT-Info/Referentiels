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


