import os.path
import sys
import argparse
import logging
import docx2python
import officiel
import ressourcedocx

from config import Config


__LOGGER = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description="Parse doc ressources et crée yaml", 
    usage='%(prog)s [options]'
    )
parser.add_argument(
    "DOCUMENT", 
    nargs="?", 
    default="../google/" + "compilation-ressources-JOBO21" + ".rdocx",
    help="rdocx à parser, defaut: ../google/compilation-ressources-JOBO21.rdocx"
    )
parser.add_argument(
    "-o", 
    "--outdir",
    default= "../yaml/ressources",
    help="repertoire resultat, defaut: ../yaml/ressources"
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
import tools, activitedocx, officiel

# Récupère les données officielles
pnofficiel = officiel.Officiel()

# Ouverture du document
if not os.path.isfile(args.DOCUMENT):
    print(f"Le fichier à parser {args.DOCUMENT} n'existe pas")
    sys.exit()

docu = docx2python.docx2python(args.DOCUMENT)

docu = docu.body
docu[0] # Titre général
docu[1] # Tableau de synthèse des ressources
nbre_ressources = 0


ENTETES_BUT1 = ["Nom", "Code", "Semestre", "Heures de formation", "dont heures de TP", "SAÉ", "Prérequis", "Descriptif", "Mots"]

"""
Format du parsing issu de docx2python
[  # document
    [  # table A
        [  # table A row
            [  # table A cell 1  <-- structure des tableaux
"""

liste_ressources = [] # la liste des ressources telle qu'extrait du rdocx

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
        nom_ressource = tools.caracteres_recalcitrants(res[0][1][0])

        # Création de la ressource
        r = ressourcedocx.RessourceDocx(nom_ressource, res, pnofficiel)
        liste_ressources.append(r)

        # if len(res) != 15:
            # __LOGGER.warning(f"Champs en trop ou manquants dans \"{nom_ressource}\"")
        # Parsing des données brute de la ressource
        data = [None for i in range(len(ENTETES_BUT1))] # les données attendues Nom, Code, ..., Mots clés
        apprentissages = [None for i in range(3)] # les apprentissages des 3 compétences
        coeffs = [None for i in range(3)]

        non_interprete = []
        for j in range(len(res)): # parcours des entêtes du tableau décrivant la ressource
            ligne = res[j]
            if len(ligne) == 2: # ligne de données classique champ => valeur
                champ = ligne[0][0] # le nom du champ
                i = tools.get_indice_sans_accent_ni_espace(champ, ENTETES_BUT1)  # l'indice de l'entete dans ENTETES
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
                elif "Compétence(s) ciblée(s)" in champ:
                    les_coeffs = res[j+2]
                    coeffs = [elmt[0] for elmt in les_coeffs]
        if non_interprete: # souvent Heures de formation (incluant les TP)

            try:
                indice_champ = [chp[0] for chp in non_interprete].index("Heures de formation (incluant les TP)")
            except:
                indice_champ = -1
            if indice_champ >= 0: # si le champ "Heures de formation (incluant les TP)" est trouvé
                # tente de réinjecter les heures dans Heures encadrées si elles n'on pas déjà été renseignées
                indice_heure = tools.get_indice("formation encadrée", ENTETES_BUT1)
                if not data[indice_heure]:
                    print(f"Dans \"{nom_ressource}\", réinjection de \"Heures de formation (incluant les TP)\" dans \"formation encadrée\"")
                    data[indice_heure] = champ[1]
                    non_interprete = non_interprete[:indice_champ] + non_interprete[indice_champ+1:] # supprime le champ

            if non_interprete:
                __LOGGER.warning(f"Dans \"{nom_ressource}\", champs en trop non interprétés  : " + ",".join(
                    [chp[0] for chp in non_interprete]))

        # Analyse des champs manquants
        champ_manquants = []
        for (j, champ) in enumerate(ENTETES_BUT1):
            if not data[j]:
                champ_manquants += [champ]
        if champ_manquants:
            __LOGGER.warning(f"Dans \"{nom_ressource}\", champs manquants  : " + ",".join(champ_manquants))

        # Sauvegarde des champs de la ressource
        info = tuple(data[1:])
        r.charge_informations(*info)
        r.charge_ac(apprentissages)
        r.charge_coeffs(coeffs)

# fin du parsing
print(f"{nbre_ressources} ressources")

# ************************************************************************

# Post traitement des ressources => gestion des heures/des acs/ + tri par semestre
ressources = {"S1" : [], "S2": []}

for (i, r) in enumerate(liste_ressources):
    if r.numero_semestre.startswith("Projet "):
        print("ici")
    r.nettoie_champs()

    # Remet en forme les mots-clés
    # Tri dans le bon semestre
    ressources[r.numero_semestre] += [r]

# complète les codes d'après les numéros
for sem in ressources:
    for (i, r) in enumerate(ressources[sem]):
        if not r.code:
            if i == 0:
                r.code = "R" + sem[1] + "01"
            elif ressources[sem][i-1].code:
                r.code = "R" + sem[1] + "{:02d}".format(int(ressources[sem][i-1].code[-2:])+1)

# Export yaml
WITH_EXPORT = True
for sem in ressources:
    for r in ressources[sem]:
        output = r.to_yaml()
        if WITH_EXPORT and r.code:
            fichier = f"{args.outdir}/{r.code}.yml"
            __LOGGER.warning(f"writing '{fichier}")
            with open(fichier, "w", encoding="utf8") as fid:
                fid.write(output)

