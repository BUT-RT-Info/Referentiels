import string
import logging
import re
import yaml
import unicodedata

__LOGGER = logging.getLogger(__name__)

# Récupère les informations officielles sur les ressources (code/nom)
with open("pn/ressources.yml", 'r', encoding="utf8") as fid:
    DATA_RESSOURCES = yaml.load(fid.read(), Loader=yaml.Loader)
# Récupère les données officielles des ACs
with open("pn/acs.yml", 'r', encoding="utf8") as fid:
    DATA_ACS = yaml.load(fid.read(), Loader=yaml.Loader)

class Ressource():
    def __init__(self, nom, brute):
        self.nom = nom
        self.brute = brute # les données brutes de la ressource

    def charge_informations(self, code, semestre, heures_encadrees, tp, sae, prerequis, description, mots):
        self.code = code
        self.semestre = semestre # <--
        self.heures_encadrees = heures_encadrees
        self.tp = tp
        self.sae = sae
        self.prerequis = prerequis
        self.description = description
        self.mots = mots

    def charge_ac(self, apprentissages):
        self.apprentissages = apprentissages

    def __str__(self):
        print(self.nom + " " + self.code)


def nettoie_heure(champ):
    """Nettoie le champ (horaire) (de la forme 46h ou 33...) pour n'en extraire que la valeur numérique"""
    temp = champ.rstrip().lower()
    champs = temp.split(" ")
    if champs[0][0] not in string.digits:
        __LOGGER.warning("champ heure non analysable/analyse")
    else:
        heure = champs[0].split("h")[0]
        return int(heure)

def nettoie_code(champ):
    """Recherche les codes ressources de la forme RXXX dans champ"""
    codes = re.findall(r"(R[0-9][0-9][0-9])", champ)
    # if len(codes) > 1:
    #    __LOGGER.warning("plusieurs codes trouvés :(")
    #elif len(codes) == 0:
    #    __LOGGER.warning("code manquant")
    if len(codes) == 1:
        return codes[0]


def supprime_accent_espace(chaine):
    purge = chaine.lower().replace("'", "").replace("’", "")
    purge = unicodedata.normalize('NFD', purge).encode('ascii', 'ignore').decode('ascii')
    purge = purge.replace(" ", "")
    return purge


def get_code_from_nom(ressource):
    nom = supprime_accent_espace(ressource.nom)
    for sem in DATA_RESSOURCES:
        for code in DATA_RESSOURCES[sem]:
            nom_data = supprime_accent_espace(DATA_RESSOURCES[sem][code])
            if nom.startswith(nom_data):
                return code

def devine_acs_by_code(champ):
    """Recherche les codes ressources de la forme ACXXX ou AC0XXX dans champ ;
    ramène les codes AC0XXX à 3 chiffres.
    """
    codes3 = re.findall(r"(AC[0-9][0-9][0-9]\D)", champ) # de code à 3 chiffres
    codes4 = re.findall(r"(AC0[0-9][0-9][0-9])", champ)

    codes3 += [ "AC" + c[-3:] for c in codes4] # supprime le 0 des acs (codage AC0111)
    return sorted(list(set(codes3)))

def devine_acs_by_nom(donnees):
    """Partant d'une chaine de caractères, détermine les codes des ACS
    présent dans la donnée, en utilisant les infos officielles de
    acs.yml"""
    acs = []
    donnees_purge = supprime_accent_espace(donnees)

    for comp in DATA_ACS:
        for code in DATA_ACS[comp]:
            acs_purge = supprime_accent_espace(DATA_ACS[comp][code])
            if acs_purge in donnees_purge:
                acs += [code]
    return sorted(list(set(acs)))

if __name__=="__main__":
    # Eléments de test
    for sem in DATA_RESSOURCES:
        for code in DATA_RESSOURCES[sem]:
            nom_data = supprime_accent_espace(DATA_RESSOURCES[sem][code])
            print(nom_data)
