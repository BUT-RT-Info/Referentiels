
import os
from ressource import *

import logging
__LOGGER = logging.getLogger(__name__)

# Chargement des ressources
REPERTOIRE_RESSOURCES = "export"
REPERTOIRE_LATEX = "../latex/ressources"
fichiers = os.listdir(REPERTOIRE_RESSOURCES)
fichiers = sorted(fichiers) # tri par ordre alphabétique

ressources = {"S1": [], "S2": []}
for file in fichiers:
    fichieryaml = REPERTOIRE_RESSOURCES + "/" + file
    r = Ressource(fichieryaml) # lecture du fichier
    sem = "S" + str(r.ressource["semestre"])
    ressources[sem].append(r)

# Export latex
for sem in ressources:
    for r in ressources[sem]:
        fichierlatex = REPERTOIRE_LATEX + "/" + "{}.tex".format(r.ressource["code"])
        contenu = r.str_to_latex()
        with open(fichierlatex, "w", encoding="utf8") as fid:
            fid.write(contenu)
        print(f"Export de {fichierlatex} ")