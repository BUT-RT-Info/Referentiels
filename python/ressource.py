import re
from officiel import *
from modeles import *
from officiel import supprime_accent_espace
import ruamel.yaml
from ruamel.yaml.scalarstring import FoldedScalarString as folded

__LOGGER = logging.getLogger(__name__)


class Ressource():
    """Classe modélisant les ressources"""
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
        self.contexte = None
        self.contenu = None
        self.mots = mots

    def charge_ac(self, apprentissages):
        self.apprentissages = apprentissages

    def __str__(self):
        print(self.nom + " " + self.code)

    def str_heures_formations(self):
        return str(self.heures_encadrees) if self.heures_encadrees else "???"

    def str_heures_tp(self):
        return str(self.tp) if self.tp else "???"

    def str_semestre(self):
        return int(self.semestre[1])

    def to_yaml(self):

        dico = {"nom": self.nom,
                "code": self.code,
                "semestre" : self.str_semestre(),
                "heures_formation": self.str_heures_formations(),
                "heures_tp": self.str_heures_tp(),
                "acs": self.apprentissages,
                "sae": "",
                "prerequis": self.prerequis,
                "contexte": folded(self.contexte),
                "contenu": folded(self.contenu),
                "motscles": self.mots
                }
        # output = yaml.dump(dico, #Dumper=yaml.Dumper,
        #    sort_keys=False, allow_unicode=True)
        output = ruamel.yaml.dump(dico, Dumper=ruamel.yaml.RoundTripDumper,
                                  allow_unicode=True)
        return output

    def to_latex(self):
        contenu = get_modele("pn/modele_ressource.tex")

        ajoutac = "\\ajoutac{%s}{%s}"
        compRT = []
        for i in range(len(self.apprentissages)):
            comps = []
            for ac in self.apprentissages[i]:
                comps.append( ajoutac % (ac, DATA_ACS["RT"+str(i+1)][ac]) )
            compRT.append("\n".join(comps))

        # ajoutsaes = "\\ajoutsae{%s}{%s}"
        # compRT = []
        # for i in range(len(self.apprentissages)):
        #     comps = []
        #     for ac in self.apprentissages[i]:
        #         code = self.apprentissages[i]
        #         comps.append(ajoutac % (code, DATA_ACS["RT" + str(i + 1)][code]))
        #     compRT.append("\n".join(comps))

        ajoutprerequis = "\\ajoutprerequis{%s}{%s}"
        prerequis = ""

        chaine = TemplateLatex(contenu).substitute(code=self.code,
                                                   nom=self.nom,
                                                   heures_formation=self.str_heures_formations(),
                                                   heures_tp=self.str_heures_tp(),
                                                   compRT1=compRT[0],
                                                   compRT2=compRT[1],
                                                   compRT3=compRT[2],
                                                   saes="",
                                                   prerequis=prerequis,
                                                   contexte=self.contexte,
                                                   contenu=self.contenu,
                                                   motscles=self.mots
                                                   )
        return chaine


def nettoie_heure(r):
    """Nettoie le champ (horaire) (de la forme 46h ou 33...) pour en extraire la valeur numérique :
    le champ peut contenir 2 volumes (heures formation puis heures tp), auquel cas les 2 valeurs sont renvoyées
    dans un tuple"""
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

def nettoie_code(r):
    """Recherche les codes ressources de la forme RXXX dans champ"""
    champ = r.code
    if r.code:
        codes = re.findall(r"(R[0-9][0-9][0-9])", champ)
        # if len(codes) > 1:
        #    __LOGGER.warning("plusieurs codes trouvés :(")
        #elif len(codes) == 0:
        #    __LOGGER.warning("code manquant")
        if len(codes) == 1:
            r.code = codes[0]
        else:
            code_devine = get_code_from_nom(r)
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
    for comp in range(3):
        donnees = r.apprentissages[comp] # chaine de caractères listant les ACS
        # donnees = donnees.replace("\t", "").replace("-", "") # supprime les tabulations
        acs_avec_code = devine_acs_by_code(donnees)
        acs_avec_nom = devine_code_by_nom_from_dict(donnees, DATA_ACS)
        acs_finaux = acs_avec_code + acs_avec_nom
        acs_finaux = [ac.replace(" ", "") for ac in acs_finaux]
        acs_finaux = sorted(list(set(acs_finaux)))
        r.apprentissages[comp] = acs_finaux

