
import docx2python, yaml
from ressource import *

import logging
__LOGGER = logging.getLogger(__name__)

REPERTOIRE = "import"
DOCUMENT = "000 compilation-ressources 2021-03-29T11_19_03.259Z"

# Ouverture du document
docu = docx2python.docx2python(REPERTOIRE + "/" + DOCUMENT + ".docx")

docu = docu.body
docu[0] # Titre général
docu[1] # Tableau de synthèse des ressources
nbre_ressources = 0


ENTETES = ["Nom",  "Code", "Semestre", "formation encadrée", "dont heures de TP",
           "SAÉ", "Prérequis", "Descriptif", "Mots"]
def get_indice(champ):
    """Récupère l'indice d'une entête"""
    for (i, entete) in enumerate(ENTETES):
        if entete in champ:
            return i
    return None

def get_indice_sans_accent_ni_espace(champ):
    """Récupère l'indice d'une entête en se débarrassant des majuscules/caractères spéciaux/espace"""
    champ_purge = supprime_accent_espace(champ)
    for (i, entete) in enumerate(ENTETES):
        entete_purge = supprime_accent_espace(entete)
        if entete_purge in champ_purge:
            return i
    return None


"""
Format du parsing issu de docx2python
[  # document
    [  # table A
        [  # table A row
            [  # table A cell 1  <-- structure des tableaux
"""

liste_ressources = [] # la liste des ressources telle qu'extrait du docx
print("*Etape 1* : Parsing")

for i in range(2, len(docu)): # A priori un tableau
    est_ressource = False
    try:
        if "Nom de la ressource" in docu[i][0][0][0]: # [03][00][0][0]
            est_ressource = True
            nbre_ressources += 1
    except:
        pass

    if est_ressource == True:
        res = docu[i] # la ressource
        nom_ressource = res[0][1][0]

        # Création de la ressource
        r = Ressource(nom_ressource, res)
        liste_ressources.append(r)

        # if len(res) != 15:
            # __LOGGER.warning(f"Champs en trop ou manquants dans \"{nom_ressource}\"")
        # Parsing des données brute de la ressource
        data = [None for i in range(len(ENTETES))] # les données attendues Nom, Code, ..., Mots clés
        apprentissages = [None for i in range(3)] # les apprentissages des 3 compétences

        non_interprete = []
        for j in range(len(res)): # parcours des entêtes du tableau décrivant la ressource
            ligne = res[j]
            if len(ligne) == 2: # ligne de données classique champ => valeur
                champ = ligne[0][0] # le nom du champ
                i = get_indice_sans_accent_ni_espace(champ)  # l'indice de l'entete dans ENTETES
                if i != None:
                    data[i] = "\n".join(res[j][1])
                    if champ == "Prérequis" and not data[i]:
                        data[i] = "aucun"
                        print(f"Dans {nom_ressource}, complète les prérequis à \"aucun\"")
                else:
                    non_interprete.append((champ, ligne[1][0]))
            else: # ligne de données soit chapeau (ex Compétences ciblées) soit détail par compétence
                champ = ligne[0][0]
                if "Apprentissages" in champ: # les compétences ciblées sont déduites de la présence d'apprentissage critiques
                    # j+1 = les ACs par compétences
                    acs = res[j+2]
                    for k in range(len(acs)):
                        apprentissages[k] = "\n".join(acs[k]) # fusionne les ACS (généralement sur plusieurs lignes)

        if non_interprete: # souvent Heures de formation (incluant les TP)

            try:
                indice_champ = [chp[0] for chp in non_interprete].index("Heures de formation (incluant les TP)")
            except:
                indice_champ = -1
            if indice_champ >= 0: # si le champ "Heures de formation (incluant les TP)" est trouvé
                # tente de réinjecter les heures dans Heures encadrées si elles n'on pas déjà été renseignées
                indice_heure = get_indice("formation encadrée")
                if not data[indice_heure]:
                    print(f"Dans \"{nom_ressource}\", réinjection de \"Heures de formation (incluant les TP)\" dans \"formation encadrée\"")
                    data[indice_heure] = champ[1]
                    non_interprete = non_interprete[:indice_champ] + non_interprete[indice_champ+1:] # supprime le champ

            if non_interprete:
                __LOGGER.warning(f"Dans \"{nom_ressource}\", champs en trop non interprétés  : " + ",".join(
                    [chp[0] for chp in non_interprete]))

        # Analyse des champs manquants
        champ_manquants = []
        for (j, champ) in enumerate(ENTETES):
            if not data[j]:
                champ_manquants += [champ]
        if champ_manquants:
            __LOGGER.warning(f"Dans \"{nom_ressource}\", champs manquants  : " + ",".join(champ_manquants))

        # Sauvegarde des champs de la ressource
        info = tuple(data[1:])
        r.charge_informations(*info)
        r.charge_ac(apprentissages)
