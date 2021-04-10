import ressource
from ressource import *
import os
import officiel

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
# tri par code croissant
for sem in ressources:
    ressources[sem] = sorted(ressources[sem], key=lambda r: r.ressource["code"])

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

for sem in saes:
    saes[sem] = sorted(saes[sem], key=lambda s: s.sae["code"])

exemples = {"S1" : {}, "S2" : {} }

for fichieryaml in fichiers_exemples:
    e = ExempleSAE(fichieryaml)
    sem = "S" + str(e.exemple["semestre"])
    sae = e.exemple["code"]
    if sae not in exemples[sem]:
        exemples[sem][sae] = []
    exemples[sem][sae].append(e)


## Bilan : acs, volume, coefficient, abbréviations
for sem in ["S1", "S2"]:
    M1 = ressource.get_matrices_ac_ressource(saes, ressources, sem)
    chaine = ressource.str_matrice(M1, saes, ressources, sem)
    #print(chaine)
    print(str_matrice(M1, saes, ressources, sem))

    chaine = ressource.to_latex_matrice_acs(M1, saes, ressources, sem)
    REPERTOIRE_SYNTHESE = "../latex/synthese"
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_acs_vs_saes_ressources.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

    coeff1 = ressource.get_matrices_coeffs(saes, ressources, sem)
    vol1 = ressource.get_matrices_volumes(saes, ressources, sem)
    chaine = ressource.to_latex_matrice_coeffs(vol1, coeff1, saes, ressources, sem)

    fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_coeffs_saes_ressources.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

    chaine = ressource.str_latex_abbreviations()
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + "abbreviations.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

## Export latex divers
if True:
    # Export latex des ressources
    for sem in ressources:
        for r in ressources[sem]:

            fichierlatex = REPERTOIRE_LATEX_RESSOURCES + "/" + "{}.tex".format(r.ressource["code"])
            contenu = r.to_latex()
            with open(fichierlatex, "w", encoding="utf8") as fid:
                fid.write(contenu)
            print(f"Export de {fichierlatex} ")

    # Export latex des sae
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