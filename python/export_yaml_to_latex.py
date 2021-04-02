from ressource import Ressource
from ressourcedocx import *
import pypandoc


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

r1 = ressources["S1"][0]
r2 = ressources["S1"][1]

temp1 = r1.ressource["contenu"]
temp2 = r2.ressource["contenu"]

output1 = pypandoc.convert_text(temp1, 'tex', format='md',
                               extra_args=['--atx-headers'])

output2 = pypandoc.convert_text(temp2, 'tex', format='md',
                               extra_args=['--atx-headers'])

print("ici")
# Export latex
for sem in ressources:
    for r in ressources[sem]:
        if r.ressource["nom"] == "R112":
            print("ici")
        fichierlatex = REPERTOIRE_LATEX + "/" + "{}.tex".format(r.ressource["code"])
        contenu = r.str_to_latex()
        with open(fichierlatex, "w", encoding="utf8") as fid:
            fid.write(contenu)
        print(f"Export de {fichierlatex} ")