def nettoie_prerequis(r):
    """Nettoie les prérequis (ressource) en les remplaçant par leur code de ressource"""
    R_avec_code = devine_ressources_by_code(r.prerequis)
    R_avec_nom = devine_code_by_nom_from_dict(r.prerequis, DATA_RESSOURCES)
    R_finaux = sorted(list(set(R_avec_code + R_avec_nom)))
    if R_finaux:
        r.prerequis = R_finaux
    else:
        r.prerequis = "Aucun"


def get_code_from_nom(ressource):
    """Récupère le code d'une ressource d'après son nom en utilisant les noms officiels
    des ressources du yaml"""
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

def split_description(r):
    """Découpe le champ description en un contexte+un contenu ; si pas possible """
    champs = r.description.split("\n")
    champs = [c for c in champs if c] # supprime les lignes vides

    indicea = 0 # la ligne mentionnant le contexte
    if True in [ligne.startswith("Contexte et ") for ligne in champs]:  # la ligne commençant par Contenus
        indicea = [ligne.startswith("Contexte et ") for ligne in champs].index(True)

    indicec = 0
    contexte = ""
    if True in [ligne.startswith("Contenus") for ligne in champs]: # la ligne commençant par Contenus
        indicec = [ligne.startswith("Contenus") for ligne in champs].index(True)
    if indicea>0:
        contexte = "\n\n".join(champs[indicea+1:indicec]) # double \n pour passage en latex
    else:
        contexte = "\n\n".join(champs[:indicec])
    contenu = "\n".join(champs[indicec+1:])

    # sauvegarde des champs
    r.contexe = contexte
    r.contenu = contenu

def remove_ligne_vide(contenus):
    """Supprime les lignes vides"""
    return [c for c in contenus if c]

def get_marqueur_numerique(contenu):
    """Revoie la liste des marqueurs numériques"""
    m = re.findall(r"(\d/|\d\s\))", contenu)
    return m

def get_marqueurs(contenus):
    """Renvoie la liste des marqueurs partant d'une liste de ligne"""
    marqueurs = []
    for ligne in contenus:
        m = re.search(r"(\t)*", ligne) # dès \t ?
        if m.group() != "":
            ajout = m.group()
        else:
            ajout = ""
        ligne = ligne.replace("\t","")[0].rstrip() # le marqueur en début de ligne (si 1 caractère)
        if ligne[0] not in string.ascii_letters and ligne[0] != "É":
            marqueurs += [ajout + ligne[0]] # tous les symboles

    marqueurs_finaux = [] # tri les marqueurs en supprimant les doublons et en gardant un ordre (pour détecter les sous listes)
    for m in marqueurs:
        if m not in marqueurs_finaux:
            marqueurs_finaux.append(m)
    return marqueurs_finaux

def nettoie_contenus(r):
    # suppression des \t
    contenu = r.contenu
    marqueurs_numeriques = get_marqueur_numerique(contenu)
    for m in marqueurs_numeriques: # remplace les marqueurs numériques
        contenu = contenu.replace(m, ">")

    contenus = [ligne.rstrip().replace("--", "-") for ligne in r.contenu.split("\n")] # les contenus
    contenus = remove_ligne_vide(contenus) # supprime les lignes vides

    marqueurs_finaux = get_marqueurs(contenus)

    contenus_fin = contenus[:] # copie des ligne
    for (i, ligne) in enumerate(contenus):
        if ligne[0] in string.digits:
            pos = marqueurs_finaux.index("1")
            if ligne[1:].startswith("/"):
                contenus_fin[i] = "\t" * pos + "* " + ligne[2:].replace("\t", "").rstrip()
            else:
                contenus_fin[i] = "\t" * pos + "* " + ligne[1:].replace("\t", "").rstrip() # la ligne avec marqueur supprimé et / supprimé
        else:
            if ligne[0] in marqueurs_finaux:
                pos = marqueurs_finaux.index(ligne[0])
                contenus_fin[i] = "\t" * pos + "* " + ligne[1:].replace("\t", "").rstrip()

    contenu = "\n".join(contenus_fin)

    r.contenu = contenu


if __name__=="__main__":
    # Eléments de test
    for sem in DATA_RESSOURCES:
        for code in DATA_RESSOURCES[sem]:
            nom_data = supprime_accent_espace(DATA_RESSOURCES[sem][code])
            print(nom_data)
