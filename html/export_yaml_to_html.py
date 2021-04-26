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
REPERTOIRE_COMPETENCES_DEFINITIVES = Config.ROOT + "/yaml/competences"
REPERTOIRE_ACS = Config.ROOT + "/python/pn"
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

# Chargement des ACs
fichieryaml = REPERTOIRE_ACS +'/acs.yml'
acs = ACs(fichieryaml)

# Chargement des Compétences
fichieryaml = REPERTOIRE_COMPETENCES_DEFINITIVES + '/RT123.yml'
competences = Competences(fichieryaml)

#Liste de string pour renommer certaines catégories (les autres qui n'ont pas besoins ont la première lettre en majuscule)
rename = {
    "heures_encadrees": "Heures encadrées",
    "heures_formation": "Heures formation",
           "heures_tp": "Heures TP",
                  "tp": "Heures TP",
              "coeffs": "Coef.",
                 "acs": "ACs",
            "motscles": "Mots clés",
                 "sae": "SAÉ",
           "prerequis": "Prérequis",
       "problematique": "Problématique",
            "modalite": "Modalité"
}

CHEMIN_TEMPLATE = Config.ROOT + "/html"
# Création de l'environnement pour charger les templates
env = Environment(trim_blocks=True, lstrip_blocks=True, loader=FileSystemLoader(CHEMIN_TEMPLATE))
# Template de chaque pages ressources, saes, exemples (doit contenir datas,rename,precedent,suivant)
template = env.from_string("""
    {% extends "base.html" %}
    {% block title %}{{data.code}} - {{data.nom}}{{data.titre}}{% endblock %}
    {% block content %}
    {% include "navigation.html" %}
            <table class="table is-bordered is-hoverable is-fullwidth">
                <tbody>
                    {% for categorie, valeur in data.items() %}
                    <tr>
                        <th>{% if rename and rename[categorie] %}{{rename[categorie]}}{% else %}{{categorie.capitalize()}}{% endif %}</th>
                        <td>
                            {#- Gestion des tableaux #}
                        {% if categorie == "motscles" -%}  
                        <div class="tags">{% for mot in valeur %}<span class="tag is-info">{{mot}}</span>{% endfor %}</div>
                            {#- Gestion des saes #}
                        {% elif categorie == "sae" or categorie == "ressources" -%}
                        <div class="tags">{% for val in valeur %}<a class="tag is-info" href="{{val.replace("É","E")}}.html">{{val}}</a>{% endfor %}</div>
                            {#- Gestion des ACS #}
                        {% elif categorie == "acs" -%}  
                        <div class="tags">{% for rt,acs in valeur.items() %}{% for ac in acs %}<a class="tag is-info" href="{{ac}}.html">{{ac}}</a>{% endfor %}{% endfor %}</div>
                            {#- Gestion des coeffs #}
                        {% elif categorie == "coeffs" -%}   
                        <div class="tags">{% for rt, coeff in valeur.items() %}<a class="tag is-info" href="{{rt}}.html">{{rt}} : {{coeff}}</a>{% endfor %}</div>
                            {#- Gestion des exemples #}
                        {% elif categorie == "exemples" -%}   
                        {% for exemple in valeur %}<a href="{{exemple.exemple["code"].replace("É","E") + "_exemple" + loop.index|string}}.html">Exemple{{loop.index}}</a>{% if not loop.last %} - {% endif %}{% endfor %}
                            {#- Gestion des prerequis #}
                        {% elif categorie == "prerequis" -%}   
                        {% if valeur != "Aucun" %}<div class="tags">{% for rt in valeur %}<span class="tag is-info">{{rt}}</span>{% endfor %}</div>
                        {%- else %}{{valeur}}{% endif %}
                            {#- Gestion des autres catégories #}
                        {% else -%}   
                        <div class="content">{{valeur}}</div>
                        {%- endif -%}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
    {% include "navigation.html" %}
    {% endblock %}
""")

# Template de chaque pages de compétences (doit contenir data,rt,precedent,suivant)
template_Competence = env.from_string("""
        {% extends "base.html" %}
        {% block title %}{{rt}}{% endblock %}
        {% block content %}
        {% include "navigation.html" %}
            <table class="table is-bordered is-hoverable is-fullwidth">
                <tbody>
                    {% for categorie, valeur in data.items() %}
                    <tr>
                        <th>{{categorie.capitalize()}}</th>
                        <td>
                        {%- if categorie == "composantes" or categorie == "situations" -%}
                            <div class="content">
                                <ul>
                                    {% for valeur in valeur %}
                                    <li>{{valeur}}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                        {% elif categorie == "niveaux" %}
                            <div class="content">
                                <ul>
                                    {% for nom, acs in valeur.items() %}
                                    <li>{{nom}}</li>
                                        <ul>
                                            {% for ac in acs %}
                                            {% if ac[:2] == "AC" %}
                                            <li><a class="tag is-info" href="{{ac}}.html">{{ac}}</a> - {{acs[ac]}}</li>
                                            {% else %}
                                            <li>{{ac}}</li>
                                            {% endif %}
                                            {% endfor %}
                                        </ul>
                                    {% endfor %}
                                </ul>
                            </div>
                        {% else -%}   
                        <div class="content">{{valeur}}</div>
                        {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% include "navigation.html" %}
        {% endblock %}
""")

