import re
from officiel import *
from modeles import *
from officiel import supprime_accent_espace, get_code_from_nom_using_dict
import ruamel.yaml
from ruamel.yaml.scalarstring import FoldedScalarString as folded

from tools import caracteres_recalcitrants

__LOGGER = logging.getLogger(__name__)


class RessourceDocx():
    """Classe modélisant les ressources, lorsqu'elles sont extraites du docx"""
    def __init__(self, nom, brut):
        self.nom = nom
        self.brut = brut # les données brutes de la ressource

    def charge_informations(self, code, semestre, heures_encadrees, tp, sae, prerequis, description, mots):
        self.code = code
        self.semestre = semestre # <--
        self.heures_encadrees = heures_encadrees
        self.tp = tp
        self.sae = sae
        self.prerequis = prerequis
        self.description = description
        self.contexte = None
        self.contenu = None
        self.mots = mots

    def charge_ac(self, apprentissages):
        self.apprentissages = apprentissages

    def __str__(self):
        print(self.nom + " " + self.code)

    def to_yaml(self):
        """Exporte la ressource en yaml"""
        dico = {"nom": self.nom,
                "code": self.code,
                "semestre" : int(self.semestre[1]),
                "heures_formation": self.heures_encadrees if self.heures_encadrees else "???",
                "heures_tp": self.tp if self.tp else "???",
                "acs": self.apprentissages,
                "sae": self.sae,
                "prerequis": self.prerequis,
                "contexte": folded(self.contexte),
                "contenu": folded(self.contenu),
                "motscles": self.mots if self.mots else ""
                }
        output = ruamel.yaml.dump(dico, Dumper=ruamel.yaml.RoundTripDumper,
                                  allow_unicode=True, width=100)
        output = output.replace("\n\n\n", "\n\n")
        return output

def nettoie_champ_heure(champ):
    try: # champ contenant uniquement un nbre d'heure
        volumes = int(champ)
        return volumes
    except:
        volumes = re.findall("(\d{2}\D|\d{1}\D)", champ)
        if len(volumes) == 1:
            return int(volumes[0][:-1])
        elif len(volumes) == 2:
            volumes = sorted(volumes, reverse=True)
            return (int(volumes[0][:-1]), int(volumes[1][:-1]))

def nettoie_heure_ressource(r):
    """Nettoie le champ (horaire) (de la forme 46h ou 33...) pour en extraire la valeur numérique :
    le champ peut contenir 2 volumes (heures formation puis heures tp), auquel cas les 2 valeurs sont renvoyées
    dans un tuple"""

    if r.heures_encadrees: # si les heures encadrées sont renseignées
        volumes = nettoie_champ_heure(r.heures_encadrees)
    if r.tp:
        r.tp = nettoie_champ_heure(r.tp)

    if isinstance(volumes, int):
        r.heures_encadrees = volumes
    elif isinstance(volumes, tuple):
        r.heures_encadrees = volumes[0]
        if not r.tp:
            r.tp = volumes[1]
        elif r.tp != volumes[1]:
            __LOGGER.warning(r"nettoie_heure: ans {r.nom}, pb dans les heures tp/td")
    else:
        r.heures_encadrees = None
        #else:
            #__LOGGER.warning("Heures non détectées")


def nettoie_heure_sae(r):
    """Nettoie les champs (horaires) des saes"""

    if r.heures_encadrees:  # si les heures encadrées sont renseignées
        r.heures_encadrees = nettoie_champ_heure(r.heures_encadrees)
    else:
        __LOGGER.warning(r"nettoie_heure_sae: dans {r.nom}, manque les heures de formation")
        r.heures_encadrees = "???"
    if r.tp:
        r.tp = nettoie_champ_heure(r.tp)
    else:
        __LOGGER.warning(r"nettoie_heure_sae: dans {r.nom}, manque les heures de tp")
        r.tp = "???"

    if r.projet:
        r.projet = nettoie_champ_heure(r.projet)
    else:
        __LOGGER.warning(r"nettoie_heure_sae: dans {r.nom}, manque les heures de projet")
        r.projet = "???"
    try:
        if r.heures_encadrees < r.tp:
            __LOGGER.warning(r"nettoie_heure_sae: dans {r.nom}, pb dans les heures formations/tp")
    except:
        pass


