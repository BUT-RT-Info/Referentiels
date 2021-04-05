from ressource import *
import os
import pypandoc


import logging
__LOGGER = logging.getLogger(__name__)

REPERTOIRE_TEMP = "export"
REPERTOIRE_RESSOURCES_DEFINITIVES = "../yaml/ressources"
REPERTOIRE_SAE_DEFINITIVES = "../yaml/saes"
REPERTOIRE_LATEX_RESSOURCES = "../latex/ressources"
REPERTOIRE_LATEX_SAES = "../latex/saes"

# Chargement des ressources : depuis les versions définitives du répertoire yaml d'abord,
# puis dans python/export si manquantes
fichiers_definitifs = os.listdir(REPERTOIRE_RESSOURCES_DEFINITIVES)
fichiers_temp = os.listdir(REPERTOIRE_TEMP)
fichiers_ressources = [REPERTOIRE_RESSOURCES_DEFINITIVES + "/" + f for f in fichiers_definitifs]
for f in fichiers_temp:
    if f not in fichiers_definitifs and f.startswith("R"):
        fichiers_ressources.append(REPERTOIRE_TEMP + "/" + f)
fichiers_ressources = sorted(fichiers_ressources) # tri par ordre alphabétique

ressources = {"S1": [], "S2": []}
for fichieryaml in fichiers_ressources:
    r = Ressource(fichieryaml) # lecture du fichier
    sem = "S" + str(r.ressource["semestre"])
    ressources[sem].append(r)

# Chargement des saé et des exemples
fichiers_definitifs = os.listdir(REPERTOIRE_SAE_DEFINITIVES)
fichiers_temp = os.listdir(REPERTOIRE_TEMP)
fichiers_saes = [REPERTOIRE_SAE_DEFINITIVES + "/" + f for f in fichiers_definitifs if "exemple" not in f]
fichiers_exemples = [REPERTOIRE_SAE_DEFINITIVES + "/" + f for f in fichiers_definitifs if "exemple" in f]
for f in fichiers_temp:
    if f not in fichiers_definitifs and f.startswith("S"):
        if "exemple" not in f:
            fichiers_saes.append(REPERTOIRE_TEMP + "/" + f)
        elif "exemple" in f:
            fichiers_exemples.append(REPERTOIRE_TEMP + "/" + f)
fichiers_saes = sorted(fichiers_saes) # tri par ordre alphabétique
fichiers_exemples = sorted(fichiers_exemples)

saes = {"S1": [], "S2": []}
for fichieryaml in fichiers_saes:
    s = SAE(fichieryaml)
    sem = "S" + str(s.sae["semestre"])
    saes[sem].append(s)


exemples = {"S1" : {}, "S2" : {} }

for fichieryaml in fichiers_exemples:
    e = ExempleSAE(fichieryaml)
    sem = "S" + str(e.exemple["semestre"])
    sae = e.exemple["code"]
    if sae not in exemples[sem]:
        exemples[sem][sae] = []
    exemples[sem][sae].append(e)


print("ici")
# Export latex des ressources
if True:
    for sem in ressources:
        for r in ressources[sem]:

            fichierlatex = REPERTOIRE_LATEX_RESSOURCES + "/" + "{}.tex".format(r.ressource["code"])
            contenu = r.to_latex()
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")

# Export latex des sae
if True:
    for sem in saes:
        for s in saes[sem]:

            fichierlatex = REPERTOIRE_LATEX_SAES + "/" + "{}.tex".format(s.sae["code"].replace("É", "E"))
            contenu = s.to_latex()
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")

# Export latex des exemples
for sem in exemples:
    for s in exemples[sem]:
        for (i, e) in enumerate(exemples[sem][s]):
            fichierlatex = REPERTOIRE_LATEX_SAES + "/" + "{}_exemple{}.tex".format(e.exemple["code"].replace("É", "E"), i+1)
            contenu = e.to_latex()
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")