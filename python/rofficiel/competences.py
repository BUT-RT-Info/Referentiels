import logging

import ruamel

from rofficiel.officiel import get_DATA_COMPETENCES
from tools import supprime_accent_espace


class Competences():
    """ Modélise une liste de compétences lorsqu'elle est extraite d'un dictionnaire """

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.competences = yaml.load(fid.read())
            except:
                Competences.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")

    def getInfo(self):
        return self.competences


def devine_code_comp_by_nom_from_dict(champ):
    """Partant d'une chaine de caractères décrivant une compétence,
    détermine le code présent dans le dico officiel,
    Le dico officiel vient d'un .yml"""
    comp = []
    DATA_COMPETENCES = get_DATA_COMPETENCES()
    champ_purge = supprime_accent_espace(champ)
    for code in DATA_COMPETENCES:
        comp_purge = supprime_accent_espace(DATA_COMPETENCES[code])
        if champ_purge in comp_purge:
            comp += [code]
    return sorted(list(set(comp)))


class ACs():
    """ Modélise une liste de acs
    lorsqu'elle est extraite d'un fichier yaml """

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML(typ="safe")
            try:
                self.acs = yaml.load(fid.read())
            except:
                ACs.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")

    def getInfo(self):
        return self.acs

    @staticmethod
    def get_acs_notation_pointe(code_acs):
        """Partant d'un code d'acs de la forme ACXXXX, renvoie
        la notation pointée ACXX.XX"""
        return code_acs[:4] + "." + code_acs[4:]


def devine_code_acs_by_nom_from_dict(champ, dico):
    """Partant d'une chaine de caractères décrivant une ressource, une SAé ou un ACS,
    détermine le code présent dans le dico officiel (dico à double entrée),
    Le dico officiel vient d'un .yml"""
    acs = []
    champ_purge = supprime_accent_espace(champ)
    for annee in dico:
        for comp in dico[annee]:
            for code in dico[annee][comp]:
                acs_purge = supprime_accent_espace(dico[annee][comp][code])
                if acs_purge in champ_purge:
                    acs += [code]
    return sorted(list(set(acs)))