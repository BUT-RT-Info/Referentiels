import logging, yaml
import unicodedata
from config import Config

__LOGGER = logging.getLogger(__name__)

# Récupère les informations officielles
## Les ressources
with open(Config.ROOT+"/python/pn/ressources.yml", 'r', encoding="utf8") as fid:
    DATA_RESSOURCES = yaml.load(fid.read(), Loader=yaml.Loader)
## Les ACS
with open(Config.ROOT+"/python/pn/acs.yml", 'r', encoding="utf8") as fid:
    DATA_ACS = yaml.load(fid.read(), Loader=yaml.Loader)
## Les SAEs
with open(Config.ROOT+"/python/pn/saes.yml", 'r', encoding="utf8") as fid:
    DATA_SAES = yaml.load(fid.read(), Loader=yaml.Loader)
## Les compétences
with open(Config.ROOT+"/yaml/competences/RT123.yml", 'r', encoding="utf8") as fid:
    DATA_COMPETENCES = yaml.load(fid.read(), Loader=yaml.Loader)
## Les abréviations
with open(Config.ROOT+"/yaml/abbreviations.yml", "r", encoding="utf8") as fid:
    DATA_ABBREVIATIONS = yaml.load(fid.read(), Loader=yaml.Loader)
## Les mostcles (commandes, logiciels, etc...)
with open(Config.ROOT+"/yaml/motscles.yml", "r", encoding="utf8") as fid:
    DATA_MOTSCLES = yaml.load(fid.read(), Loader=yaml.Loader)

AUCUN_PREREQUIS = "Aucun"

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

    for comp in DATA_ACS:
        for code in DATA_ACS[comp]:
            acs_purge = supprime_accent_espace(DATA_ACS[comp][code])
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
                           r.nom,
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
                return dico[sem][code]

def get_officiel_ressource_name_by_code(code):
    """Pour un code valide, fournit le nom officiel de la ressource (sans connaissance du semestre)"""
    return get_officiel_name_by_code_using_dict(code, DATA_RESSOURCES)

def get_officiel_sae_name_by_code(code):
    """Pour un code valide, fournit le nom officiel de la sae (sans connaissance du semestre)"""
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
    for sem in DATA_SAES:
        if sae in DATA_SAES[sem]:
            return sem

if __name__=="__main__":
    print(DATA_COMPETENCES)