import argparse
import logging
import sys
import os

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

# LIMIT_TO = ["SAÉ3.1"]
LIMIT_TO = [] # "SAÉ6.6"] #"R3.02"]

import rpn.semestre, rofficiel.officiel, rpn.activite

REPERTOIRE_RESSOURCES_DEFINITIVES = Config.ROOT + "/yaml/ressources"
REPERTOIRE_SAE_DEFINITIVES = Config.ROOT + "/yaml/saes"

REPERTOIRE_LATEX_RESSOURCES = Config.ROOT + "/latex/ressources"
REPERTOIRE_LATEX_SAES = Config.ROOT + "/latex/saes"
REPERTOIRE_SYNTHESE = Config.ROOT + "/latex/synthese"
REPERTOIRE_MODELE_LATEX = Config.ROOT + "/python/latex"

# Chargement des ressources, des SAés et des exemples
pnofficiel = rofficiel.officiel.Officiel() # charge les données officielles
semestres = {"S{}".format(d) : None for d in range(1, 7)}
# semestres = {}
semestres["SC"] = None
print("***Etape 1*** Chargement des yaml")
for sem in semestres:
    print(f" > Semestre {sem}")
    semestres[sem] = rpn.semestre.SemestrePN(sem,
                                         REPERTOIRE_RESSOURCES_DEFINITIVES,
                                         REPERTOIRE_SAE_DEFINITIVES,
                                         pnofficiel)

# Chargement des saé et des exemples


## Bilan : acs, volume, coefficient, abbréviations
for sem in semestres:
    ## Fichiers d'inclusion des semestres
    chaine = semestres[sem].to_latex_description_semestres()
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"referentiel_{sem}.tex"
    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(chaine)
    print(f"Export de {fichierlatex}")

    ## Tableurs lisant les SAEs et les ressources
    # Les SAEs
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + "liste_saes_{}.tex".format(sem)
    contenu = semestres[sem].to_latex_liste_activites(semestres[sem].saes_par_parcours)

    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(contenu)
    print(f"Export de {fichierlatex} ")

    # Les ressources
    fichierlatex = REPERTOIRE_SYNTHESE + "/" + "liste_ressources_{}.tex".format(sem)
    contenu = semestres[sem].to_latex_liste_activites(semestres[sem].ressources_par_parcours)

    with open(fichierlatex, "w", encoding="utf8") as fid:
        fid.write(contenu)
    print(f"Export de {fichierlatex} ")

    ## Matrices ACS vs saes & ressources
    if sem in ["S1", "S2"]:
        chaine = semestres[sem].to_latex_matrice_ac_vs_activites()
        fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_acs_vs_saes_ressources.tex"
        with open(fichierlatex, "w", encoding="utf8") as fid:
            fid.write(chaine)
        print(f"Export de {fichierlatex}")
    else:
        for parcours in rofficiel.officiel.PARCOURS:
            if not semestres[sem].est_complementaire():
                chaine = semestres[sem].to_latex_matrice_ac_vs_activites(parcours=parcours)
                fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_{parcours}_acs_vs_saes_ressources.tex"
                with open(fichierlatex, "w", encoding="utf8") as fid:
                    fid.write(chaine)
                print(f"Export de {fichierlatex}")

    ## Matrices dépendances saes & ressources
    if not semestres[sem].est_complementaire():
        chaine = semestres[sem].to_latex_matrice_dependance()
        fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_dependances_saes_vs_ressources.tex"
        with open(fichierlatex, "w", encoding="utf8") as fid:
            fid.write(chaine)
        print(f"Export de {fichierlatex}")

    # Matrice textuelle
    # (M1, acs_du_semestre, codes_activites) = semestres[sem].get_matrice_ac_vs_activites()
    # chaine = semestres[sem].str_matrice_vs_activites(M1, acs_du_semestre, codes_activites)
    # print(chaine)

    ## Matrice des acs vs saes et ressources
    if not semestres[sem].est_complementaire():
        fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_acs_vs_saes_ressources.tex"
        with open(fichierlatex, "w", encoding="utf8") as fid:
             fid.write(chaine)
        print(f"Export de {fichierlatex}")


    # coeff1 = semestres[sem].get_matrice_coeffs_comp_vs_activites()
    # vol1 = semestres[sem].get_matrice_volumes_comp_vs_activites()
    # chaine = semestres[sem].to_latex_matrice_coeffs_et_volumes_comp_vs_activites()

    # fichierlatex = REPERTOIRE_SYNTHESE + "/" + f"{sem}_coeffs_saes_ressources.tex"
    # with open(fichierlatex, "w", encoding="utf8") as fid:
    #    fid.write(chaine)
    # print(f"Export de {fichierlatex}")

    # chaine = rpn.latex.to_latex_abbreviations(pnofficiel.DATA_ABBREVIATIONS)
    # fichierlatex = REPERTOIRE_SYNTHESE + "/" + "abbreviations.tex"
    # with open(fichierlatex, "w", encoding="utf8") as fid:
    #    fid.write(chaine)
    # print(f"Export de {fichierlatex}")

