"""
Analyse différents éléments du PN d'après les fichiers yaml
"""

import os
import glob
import argparse
import logging
import sys

import semestre
from config import Config

__LOGGER = logging.getLogger(__name__)


parser = argparse.ArgumentParser(description="Analyse d'éléments du PN")
parser.add_argument(
    "-r", 
    "--root", 
    default="..", 
    help="repertoire de base (racine) pour chercher les fichiers de données"
    )
args = parser.parse_args()
Config.ROOT = args.root

import ressource


REPERTOIRE_RESSOURCES_DEFINITIVES = Config.ROOT + "/yaml/ressources"
REPERTOIRE_SAE_DEFINITIVES = Config.ROOT + "/yaml/saes"

# Chargement des ressources : depuis les versions définitives du répertoire yaml d'abord,
# puis dans python/export si manquantes
fichiers_ressources = [os.path.split(x)[1] for x in glob.glob(REPERTOIRE_RESSOURCES_DEFINITIVES+'/*.yml')]
fichiers_ressources = sorted(fichiers_ressources) # tri par ordre alphabétique
ressources = {"S1": [], "S2": []}
for fichieryaml in fichiers_ressources:
    r = ressource.Ressource(fichieryaml) # lecture du fichier
    sem = "S" + str(r.ressource["semestre"])
    ressources[sem].append(r)
# tri par code croissant
for sem in ressources:
    ressources[sem] = sorted(ressources[sem], key=lambda r: r.ressource["code"])

# Chargement des saé et des exemples
fichiers_definitifs = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_SAE_DEFINITIVES+'/*.yml') ]
fichiers_saes = [REPERTOIRE_SAE_DEFINITIVES + "/" + f for f in fichiers_definitifs if "exemple" not in f]
fichiers_saes = sorted(fichiers_saes) # tri par ordre alphabétique

saes = {"S1": [], "S2": []}
for fichieryaml in fichiers_saes:
    s = ressource.SAE(fichieryaml)
    sem = "S" + str(s.sae["semestre"])
    saes[sem].append(s)

for sem in saes:
    saes[sem] = sorted(saes[sem], key=lambda s: s.sae["code"])

## Bilan : acs, volume, coefficient, abbréviations
for sem in ["S1", "S2"]:
    vol1 = semestre.get_matrice_volumes_comp_vs_activites(saes, ressources, sem)

