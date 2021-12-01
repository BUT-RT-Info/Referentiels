import re

import rofficiel.officiel
import rdocx.docx, rdocx.ressourcedocx, rdocx.saedocx, rdocx.exempledocx
import tools
import logging

# Entêtes recherchées dans une ressource (BUT1 ou BUT2/3)
ENTETES_RESSOURCES = ["Nom", "Code", "Semestre", "Heures de formation", "dont heures de TP",
                        "dont heures de CM", "dont heures de TD", "Fiche d’adaptation locale",
                        "SAÉ", "Prérequis", "Descriptif", "Mots", "Parcours", "Exemple"]

# Entêtes recherchées dans une SAE BUT1 / BUT23
ENTETES_CHAPEAU = ["Titre", # Libellé
                   "Code", # Libellé cours
                   "Semestre",
                   "Heures de formation", # Préconisation heures totales
                   "dont heures de TP", # Préconisation heures TP
                   "dont heures de CM", "dont heures de TD", "Adaptation locale",
                   "Heures \"projet tutoré\"", # Préconisation "projet tutoré"
                   "Objectifs", # "Objectifs et descriptions"
                   "Description", #  + description générique
                   "Liste des ressources", # Ressources combinées
                   "Type de livrable", # rien
                   "Mots", # Rien
                   "Parcours" # TC ou parcours
                   ]

ENTETES_EXEMPLES = ["Titre", "Description", "Formes", "Quelle problématique",
                    "Modalités"]

__LOGGER = logging.getLogger(__name__)

def get_docx_format(tableau_document): # <- doc[i]
    """Renvoie le format (BUT1 ou BUT23) du contenu lu dans un rdocx"""
    try:
        if "Nom de la " in tableau_document[0][0][0] or "Titre de la " in tableau_document[0][0][0]:
            return "BUT1"
    except:
        pass
    try: # BUT 23
        if "Code " in tableau_document[0][0][0] or "Code SAE" in tableau_document[0][0][0]:
            return "BUT23"
    except:
        pass
    raise Exception("Version BUT1/BUT23 de la fiche non détectée")


def get_type_fiche(tableau_document): # <- docu[i]
    """Indique si la fiche est une ressource ou une SAE"""
    if "ressource" in tableau_document[0][0][0].lower():
        return "RESSOURCE"
    else:
        return "SAE"