def nettoie_code(r, type = "ressource"):
    """Recherche les codes dans le champ:
    * de la forme RXXX si type=ressource
    * de la forme SAE|éXX si type=sae"""

    champ = r.code
    if r.code:
        if type == "ressource":
            codes = re.findall(r"(R[0-9][0-9][0-9])", champ)
        else: # type = "sae"
            codes = re.findall(r"(SAE[0-9][0-9]|SAÉ[0-9][0-9])", champ)
            # ajout des É
            codes = [c.replace("E", "É") for c in codes]
        # if len(codes) > 1:
        #    __LOGGER.warning("plusieurs codes trouvés :(")
        #elif len(codes) == 0:
        #    __LOGGER.warning("code manquant")
        if len(codes) == 1:
            r.code = codes[0]
        else:
            if type == "ressource":
                code_devine = get_code_from_nom_using_dict(r, DATA_RESSOURCES)
            else:
                code_devine = get_code_from_nom_using_dict(r, DATA_SAES)
            if code_devine:
                __LOGGER.warning(f"nettoie_code : \"{r.nom}\" => code {code_devine}")
                r.code = code_devine
            else:
                r.code = None
                __LOGGER.warning(f"nettoie_code : \"{r.nom}\" => code manquant")

def nettoie_semestre(r):
    """Nettoie les semestres : semestre 1 => "S1", semestre 2 => "S2" """
    if r.semestre:
        if "1" in r.semestre:
            r.semestre = "S1"
        elif "2" in r.semestre:
            r.semestre = "S2"
        else:
            __LOGGER.warning(f"nettoie_semestre : dans \"{r.nom}, PAS de semestre => rattaché au S2")
            r.semestre = "S2"
    else:
        __LOGGER.warning(f"nettoie_semestre : dans \"{r.nom}, PAS de semestre => rattaché au S2")
        r.semestre = "S2"

def nettoie_titre(r):
    """Nettoie le titre en utilisant les titres officiels"""
    def devine_nom_from_ressources(champ):
        champ_purge = supprime_accent_espace(champ)
        for sem in DATA_RESSOURCES:
            for code in DATA_RESSOURCES[sem]:
                nom_purge = supprime_accent_espace(DATA_RESSOURCES[sem][code])
                if champ_purge.startswith(nom_purge):
                    return DATA_RESSOURCES[sem][code] # le bon nom

    old = r.nom
    titre = devine_nom_from_ressources(r.nom)
    if titre and titre != old:
        __LOGGER.warning(f"nettoie_titre : {old} => titre \"{titre}\"")
        r.nom = titre

def nettoie_acs(r):
    """Nettoie les acs d'une ressource en les remplaçant par leur code pour les 3 compétences"""
    if len(r.apprentissages) != 3:
        __LOGGER.warning(f"nettoie_acs : Problème dans le nombre de compétences de {r.nom}")
    dico = {}
    for comp in range(3):
        donnees = r.apprentissages[comp] # chaine de caractères listant les ACS
        # donnees = donnees.replace("\t", "").replace("-", "") # supprime les tabulations
        acs_avec_code = devine_acs_by_code(donnees)
        acs_avec_nom = devine_code_by_nom_from_dict(donnees, DATA_ACS)
        if acs_avec_code and set(acs_avec_nom).intersection(set(acs_avec_code)) != set(acs_avec_nom):
            __LOGGER.warning(f"Dans {r.nom}, revoir les ACS : {acs_avec_code} vs {acs_avec_nom}")
        acs_finaux = acs_avec_code + acs_avec_nom
        acs_finaux = [ac.replace(" ", "") for ac in acs_finaux]
        acs_finaux = sorted(list(set(acs_finaux)))
        dico["RT" + str(comp+1)] = acs_finaux
    r.apprentissages = dico # [comp] = acs_finaux

def nettoie_sae(r):
    """Nettoie le champ SAe d'une ressource en détectant les codes"""
    SAE_avec_code = devine_sae_by_code(r.sae)
    liste = [l.rstrip() for l in SAE_avec_code]
    r.sae = liste
    if not r.sae:
        __LOGGER.warning(f"nettoie_sae: dans {r.nom} pas de SAE (:")

def nettoie_ressources(r):
    """Nettoie le champ ressource d'une sae en détectant les codes"""
    ressources_avec_code = devine_ressources_by_code(r.ressources)
    liste = [l.rstrip() for l in ressources_avec_code]
    r.ressources = liste
    if not r.ressources:
        __LOGGER.warning(f"nettoie_ressources: dans {r.nom} pas de ressources (:")

def nettoie_prerequis(r):
    """Nettoie les prérequis (ressource) en les remplaçant par leur code de ressource"""
    R_avec_code = devine_ressources_by_code(r.prerequis)
    R_avec_nom = devine_code_by_nom_from_dict(r.prerequis, DATA_RESSOURCES)
    liste = R_avec_code + R_avec_nom
    liste = [l.rstrip().replace(",", "").replace(".","") for l in liste] # supprime les espaces
    R_finaux = sorted(list(set(liste)))
    if R_finaux:
        r.prerequis = R_finaux
    else:
        r.prerequis = "Aucun"