# Template de chaque pages de ACs (doit contenir data, precedent, suivant)
template_AC = env.from_string("""
        {% extends "base.html" %}
        {% block title %}{{data["ac"]}}{% endblock %}
        {% block content %}
        {% include "navigation.html" %}
            <div class="content">
                <h1>{{data["ac"]}}</h1>
                <p>{{data["titre"]}}</p>
            </div>
        {% include "navigation.html" %}
        {% endblock %}
""")

# Template de la liste des ressources par semestre (doit contenir data,sem)
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

# Template de la liste des saes ou ressources (doit contenir data,titre)
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

def formatHTML(string):
    """ Retourne un string avec les balises <ul> , <li> et <p> correctement placé, code plus compliqué pour ce qu'il fait"""
    texte = "\n"
    phrases = list(filter(None,string.split("\n")))
    i = 0
    while i < len(phrases):
        if "* " in phrases[i]: # première balise li détecté
            texte += "<ul>\n" # \n permet d'améliorer la lisibilité dans les fichiers html
            while i < len(phrases) and "*" in phrases[i]: # Tant qu'il y a des * on continue de créer des balises
                texte += "  <li>" + phrases[i][2:] + "</li>\n"
                if i+1 < len(phrases):
                    if phrases[i+1][:3] == "  *": # Si il y a une liste dans un li
                        texte += "  <ul>\n"
                        while i + 1 < len(phrases) and phrases[i+1][:2] == "  ": # Tant qu'on est dans la liste
                            if "*" in phrases[i+1]:
                                texte += "      <li>" + phrases[i+1][4:] + "</li>\n"
                            else:
                                texte = texte[:-6]
                                while i + 1 < len(phrases) and phrases[i+1][:2] == "  ": # Si il y a des retour chariot
                                    texte += phrases[i+1][3:]
                                    i += 1
                                i -= 1
                            i += 1
                        texte += "  </ul>\n"
                    elif phrases[i+1][:2] == "  ": # Retour à la ligne d'un li
                        texte = texte[:-6]
                        while i + 1 < len(phrases) and phrases[i+1][:2] == "  ":
                            texte += phrases[i+1][1:]
                            i += 1
                        texte += "</li>\n"
                i += 1
            texte += "</ul>\n"
            i -= 1
        else:
            texte += "<p>" + phrases[i] + "</p>\n"
        i += 1
    return texte[:-1] # On enlève le dernier \n 

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
        # Formatage de string en html
        data["contenu"] = formatHTML(data["contenu"])
        data["contexte"] = formatHTML(data["contexte"])
        # Sépare les motclés pour former des tags
        data["motscles"] = motscles(data["motscles"])
        # Ajoute les liens pour les boutons "Suivant" et "Précédent"
        datas = {"data":data, "rename": rename}
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
        data["description"] = formatHTML(data["description"])
        data["livrables"] = formatHTML(data["livrables"])
        data["motscles"] = motscles(data["motscles"])
        datas = {"data":data, "rename": rename}
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
            data["description"] = formatHTML(data["description"])
            data["modalite"] = formatHTML(data["modalite"])
            datas = {"data":data, "rename": rename}
            if(j > 0): datas["precedent"] = "SAE" + data["code"][-2:] + "_exemple" + str(i-1) + ".html"
            if(j < len(exemples[sem][sae]) - 1): datas["suivant"] = "SAE" + data["code"][-2:] + "_exemple" + str(i+1) + ".html"
            template.stream(datas).dump(REPERTOIRE_HTML + "/" + data["code"].replace("É","E") + "_exemple" + str(i) + ".html")
            i+=1

# Création des pages individuelles ACs, Compétences
for indexRt, rt in enumerate(acs.getInfo()):

    # ACs
    for i, (ac, desc) in enumerate(acs.getInfo()[rt].items()):
        data = {}
        data["ac"] = ac
        data["titre"] = desc
        datas = {"data":data}
        if i > 0: datas["precedent"] = list(acs.getInfo()[rt].keys())[i-1] + ".html"
        elif indexRt > 0: datas["precedent"] = list(acs.getInfo()["RT" + str(int(rt[-1])-1)].keys())[-1] + ".html"
        if i < len(acs.getInfo()[rt])-1: datas["suivant"] = list(acs.getInfo()[rt].keys())[i+1] + ".html"
        elif indexRt < len(acs.getInfo())-1: datas["suivant"] = list(acs.getInfo()["RT" + str(int(rt[-1])+1)].keys())[0] + ".html"
        template_AC.stream(datas).dump(REPERTOIRE_HTML + "/" + ac + ".html")
    
    # Compétences
    data = {}
    for categorie, valeur in competences.getInfo()[rt].items():
        data[categorie] = valeur
    data["description"] = formatHTML(data["description"])
    datas = {"data": data, "rt": rt}
    if indexRt > 0: datas["precedent"] = "RT" + str(indexRt) + ".html"
    if indexRt <= len(competences.getInfo()): datas["suivant"] = "RT" + str(indexRt + 2) + ".html"
    template_Competence.stream(datas).dump(REPERTOIRE_HTML + "/" + rt + ".html")