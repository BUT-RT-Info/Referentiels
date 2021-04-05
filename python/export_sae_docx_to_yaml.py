
import docx2python
from ressourcedocx import *
from tools import *

import logging
__LOGGER = logging.getLogger(__name__)

REPERTOIRE = "import"
DOCUMENT = "sae_v0"

# Ouverture du document
docu = docx2python.docx2python(REPERTOIRE + "/" + DOCUMENT + ".docx")

docu = docu.body
docu[0] # Titre général
docu[1] # Tableau de synthèse des ressources



ENTETES_CHAPEAU = ["Titre",  "Code", "Semestre", "Heures de formation",
                   "dont heures de TP",
                   "Heures \"projet",
                   "Description",
                   "Liste des ressources", "Type de livrable", "Mots clefs"]
ENTETES_EXEMPLES = ["Titre", "Description", "Formes", "Quelle problématique",
                    "Modalités"]

"""
Format du parsing issu de docx2python
[  # document
    [  # table A
        [  # table A row
            [  # table A cell 1  <-- structure des tableaux
"""


print("*Etape 1* : Parsing")
nbre_saes = 0
last_sae = None
liste_saes = [] # la liste des saes telle qu'extraite du docx
liste_exemples = {} # la liste des exemples de chaque SAé

for i in range(1, len(docu)): # A priori un tableau
    est_sae, est_exemple = False, False
    try:
        if "Titre de la " in docu[i][0][0][0] or "Nom de la " in docu[i][0][0][0]: # [03][00][0][0]
            if "Code" in docu[i][1][0][0]:
                est_sae = True
                nbre_saes += 1
            else: # c'est un exemple
                est_exemple = True
    except:
        pass

    if est_sae == True:
        res = docu[i] # la ressource
        nom_sae = caracteres_recalcitrants(res[0][1][0])

        # Création de la ressource
        r = SAEDocx(nom_sae, res)
        liste_saes.append(r)

        # Parsing des données brute de la sae
        data = [None for i in range(len(ENTETES_CHAPEAU))] # les données attendues Nom, Code, ..., Mots clés
        apprentissages = [None for i in range(3)] # les apprentissages des 3 compétences

        non_interprete = []
        for j in range(len(res)): # parcours des entêtes du tableau décrivant la ressource
            ligne = res[j]
            if len(ligne) == 2: # ligne de données classique champ => valeur
                champ = caracteres_recalcitrants(ligne[0][0]) # le nom du champ
                if champ.startswith("Nom de la"):
                    champ = "Titre de la" # corrige les noms/titres
                i = get_indice_sans_accent_ni_espace(champ, ENTETES_CHAPEAU)  # l'indice de l'entete dans ENTETES
                if i != None:
                    data[i] = caracteres_recalcitrants("\n".join(res[j][1]))
                else:
                    non_interprete.append((champ, ligne[1][0]))
            else: # ligne de données soit chapeau (ex Compétences ciblées) soit détail par compétence
                champ = ligne[0][0]

                if "Apprentissage(s)" in champ: # les compétences ciblées sont déduites de la présence d'apprentissage critiques
                    # j+1 = les ACs par compétences
                    acs = res[j+2]
                    for k in range(len(acs)):
                        apprentissages[k] = caracteres_recalcitrants("\n".join(acs[k])) # fusionne les ACS (généralement sur plusieurs lignes)

        if non_interprete: # souvent Heures de formation (incluant les TP)

            __LOGGER.warning(f"Dans la saé \"{nom_sae}\", champs en trop non interprétés  : " + ",".join(
                    [chp[0] for chp in non_interprete]))

        # Analyse des champs manquants
        champ_manquants = []
        for (j, champ) in enumerate(ENTETES_CHAPEAU):
            if not data[j]:
                champ_manquants += [champ]
        if champ_manquants:
            __LOGGER.warning(f"Dans \"{nom_sae}\", champs manquants  : " + ",".join(champ_manquants))

        # Sauvegarde des champs de la ressource
        info = tuple(data[1:])
        r.charge_informations(*info)
        r.charge_ac(apprentissages)

        # nettoie le titre et le code
        r.nettoie_code()
        r.nettoie_titre_sae()


        last_sae = r.code
        liste_exemples[r.code] = []

    elif est_exemple == True:
        res = docu[i] # la ressource
        nom_exemple = caracteres_recalcitrants(res[0][1][0])

        # Création de la ressource
        r = ExempleSAEDocx(nom_exemple, res, last_sae)
        liste_exemples[last_sae].append(r)

        # Parsing des données brute de la sae
        data = [None for i in range(len(ENTETES_EXEMPLES))] # les données attendues Nom, Code, ..., Mots clés
        apprentissages = [None for i in range(3)] # les apprentissages des 3 compétences

        non_interprete = []
        for j in range(len(res)): # parcours des entêtes du tableau décrivant la ressource
            ligne = res[j]
            if len(ligne) == 2: # ligne de données classique champ => valeur
                champ = caracteres_recalcitrants(ligne[0][0]) # le nom du champ
                i = get_indice_sans_accent_ni_espace(champ, ENTETES_EXEMPLES)  # l'indice de l'entete dans ENTETES
                if i != None:
                    data[i] = caracteres_recalcitrants("\n".join(res[j][1]))
                else:
                    non_interprete.append((champ, ligne[1][0]))
            else: # ligne de données soit chapeau (ex Compétences ciblées) soit détail par compétence
                print("??? plus de 2 colonnes ?")

        if non_interprete: # souvent Heures de formation (incluant les TP)

            __LOGGER.warning(f"Dans l'exemple \"{nom_exemple}\", champs en trop non interprétés  : " + ",".join(
                    [chp[0] for chp in non_interprete]))

        # Analyse des champs manquants
        champ_manquants = []
        for (j, champ) in enumerate(ENTETES_EXEMPLES):
            if not data[j]:
                champ_manquants += [champ]
        if champ_manquants:
            __LOGGER.warning(f"Dans \"{nom_exemple}\", champs manquants  : " + ",".join(champ_manquants))

        # Sauvegarde des champs de la ressource
        info = tuple(data[1:])
        r.charge_informations(*info)

