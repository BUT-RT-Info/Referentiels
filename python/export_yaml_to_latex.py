import argparse
import logging
import sys

import semestre, officiel
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
args = parser.parse_args()
Config.ROOT = args.root

import activite
from activite import *

REPERTOIRE_RESSOURCES_DEFINITIVES = Config.ROOT + "/yaml/ressources"
REPERTOIRE_SAE_DEFINITIVES = Config.ROOT + "/yaml/saes"

REPERTOIRE_LATEX_RESSOURCES = Config.ROOT + "/latex/ressources"
REPERTOIRE_LATEX_SAES = Config.ROOT + "/latex/saes"
REPERTOIRE_SYNTHESE = Config.ROOT + "/latex/synthese"

# Chargement des ressources, des SAés et des exemples
pnofficiel = officiel.Officiel() # charge les données officielles
semestres = {"S1" : None,
             "S2" : None}
for sem in semestres:
    semestres[sem] = semestre.SemestrePN(sem,
                                         REPERTOIRE_RESSOURCES_DEFINITIVES,
                                         REPERTOIRE_SAE_DEFINITIVES,
                                         pnofficiel)

# Chargement des saé et des exemples

## Bilan : acs, volume, coefficient, abbréviations
for sem in semestres:
    M1 = semestres[sem].get_matrice_ac_vs_activites()
    chaine = semestres[sem].str_matrice_ac_vs_activites()
    # print(chaine)

    chaine = semestres[sem].to_latex_matrice_ac_vs_activites()
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_acs_vs_saes_ressources.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

    coeff1 = semestres[sem].get_matrice_coeffs_comp_vs_activites()
    vol1 = semestres[sem].get_matrice_volumes_comp_vs_activites()
    chaine = semestres[sem].to_latex_matrice_coeffs_et_volumes_comp_vs_activites()

    fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_coeffs_saes_ressources.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

    chaine = latex.to_latex_abbreviations(pnofficiel.DATA_ABBREVIATIONS)
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + "abbreviations.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

## Export latex divers (désactivé par défaut pour gagner du temps)
if not args.all:
    __LOGGER.warning(f"{sys.argv[0]}: reduced version (use -a to get full docs)")
else:
    # Export latex des ressources
    for sem in semestres:
        for code in semestres[sem].ressources:
            r = semestres[sem].ressources[code]
            fichierlatex = REPERTOIRE_LATEX_RESSOURCES + "/" + "{}.tex".format(r.yaml["code"])
            contenu = r.to_latex()
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")

    # Export latex des sae
    for sem in semestres:
        for code in semestres[sem].saes:
            s = semestres[sem].saes[code]
            fichierlatex = REPERTOIRE_LATEX_SAES + "/" + "{}.tex".format(s.yaml["code"].replace("É", "E"))
            contenu = s.to_latex()
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")

    # Export latex des exemples
    for sem in semestres:
        for s in semestres[sem].exemples:
            for (i, e) in enumerate(semestres[sem].exemples[s]):
                fichierlatex = REPERTOIRE_LATEX_SAES + "/" + "{}_exemple{}.tex".format(e.exemple["code"].replace("É", "E"), i+1)
                contenu = e.to_latex()
                with open(fichierlatex, "w", encoding="utf8") as fid:
                    fid.write(contenu)
                print(f"Export de {fichierlatex} ")