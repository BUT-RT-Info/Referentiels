import os
import sys
import argparse
import glob

sys.path.insert(0,"../python")
from config import Config
from jinja2 import Template, Environment, FileSystemLoader

# Description des arguments possibles du programme
parser = argparse.ArgumentParser(description="Conversion des YAML en HTML")
parser.add_argument(
    "-r",
    "--root",
    default="..",
    help="repertoire de base (racine) pour chercher les fichiers de données"
)
args = parser.parse_args()
Config.ROOT = args.root

import ressource
from ressource import *

# Chemins des différents dossiers
REPERTOIRE_TEMP = Config.ROOT + "/python/export"
REPERTOIRE_RESSOURCES_DEFINITIVES = Config.ROOT + "/yaml/ressources"
REPERTOIRE_SAE_DEFINITIVES = Config.ROOT + "/yaml/saes"
REPERTOIRE_HTML = Config.ROOT + "/html/export"

# Créer le dossier html/export s'il n'existe pas
if not os.path.exists(REPERTOIRE_HTML):
    os.makedirs(REPERTOIRE_HTML)

# Chargement des ressources : depuis les versions définitives du répertoire yaml d'abord,
# puis dans python/export si manquantes
fichiers_definitifs = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_RESSOURCES_DEFINITIVES+'/*.yml') ] #nom fichier dans yaml/ressources
fichiers_temp = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_TEMP+'/*.yml') ] #nom fichier dans python/export
fichiers_ressources = [REPERTOIRE_RESSOURCES_DEFINITIVES + "/" + f for f in fichiers_definitifs] # chemins de fichier ressources YAML
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
fichiers_definitifs = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_SAE_DEFINITIVES+'/*.yml') ]
fichiers_temp = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_TEMP+'/*.yml') ]
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

CHEMIN_TEMPLATE = Config.ROOT + "/html"
# Création de l'environnement pour charger les templates
env = Environment(trim_blocks=True, lstrip_blocks=True, loader=FileSystemLoader(CHEMIN_TEMPLATE))
# Template de chaque pages ressources, saes, exemples
template = env.from_string("""
    {% extends "base.html" %}
    {% block title %}{{data.code}} - {{data.nom}}{{data.titre}}{% endblock %}
    {% block content %}
            <nav class="level is-mobile">
                <div class="level-left">
                    <div class="level-item">
                        <a class="button is-primary{% if not precedent %} is-static"{% else %} is-outlined" href="{{precedent}}"{% endif %}>
                            <span class="icon is-small">
                                <i class="fas fa-arrow-left"></i>
                            </span>
                            <span>Précédent</span>
                        </a>
                    </div>
                </div>
                <div class="level-right">
                    <div class="level-item">
                        <a class="button is-primary{% if not suivant %} is-static"{% else %} is-outlined" href="{{suivant}}"{% endif %}>
                            <span>Suivant</span>
                            <span class="icon is-small">
                                <i class="fas fa-arrow-right"></i>
                            </span>
                        </a>
                    </div>   
                </div>
            </nav>
            <table class="table is-bordered is-hoverable is-fullwidth">
                <tbody>
                    {% for categorie, valeur in data.items() %}
                    <tr>
                        <th>{{categorie.capitalize()}}</th>
                        <td>
                            {#- Gestion des tableaux #}
                        {% if categorie == "motscles" or categorie == "sae" or categorie == "ressources" -%}   
                        <div class="tags">{% for mot in valeur %}<span class="tag is-info">{{mot}}</span>{% endfor %}</div>
                            {#- Gestion des ACS #}
                        {% elif categorie == "acs" -%}  
                        <div class="tags">{% for rt,acs in valeur.items() %}{% for ac in acs %}<span class="tag is-info">{{ac}}</span>{% endfor %}{% endfor %}</div>
                            {#- Gestion des coeffs #}
                        {% elif categorie == "coeffs" -%}   
                        <div class="tags">{% for rt, coeff in valeur.items() %}<span class="tag is-info">{{rt}} : {{coeff}}</span>{% endfor %}</div>
                            {#- Gestion des exemples #}
                        {% elif categorie == "exemples" -%}   
                        {% for exemple in valeur %}<a href="{{exemple.exemple["code"].replace("É","E") + "_exemple" + loop.index|string}}.html">Exemple{{loop.index}}</a>{% if not loop.last %} - {% endif %}{% endfor %}
                            {#- Gestion des prerequis #}
                        {% elif categorie == "prerequis" -%}   
                        {% if valeur != "Aucun" %}<div class="tags">{% for rt in valeur %}<span class="tag is-info">{{rt}}</span>{% endfor %}</div>
                        {%- else %}{{valeur}}{% endif %}
                            {#- Gestion des autres catégories #}
                        {% else -%}   
                        {{valeur}}
                        {%- endif -%}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <nav class="level is-mobile">
                <div class="level-left">
                    <div class="level-item">
                        <a class="button is-primary{% if not precedent %} is-static"{% else %} is-outlined" href="{{precedent}}"{% endif %}>
                            <span class="icon is-small">
                                <i class="fas fa-arrow-left"></i>
                            </span>
                            <span>Précédent</span>
                        </a>
                    </div>
                </div>
                <div class="level-right">
                    <div class="level-item">
                        <a class="button is-primary{% if not suivant %} is-static"{% else %} is-outlined" href="{{suivant}}"{% endif %}>
                            <span>Suivant</span>
                            <span class="icon is-small">
                                <i class="fas fa-arrow-right"></i>
                            </span>
                        </a>
                    </div>   
                </div>
            </nav>
    {% endblock %}
""")

