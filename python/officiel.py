"""
Module dédié aux éléments synthétiques (extrait des tableaux de synthèse
maintenu par le PACD) sur les ressources, les SAés, les Compétences et les ACS.
Parmi ces éléments, les codes et les noms officiels ; des tags pour calcul
d'information de répartition.

Les ressources sont décrites dans un fichier yaml/ressources.yml structuré par semestre
et par code, de la forme :

.. code-block:: python

   S1:
     R101:
       nom: "Initiation aux réseaux informatiques"
       tags-thematiques: ["réseau", "métier"]

Idem pour les SAés, dans yaml/saes.yml de la forme :

.. code-block:: python

   S1:
     SAE11:
       nom: "..."
       tags-thematiques: ["métier"]

"""

import logging, yaml, ruamel
import unicodedata
from config import Config

__LOGGER = logging.getLogger(__name__)

# *************************************** #
# Récupère les informations officielles  #
## Les ressources
def get_DATA_RESSOURCES(repertoire = "yaml/pn"):
    """Récupère les informations sur les ressources (triées par semestre
    et par nom), en extrayant les données du fichier yaml/ressources.yml.
    """
    with open(Config.ROOT + "/" + repertoire + "/ressources.yml", 'r', encoding="utf8") as fid:
        DATA_RESSOURCES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_RESSOURCES


## Les ACS
def get_DATA_ACS(repertoire = "yaml/pn"):
    """Récupère les informations des ACS,
    en extrayant les données du fichier yaml/competences.yml"""
    with open(Config.ROOT+"/"+ repertoire +"/acs.yml", 'r', encoding="utf8") as fid:
        DATA_ACS = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_ACS

## Les SAEs
def get_DATA_SAES(repertoire = "yaml/pn"):
    """Récupère les informations des SAés (triées par semestre et par nom),
    en extrayant les données du fichier yaml/saes.yml"""
    with open(Config.ROOT+"/"+ repertoire +"/saes.yml", 'r', encoding="utf8") as fid:
        DATA_SAES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_SAES

## Les compétences
def get_DATA_COMPETENCES(repertoire = "yaml/competences"):
    with open(Config.ROOT+"/"+ repertoire + "/RT123.yml", 'r', encoding="utf8") as fid:
        DATA_COMPETENCES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_COMPETENCES

## Les abréviations
def get_DATA_ABBREVIATIONS(repertoire = "yaml"):
    with open(Config.ROOT+"/"+ repertoire +"/abbreviations.yml", "r", encoding="utf8") as fid:
        DATA_ABBREVIATIONS = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_ABBREVIATIONS

## Les mostcles (commandes, logiciels, etc...)
def get_MOTS_CLES(repertoire = "yaml"):
    with open(Config.ROOT+"/"+ repertoire +"/motscles.yml", "r", encoding="utf8") as fid:
        DATA_MOTSCLES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_MOTSCLES

AUCUN_PREREQUIS = "Aucun"

class Officiel():
    """
    Récupère et stocke des informations dites *officielles*, fournies par différents
    fichiers yaml (conçus manuellement).

    Certaines traduisent les tableurs de synthèse du GT-BUT avec :

    * le nom des ressources (cf. ressources.yml)
    * le nom des saés (cf. saes.yml)
    * les compétences (cf. RT123.yml)
    * les  apprentissages critiques (structurées par compétences) (cf. acs.yml)

    D'autres donnent : les mots-clés, les abréviations propres à RT (cf. motscles.yml, abreviations.yml).

    Fournit également différentes méthodes pour exploiter ces données officielles.
    """

    def __init__(self):

        ## Les ressources
        self.DATA_RESSOURCES = get_DATA_RESSOURCES()
        ## Les ACS
        self.DATA_ACS = get_DATA_ACS()
        ## Les SAEs
        self.DATA_SAES = get_DATA_SAES()
        ## Les compétences
        self.DATA_COMPETENCES = get_DATA_COMPETENCES()
        ## Les abréviations
        self.DATA_ABBREVIATIONS = get_DATA_ABBREVIATIONS()
        ## Les mostcles (commandes, logiciels, etc...)
        self.DATA_MOTSCLES = get_MOTS_CLES()


    def get_ressource_name_by_code(self, code):
        """Pour un code de ressource valide (existant dans ``DATA_RESSOURCES``)
        et ce sans connaissance du semestre,
        fournit le nom officiel de la ressource
        """
        return get_officiel_name_by_code_using_dict(code, self.DATA_RESSOURCES)

    def get_sae_name_by_code(self, code):
        """Pour un code de saé valide (existant dans ``DATA_SAES``)
        et ce sans connaissance du semestre,
        fournit le nom officiel de la sae
        """
        return get_officiel_name_by_code_using_dict(code, self.DATA_SAES)

    def get_sem_sae_by_code(self, code_sae):
        """Récupère le semestre de la sae d'après son ``code_sae``
        """
        for sem in self.DATA_SAES:
            if code_sae in self.DATA_SAES[sem]:
                return sem


def supprime_accent_espace(chaine):
    """Met une chaine en minuscule, supprime les accents, les ponctuations et les espaces"""
    purge = chaine.lower().replace("'", "").replace("’", "")
    purge = unicodedata.normalize('NFD', purge).encode('ascii', 'ignore').decode('ascii')
    purge = purge.replace(" ", "")
    return purge

def devine_code_by_nom_from_dict(champ, dico):
    """Partant d'une chaine de caractères décrivant une ressource, une SAé ou un ACS,
    détermine le code présent dans le dico officiel (dico à double entrée),
    Le dico officiel vient d'un .yml"""
    acs = []
    champ_purge = supprime_accent_espace(champ)
    for comp in dico:
        for code in dico[comp]:
            acs_purge = supprime_accent_espace(dico[comp][code])
            if acs_purge in champ_purge:
                acs += [code]
    return sorted(list(set(acs)))



def get_officiel_name_by_code_using_dict(code, dico):
    """Extrait un nom à partir d'un code (pour les RESSOURCES ou les SAES)"""
    for sem in dico:
        for rcode in dico[sem]:
            if rcode==code:
                return dico[sem][code]

def get_code_from_nom_using_dict(nom, dico):
    """Récupère le code d'une ressource d'après son nom en utilisant les noms officiels
    des ressources du yaml si dico == DATA_RESSOURCES ; sinon fait de même avec les SAE"""
    nom = supprime_accent_espace(nom)
    for sem in dico:
        for code in dico[sem]:
            nom_data = supprime_accent_espace(dico[sem][code])
            if nom.startswith(nom_data):
                return code

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

class ACs():
    """ Modélise une liste de acs lorsqu'elle est extraite d'un fichier yaml """

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


if __name__=="__main__":
    print("toto")
