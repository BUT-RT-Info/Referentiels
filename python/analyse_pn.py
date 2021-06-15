"""
Analyse différents éléments du PN d'après les fichiers yaml
"""

import os
import glob
import argparse
import logging
import sys
import matplotlib.pyplot

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

tags = ["anglais", "communication", "maths-physique", "PPP-portfolio", "réseau", "télécom", "informatique"]

pn = {}
vol_tags = {}
for sem in ["S1", "S2"]:
    pn[sem] = semestre.SemestrePN(sem, REPERTOIRE_RESSOURCES_DEFINITIVES,
                                        REPERTOIRE_SAE_DEFINITIVES)
    mat = pn[sem].get_matrices_dependances()

    # volume horaire du semestre
    heures_saes = pn[sem].get_volumes_horaires_saes()
    print("SAE\n", heures_saes)
    heures_ressources = pn[sem].get_volumes_horaires_ressources()
    print("Ressources\n", heures_ressources)


    vol_tags[sem] = pn[sem].get_volumes_horaires_tous_tags(cible="ressources")
    pprint.pprint(vol_tags)

    total = sum([vol_tags[tag] if tag in vol_tags else 0 for tag in tags])
    if total != heures_ressources[0]:
        print("Problème dans le calcul des heures tags")

## Heures par semestre
## **************
semestres_dut_encadrees = [480, 540, 510, 270]
semestres_dut_projet = [60, 60, 90, 90]

semestres_but_encadrees = [440, 465, 435, 240, 340, 80]
semestres_but_projet = [80, 90, 125, 55, 170, 80]

semestres_lpro_encadrees = [300, 150]
semestres_lpro_projet = [50, 90]

fig = matplotlib.pyplot.figure()
matplotlib.pyplot.grid(ls="dashed")
width = 0.4
### Les heures encadrées
abscisses = range(len(semestres_dut_encadrees))
p1 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], semestres_dut_encadrees, width=width,
                           color="lightblue", edgecolor='black')
abscisses = range(len(semestres_but_encadrees))
p3 = matplotlib.pyplot.bar([a + width/2 for a in abscisses], semestres_but_encadrees, width=width,
                           color="lightyellow", edgecolor='black')
abscisses = [4, 5]
p4 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], semestres_lpro_encadrees, width=width,
                           color="peachpuff", edgecolor='black')
### Un slot pour legend
p5 = matplotlib.pyplot.bar([- width/2], [semestres_dut_projet[0]], width=width,
                           bottom=[semestres_dut_encadrees[0]],
             color='white', edgecolor='black', hatch="//")
### Les projets
abscisses = range(len(semestres_dut_encadrees))
p2 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], semestres_dut_projet, width=width,
                           bottom=semestres_dut_encadrees,
             color='lightblue', edgecolor='black', hatch="//")
abscisses = range(len(semestres_but_encadrees))
p4 = matplotlib.pyplot.bar([a + width/2 for a in abscisses], semestres_but_projet, width=width,
                           bottom=semestres_but_encadrees,
                           color="lightyellow", edgecolor='black', hatch="//")
abscisses = [4, 5]
p4 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], semestres_lpro_projet, width=width,
                           bottom=semestres_lpro_encadrees,
                           color="peachpuff", edgecolor='black', hatch="//")

matplotlib.pyplot.title('Heures de formation encadrées et heures projet par semestre')
abscisses = range(len(semestres_but_encadrees))
matplotlib.pyplot.xticks(abscisses, ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'], rotation=45)
matplotlib.pyplot.legend(labels=['DUT', 'BUT', '~LPro', 'h. projet'])
matplotlib.pyplot.ylabel("Heures")
matplotlib.pyplot.axis([-1, 6, 0, 700])
matplotlib.pyplot.tight_layout()

# Ajout des heures
abscisses = range(len(semestres_dut_encadrees))
for (i, val) in enumerate(semestres_dut_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] - width/2
    y0 = 4
    val = semestres_dut_encadrees[i] + semestres_dut_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(semestres_dut_projet[i]) + "\n+\n" + str(semestres_dut_encadrees[i]),
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontstyle="italic")
abscisses = range(len(semestres_but_encadrees))
for (i, val) in enumerate(semestres_but_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] + width/2
    y0 = 4
    val = semestres_but_encadrees[i] + semestres_but_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(semestres_but_projet[i]) + "\n+\n" + str(semestres_but_encadrees[i]),
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontweight="bold")
abscisses = [4, 5]
for (i, val) in enumerate(semestres_lpro_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] - width/2
    y0 = 4
    val = semestres_lpro_encadrees[i] + semestres_lpro_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(semestres_lpro_projet[i]) + "\n+\n" + str(semestres_lpro_encadrees[i]),
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontstyle="italic")