def get_ressource_BUT1_from_google(code_ressource, res):
    """Lit les infos du rdocx pour une ressource du BUT1 à partir du tableau"""
    # if len(res) != 15:
    # __LOGGER.warning(f"Champs en trop ou manquants dans \"{nom_ressource}\"")
    # Parsing des données brute de la ressource
    data = [None for i in range(len(ENTETES_RESSOURCES))]  # les données attendues Nom, Code, ..., Mots clés
    apprentissages = [None for i in range(3)]  # les apprentissages des 3 compétences
    coeffs = [None for i in range(3)]

    k = tools.get_indice("Parcours", ENTETES_RESSOURCES)
    data[k] = 'Tronc commun' # Pas de mention du parcours dans les fiches de BUT1

    non_interprete = []
    for j in range(len(res)):  # parcours des entêtes du tableau décrivant la ressource
        ligne = res[j]
        if len(ligne) == 2:  # ligne de données classique champ => valeur
            champ = ligne[0][0]  # le nom du champ
            i = tools.get_indice_sans_accent_ni_espace(champ, ENTETES_RESSOURCES)  # l'indice de l'entete dans ENTETES
            if i != None:
                data[i] = tools.caracteres_recalcitrants("\n".join(res[j][1]))
                if champ == "Prérequis" and not data[i]:
                    data[i] = rofficiel.officiel.AUCUN_PREREQUIS
                    __LOGGER.warning(f"{code_ressource}: complète les prérequis à {rofficiel.officiel.AUCUN_PREREQUIS}")
            else:
                non_interprete.append((champ, ligne[1][0]))
        else:  # ligne de données soit chapeau (ex Compétences ciblées) soit détail par compétence
            champ = ligne[0][0]
            if "Apprentissages" in champ:  # les compétences ciblées sont déduites de la présence d'apprentissage critiques
                # j+1 = les ACs par compétences
                acs = res[j + 2]
                for k in range(len(acs)):
                    apprentissages[k] = tools.caracteres_recalcitrants(
                        "\n".join(acs[k]))  # fusionne les ACS (généralement sur plusieurs lignes)
            elif "Compétence(s) ciblée(s)" in champ:
                les_coeffs = res[j + 2]
                coeffs = [elmt[0] for elmt in les_coeffs]
    if non_interprete:  # souvent Heures de formation (incluant les TP)

        try:
            indice_champ = [chp[0] for chp in non_interprete].index("Heures de formation (incluant les TP)")
        except:
            indice_champ = -1
        if indice_champ >= 0:  # si le champ "Heures de formation (incluant les TP)" est trouvé
            # tente de réinjecter les heures dans Heures encadrées si elles n'on pas déjà été renseignées
            indice_heure = tools.get_indice("formation encadrée", ENTETES_RESSOURCES)
            if not data[indice_heure]:
                print(
                    f"{code_ressource}: réinjection de \"Heures de formation (incluant les TP)\" dans \"formation encadrée\"")
                data[indice_heure] = champ[1]
                non_interprete = non_interprete[:indice_champ] + non_interprete[indice_champ + 1:]  # supprime le champ

        if non_interprete:
            __LOGGER.warning(f"{code_ressource}: champs en trop non interprétés  : " + ",".join(
                [chp[0] for chp in non_interprete]))

    # Analyse des champs manquants
    champ_manquants = []
    for (j, champ) in enumerate(ENTETES_RESSOURCES):
        if not data[j]:
            champ_manquants += [champ]
    if champ_manquants:
        __LOGGER.warning(f"{code_ressource}: champs manquants : " + ", ".join(champ_manquants))

    # Sauvegarde des champs de la ressource
    info = tuple(data[1:])
    competences = [] # Ajoute les compétences
    for (i, c) in enumerate(coeffs):
        if coeffs[i]:
            competences.append("RT" + str(i+1))
    return info, apprentissages, competences, coeffs


