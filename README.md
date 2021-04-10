# Référentiel de formation R&T

## Installation sur Mac

Avec Anaconda:

    conda install pypandoc
    conda install ruamel
    conda install ruamel.yaml
    pip install docx2python

Sans Anaconda, remplacer `conda` par `pip`.

## Utilisation

Les sources sont les fichiers GoogleDoc (drive), réunis par un script Apps Scripts (`FusionneFiches`) qui permet d'obtenir deux documents: l'un réunissant les fiches ressources, l'autre les fiches SAÉ.

### Extraction des informations
Les fichiers `.docx` sont analysés pour créer les documents `yaml`. On a un script pour les ressource et un autre pour les SAÉ.

#### Ressources

    cd python
    python export_docx_to_yaml.py [nom du fichier docx]

par exemple:

    python export_docx_to_yaml.py import/compilation-ressources\ 2021-04-10T07_38_45.782Z.docx

#### SAÉs

    python export_sae_docx_to_yaml.py import/compilation-saes\ 2021-04-10T07_37_48.302Z.docx 


### Génération du LaTeX

    cd python
    python export_yaml_to_latex.py --full

### Génération de PDF

    cd latex
    pdflatex pn_formation
    pdflatex pn_formation

Le résultat est `pn_formation.pdf`.