# fin du parsing
print(f"{nbre_saes} saes")
for s in liste_exemples:
    print(f"{s} :" + str(len(liste_exemples[s])) + " exemples")

# ************************************************************************
print("*Etape 2* : Post-traitement")

# Post traitement des saes => gestion des heures/des acs/ + tri par semestre
print(" > SAE")
saes = {"S1" : [], "S2": []}

for s in liste_saes:
    print(f"{s.nom}")
    s.nettoie_heures_sae()
    s.nettoie_semestre()
    s.nettoie_acs()
    s.nettoie_ressources()
    s.nettoie_description()
    s.nettoie_livrables_sae()
    s.nettoie_mots_cles()

    # Tri dans le bon semestre
    saes[s.semestre] += [s]

# Post traitement des exemples "S1" => "codesae chapeau" => "ExempleSAE"
exemples = {"S1" : {}, "S2" : {} }
print(" > Exemples")
for s in liste_exemples: # la sae

    sem = get_officiel_sem_sae_by_code(s)
    exemples[sem][s] = []
    for e in liste_exemples[s]:
        print(f"{s} : {e.nom}")
        if e.nom.startswith("Caractériser un support radio"):
            print("ici")
        e.nettoie_champs()

        # Tri dans le bon semestre
        exemples[sem][s].append(e)

# Export yaml
print("*Etape 3* : Export yaml")
for sem in saes:
     for s in saes[sem]:
         output = s.to_yaml()
         if s.code:
             fichier = "export/{}.yml".format(s.code.replace("É", "E"))
             with open(fichier, "w", encoding="utf8") as fid:
                 fid.write(output)

for sem in exemples:
     for s in exemples[sem]:
         for (i, e) in enumerate(exemples[sem][s]):
            output = e.to_yaml()
            fichier = "export/{}_exemple{}.yml".format(s.replace("É", "E"), i+1)
            with open(fichier, "w", encoding="utf8") as fid:
                fid.write(output)