####################################################
tags = ["anglais", "expr-comm.", "PPP-Portfolio\nentreprise", "maths",
        "reseau", "télécom\nphysique",
        "informatique", "saes-projet", "parcours"]

## -> 1ère année
dut_1A_encadrees = [75, 60, 30, 120, 240, 270, 180, 45, 0]
dut_1A_projet = [0]*7 + [120] + [0]
nbre_heures_dut = sum(semestres_dut_encadrees[0:1])
dut_1A_pourcentage_encadrees = [int(val/nbre_heures_dut*100) for val in dut_1A_encadrees]
but_1A_encadrees = [75, 60, 30,
                    120, 220, 159, 137, 99, 0]
but_1A_projet = [0, 0, 6, 0, 0, 0, 0, 164, 0]
nbre_heures_but = sum(semestres_but_encadrees[0:1])
but_1A_pourcentage_encadrees = [int(val/nbre_heures_but*100) for val in but_1A_encadrees]

# Diagramme bâton
fig = matplotlib.pyplot.figure()
matplotlib.pyplot.grid(ls="dashed")
width = 0.4
abscisses = range(len(tags))
p1 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_1A_encadrees, width=width,
                      color="lightblue", edgecolor='black')
p3 = matplotlib.pyplot.bar([a + width/2 for a in abscisses], but_1A_encadrees, width=width,
                      color="lightyellow", edgecolor='black')
# Pour les heures projet
p5 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_1A_projet, width=width,
                           bottom=dut_1A_encadrees,
                      color="white", edgecolor='black', hatch="//")
p1 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_1A_projet, width=width,
                           bottom=dut_1A_encadrees,
                      color="lightblue", edgecolor='black', hatch="//")
p4 = matplotlib.pyplot.bar([a + width/2 for a in abscisses], but_1A_projet, width=width,
                      bottom=but_1A_encadrees,
                      color="lightyellow", edgecolor='black', hatch="//"
                      )
matplotlib.pyplot.title('Répartition par thème en 1ère année'.format(sem))
matplotlib.pyplot.xticks(abscisses, tags, rotation=45)
matplotlib.pyplot.legend(labels=['DUT', 'BUT', 'h. projet'])
matplotlib.pyplot.axis([-1, len(tags), 0, 300])
# Ajout des %
for (i, val) in enumerate(dut_1A_pourcentage_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] - width/2
    y0 = 4
    val = dut_1A_encadrees[i] + dut_1A_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(dut_1A_pourcentage_encadrees[i]) + "%",
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontstyle="italic")

for (i, val) in enumerate(but_1A_pourcentage_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] + width/2 + 0.1
    y0 = 12
    val = but_1A_encadrees[i] + but_1A_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(but_1A_pourcentage_encadrees[i]) + "%",
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontweight='bold')
matplotlib.pyplot.tight_layout()


## -> 2ème année
dut_2A_encadrees = [60, 45, 75, 30, 210, 210, 120, 30, 0]
dut_2A_projet = [0]*7 + [180] + [0]
nbre_heures_dut = sum(semestres_dut_encadrees[2:3])
dut_2A_pourcentage_encadrees = [int(val/nbre_heures_dut*100) for val in dut_2A_encadrees]
but_2A_encadrees = [60, 30, 45, 45, 135, 180, 90, 0, 90]
but_2A_projet = [0, 0, 6, 0, 0, 0, 0, 180, 0]
nbre_heures_but = sum(semestres_dut_encadrees[3:4])
but_2A_pourcentage_encadrees = [int(val/nbre_heures_but*100) for val in but_2A_encadrees]

# Diagramme bâton
fig = matplotlib.pyplot.figure()
matplotlib.pyplot.grid(ls="dashed")
width = 0.4
abscisses = range(len(tags))
p1 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_2A_encadrees, width=width,
                      color="lightblue", edgecolor='black')
p3 = matplotlib.pyplot.bar([a + width/2 for a in abscisses], but_2A_encadrees, width=width,
                      color="lightyellow", edgecolor='black')
# Pour les heures projet
p5 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_2A_projet, width=width,
                           bottom=dut_2A_encadrees,
                      color="white", edgecolor='black', hatch="//")
p1 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_2A_projet, width=width,
                           bottom=dut_2A_encadrees,
                      color="lightblue", edgecolor='black', hatch="//")
p4 = matplotlib.pyplot.bar([a + width/2 for a in abscisses], but_2A_projet, width=width,
                      bottom=but_2A_encadrees,
                      color="lightyellow", edgecolor='black', hatch="//"
                      )
