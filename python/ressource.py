import string
import logging
__LOGGER = logging.getLogger(__name__)

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


