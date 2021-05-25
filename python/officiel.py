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
import unicodedata
from config import Config

__LOGGER = logging.getLogger(__name__)

REPERTOIRE = "yaml"

# *************************************** #
# Récupère les informations officielles  #
## Les ressources
def get_DATA_RESSOURCES(repertoire = REPERTOIRE):
    """Récupère les informations sur les ressources (triées par semestre
    et par nom), en extrayant les données du fichier yaml/ressources.yml.
    """
    with open(Config.ROOT + "/" + repertoire + "/ressources.yml", 'r', encoding="utf8") as fid:
        DATA_RESSOURCES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_RESSOURCES


## Les ACS
def get_DATA_ACS(repertoire = REPERTOIRE):
    """Récupère les informations des ACS,
    en extrayant les données du fichier yaml/competences.yml"""
    with open(Config.ROOT+"/"+ repertoire +"/acs.yml", 'r', encoding="utf8") as fid:
        DATA_ACS = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_ACS

## Les SAEs
def get_DATA_SAES(repertoire = REPERTOIRE):
    """Récupère les informations des SAés (triées par semestre et par nom),
    en extrayant les données du fichier yaml/saes.yml"""
    with open(Config.ROOT+"/"+REPERTOIRE+"/saes.yml", 'r', encoding="utf8") as fid:
        DATA_SAES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_SAES

## Les compétences
def get_DATA_COMPETENCES():
    with open(Config.ROOT+"/"+REPERTOIRE+"/competences/RT123.yml", 'r', encoding="utf8") as fid:
        DATA_COMPETENCES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_COMPETENCES

## Les abréviations
def get_DATA_ABBREVIATIONS():
    with open(Config.ROOT+"/"+REPERTOIRE+"/abbreviations.yml", "r", encoding="utf8") as fid:
        DATA_ABBREVIATIONS = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_ABBREVIATIONS

## Les mostcles (commandes, logiciels, etc...)
def get_MOTS_CLES():
    with open(Config.ROOT+"/"+REPERTOIRE+"/motscles.yml", "r", encoding="utf8") as fid:
        DATA_MOTSCLES = yaml.load(fid.read(), Loader=yaml.Loader)
    return DATA_MOTSCLES

AUCUN_PREREQUIS = "Aucun"

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
            if isinstance(dico[comp][code], dict) and "nom" in dico[comp][code]:
                nom = dico[comp][code]["nom"]
            else:
                nom = dico[comp][code]
            acs_purge = supprime_accent_espace(nom)
            if acs_purge in champ_purge:
                acs += [code]
    return sorted(list(set(acs)))



def affiche_bilan_heures(ressources, sem):
    """Renvoie une chaine décrivant un bilan des heures pour un sem donné"""
    ligne = "{:20s} | {:75s} | {:10s} | {:10s} |"
    trait = "-"*len(ligne.format("", "", "", ""))

    ressem = ressources[sem] # les ressources du semestre
    chaine = ""
    chaine += trait + "\n"
    chaine += ligne.format("Code", "Ressource", "Form.", "dont TP") + "\n"
    chaine += trait + "\n"
    for r in ressem:
        chaine += ligne.format(r.code if r.code else "MANQUANT",
                               # r.nom[:30] + ("..." if len(r.nom) > 30 else "") ,
                               r.semestre,
                               str(r.heures_encadrees) if r.heures_encadrees else "MANQUANT",
                               str(r.tp) if r.tp else "MANQUANT") + "\n"
    heures_formation_total = sum([r.heures_encadrees for r in ressem if r.heures_encadrees != None])
    heures_tp_total = sum([r.tp for r in ressem if r.tp != None])
    chaine += trait + "\n"
    chaine += ligne.format("", "Total", str(heures_formation_total), str(heures_tp_total)) + "\n"
    chaine += trait + "\n"
    return chaine

def get_officiel_name_by_code_using_dict(code, dico):
    """Extrait un nom à partir d'un code (pour les RESSOURCES ou les SAES)"""
    for sem in dico:
        for rcode in dico[sem]:
            if rcode==code:
                return dico[sem][code]["nom"]

def get_officiel_ressource_name_by_code(code):
    """Pour un code valide, fournit le nom officiel de la ressource (sans connaissance du semestre)"""
    DATA_RESSOURCES = get_DATA_RESSOURCES()
    return get_officiel_name_by_code_using_dict(code, DATA_RESSOURCES)

def get_officiel_sae_name_by_code(code):
    """Pour un code valide, fournit le nom officiel de la sae (sans connaissance du semestre)"""
    DATA_SAES = get_DATA_SAES()
    return get_officiel_name_by_code_using_dict(code, DATA_SAES)

def get_code_from_nom_using_dict(nom, dico):
    """Récupère le code d'une ressource d'après son nom en utilisant les noms officiels
    des ressources du yaml si dico == DATA_RESSOURCES ; sinon fait de même avec les SAE"""
    nom = supprime_accent_espace(nom)
    for sem in dico:
        for code in dico[sem]:
            nom_data = supprime_accent_espace(dico[sem][code])
            if nom.startswith(nom_data):
                return code

def get_officiel_sem_sae_by_code(sae):
    """Récupère le semestre de la SAE d'après son code"""
    DATA_SAES = get_DATA_SAES()
    for sem in DATA_SAES:
        if sae in DATA_SAES[sem]:
            return sem

if __name__=="__main__":
    DATA_COMPETENCES = get_DATA_COMPETENCES()
    print(DATA_COMPETENCES)