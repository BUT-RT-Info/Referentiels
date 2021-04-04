
import docx2python
from ressourcedocx import *
import tools

import logging

from tools import get_indice, get_indice_sans_accent_ni_espace

__LOGGER = logging.getLogger(__name__)

REPERTOIRE = "import"
DOCUMENT = "ressources_v0"

# Ouverture du document
docu = docx2python.docx2python(REPERTOIRE + "/" + DOCUMENT + ".docx")

docu = docu.body
docu[0] # Titre général
docu[1] # Tableau de synthèse des ressources
nbre_ressources = 0


ENTETES = ["Nom",  "Code", "Semestre", "Heures de formation", "dont heures de TP",
           "SAÉ", "Prérequis", "Descriptif", "Mots"]

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
        r = RessourceDocx(nom_ressource, res)
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
                i = get_indice_sans_accent_ni_espace(champ, ENTETES)  # l'indice de l'entete dans ENTETES
                if i != None:
                    data[i] = tools.caracteres_recalcitrants("\n".join(res[j][1]))
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
                        apprentissages[k] = tools.caracteres_recalcitrants("\n".join(acs[k])) # fusionne les ACS (généralement sur plusieurs lignes)

        if non_interprete: # souvent Heures de formation (incluant les TP)

            try:
                indice_champ = [chp[0] for chp in non_interprete].index("Heures de formation (incluant les TP)")
            except:
                indice_champ = -1
            if indice_champ >= 0: # si le champ "Heures de formation (incluant les TP)" est trouvé
                # tente de réinjecter les heures dans Heures encadrées si elles n'on pas déjà été renseignées
                indice_heure = get_indice("formation encadrée", ENTETES)
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
    r.nettoie_titre_ressource()
    r.nettoie_heures()
    r.nettoie_code()
    r.nettoie_semestre()
    r.nettoie_acs()
    r.nettoie_sae()
    r.nettoie_prerequis()
    r.nettoie_mots_cles()


    # Remet en forme le descriptif
    r.split_description()
    r.nettoie_contenu()

    # Remet en forme les mots-clés
    # Tri dans le bon semestre
    ressources[r.semestre] += [r]

# complète les codes d'après les numéros
for sem in ressources:
    for (i, r) in enumerate(ressources[sem]):
        if not r.code:
            if i == 0:
                r.code = "R" + sem[1] + "01"
            elif ressources[sem][i-1].code:
                r.code = "R" + sem[1] + "{:02d}".format(int(ressources[sem][i-1].code[-2:])+1)

# ************************************************************************
# Affichages divers
# Le tableau des heures ressources
for sem in ressources: # parcours des semestres
    # print(f"Semestre {sem}")
    chaine = affiche_bilan_heures(ressources, sem)


# Matrice ACS/ressources
matrices = {}
les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]
nbre_acs = len(les_codes_acs)

for sem in ressources:
    # print("Matrice du semestre " + sem)
    (matrices[sem], chaine) = get_matrices_ac_ressource(ressources, sem)

# Export yaml
WITH_EXPORT = True
for sem in ressources:
    for r in ressources[sem]:
        output = r.to_yaml()
        if WITH_EXPORT and r.code:
            fichier = "export/{}.yml".format(r.code)
            with open(fichier, "w", encoding="utf8") as fid:
                fid.write(output)