def get_ressource_BUT23_from_google(code_ressource, docu):
    """Lit les infos du rdocx pour une ressource du BUT23 à partir du tableau"""
    # if len(res) != 15:
    # __LOGGER.warning(f"Champs en trop ou manquants dans \"{nom_ressource}\"")

    data = [None for i in range(len(ENTETES_RESSOURCES))]  # les données attendues Nom, Code, ..., Mots clés
    apprentissages = []  # les apprentissages des 5 compétences
    competences = []
    coeffs = {} # si existant

    non_interprete = []
    for i in range(len(docu)):
        res = docu[i] # le tableau en cours

        # la 1ère ligne
        ligne = res[0]
        if len(ligne) == 1:
            champ = ligne[0][0]
            k = None
            if champ.startswith("Description"):
                k = tools.get_indice_sans_accent_ni_espace("Descriptif", ENTETES_RESSOURCES)
                val = "\n".join(res[1][0]).strip() # toutes les lignes
                if not val:
                    __LOGGER.warning(f"{code_ressource}: Ressource non rédigée ?")
            elif champ.startswith("Mots"):
                k = tools.get_indice_sans_accent_ni_espace("Mots", ENTETES_RESSOURCES)
                val = res[1][0][0]
            elif champ.startswith("Parcours"):
                k = tools.get_indice_sans_accent_ni_espace("Parcours", ENTETES_RESSOURCES)
                val = res[1][0][0]
            elif champ.startswith("Semestre"):
                val = champ.split(":")[-1].strip()
                k = tools.get_indice_sans_accent_ni_espace("Semestre", ENTETES_RESSOURCES)
            elif "Prérequis" in champ:
                k = tools.get_indice_sans_accent_ni_espace("Prérequis", ENTETES_RESSOURCES)
                val = []
                for l in range(1, len(res)):
                    if res[l][0][0]:
                        val.append(res[l][0][0])
                val = "\n".join(val)
                if not val:
                    val = rofficiel.officiel.AUCUN_PREREQUIS
                    __LOGGER.warning(f"{code_ressource}: complète les prérequis à {rofficiel.officiel.AUCUN_PREREQUIS}")
                data[k] = val
            elif "SAÉ" in champ:
                k = tools.get_indice_sans_accent_ni_espace("SAÉ", ENTETES_RESSOURCES)
                val = []
                for l in range(1, len(res)):
                    if res[l][0][0]:
                        val.append(res[l][0][0])
                val = tools.caracteres_recalcitrants("\n".join(val))
            elif "Exemple(s) de" in champ: # exemple de mise en oeuvre
                k = tools.get_indice_sans_accent_ni_espace("Exemple", ENTETES_RESSOURCES)
                val = res[1][0]
                val = "\n".join(val)
            if k != None:
                data[k] = tools.caracteres_recalcitrants(val)

        elif len(ligne) == 2:  # ligne de données classique champ => valeur ou tableau des heures
            champ = ligne[0][0]  # le nom du champ
            if "Heures totales" in champ:
                k = tools.get_indice_sans_accent_ni_espace("Heures de formation",
                                                           ENTETES_RESSOURCES)  # l'indice de l'entete dans ENTETES
                data[k] = res[1][0][0]
                k = tools.get_indice_sans_accent_ni_espace("dont heures de TP", ENTETES_RESSOURCES)
                data[k] = res[1][1][0]
            elif "Compétences" in champ: # et apprentissage
                # D'abord les comp puis les AC
                positions = [res[j][0][0].startswith("Apprentissages") for j in range(len(res))] # l'indice de début des AC
                deb_apprentissage = positions.index(True)
                competences = []
                for k in range(0, deb_apprentissage):
                    competences.append(tools.caracteres_recalcitrants(res[k][1][0]))
                # Apprentissages critiques
                apprentissages = []
                for k in range(deb_apprentissage, len(res)): # res[k][1][i]
                    for ligne in range(len(res[k][1])):
                        if res[k][1][ligne]:
                            apprentissages.append(tools.caracteres_recalcitrants(res[k][1][ligne]))
            elif "Fiche d'adaptation" in champ: # adaptation locale et préconisation
                k = tools.get_indice_sans_accent_ni_espace("Adaptation locale", ENTETES_RESSOURCES)
                data[k] = res[0][1][0]
                k = tools.get_indice_sans_accent_ni_espace("dont heures de CM", ENTETES_RESSOURCES)
                data[k] = res[1][1][0]
                k = tools.get_indice_sans_accent_ni_espace("dont heures de TD", ENTETES_RESSOURCES)
                data[k] = res[2][1][0]

        else:  # ligne avec colonne de données => chapeau
            champ = ligne[0][0]
            if "Code" in champ:
                ordre_semestre = res[1][1][0]
                k = tools.get_indice_sans_accent_ni_espace("Code", ENTETES_RESSOURCES)
                data[k] = res[1][0][0] if res[1][0][0] else res[1][3][0] # le code
                k = tools.get_indice_sans_accent_ni_espace("Nom", ENTETES_RESSOURCES)
                data[k] = res[1][2][0] # le nom

    # Nettoie info
    for (k, val) in enumerate(data):
        if val:
            data[k] = tools.caracteres_recalcitrants(val)

    # Analyse des champs manquants
    champ_manquants = []
    for (j, champ) in enumerate(ENTETES_RESSOURCES):
        if not data[j]:
            champ_manquants += [champ]
    if champ_manquants:
        __LOGGER.warning(f"{code_ressource}: champs manquants : " + ", ".join(champ_manquants))

    # Sauvegarde des champs de la ressource
    info = tuple(data[1:])
    return info, apprentissages, competences, coeffs


