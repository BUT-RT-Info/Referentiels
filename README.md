# Référentiel de formation R&T

## Installation sur Mac

Avec Anaconda:

    conda install pypandoc
    conda install ruamel
    conda install ruamel.yaml
    pip install docx2python
    pip install Jinja2

Sans Anaconda, remplacer `conda` par `pip`.

## Utilisation

OLD : Les sources sont les fichiers GoogleDoc (drive), réunis par un script Apps Scripts (`FusionneFiches`) qui permet d'obtenir deux documents : l'un réunissant les fiches ressources, l'autre les fiches SAÉ.

NEW: Les sources sont les fichiers GooglDoc (drive) téléchargés en local dans le répertoire google/ en partant du document de synthèse BUT-RT-S1-S6.xlsx en utilisant les liens de la première feuille et en utilisant l'API Google Drive. 

Le téléchargement suppose de configurer l'OAuth sur un compte google par le biais d'une application déclarée sur cloud.google.

### Extraction des informations

Les fichiers `.docx` sont analysés pour créer les documents `yaml` (dans un `REPERTOIRE_EXPORT` configurable), avec un script pour les ressources et un autre pour les SAÉ.

L'analyse s'appuie sur les fichiers `python/pn/ressources.yml` et `python/pn/saes.yml` qui traduisent le découpage en ressources/SAés et les noms actés le GT-BUT (cf. tableaur google BUT S1-S6).

#### Ressources

    cd python
    python export_ressources_docx_to_yaml.py -o REPERTOIRE_EXPORT [nom du fichier docx]

Par exemple:

    python export_ressources_docx_to_yaml.py import/compilation-ressources.docx

#### SAÉs

    cd python
    python export_sae_docx_to_yaml.py -o REPERTOIRE_EXPORT [nom du fichier docx] 

Par exemple:

    python export_sae_docx_to_yaml.py import/compilation-saes.docx 


### Génération du LaTeX

Les documents `yaml` décrivant les ressources et les SAés créés (dans un `REPERTOIRE_EXPORT`) sont retraités pour générer différents fichiers latex nécessaires à la compilation du PN en PDF

    cd python
    python export_yaml_to_latex.py -a

Les fichiers latex se basent sur 3 modèles `python/pn/modele_ressource.tex`,
`python/pn/modele_sae.tex`, `python/pn/modele_exemple_sae.tex`.

Le script suppose que l'arborescence suivante :

    python
        |- codes python ...
    yaml
        |- ressources
        |   |- les yaml de ressources
        |- saes
            |- les yaml de saes
    latex
        |- ressources
        |   |- les tex de ressources
        |- saes
        |   |- les tex de saes
        |- synthese
        |   |- les tex des tableaux de synthèse (matrices AC/comp)

### Génération de PDF

    cd latex
    pdflatex pn_formation
    pdflatex pn_formation

Le résultat est `pn_formation.pdf`.

### Génération du Html

    cd html
    python export_yaml_to_html.py

## Organisation des fichiers

    html/export   fichiers html générés par export_yaml_to_html.py à partir des yaml
    python/import   fichiers docx à traiter
    python/export   fichier yaml générés par export_docx_to_yaml.py à partir des docx
    yaml/ressources versions éditées manuellement ??
    latex/ressources    fiches au format LaTeX générées par export_yaml_to_latex.py