def nettoie_mots_cles(r):
    mots = r.mots # .encode('utf8', 'ignore').decode('utf8')
    mots = mots.replace(".", "").replace(";", ",")
    mots = mots.replace(" ,", ",")
    r.mots = mots


def devine_acs_by_code(champ):
    """Recherche les codes ressources de la forme ACXXX ou AC0XXX dans champ ;
    ramène les codes AC0XXX à 3 chiffres.
    """
    codes3 = re.findall(r"(AC[0-9][0-9][0-9]\D)", champ) # de code à 3 chiffres
    codes4 = re.findall(r"(AC0[0-9][0-9][0-9])", champ)

    codes3 = [c.rstrip() for c in codes3]
    codes4 = [c.rstrip() for c in codes4]
    codes4 += [ "AC0" + c[-3:] for c in codes3] # ajoute les 0 manquants des acs (codage AC0111)

    return sorted(list(set(codes4)))

def devine_ressources_by_code(champ):
    """Recherche les codes ressources de la forme RXXX dans champ ;
    """
    codes = re.findall(r"(R\d{3}\D)", champ) # de code à 3 chiffres
    return sorted(list(set(codes)))

def devine_ressources_by_nom(donnees):
    """Partant d'une chaine de caractères, détermine les ressources
    présentes dans la donnée, en utilisant les infos officielles de
    ressources.yml"""
    donnees_purge = supprime_accent_espace(donnees)
    codes = []
    for sem in DATA_RESSOURCES:
        for code in DATA_RESSOURCES[sem]:
            nom_purge = supprime_accent_espace(DATA_RESSOURCES[sem][code])
            if nom_purge in donnees_purge:
                codes += [code]
    return sorted(list(set(codes)))

def devine_sae_by_code(donnees):
    """Partant d'une chaine de caractères, détermine les codes des SAE"""
    codes = re.findall(r"(SAE\d\d)\D", donnees)
    codes += re.findall(r"(SAÉ\d\d)\D", donnees)# de code à 3 chiffres
    for (i, code) in enumerate(codes):
        codes[i] = codes[i].replace("E", "É")
    return sorted(list(set(codes)))

def split_description(r):
    """Découpe le champ description en un contexte+un contenu ; si pas possible """
    champs = r.description.split("\n")
    champs = [c for c in champs if c] # supprime les lignes vides

    indicea = 0 # la ligne mentionnant le contexte
    if True in [ligne.startswith("Contexte et ") for ligne in champs]:  # la ligne commençant par Contenus
        indicea = [ligne.startswith("Contexte et ") for ligne in champs].index(True)

    indicec = 0
    contexte = []
    if True in [ligne.startswith("Contenus") for ligne in champs]: # la ligne commençant par Contenus
        indicec = [ligne.startswith("Contenus") for ligne in champs].index(True)
    if True in [ligne.startswith("Contexte et ") for ligne in champs]:
        contexte = champs[indicea+1:indicec]
    else:
        contexte = champs[:indicec]
    # suppression des lignes vides
    contexte = "\n".join(remove_ligne_vide(contexte))
    # suppression des liens
    contexte = remove_link(contexte)
    if not contexte:
        contexte = "Aucun"
    contenu = "\n".join(champs[indicec+1:])


    # sauvegarde des champs
    r.contexte = contexte
    r.contenu = contenu

def remove_link(contenu):
    liens = re.findall("(<a\s.*\">)", contenu)
    for m in liens:
        contenu = contenu.replace(m, "")
    contenu = contenu.replace("</a>", "")
    return contenu

def remove_ligne_vide(contenus):
    """Supprime les lignes vides"""
    if isinstance(contenus, list):
        return [c for c in contenus if c.rstrip()]
    else: # contenu = chaine
        temp = contenus.split("\n")
        temp = [t for t in temp if t.replace("\t", "").rstrip()]
        return "\n".join(temp)

def get_marqueur_numerique(contenu):
    """Revoie la liste des marqueurs numériques"""
    m = re.findall(r"(\d/|\d\s/)", contenu)
    m += re.findall(r"(\d\s\)|\d\))", contenu) # les marqueurs de la forme 1)
    m += re.findall(r"(--\s|--\t)", contenu)
    return m

