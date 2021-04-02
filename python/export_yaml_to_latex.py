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
saes = {"S1": [], "S2": []}
for file in fichiers:
    fichieryaml = REPERTOIRE_RESSOURCES + "/" + file
    if file.startswith("R"): # si c'est une ressources
        r = Ressource(fichieryaml) # lecture du fichier
        sem = "S" + str(r.ressource["semestre"])
        ressources[sem].append(r)

# Eléments de tests
r1 = ressources["S1"][0]

temp1 = r1.ressource["contenu"]
output1 = pypandoc.convert_text(temp1, 'tex', format='md',
                               extra_args=['--atx-headers'])


print("ici")
# Export latex
for sem in ressources:
    for r in ressources[sem]:

        fichierlatex = REPERTOIRE_LATEX + "/" + "{}.tex".format(r.ressource["code"])
        contenu = r.to_latex()
        with open(fichierlatex, "w", encoding="utf8") as fid:
            fid.write(contenu)
        print(f"Export de {fichierlatex} ")