matplotlib.pyplot.title('Répartition (prévisionnelle) par thème en 2ème année')
matplotlib.pyplot.xticks(abscisses, tags, rotation=45)
matplotlib.pyplot.legend(labels=['DUT', 'BUT', 'h. projet'], loc="upper left")
matplotlib.pyplot.axis([-1, len(tags), 0, 300])
# Ajout des %
for (i, val) in enumerate(dut_2A_pourcentage_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] - width/2
    y0 = 4
    val = dut_2A_encadrees[i] + dut_2A_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(dut_2A_pourcentage_encadrees[i]) + "%",
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontstyle="italic")

for (i, val) in enumerate(but_2A_pourcentage_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] + width/2 + 0.1
    y0 = 12
    val = but_2A_encadrees[i] + but_2A_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(but_2A_pourcentage_encadrees[i]) + "%",
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontweight='bold')
matplotlib.pyplot.tight_layout()

### 1+2 A
dut_encadrees = [dut_1A_encadrees[i] + dut_2A_encadrees[i] for i in range(len(dut_1A_encadrees))]
dut_projet = [dut_1A_projet[i] + dut_2A_projet[i] for i in range(len(dut_1A_encadrees))]
nbre_heures_dut = sum(semestres_dut_encadrees[0:3])
but_encadrees = [but_1A_encadrees[i]+but_2A_encadrees[i] for i in range(len(dut_1A_encadrees))]
but_projet = [but_1A_projet[i]+but_2A_projet[i] for i in range(len(dut_1A_encadrees))]
nbre_heures_but = sum(semestres_but_encadrees[0:3])
dut_pourcentage_encadrees = [int(val/nbre_heures_dut*100) for val in dut_encadrees]
but_pourcentage_encadrees = [int(val/nbre_heures_but*100) for val in but_encadrees]

# Diagramme bâton
fig = matplotlib.pyplot.figure()
matplotlib.pyplot.grid(ls="dashed")
width = 0.4
abscisses = range(len(tags))
p1 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_encadrees, width=width,
                      color="lightblue", edgecolor='black')
p3 = matplotlib.pyplot.bar([a + width/2 for a in abscisses], but_encadrees, width=width,
                      color="lightyellow", edgecolor='black')
# Pour les heures projet
p5 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_projet, width=width,
                           bottom=dut_encadrees,
                      color="white", edgecolor='black', hatch="//")
p1 = matplotlib.pyplot.bar([a - width/2 for a in abscisses], dut_projet, width=width,
                           bottom=dut_encadrees,
                      color="lightblue", edgecolor='black', hatch="//")
p4 = matplotlib.pyplot.bar([a + width/2 for a in abscisses], but_projet, width=width,
                      bottom=but_encadrees,
                      color="lightyellow", edgecolor='black', hatch="//"
                      )
matplotlib.pyplot.title('Répartition (prévisionnelle) par thème en 1A et 2A')
matplotlib.pyplot.xticks(abscisses, tags, rotation=45)
matplotlib.pyplot.ylabel('Heures encadrées / projet')
matplotlib.pyplot.legend(labels=['DUT', 'BUT', 'h. projet'], loc="upper left")
matplotlib.pyplot.axis([-1, len(tags), 0, 600])
# Ajout des %
for (i, val) in enumerate(dut_pourcentage_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] - width/2
    y0 = 4
    val = dut_encadrees[i] + dut_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(dut_pourcentage_encadrees[i]) + "%",
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontstyle="italic")

for (i, val) in enumerate(but_pourcentage_encadrees): # pour chaque pourcentage
    x0 = abscisses[i] + width/2 + 0.1
    y0 = 12
    val = but_encadrees[i] + but_projet[i] + 10
    matplotlib.pyplot.text(x0, val, str(but_pourcentage_encadrees[i]) + "%",
                           horizontalalignment='center',
                           color="black",
                           fontsize=7, fontweight='bold')
matplotlib.pyplot.tight_layout()

## Pie DUT
fig = matplotlib.pyplot.figure()
matplotlib.pyplot.pie(dut_encadrees[:-1], labels=tags[:-1], autopct='%d%%',
        startangle=90)
matplotlib.pyplot.title('Répartition par thème du DUT')

fig = matplotlib.pyplot.figure()
matplotlib.pyplot.pie(but_encadrees, labels=tags, autopct='%d%%',
        startangle=90)
matplotlib.pyplot.title('Répartition (prévisionnelle) par thème du BUT1/2')
matplotlib.pyplot.show()

