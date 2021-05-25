
import sys
import argparse
import logging
import docx2python
import officiel


from config import Config

__LOGGER = logging.getLogger(__name__)
REPERTOIRE = "../google"

parser = argparse.ArgumentParser(
    description="Parse doc ressources et crée SAE", 
    usage='%(prog)s [options]'
    )
parser.add_argument(
    "DOCUMENT", 
    nargs="?", 
    default=REPERTOIRE + "/" + "sae_v0" + ".docx"
    )
parser.add_argument(
    "-o", 
    "--outdir", 
    default="../yaml/saes",
    help="repertoire resultat, defaut: ../yaml/saes"
    )
parser.add_argument(
    "-r", 
    "--root", 
    default="..", 
    help="repertoire de base (racine) pour chercher les fichiers de données"
    )
args = parser.parse_args()
Config.ROOT = args.root

__LOGGER.warning(f"{sys.argv[0]} processing {args.DOCUMENT}")
__LOGGER.warning(f"{sys.argv[0]} outputs to {args.outdir}")

# Ces imports doivent être faits après la config
import tools
import ressourcedocx

# Ouverture du document
docu = docx2python.docx2python(args.DOCUMENT)

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
        nom_sae = tools.caracteres_recalcitrants(res[0][1][0])

        # Création de la ressource
        r = ressourcedocx.SAEDocx(nom_sae, res)
        liste_saes.append(r)

        # Parsing des données brute de la sae
        data = [None for i in range(len(ENTETES_CHAPEAU))] # les données attendues Nom, Code, ..., Mots clés
        apprentissages = [None for i in range(3)] # les apprentissages des 3 compétences
        coeffs = [None for i in range(3)]

        non_interprete = []
        for j in range(len(res)): # parcours des entêtes du tableau décrivant la ressource
            ligne = res[j]
            if len(ligne) == 2: # ligne de données classique champ => valeur
                champ = tools.caracteres_recalcitrants(ligne[0][0]) # le nom du champ
                if champ.startswith("Nom de la"):
                    champ = "Titre de la" # corrige les noms/titres
                i = tools.get_indice_sans_accent_ni_espace(champ, ENTETES_CHAPEAU)  # l'indice de l'entete dans ENTETES
                if i != None:
                    data[i] = tools.caracteres_recalcitrants("\n".join(res[j][1]))
                else:
                    non_interprete.append((champ, ligne[1][0]))
            else: # ligne de données soit chapeau (ex Compétences ciblées) soit détail par compétence
                champ = ligne[0][0]

                if "Apprentissage(s)" in champ: # les compétences ciblées sont déduites de la présence d'apprentissage critiques
                    # j+1 = les ACs par compétences
                    acs = res[j+2]
                    for k in range(len(acs)):
                        apprentissages[k] = tools.caracteres_recalcitrants("\n".join(acs[k])) # fusionne les ACS (généralement sur plusieurs lignes)
                elif "Compétence(s) ciblée(s)" in champ:
                    les_coeffs = res[j+2]
                    coeffs = [elmt[0] for elmt in les_coeffs]

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
        r.charge_coeffs(coeffs)

        # nettoie le titre et le code
        r.nettoie_code()
        r.nettoie_titre_sae()


        last_sae = r.code
        liste_exemples[r.code] = []

    elif est_exemple == True:
        res = docu[i] # la ressource
        nom_exemple = tools.caracteres_recalcitrants(res[0][1][0])

        # Création de la ressource
        r = ressourcedocx.ExempleSAEDocx(nom_exemple, res, last_sae)
        liste_exemples[last_sae].append(r)

        # Parsing des données brute de la sae
        data = [None for i in range(len(ENTETES_EXEMPLES))] # les données attendues Nom, Code, ..., Mots clés
        apprentissages = [None for i in range(3)] # les apprentissages des 3 compétences

        non_interprete = []
        for j in range(len(res)): # parcours des entêtes du tableau décrivant la ressource
            ligne = res[j]
            if len(ligne) == 2: # ligne de données classique champ => valeur
                champ = tools.caracteres_recalcitrants(ligne[0][0]) # le nom du champ
                i = tools.get_indice_sans_accent_ni_espace(champ, ENTETES_EXEMPLES)  # l'indice de l'entete dans ENTETES
                if i != None:
                    data[i] = tools.caracteres_recalcitrants("\n".join(res[j][1]))
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
    s.nettoie_champs()

    # Tri dans le bon semestre
    saes[s.semestre] += [s]

# Post traitement des exemples "S1" => "codesae chapeau" => "ExempleSAE"
exemples = {"S1" : {}, "S2" : {} }
print(" > Exemples")
for s in liste_exemples: # la sae
    sem = officiel.get_officiel_sem_sae_by_code(s)
    exemples[sem][s] = []

    for e in liste_exemples[s]:
        print(f"{s} : {e.semestre}")
        e.nettoie_champs()

        # Tri dans le bon semestre
        exemples[sem][s].append(e)

# Export yaml
print("*Etape 3* : Export yaml")
for sem in saes:
     for s in saes[sem]:
         output = s.to_yaml()
         if s.code:
             code_clean = s.code.replace("É", "E")
             fichier = f"{args.outdir}/{code_clean}.yml"
             __LOGGER.warning(f"writing '{fichier}")
             with open(fichier, "w", encoding="utf8") as fid:
                 fid.write(output)

for sem in exemples:
     for s in exemples[sem]:
         for (i, e) in enumerate(exemples[sem][s]):
            output = e.to_yaml()
            code_clean = s.replace("É", "E")
            fichier = f"{args.outdir}/{code_clean}_exemple{i+1}.yml"
            __LOGGER.warning(f"writing '{fichier}")
            with open(fichier, "w", encoding="utf8") as fid:
                fid.write(output)