def get_marqueurs(contenu):
    """Renvoie la liste des marqueurs (à 1 caractère) partant d'un contenu - splitable en plusieurs lignes
    (éventuellement vide)"""
    contenus = [ligne.rstrip() for ligne in contenu.split("\n")]  # les contenus

    marqueurs = []
    for ligne in contenus:
        m = re.search(r"(\t)*", ligne) # y a-t-il des tabulations ?
        if m.group() != "":
            ajout = m.group()
        else:
            ajout = ""
        ligne = ligne.replace("\t","").rstrip() # supprime les tabulations pour rapatrier le marqueur en début de ligne
        if ligne: # si la ligne n'est pas vide, cherche le marqueur en début de ligne (si 1 caractère)
            if ligne[0] not in string.ascii_letters and ligne[0] != "É" and ligne[0] != "/":
                marqueurs += [ajout + ligne[0]] # tous les symboles

    marqueurs_finaux = [] # tri les marqueurs en supprimant les doublons et en gardant un ordre (pour détecter les sous listes)
    for m in marqueurs:
        if m not in marqueurs_finaux:
            marqueurs_finaux.append(m)
    return marqueurs_finaux

def get_marqueur_from_liste(ligne, marqueurs):
    """Renvoie le marqueur qui marque le début d'une ligne parmi une liste de marqueurs recherchés"""
    for m in marqueurs:
        if ligne.startswith(m):
            return m


def remplace_marqueur_numerique_with_caracteres(contenu):
    """Remplace les marqueurs numériques par des marqueurs > lorsque présents dans un contenu"""
    marqueurs_numeriques = get_marqueur_numerique(contenu)
    for m in marqueurs_numeriques: # remplace les marqueurs numériques
        contenu = contenu.replace(m, ">")
    return contenu

def convert_to_markdown(contenu):
    """Convertit un contenu avec des marqueurs en markdown"""
    contenu = remplace_marqueur_numerique_with_caracteres(contenu)
    marqueurs_finaux = get_marqueurs(contenu)
    lignes = contenu.split("\n")
    contenus_fin =  lignes[:] # copie des ligne
    for (i, ligne) in enumerate(lignes):
        m = get_marqueur_from_liste(ligne, marqueurs_finaux) # identifie la présence d'un marqueur dans la ligne
        if m:
            pos = marqueurs_finaux.index(m)
            contenus_fin[i] = "\t" * (pos) + "* " + ligne.replace(m, "").replace("\t", "").rstrip()
    contenu = "\n\n".join(contenus_fin)
    return contenu


def nettoie_contenus_ressource(r):
    """Partant du contenu détaillé d'une ressource, la transforme
    en markdown en générant les listes à puces"""
    contenu = r.contenu.replace(" / ", "/")
    contenu = convert_to_markdown(contenu)
    r.contenu = contenu

def nettoie_livrables_sae(s):
    """Partant du contenu détaillé d'une ressource, la transforme
    en markdown en générant les listes à puces"""
    contenu = s.livrables
    contenu = convert_to_markdown(contenu)
    s.livrables = contenu

class SAEDocx():

    def __init__(self, nom, brut):
        self.nom = nom
        self.brut = brut  # les données brutes de la ressource

    def charge_informations(self, code, semestre, heures_encadrees, tp, projet, description, ressources, livrables, mots):
        self.code = code
        self.semestre = semestre  # <--
        self.heures_encadrees = heures_encadrees
        self.tp = tp
        self.projet = projet
        self.description = description
        self.ressources = ressources
        self.livrables = livrables
        self.mots = mots

    def charge_ac(self, apprentissages):
        self.apprentissages = apprentissages

    def to_yaml(self):
        """Exporte la ressource en yaml"""
        dico = {"titre": self.nom,
                "code": self.code,
                "semestre": int(self.semestre[1]),
                "heures_encadrees": self.heures_encadrees if self.heures_encadrees else "???",
                "tp": self.tp if self.tp else "???",
                "projet": self.projet if self.projet else "???",
                "description": folded(self.description),
                "acs": self.apprentissages,
                "ressources": self.ressources,
                "livrables": folded(self.livrables),
                "motscles": self.mots if self.mots else ""
                }
        output = ruamel.yaml.dump(dico, Dumper=ruamel.yaml.RoundTripDumper,
                                      allow_unicode=True, width=100)
        output = output.replace("\n\n\n", "\n\n")
        return output


class ExempleSAEDocx():

    def __init__(self, nom, brut):
        self.nom = nom
        self.brut = brut  # les données brutes de la ressource

    def charge_informations(self, description, formes, problematique, modalite):
        self.description = description
        self.formes = formes  # <--
        self.problematique = problematique
        self.modalite = modalite


if __name__=="__main__":
    # Eléments de test
    for sem in DATA_RESSOURCES:
        for code in DATA_RESSOURCES[sem]:
            nom_data = supprime_accent_espace(DATA_RESSOURCES[sem][code])
            print(nom_data)