# Template de la liste des ressources par semestre
template_List_Ressource = env.from_string("""
        {% extends "base.html" %}
        {% block title %}Liste des Ressources du semestre {{sem}}{% endblock %}
        {% block content %}
            <div class="content">
                <ul><h1>Liste des ressources du semestre {{sem}}</h1>
                    {% for ressource in data %}
                    <li><a href="{{ressource.ressource["code"] + ".html"}}">{{ressource.ressource["code"]}} - {{ressource.ressource["nom"]}}</a></li>
                    {% endfor %}
                </ul>
            </div>
        {% endblock %}
""")

# Template de la liste des saes ou ressources
template_List = env.from_string("""
        {% extends "base.html" %}
        {% block title %}Liste des {{title}}{% endblock %}
        {% block content %}
            <div class="content">
                <ul><h1>Liste des {{title}}</h1>
                    {% for sem, liste in data.items() %}
                        {% for page in liste %}
                    <li><a href="{{page.getInfo()["code"].replace("É","E") + ".html"}}">{{page.getInfo()["code"]}} - {{page.getInfo()["titre"]}}{{page.getInfo()["nom"]}}</a></li>
                        {% endfor %}
                    {% endfor %}
                </ul>
            </div>
        {% endblock %}
""")

def motscles(mc):
    """ Retourne un tableau de mots clés en prenant compte des parenthèses """
    motscles = []
    mot = ""
    i = 0
    while i < len(mc):
        if mc[i] == "(":
            while mc[i] != ")":
                mot += mc[i]
                i += 1
        elif mc[i] == "," and mc[i+1] == " ":
            motscles.append(mot)
            mot = ""
            i += 2
        mot += mc[i]
        i += 1
    motscles.append(mot)
    return motscles

#Créer un fichier contenant la liste des saes
datas = {"data" : saes, "title": "SAE"} # "data" contient un tableau des saes
template_List.stream(datas).dump(REPERTOIRE_HTML + "/SAE.html")

#Créer un fichier contenant la liste des ressources
datas = {"data" : ressources, "title": "Ressources"}
template_List.stream(datas).dump(REPERTOIRE_HTML + "/ressources.html")