def parse_docu_ressource(code_ressource, docu, pnofficiel):
    """
    Parse un document google exporté en .rdocx, avec pour son code_ressource donné.
    Format du parsing issu de docx2python
    [  # document
        [  # table A
            [  # table A row
                [  # table A cell 1  <-- structure des tableaux
    """
    # A priori un tableau avec un titre (AnnexeD ou Données) puis les tableaux de synthèse de la ressource
    res = docu[1]  # le 1er contenu
    version = get_docx_format(res)

    if version == "BUT1":
        nom_ressource = tools.caracteres_recalcitrants(res[0][1][0])
    else:  # version BU12
        nom_ressource = tools.caracteres_recalcitrants(res[1][2][0])

    # Création de la ressource
    r = rdocx.ressourcedocx.RessourceDocx(nom_ressource, code_ressource, res, pnofficiel)

    if version == "BUT1":
        info, apprentissages, competences, coeffs = get_ressource_BUT1_from_google(code_ressource, docu[1])  # le tableau de la fiche
    else:
        info, apprentissages, competences, coeffs = get_ressource_BUT23_from_google(code_ressource, docu[1:])  # le docu

    r.charge_informations(*info)
    r.charge_ac(apprentissages)
    r.charge_competences(competences)
    r.charge_coeffs(coeffs)


    return r


def get_sae_BUT1_from_google(code, res, pnofficiel):
    """Récupère les info sur une SAE chapeau avec son code/le docu google/ l'indice de ligne auquel débute la sae
    dans le docu"""
    # res = docu[i]  # la ressource
    nom_sae = tools.caracteres_recalcitrants(res[0][1][0])

    # Parsing des données brute de la sae
    data = [None for i in range(len(ENTETES_CHAPEAU))]  # les données attendues Nom, Code, ..., Mots clés
    apprentissages = [None for i in range(3)]  # les apprentissages des 3 compétences
    coeffs = [None for i in range(3)]

    k = tools.get_indice("Parcours", ENTETES_CHAPEAU)
    data[k] = 'Tronc commun'  # Pas de mention du parcours dans les fiches de BUT1

    non_interprete = []
    for j in range(len(res)):  # parcours des entêtes du tableau décrivant la ressource
        ligne = res[j]
        if len(ligne) == 2:  # ligne de données classique champ => valeur
            champ = tools.caracteres_recalcitrants(ligne[0][0])  # le nom du champ
            if champ.startswith("Nom de la"):
                champ = "Titre de la"  # corrige les noms/titres
            i = tools.get_indice_sans_accent_ni_espace(champ,
                                                       ENTETES_CHAPEAU)  # l'indice de l'entete dans ENTETES
            if i != None:
                data[i] = tools.caracteres_recalcitrants("\n".join(res[j][1]))
            else:
                non_interprete.append((champ, ligne[1][0]))
        else:  # ligne de données soit chapeau (ex Compétences ciblées) soit détail par compétence
            champ = ligne[0][0]

            if "Apprentissage(s)" in champ:  # les compétences ciblées sont déduites de la présence d'apprentissage critiques
                # j+1 = les ACs par compétences
                acs = res[j + 2]
                for k in range(len(acs)):
                    apprentissages[k] = tools.caracteres_recalcitrants(
                        "\n".join(acs[k]))  # fusionne les ACS (généralement sur plusieurs lignes)
            elif "Compétence(s) ciblée(s)" in champ:
                les_coeffs = res[j + 2]
                coeffs = [elmt[0] for elmt in les_coeffs]

    if non_interprete:  # souvent Heures de formation (incluant les TP)

        __LOGGER.warning(f"{code}: champs en trop non interprétés : " + ", ".join(
            [chp[0] for chp in non_interprete]))

    # Analyse des champs manquants
    champ_manquants = []
    for (j, champ) in enumerate(ENTETES_CHAPEAU):
        if not data[j]:
            champ_manquants += [champ]
    if champ_manquants:
        __LOGGER.warning(f"{code}: champs manquants : " + ", ".join(champ_manquants))

    # Sauvegarde des champs de la ressource
    info = tuple(data[1:])
    competences = []  # Ajoute les compétences
    for (i, c) in enumerate(coeffs):
        if coeffs[i]:
            competences.append("RT" + str(i + 1))

    return (info, apprentissages, competences, coeffs)


