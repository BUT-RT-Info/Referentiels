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

import logging, yaml
from config import Config
import tools

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

## Les intitules des compétences
def get_DATA_COMPETENCES(repertoire = "yaml/pn"):
    """Récupère les informations des ACS,
    en extrayant les données du fichier yaml/competences.yml"""
    with open(Config.ROOT+"/"+ repertoire +"/competences.yml", 'r', encoding="utf8") as fid:
        DATA_COMPETENCES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_COMPETENCES


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
def get_DATA_COMPETENCES_DETAILLEES(repertoire = "yaml/competences"):
    DATA_COMPETENCES = {}
    fichier = ["RT1.yml", "RT2.yml", "RT3.yml", "IOM.yml", "Cyber.yml", "ROM.yml", "DevCloud.yml", "PilPro.yml"]
    for f in fichier:
        chemin = Config.ROOT + "/"+ repertoire + "/" + f
        with open(chemin, 'r', encoding="utf8") as fid:
            donnees = yaml.load(fid.read(), Loader=yaml.Loader)
            DATA_COMPETENCES = {**DATA_COMPETENCES, **donnees} # fusion dictionnaire
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
        self.DATA_COMPETENCES_DETAILLEES = get_DATA_COMPETENCES_DETAILLEES()
        ## Les abréviations
        self.DATA_ABBREVIATIONS = get_DATA_ABBREVIATIONS()
        ## Les mostcles (commandes, logiciels, etc...)
        self.DATA_MOTSCLES = get_MOTS_CLES()
        ## L'association ressources -> fichier.rdocx
        self.DATA_R_DOCX = get_DATA_R_DOCX()


    def get_ressource_name_by_code(self, code):
        """Pour un code de ressource valide (existant dans ``DATA_RESSOURCES``)
        et ce, sans connaissance de l'année, ni du semestre, fournit le nom officiel de la ressource
        """
        return get_officiel_name_by_code_using_dict(code, self.DATA_RESSOURCES)


    def get_noms_niveaux(self):
        """Partant de la description détaillée des compétences DATA_COMPETENCES_DETAILLES, renvoie le nom
        des niveaux triés par année sous la forme d'un dictionnaire :
        { 'BUT1': {'RT1': [niveau1, niveau2, niveau3]}, ... } """
        niveaux = {"BUT{}".format(i): {} for i in range(1, 4)}
        for annee in niveaux:
            comp_communes = {"RT{}".format(i): [] for i in range(1, 4)}
            if annee == "BUT1": # ajout des compétences de parcours
                niveaux[annee] = comp_communes
            else:
                comp_parcours = {"{}{}".format(p, i): None for i in range(1, 3) for p in PARCOURS}
                niveaux[annee] = {**comp_communes, **comp_parcours}

        for comp in self.DATA_COMPETENCES_DETAILLEES:
            nbre_niveaux = len(self.DATA_COMPETENCES_DETAILLEES[comp]["niveaux"])
            nivs = list(self.DATA_COMPETENCES_DETAILLEES[comp]["niveaux"].keys())
            if nbre_niveaux == 3:
                assert "RT" in comp, "officiel: Pb dans les niveaux de la comp"
                for annee in range(0, 3): # l'année
                    assert comp in niveaux["BUT{}".format(annee+1)], f"officiel: {comp} manquante"
                    niveaux["BUT{}".format(annee+1)][comp] = nivs[annee]
            else:
                for annee in range(0, 2): # l'année
                    assert comp in niveaux["BUT{}".format(annee+2)], f"officiel: {comp} manquante"
                    niveaux["BUT{}".format(annee+2)][comp] = nivs[annee]
        return niveaux


    def get_sae_name_by_code(self, code):
        """Pour un code de saé (en notation pointé, et existant dans ``DATA_SAES``)
        et ce sans connaissance du semestre,  fournit le nom officiel de la sae
        """
        return get_officiel_name_by_code_using_dict(code, self.DATA_SAES)


    def get_sem_activite_by_code(self, code):
        """Récupère le semestre d'une activité (ressource ou SAé) d'après son ``code``
        """
        for sem in self.DATA_RESSOURCES:
            if code in self.DATA_RESSOURCES[sem]:
                return sem

        for sem in self.DATA_SAES:
            if code in self.DATA_SAES[sem]:
                return sem
        # sinon non trouvé


    def get_docx_file_by_code(self, code):
        """Renvoie le nom du fichier rdocx contenant le descriptif d'une ressource ou d'une SAE
        à l'aide de son code"""
        for sem in self.DATA_R_DOCX:
            if code in self.DATA_R_DOCX[sem]:
                return self.DATA_R_DOCX[sem][code]
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


def devine_code_activite_by_nom_from_dict(champ, dico):
    """Partant d'une chaine de caractères décrivant une ressource, une SAé ou un ACS,
    détermine le code présent dans le dico officiel (dico à double entrée),
    Le dico officiel vient d'un .yml"""
    codes = []
    champ_purge = tools.supprime_accent_espace(champ)
    for comp in dico:
        for code in dico[comp]:
            code_purge = tools.supprime_accent_espace(dico[comp][code])
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
    nom = tools.supprime_accent_espace(nom)
    for sem in dico:
        for code in dico[sem]:
            nom_data = tools.supprime_accent_espace(dico[sem][code])
            if nom.startswith(nom_data):
                return code


if __name__=="__main__":
    import pprint
    pn = Officiel()
    niveaux = pn.get_noms_niveaux()
    pprint.pprint(niveaux)