# Création des pages individuelles ressources, saes, exemples
for indexSem, sem in enumerate(ressources):
    for i, ressource in enumerate(ressources[sem]):
        data = {}
        for categorie, valeur in ressource.ressource.items():
            data[categorie] = valeur
        # Ajout des espaces en html
        data["contenu"] = data["contenu"].replace("\n","<br>")
        data["contexte"] = data["contexte"].replace("\n","<br><br>")
        # Sépare les motclés pour former des tags
        data["motscles"] = motscles(data["motscles"])
        # Ajoute les liens pour les boutons "Suivant" et "Précédent"
        datas = {"data":data}
        if(i > 0): datas["precedent"] = "R" + str(int(ressource.ressource["code"][1:])-1) + ".html"
        elif(indexSem > 0): datas["precedent"] = "R" + ressources[list(ressources.keys())[indexSem - 1]][-1].ressource["code"][1:] + ".html"
        if(i < len(ressources[sem]) - 1): datas["suivant"] = "R" + str(int(ressource.ressource["code"][1:])+1) + ".html"
        elif(indexSem < len(ressources) - 1): datas["suivant"] = "R" + str((int(sem[-1:])+1)*100+1) + ".html"
        # Créer un fichier html depuis un TemplateStream créer à partir du template et des données dans "data" qui remplace les variables
        template.stream(datas).dump(REPERTOIRE_HTML + "/" + data["code"] + ".html")
    
    #Créer un fichier contenant la liste des ressources du semestre
    data = {"data" : ressources[sem],"sem" : sem} # "data" contient un tableau des ressources du semestre
    template_List_Ressource.stream(data).dump(REPERTOIRE_HTML + "/ressources" + str(sem) + ".html")

    for i, sae in enumerate(saes[sem]):
        data = {}
        for categorie, valeur in sae.sae.items():
            data[categorie] = valeur
        # On regarde si des exemples du sae existent, si True, on les ajoute dans "data"
        if(sae.sae["code"] in exemples[sem]) : 
            data["exemples"] = exemples[sem][sae.sae["code"]]
        data["description"] = data["description"].replace("\n","<br><br>")
        data["livrables"] = data["livrables"].replace("\n","<br><br>")
        data["motscles"] = motscles(data["motscles"])
        datas = {"data":data}
        if(i > 0): datas["precedent"] = "SAE" + str(int(sae.sae["code"][3:])-1) + ".html"
        elif(indexSem > 0): datas["precedent"] = "SAE" + saes[list(saes.keys())[indexSem - 1]][-1].sae["code"][3:] + ".html" # saes[list(saes.keys())[indexSem - 1]][-1].sae["code"][3:] -> "code" du dernier sae du semestre précédent
        if(i < len(saes[sem]) - 1): datas["suivant"] = "SAE" + str(int(sae.sae["code"][3:])+1) + ".html"
        elif(indexSem < len(saes) - 1): datas["suivant"] = "SAE" + str((int(sem[-1:])+1)*10+1) + ".html"
        template.stream(datas).dump(REPERTOIRE_HTML + "/" + data["code"].replace("É","E") + ".html")

    for sae in exemples[sem]:
        i = 1 # Nommage des fichiers exemple sae peut être modifier
        for j, exemple in enumerate(exemples[sem][sae]):
            data = {}
            for categorie, valeur in exemple.exemple.items():
                data[categorie] = valeur
                if (isinstance(valeur,str)):
                    data[categorie] = data[categorie].replace("\n","<br><br>")
            datas = {"data":data}
            if(j > 0): datas["precedent"] = "SAE" + data["code"][-2:] + "_exemple" + str(i-1) + ".html"
            if(j < len(exemples[sem][sae]) - 1): datas["suivant"] = "SAE" + data["code"][-2:] + "_exemple" + str(i+1) + ".html"
            template.stream(datas).dump(REPERTOIRE_HTML + "/" + data["code"].replace("É","E") + "_exemple" + str(i) + ".html")
            i+=1