## Liste des ressources/SAEs par semestre et parcours
for parcours in rofficiel.officiel.PARCOURS:
    print("***", parcours)
    for sem in semestres: # pour chaque semestre
        print(" > Semestre", sem)
        if not semestres[sem].est_complementaire():
            codes_ressources = semestres[sem].tri_codes_ressources(parcours=parcours)
            # print(codes_ressources)
            for c in codes_ressources:
                chaine = ""
                chaine += semestres[sem].ressources[c].yaml["nom"]
                chaine += " (~{}h)".format(semestres[sem].ressources[c].yaml["heures_formation"])
                chaine += " : " + semestres[sem].ressources[c].yaml["motscles"]
            # print(chaine)


## Export latex divers (désactivé par défaut pour gagner du temps)
if not args.all:
    __LOGGER.warning(f"{sys.argv[0]}: reduced version (use -a to get full docs)")
else:
    # Création des listes de synthèse
    for sem in semestres:
        if not os.path.exists(REPERTOIRE_SYNTHESE):
            os.mkdir(REPERTOIRE_SYNTHESE)

    inclusion = []
    # Création des répertoires
    for sem in semestres:
        if not os.path.exists(REPERTOIRE_LATEX_RESSOURCES + "/" + sem):
            os.mkdir(REPERTOIRE_LATEX_RESSOURCES + "/" + sem)

    # Export latex des ressources
    for sem in semestres:
        for code in semestres[sem].ressources:
            if not LIMIT_TO or code in LIMIT_TO:
                r = semestres[sem].ressources[code]
                fichierlatex = REPERTOIRE_LATEX_RESSOURCES + "/" + sem + "/" + "{}.tex".format(r.yaml["code"])
                contenu = r.to_latex()

                with open(fichierlatex, "w", encoding="utf8") as fid:
                    fid.write(contenu)
                print(f"Export de {fichierlatex} ")
                # inclusion.append("ressources/" + sem + "/" + "{}.tex".format(r.yaml["code"]))

    # Création des répertoires
    for sem in semestres:
        if not os.path.exists(REPERTOIRE_LATEX_SAES + "/" + sem):
            os.mkdir(REPERTOIRE_LATEX_SAES + "/" + sem)

    # Export latex des sae
    for sem in semestres:
        for code in semestres[sem].saes:
            if not LIMIT_TO or code in LIMIT_TO:
                s = semestres[sem].saes[code]
                fichierlatex = REPERTOIRE_LATEX_SAES + "/" + sem + "/" + "{}.tex".format(s.yaml["code"].replace("É", "E"))
                contenu = s.to_latex()

                with open(fichierlatex, "w", encoding="utf8") as fid:
                    fid.write(contenu)
                print(f"Export de {fichierlatex} ")
                inclusion.append("saes/" + sem + "/" + "{}.tex".format(s.yaml["code"]))

    # Export latex des exemples
    # for sem in semestres:
    #    for s in semestres[sem].exemples:
    #        for (i, e) in enumerate(semestres[sem].exemples[s]):
    #            fichierlatex = REPERTOIRE_LATEX_SAES + "/" + "{}_exemple{}.tex".format(e.exemple["code"].replace("É", "E"), i+1)
    #            contenu = e.to_latex(REPERTOIRE_MODELE_LATEX + "/modele_exemple_sae.tex")
    #            with open(fichierlatex, "w", encoding="utf8") as fid:
    #                fid.write(contenu)
    #            print(f"Export de {fichierlatex} ")

    for val in inclusion:
        pass
        # print("\\input{%s} \\newpage" % (val.replace("É", "E")))