import logging, yaml
import unicodedata
from config import Config

__LOGGER = logging.getLogger(__name__)

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
        with open(Config.ROOT+"/yaml/pn/ressources.yml", 'r', encoding="utf8") as fid:
            self.DATA_RESSOURCES = yaml.load(fid.read(), Loader=yaml.Loader)
        ## Les ACS
        with open(Config.ROOT+"/yaml/pn/acs.yml", 'r', encoding="utf8") as fid:
            self.DATA_ACS = yaml.load(fid.read(), Loader=yaml.Loader)
        ## Les SAEs
        with open(Config.ROOT+"/yaml/pn/saes.yml", 'r', encoding="utf8") as fid:
            self.DATA_SAES = yaml.load(fid.read(), Loader=yaml.Loader)
        ## Les compétences
        with open(Config.ROOT+"/yaml/competences/RT123.yml", 'r', encoding="utf8") as fid:
            self.DATA_COMPETENCES = yaml.load(fid.read(), Loader=yaml.Loader)
        ## Les abréviations
        with open(Config.ROOT+"/yaml/abbreviations.yml", "r", encoding="utf8") as fid:
            self.DATA_ABBREVIATIONS = yaml.load(fid.read(), Loader=yaml.Loader)
        ## Les mostcles (commandes, logiciels, etc...)
        with open(Config.ROOT+"/yaml/motscles.yml", "r", encoding="utf8") as fid:
            self.DATA_MOTSCLES = yaml.load(fid.read(), Loader=yaml.Loader)


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
    """Met en minuscule, supprime les accents, les ponctuations et les espaces"""
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


if __name__=="__main__":
    print("toto")