def get_sae_BUT23_from_google(code_sae, docu):
    """Lit les infos du rdocx pour une SAE (et ses exemples) du BUT23 à partir du tableau"""
    # if len(res) != 15:
    # __LOGGER.warning(f"Champs en trop ou manquants dans \"{nom_ressource}\"")
    # Parsing des données brute de la ressource
    data = [None for i in range(len(ENTETES_CHAPEAU))]  # les données attendues Nom, Code, ..., Mots clés
    apprentissages = []  # les apprentissages des 5 compétences
    competences = []
    coeffs = {} # si existant
    exemples = "" # les exemples

    non_interprete = []
    for i in range(len(docu)):
        res = docu[i] # le tableau en cours

        # la 1ère ligne
        ligne = res[0]
        if len(ligne) == 1:
            champ = ligne[0][0]
            k = None
            if champ.startswith("Objectifs"):
                k = tools.get_indice_sans_accent_ni_espace("Objectifs", ENTETES_CHAPEAU)
                val = "\n".join(res[1][0]).strip() # toutes les lignes
                if not val:
                    __LOGGER.warning(f"{code_sae}: Ressource non rédigée ?")
            elif champ.startswith("Description"):
                k = tools.get_indice_sans_accent_ni_espace("Description", ENTETES_CHAPEAU)
                val = "\n".join(res[1][0]).strip()  # toutes les lignes
                if not val:
                    __LOGGER.warning(f"{code_sae}: Ressource non rédigée ?")
            elif champ.startswith("Mots"):
                k = tools.get_indice_sans_accent_ni_espace("Mots", ENTETES_CHAPEAU)
                val = res[1][0][0]
            elif champ.startswith("Parcours"):
                k = tools.get_indice_sans_accent_ni_espace("Parcours", ENTETES_CHAPEAU)
                val = res[1][0][0]
            elif champ.startswith("Semestre"):
                val = champ.split(":")[-1].strip()
                k = tools.get_indice_sans_accent_ni_espace("Semestre", ENTETES_CHAPEAU)
            elif "Ressources combinées" in champ:
                k = tools.get_indice_sans_accent_ni_espace("Liste des ressources", ENTETES_CHAPEAU)
                val = []
                for l in range(1, len(res)):
                    if res[l][0][0]:
                        val.append(res[l][0][0])
                val = "\n".join(val)
                if not val:
                    __LOGGER.warning(f"{code_sae}: manque les ressources combinées")
            elif "Type de livrable" in champ:
                k = tools.get_indice_sans_accent_ni_espace("Type de livrable", ENTETES_CHAPEAU)
                val = res[1][0][0]
                val = tools.caracteres_recalcitrants(val)
            elif "Exemple(s) de mise" in champ:
                exemples = tools.caracteres_recalcitrants("\n".join(res[1][0]))
            # sauvegarde
            if k != None:
                data[k] = val

        elif len(ligne) == 3:  # ligne de données classique champ => valeur ou tableau des heures
            champ = ligne[0][0]  # le nom du champ
            if "Préconisation heures totales" in champ:
                k = tools.get_indice_sans_accent_ni_espace("Heures de formation",
                                                           ENTETES_CHAPEAU)  # l'indice de l'entete dans ENTETES
                data[k] = res[1][0][0]
                k = tools.get_indice_sans_accent_ni_espace("dont heures de TP", ENTETES_CHAPEAU)
                data[k] = res[1][1][0]
                k = tools.get_indice_sans_accent_ni_espace("Heures \"projet tutoré\"", ENTETES_CHAPEAU)
                data[k] = res[1][2][0]

        elif len(ligne) == 2:  # ligne de données classique champ => valeur ou tableau des heures
            champ = ligne[0][0]  # le nom du champ
            if "Compétences" in champ: # et apprentissage
                # D'abord les comp puis les AC
                positions = [res[j][0][0].startswith("Apprentissages") for j in range(len(res))] # l'indice de début des AC
                deb_apprentissage = positions.index(True)
                competences = []
                for k in range(0, deb_apprentissage):
                    competences.append(tools.caracteres_recalcitrants(res[k][1][0]))
                # Apprentissages critiques
                apprentissages = []
                for k in range(deb_apprentissage, len(res)): # res[k][1][i]
                    for ligne in range(len(res[k][1])):
                        if res[k][1][ligne]:
                            apprentissages.append(tools.caracteres_recalcitrants(res[k][1][ligne]))

            elif "Fiche d" in champ:  # adaptation locale et préconisation
                k = tools.get_indice_sans_accent_ni_espace("Adaptation locale", ENTETES_CHAPEAU)
                data[k] = res[0][1][0]
                k = tools.get_indice_sans_accent_ni_espace("dont heures de CM", ENTETES_CHAPEAU)
                data[k] = res[1][1][0]
                k = tools.get_indice_sans_accent_ni_espace("dont heures de TD", ENTETES_CHAPEAU)
                data[k] = res[2][1][0]

        else:  # ligne avec colonne de données => chapeau taille 4
            champ = ligne[0][0]
            if "Code" in champ:
                ordre_semestre = res[1][1][0]
                k = tools.get_indice_sans_accent_ni_espace("Code", ENTETES_CHAPEAU)
                data[k] = res[1][0][0] if res[1][0][0] else res[1][3][0] # le code RT
                code_RT = data[k]
                k = tools.get_indice_sans_accent_ni_espace("Titre", ENTETES_CHAPEAU)
                data[k] = res[1][2][0] # le nom

    # Nettoie les caractères gênants
    for (k, val) in enumerate(data):
        if val:
            data[k] = tools.caracteres_recalcitrants(val)

    # Analyse des champs manquants
    champ_manquants = []
    for (j, champ) in enumerate(ENTETES_CHAPEAU):
        if not data[j]:
            champ_manquants += [champ]
    if champ_manquants:
        __LOGGER.warning(f"{code_sae}: champs manquants : " + ", ".join(champ_manquants))

    # Analyse des exemples
    exemples = tools.remove_ligne_vide(exemples) # supprime les lignes vides
    liste_exemples = {}
    if exemples:
        marqueurs = re.findall(r"Exemple\s*\d\s*:{0,1}", exemples)
        if marqueurs:
            positions = {m: exemples.index(m) for m in marqueurs} # la position des exemples
            for (i, m) in enumerate(marqueurs):
                deb = positions[m] + len(m)
                if i < len(marqueurs) -1:
                    fin = positions[marqueurs[i+1]]
                else:
                    fin = len(exemples)
                extrait = exemples[deb:fin] # la 1ère ligne = titre ?
                lignes = extrait.split("\n")
                liste_exemples[i] = [lignes[0], # titre
                                    "\n".join(lignes[1:]), # description
                                    None, # forme
                                    None, # problématique
                                    None] # modalité
        else:
            __LOGGER.warning(f"{code_sae} : Pas d'exemples parsés / trouvés")
            # ENTETES_EXEMPLES = ["Titre", "Description", "Formes", "Quelle problématique",
            #                     "Modalités"]
            liste_exemples[0] = [None, # titre
                                 exemples,
                                 None,
                                 None,
                                 None]



    # Sauvegarde des champs de la ressource
    info = tuple(data[1:])
    return info, apprentissages, competences, coeffs, liste_exemples


