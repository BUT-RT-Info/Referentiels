import os.path
import argparse
import logging
import docx2python

from config import Config

parser = argparse.ArgumentParser(
    description="Parse doc ressources et crée yaml", 
    usage='%(prog)s [options]'
    )
# parser.add_argument(
#    "DOCUMENT",
#    nargs="?",
#    default="../google/" + "compilation-ressources-JOBO21" + ".rdocx",
#    help="rdocx à parser, defaut: ../google/compilation-ressources-JOBO21.rdocx"
#    )
parser.add_argument(
    "-o", 
    "--outdir",
    default= "../yaml/",
    help="repertoire resultat, defaut: ../yaml/"
    )
parser.add_argument(
    "-r", 
    "--root", 
    default="..", 
    help="repertoire de base (racine) pour chercher les fichiers de données"
    )
args = parser.parse_args()
Config.ROOT = args.root

# __LOGGER.warning(f"{sys.argv[0]} processing {args.DOCUMENT}")
# __LOGGER.warning(f"{sys.argv[0]} outputs to {args.outdir}")

# Ces imports doivent être faits après la config
import rofficiel.officiel
import rdocx.parsedocx
# from rdocx.parsedocx import get_docx_format, get_type_fiche, parse_docu_ressource, parse_docu_sae

__LOGGER = logging.getLogger(__name__)
# logging.basicConfig(filename='export_pn.log.txt', level=logging.WARNING)

# Récupère les données officielles
pnofficiel = rofficiel.officiel.Officiel()

# Ouverture du document
# if not os.path.isfile(args.DOCUMENT):
#    print(f"Le fichier à parser {args.DOCUMENT} n'existe pas")
#    sys.exit()

# Pour debuggage, donne les codes sur lesquelles se focuser
# LIMIT_TO = ["SAÉ3.2"] # ["R3.21"] #"R4.01"] # ["R1.01", "R3.14"]
LIMIT_TO = [] # "SAÉ1.1"] # "R3.02"] #"SAÉ3.2"]

REPERTOIRE_GOOGLE = "../google/"

liste_ressources = []  # la liste des ressources telle qu'extrait du rdocx
liste_saes = []
liste_exemples_saes = {} # la liste des exemples de chaque SAé
last_sae = None

DATA_RESSOURCES = rofficiel.officiel.get_DATA_RESSOURCES() # les ressources du PN
DATA_SAES = rofficiel.officiel.get_DATA_SAES() # les saés du PN

print("*** ETAPE 1*** Lecture des google.docx avec parsing des informations")
for sem in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']: # DATA_RESSOURCES: # ['S1']: #
    for code in {**DATA_RESSOURCES[sem], **DATA_SAES[sem]}: #
        if not LIMIT_TO or code in LIMIT_TO:
            fichier = pnofficiel.get_docx_file_by_code(code)
            if fichier == None:
                raise Exception( f"{code} n'existe pas")

            fichier = REPERTOIRE_GOOGLE + fichier
            if not fichier or not os.path.exists(fichier):
                print(f"{fichier} manquant pour la fiche {code}")
            else:
                docu = docx2python.docx2python(fichier)
                docu = docu.body

                # A priori un tableau avec un titre (AnnexeD ou Données) puis les tableaux de synthèse de la ressource
                type_fiche = False

                try:
                    res = docu[1]  # le 1er contenu
                    version = rdocx.parsedocx.get_docx_format(res)
                    type_fiche = rdocx.parsedocx.get_type_fiche(res)
                except:
                    pass

                if type_fiche == "RESSOURCE":
                    r = rdocx.parsedocx.parse_docu_ressource(code, docu, pnofficiel)
                    if r:
                        liste_ressources.append(r)
                else: # type_fiche == "SAE":
                    (s, liste_exemples) = rdocx.parsedocx.parse_docu_sae(code, docu, pnofficiel)
                    liste_saes.append(s)
                    liste_exemples_saes[code] = liste_exemples

# fin du parsing
nbre_exemples = sum([len(liste_exemples_saes[cle]) for cle in liste_exemples_saes])
print(f"{len(liste_ressources)} ressources")
print(f"{len(liste_saes)} saes")
print(f"{nbre_exemples} exemples")

# ************************************************************************

print("*** ETAPE 2*** Post-traitement/nettoyage des informations")

# Post traitement des ressources => gestion des heures/des acs/ + tri par semestre
ressources = {"S{}".format(d) : [] for d in range(1, 7)}
print(" > Ressources :")
for (i, r) in enumerate(liste_ressources):
    r.nettoie_champs()

    # Remet en forme les mots-clés
    # Tri dans le bon semestre
    ressources["S" + r.semestre] += [r]

saes = {"S{}".format(d) : [] for d in range(1, 7)}
print(" > SAE")
for s in liste_saes:
    print(f"{s.nom}")
    s.nettoie_champs()

    # Tri dans le bon semestre
    saes["S" + s.semestre] += [s]

exemples = {"S{}".format(d) : {} for d in range(1, 7)}
print(" > Exemples")
for s in liste_exemples_saes: # la sae
    sem = pnofficiel.get_sem_activite_by_code(s)
    exemples[sem][s] = []
    print(s)
    for e in liste_exemples_saes[s]:
        print(e)
        e.nettoie_champs()

        # Tri dans le bon semestre
        exemples[sem][s].append(e)

# Export yaml
print("*** ETAPE 3*** Export yaml")
WITH_EXPORT = True
repertoire = f"{args.outdir}ressources"
if not os.path.exists(repertoire):
    os.mkdir(repertoire)

print(" > Ressources")
for sem in ressources:
    rep = repertoire + f"/{sem}"
    if not os.path.exists(rep):
        os.mkdir(rep)
    for r in ressources[sem]:
        output = r.to_yaml()
        if WITH_EXPORT and r.code:
            fichier = f"{rep}/{r.code}.yml"
            __LOGGER.warning(f"writing '{fichier}")
            with open(fichier, "w", encoding="utf8") as fid:
                fid.write(output)

print(" > SAE")
repertoire = f"{args.outdir}saes"
if not os.path.exists(repertoire):
    os.mkdir(repertoire)

for sem in saes:
    rep = repertoire + f"/{sem}"
    if not os.path.exists(rep):
        os.mkdir(rep)
    for s in saes[sem]:
         output = s.to_yaml()
         if WITH_EXPORT and s.code:
             code_clean = s.code.replace("É", "E")
             fichier = f"{rep}/{code_clean}.yml"
             __LOGGER.warning(f"writing '{fichier}")
             with open(fichier, "w", encoding="utf8") as fid:
                 fid.write(output)

print(" > Exemples de SAE")
for sem in exemples:
    rep = repertoire + f"/{sem}"
    if not os.path.exists(rep):
        os.mkdir(rep)
    for s in exemples[sem]:
         for (i, e) in enumerate(exemples[sem][s]):
            output = e.to_yaml()
            code_clean = s.replace("É", "E")
            fichier = f"{rep}/{code_clean}_exemple{i+1}.yml"
            __LOGGER.warning(f"writing '{fichier}")
            with open(fichier, "w", encoding="utf8") as fid:
                fid.write(output)