from ressource import Ressource, SAE
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
    if file.startswith("R"): # si c'est une ressources
        r = Ressource(fichieryaml) # lecture du fichier
        sem = "S" + str(r.ressource["semestre"])
        ressources[sem].append(r)

# Chargement des ressources
REPERTOIRE_SAE = "export"
REPERTOIRE_LATEX = "../latex/saes"
fichiers = os.listdir(REPERTOIRE_RESSOURCES)
fichiers = sorted(fichiers) # tri par ordre alphabétique

saes = {"S1": [], "S2": []}
for file in fichiers:
    fichieryaml = REPERTOIRE_RESSOURCES + "/" + file
    if file.startswith("S"): # si c'est une sae
        s = SAE(fichieryaml)
        sem = "S" + str(s.sae["semestre"])
        saes[sem].append(s)

# Eléments de tests
r1 = ressources["S1"][0]

temp1 = r1.ressource["contenu"]
output1 = pypandoc.convert_text(temp1, 'tex', format='md',
                               extra_args=['--atx-headers'])


print("ici")
# Export latex des ressources
if False:
    for sem in ressources:
        for r in ressources[sem]:

            fichierlatex = REPERTOIRE_LATEX + "/" + "{}.tex".format(r.ressource["code"])
            contenu = r.to_latex()
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")

# Export latex des ressources
for sem in saes:
    for s in saes[sem]:

        fichierlatex = REPERTOIRE_LATEX + "/" + "{}.tex".format(s.sae["code"].replace("É", "E"))
        contenu = s.to_latex()
        with open(fichierlatex, "w", encoding="utf8") as fid:
            fid.write(contenu)
        print(f"Export de {fichierlatex} ")