def get_exemple_sae_BUT1_from_google(nom_exemple, res):
    """Récupère les infos d'un exemple de SAE"""
    # Parsing des données brute de l'exemple de la Saé
    data = [None for i in range(len(ENTETES_EXEMPLES))]  # les données attendues Nom, Code, ..., Mots clés

    non_interprete = []
    for j in range(len(res)):  # parcours des entêtes du tableau décrivant la ressource
        ligne = res[j]
        if len(ligne) == 2:  # ligne de données classique champ => valeur
            champ = tools.caracteres_recalcitrants(ligne[0][0])  # le nom du champ
            i = tools.get_indice_sans_accent_ni_espace(champ,
                                                       ENTETES_EXEMPLES)  # l'indice de l'entete dans ENTETES
            if i != None:
                data[i] = tools.caracteres_recalcitrants("\n".join(res[j][1]))
            else:
                non_interprete.append((champ, ligne[1][0]))
        else:  # ligne de données soit chapeau (ex Compétences ciblées) soit détail par compétence
            print("??? plus de 2 colonnes ?")

    if non_interprete:  # souvent Heures de formation (incluant les TP)

        __LOGGER.warning(f"Dans l'exemple \"{nom_exemple}\", champs en trop non interprétés  : " + ",".join(
            [chp[0] for chp in non_interprete]))

    # Analyse des champs manquants
    champ_manquants = []
    for (j, champ) in enumerate(ENTETES_EXEMPLES):
        if not data[j]:
            champ_manquants += [champ]
    if champ_manquants:
        __LOGGER.warning(f"Dans \"{nom_exemple}\", champs manquants  : " + ",".join(champ_manquants))

    # Sauvegarde des champs de la ressource
    info = tuple(data[1:])
    return info


