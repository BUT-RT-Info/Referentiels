"""
Analyse différents éléments du PN d'après les fichiers yaml
"""

import os
import glob
import argparse
import logging
import sys

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

import semestre
import pprint

REPERTOIRE_RESSOURCES_DEFINITIVES = Config.ROOT + "/yaml/ressources"
REPERTOIRE_SAE_DEFINITIVES = Config.ROOT + "/yaml/saes"

pn = {}
for sem in ["S1", "S2"]:
    pn[sem] = semestre.SemestrePN(sem, REPERTOIRE_RESSOURCES_DEFINITIVES,
                                        REPERTOIRE_SAE_DEFINITIVES)
    mat = pn[sem].get_matrices_dependances()
    # volume horaire du semestre
    heures = pn[sem].get_volumes_horaires_saes()
    print("SAE\n", heures)
    heures = pn[sem].get_volumes_horaires_ressources()
    print("Ressources\n", heures)

    vol_tags = pn[sem].get_volumes_horaires_tous_tags()
    pprint.pprint(vol_tags)
#    pprint.pprint(mat)

## Bilan : acs, volume, coefficient, abbréviations
# for sem in ["S1", "S2"]:
#    vol1 = ressource.get_matrices_volumes(saes, ressources, sem)