# fin du parsing
print(f"{nbre_ressources} ressources")

# ************************************************************************

# Post traitement des ressources => gestion des heures/des acs/ + tri par semestre
ressources = {"S1" : [], "S2": []}

for r in liste_ressources:
    # Nettoie le champ heures_encadrees
    if r.heures_encadrees:
        volumes = nettoie_heure(r.heures_encadrees)
    if r.tp:
        r.tp = nettoie_heure(r.tp)
    if isinstance(volumes, int):
        r.heures_encadrees = volumes
    elif isinstance(volumes, tuple):
        r.heures_encadrees = volumes[0]
        if not r.tp:
            r.tp = volumes[1]
        elif r.tp != volumes[1]:
            __LOGGER.warning(r"Dans {r.nom}, pb dans les heures tp/td")
    else:
        r.heures_encadrees = None

    # Nettoie les codes
    if r.code:
        r.code = nettoie_code(r.code)
        if not r.code: # Recherche le code dans les ressources
            code_devine = get_code_from_nom(r)
            if code_devine:
                __LOGGER.warning(f"Dans \"{r.nom}\", remplace le code par {code_devine}")
                r.code = code_devine

    # Nettoie les semestres
    if r.semestre:
        if "1" in r.semestre:
            r.semestre = "S1"
        elif "2" in r.semestre:
            r.semestre = "S2"
        else:
            __LOGGER.warning(f"Dans \"{r.nom}, PAS de semestre => rattaché au S2")
            r.semestre = "S2"
    else:
        __LOGGER.warning(f"Dans \"{r.nom}, PAS de semestre => rattaché au S2")
        r.semestre = "S2"
    # Remet en forme le titre
    if r.code:
        if supprime_accent_espace(r.nom) != supprime_accent_espace(DATA_RESSOURCES[r.semestre][r.code]):
            __LOGGER.warning(r"Dans {r.nom}, pb dans le nom de la ressource : devient " + DATA_RESSOURCES[r.semestre][r.code])
        r.nom = DATA_RESSOURCES[r.semestre][r.code]

    # Remet en forme les ACs
    acs = r.apprentissages
    if len(acs) != 3:
        __LOGGER.warning(f"Problème dans le nombre de compétences de {r.nom}")
    for comp in range(3):
        donnees = acs[comp] # chaine de caractères listant les ACS
        # donnees = donnees.replace("\t", "").replace("-", "") # supprime les tabulations
        acs_avec_code = devine_acs_by_code(donnees)
        acs_avec_nom = devine_acs_by_nom(donnees)
        acs_finaux = sorted(list(set(acs_avec_code + acs_avec_nom)))
        r.apprentissages[comp] = acs_finaux

    # Tri dans le bon semestre
    ressources[r.semestre] += [r]

# ************************************************************************
# Affichages divers


# Bilan des heures & Calcul somme des heures par semestre
ligne = "{:20s} | {:75s} | {:10s} | {:10s} |"
trait = "-"*len(ligne.format("", "", "", ""))

for sem in ressources: # parcours des semestres
    ressem = ressources[sem] # les ressources du semestre
    print(f"Semestre {sem}")
    print(trait, ligne.format("Code", "Ressource", "Form.", "dont TP"), trait, sep="\n")
    for r in ressem:
        print(ligne.format(r.code if r.code else "MANQUANT",
                           # r.nom[:30] + ("..." if len(r.nom) > 30 else "") ,
                           r.nom,
                           str(r.heures_encadrees) if r.heures_encadrees else "MANQUANT",
                           str(r.tp) if r.tp else "MANQUANT"))
    heures_formation_total = sum([r.heures_encadrees for r in ressem if r.heures_encadrees != None])
    heures_tp_total = sum([r.tp for r in ressem if r.tp != None])
    print(trait, ligne.format("", "Total", str(heures_formation_total), str(heures_tp_total)), trait, sep="\n")



# Matrice ACS/ressources
matrices = {}
les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]
nbre_acs = len(les_codes_acs)

for sem in ressources:
    ressem = ressources[sem] # les ressources du semestre
    nbre_ressources_semestre = len(DATA_RESSOURCES[sem])
    if len(ressem) != nbre_ressources_semestre:
        __LOGGER.warning(f"Pb => il manque des ressources au {sem}")

    matrices[sem] = [[False]*nbre_ressources_semestre]*nbre_acs
    for (i, r) in enumerate(ressem): # pour chaque ressource
        for comp in r.apprentissages: # pour chaque comp

            for (j, ac) in enumerate(les_codes_acs): # pour chaque ac
                if ac in r.apprentissages[comp]: # si l'ac est prévue dans la ressource
                    matrices[r.semestre][j][i] = True

print(matrices["S1"])
