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

## L'association code ressource -> fichier google
def get_DATA_R_DOCX(repertoire = "yaml/docx"):
    with open(Config.ROOT+"/"+ repertoire +"/docx.yml", "r", encoding="utf8") as fid:
        DATA_R_DOCX = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_R_DOCX

AUCUN_PREREQUIS = "Aucun"

PARCOURS = ["Cyber", "DevCloud", "IOM", "ROM", "PilPro"]

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
        ## L'association ressources -> fichier.docx
        self.DATA_R_DOCX = get_DATA_R_DOCX()


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


    def get_sem_ressource_by_code(self, code_ressource):
        """Récupère le semestre de la sae d'après son ``code_sae``
        """
        for sem in self.DATA_RESSOURCES:
            if code_ressource in self.DATA_RESSOURCES[sem]:
                return sem


    def get_sem_sae_by_code(self, code_sae):
        """Récupère le semestre de la sae d'après son ``code_sae``
        """
        for sem in self.DATA_SAES:
            if code_sae in self.DATA_SAES[sem]:
                return sem


    def get_docx_file_by_code(self, code_ressource):
        """Renvoie le nom du fichier docx contenant le descriptif d'une ressource à l'aide de son code"""
        for sem in self.DATA_R_DOCX:
            if code_ressource in self.DATA_R_DOCX[sem]:
                return self.DATA_R_DOCX[sem][code_ressource]
        return None


    def get_comp_from_acs_code(self, code_acs):
        """Renvoie le nom/code de la comp en utilisant le code (notation pointé) d'un acs"""
        for annee in self.DATA_ACS:
            for comp in self.DATA_ACS[annee]:
                if code_acs in self.DATA_ACS[annee][comp]:
                    return comp
        return None

    @staticmethod
    def get_annee_from_semestre(sem):
        """Renvoie l'année en fonction d'un semestre"""
        if sem in ["1", "2"]:
            return "BUT1"
        elif sem in ["3", "4"]:
            return "BUT2"
        else:
            return "BUT3"


def supprime_accent_espace(chaine):
    """Met une chaine en minuscule, supprime les accents, les ponctuations et les espaces"""
    purge = chaine.lower().replace("'", "").replace("’", "")
    purge = unicodedata.normalize('NFD', purge).encode('ascii', 'ignore').decode('ascii')
    purge = purge.replace(" ", "")
    return purge


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


def devine_code_activite_by_nom_from_dict(champ, dico):
    """Partant d'une chaine de caractères décrivant une ressource, une SAé ou un ACS,
    détermine le code présent dans le dico officiel (dico à double entrée),
    Le dico officiel vient d'un .yml"""
    codes = []
    champ_purge = supprime_accent_espace(champ)
    for comp in dico:
        for code in dico[comp]:
            code_purge = supprime_accent_espace(dico[comp][code])
            if code_purge in champ_purge:
                codes += [code]
    return sorted(list(set(codes)))



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


def get_ressource_notation_pointe(code_ressource): # => à remplacer
    """Renvoie la notation pointée d'une ressource partant
    de RXXX"""
    return code_ressource[:2] + "." + code_ressource[-2:]


def get_sae_notation_pointe(code_sae):
    """Renvoie la notation pointée d'une sae"""
    return code_sae[:4] + ".0" + code_sae[-1]


def mapping_code_RXXX_vers_code_pointe(code):
    """Renvoie le code d'une ressource en utilisant le mapping"""
    DATA_R_DOCX = get_DATA_R_DOCX()
    for sem in DATA_R_DOCX:
        for mod in DATA_R_DOCX[sem]:
            if DATA_R_DOCX[sem][mod].lower().startswith(code.lower()):
                return mod
    __LOGGER.warning(f"Pb: Le code {code} n'a pas pu être mappé en RX.XX")

def mapping_code_AC0XXX_vers_code_pointe(code):
    """Réalise le mapping d'un AC avec l'ancien systeme de numeroration
    vers le nouveau :
    ancien : AC0can ou ACcan avec c=n° de la compétence, a=annee, n=numero
    nouveau : ACac.0n avec a=annee, c=competence, n=numero"""
    if len(code) == 6: # supprime le 0 très certainement en trop
        if "AC0" in code or "AC1" in code:
            code = "AC" + code[3:]
        else:
            raise Exception("Décodage de l'AC non prévu")
    elif len(code) != 5:
        raise Exception("Décodage de l'AC non prévu")
    comp, annee, numero = code[2], code[3], code[4]
    renumerote = "AC" + annee + comp + "0" + numero
    return ACs.get_acs_notation_pointe(renumerote)





if __name__=="__main__":
    print("toto")
