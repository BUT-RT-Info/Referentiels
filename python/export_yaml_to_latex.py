import os
import glob
import argparse
import logging
import sys

import latex
from config import Config

__LOGGER = logging.getLogger(__name__)


parser = argparse.ArgumentParser(description="Conversion des YAML en LaTeX")
parser.add_argument(
    "-a", 
    "--all", 
    action="store_true", 
    help="exporte le LaTeX complet"
    )
parser.add_argument(
    "-r", 
    "--root", 
    default="..", 
    help="repertoire de base (racine) pour chercher les fichiers de données"
    )
parser.add_argument(
    "-c",
    "--ccn",
    action="store_true", 
    help="génère éléments pour version CCN (moins de détails)"
    )
parser.add_argument(
    "-i",
    "--acd",
    action="store_true", 
    help="génère éléments pour version ACD (tous les détails) (par défaut)"
    )
args = parser.parse_args()
Config.ROOT = args.root
Config.ccn = args.ccn

import activite
from activite import *
import officiel

REPERTOIRE_RESSOURCES = Config.ROOT + "/yaml/ressources"
REPERTOIRE_SAE = Config.ROOT + "/yaml/saes"
REPERTOIRE_LATEX_RESSOURCES = Config.ROOT + "/latex/ressources"
REPERTOIRE_LATEX_SAES = Config.ROOT + "/latex/saes"
REPERTOIRE_SYNTHESE = Config.ROOT + "/latex/synthese"
REPERTOIRE_MODELE_LATEX = Config.ROOT + "/python/latex"

# Chargement des ressources
print("> Etape 1 : Chargement des ressources")
fichiers_ressources = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_RESSOURCES+'/*.yml') ]
fichiers_ressources = sorted(fichiers_ressources) # tri par ordre alphabétique

ressources = {"S1": [], "S2": []}
for fichieryaml in fichiers_ressources:
    r = Ressource(REPERTOIRE_RESSOURCES + "/" + fichieryaml) # lecture du fichier
    sem = "S" + str(r.ressource["semestre"])
    ressources[sem].append(r)
# tri par code croissant
for sem in ressources:
    ressources[sem] = sorted(ressources[sem], key=lambda r: r.ressource["code"])

# Chargement des saé et des exemples
fichiers_definitifs = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_SAE+'/*.yml') ]
fichiers_saes = [f for f in fichiers_definitifs if "exemple" not in f]
fichiers_saes = sorted(fichiers_saes) # tri par ordre alphabétique
fichiers_exemples = [f for f in fichiers_definitifs if "exemple" in f]
fichiers_exemples = sorted(fichiers_exemples)

print("> Etape 2 : Chargement des chapeaux de SAEs")
saes = {"S1": [], "S2": []}
for fichieryaml in fichiers_saes:
    s = SAE(REPERTOIRE_SAE + "/" + fichieryaml)
    sem = "S" + str(s.sae["semestre"])
    saes[sem].append(s)

for sem in saes:
    saes[sem] = sorted(saes[sem], key=lambda s: s.sae["code"])

print("> Etape 3 : Chargement des exemples de SAEs")
exemples = {"S1" : {}, "S2" : {} }

for fichieryaml in fichiers_exemples:
    e = ExempleSAE(REPERTOIRE_SAE + "/" + fichieryaml)
    sem = "S" + str(e.exemple["semestre"])
    sae = e.exemple["code"]
    if sae not in exemples[sem]:
        exemples[sem][sae] = []
    exemples[sem][sae].append(e)


## Bilan : acs, volume, coefficient, abbréviations
print("> Etape 4 : Export latex des matrices d'apprentissages critiques/de volume horaire/de coefficients")
for sem in ["S1", "S2"]:
    M1 = activite.get_matrices_ac_ressource(saes, ressources, sem)
    chaine = activite.str_matrice(M1, saes, ressources, sem)
    #print(chaine)
    print(str_matrice(M1, saes, ressources, sem))

    chaine = latex.to_latex_matrice_acs(M1, saes, ressources, sem)
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_acs_vs_saes_ressources.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

    coeff1 = activite.get_matrices_coeffs(saes, ressources, sem)
    vol1 = activite.get_matrices_volumes(saes, ressources, sem)
    chaine = latex.to_latex_matrice_coeffs(vol1, coeff1, saes, ressources, sem)

    fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_coeffs_saes_ressources.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

    chaine = latex.str_latex_abbreviations()
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + "abbreviations.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

## Export latex divers (désactivé par défaut pour gagner du temps)
if not args.all:
    __LOGGER.warning(f"{sys.argv[0]}: reduced version (use -a to get full docs)")
else:
    # Export latex des ressources
    print("> Etape 5 : Export latex des ressources")
    for sem in ressources:
        for r in ressources[sem]:

            fichierlatex = REPERTOIRE_LATEX_RESSOURCES + "/" + "{}.tex".format(r.ressource["code"])
            contenu = r.to_latex(REPERTOIRE_MODELE_LATEX + "/modele_ressource.tex")
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")

    # Export latex des sae
    for sem in saes:
        for s in saes[sem]:
            fichierlatex = REPERTOIRE_LATEX_SAES + "/" + "{}.tex".format(s.sae["code"].replace("É", "E"))
            contenu = s.to_latex(REPERTOIRE_MODELE_LATEX +"/modele_sae.tex")
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")

    # Export latex des exemples
    for sem in exemples:
        for s in exemples[sem]:
            for (i, e) in enumerate(exemples[sem][s]):
                fichierlatex = REPERTOIRE_LATEX_SAES + "/" + "{}_exemple{}.tex".format(e.exemple["code"].replace("É", "E"), i+1)
                contenu = e.to_latex(REPERTOIRE_MODELE_LATEX + "/modele_exemple_sae.tex")
                with open(fichierlatex, "w", encoding="utf8") as fid:
                    fid.write(contenu)
                print(f"Export de {fichierlatex} ")