def parse_docu_sae(code_sae, docu, pnofficiel):
    """
        Parse un document google exporté en .rdocx, avec pour son code_ressource donné.
    """
    version = get_docx_format(docu[1])
    liste_exemples = []

    if version == "BUT1":
        for i in range(1, len(docu)):
            est_sae, est_exemple = False, False
            try:
                if "Titre de la " in docu[i][0][0][0] or "Nom de la " in docu[i][0][0][0]: # [03][00][0][0]
                    if "Code" in docu[i][1][0][0]:
                        est_sae = True
                    else: # c'est un exemple
                        est_exemple = True
            except:
                pass

            if est_sae == True:
                res = docu[i]  # la ressource
                nom_sae = tools.caracteres_recalcitrants(res[0][1][0])

                # Création de la ressource
                s = rdocx.saedocx.SAEDocx(nom_sae, code_sae, res, pnofficiel)

                info, apprentissages, competences, coeffs = get_sae_BUT1_from_google(code_sae, res, pnofficiel)

                # Sauvegarde des champs de la sae
                s.charge_informations(*info)
                s.charge_ac(apprentissages)
                s.charge_competences(competences)
                s.charge_coeffs(coeffs)

                # nettoie le titre et le code
                s.nettoie_code()
                s.nettoie_titre_sae()

            elif est_exemple == True:
                res = docu[i]  # la ressource
                nom_exemple = tools.caracteres_recalcitrants(res[0][1][0])

                # Création de l'exemple
                e = rdocx.exempledocx.ExempleSAEDocx(nom_exemple, res, s.code, s.codeRT, pnofficiel) # fourni les codes de la sae rattachée
                info = get_exemple_sae_BUT1_from_google(nom_exemple, res)
                e.charge_informations(*info)
                liste_exemples.append(e)

        return (s, liste_exemples)
    elif version == "BUT23":
        res = docu[1]
        nom_sae = tools.caracteres_recalcitrants(res[1][2][0])

        s = rdocx.saedocx.SAEDocx(nom_sae, code_sae, res, pnofficiel)
        info, apprentissages, competences, coeffs, exemples = get_sae_BUT23_from_google(code_sae, docu)

        s.charge_informations(*info)
        s.charge_ac(apprentissages)
        s.charge_competences(competences)
        s.charge_coeffs(coeffs)

        # nettoie le titre et le code

        s.nettoie_code()
        s.nettoie_titre_sae()
        # Créé les exemples
        liste_exemples = []
        for no in exemples: # 1 dictionnaire n° => info:
            e = rdocx.exempledocx.ExempleSAEDocx(exemples[no][0], "", s.code, s.codeRT,
                                                pnofficiel)  # fourni les codes de la sae rattachée
            info = exemples[no][1:]
            e.charge_informations(*info)
            liste_exemples.append(e)
        # Doit reparcourir le même doc à la recherche des exemples
        return (s, liste_exemples)
    else:
        print("SAE de BUT1 ou BUT2/3 non détectée")


