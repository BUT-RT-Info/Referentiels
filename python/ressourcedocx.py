import re, logging
import officiel
from modeles import *
import ruamel.yaml
from ruamel.yaml.scalarstring import FoldedScalarString as folded


__LOGGER = logging.getLogger(__name__)

class Docx():
    """Classe de base pour les ressources/saé/exemples du docx"""
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, nom, brut):
        self.nom = nom
        self.code = None # chargé ultérieurement
        self.brut = brut  # les données brutes de la ressource/saé
        self.semestre = None # le semestre de la ressource/saé (chargé ultérieurement)
        self.apprentissages = None # les acs (chargés ultérieurement)
        self.mots = None # les mots-clés chargés ultérieurement
        self.coeffs = None # chargés ultérieurement

    def charge_ac(self, apprentissages):
        self.apprentissages = apprentissages

    def charge_coeffs(self, coeffs):
        self.coeffs = coeffs

    def __str__(self):
        print(self.nom + " " + self.code)

    def nettoie_semestre(self):
        """Pour une ressource, ou une SAE, nettoie le champ semestre"""
        if self.semestre:
            if "1" in self.semestre:
                self.semestre = "S1"
            elif "2" in self.semestre:
                self.semestre = "S2"
            else:
                Docx.__LOGGER.warning(f"nettoie_semestre : dans \"{self.nom}, PAS de semestre => rattaché au S2")
                self.semestre = "S2"
        else:
            Docx.__LOGGER.warning(f"nettoie_semestre : dans \"{self.nom}, PAS de semestre => rattaché au S2")
            self.semestre = "S2"

    def nettoie_acs(self):
        """Nettoie les acs d'une ressource ou d'une saé,
        en les remplaçant par leur code pour les 3 compétences"""

        if len(self.apprentissages) != 3:
            Docx.__LOGGER.warning(f"nettoie_acs : Problème dans le nombre de compétences de {self.nom}")

        dico = {}
        DATA_ACS = officiel.get_DATA_ACS()
        for comp in range(3):
            donnees = self.apprentissages[comp]  # chaine de caractères listant les ACS

            acs_avec_code = devine_acs_by_code(donnees) # récupère les codes des acs
            acs_avec_code = [ac.replace(" ", "") for ac in acs_avec_code]  # supprime les espaces inutiles

            acs_avec_nom = officiel.devine_code_by_nom_from_dict(donnees, DATA_ACS) # récupère les codes en utilisant les noms
            acs_avec_nom = [ac.replace(" ", "") for ac in acs_avec_nom]  # supprime les espaces inutiles

            if acs_avec_code and set(acs_avec_nom).intersection(set(acs_avec_code)) != set(acs_avec_nom):
                Docx.__LOGGER.warning(f"Dans {self.nom}, revoir les ACS : {acs_avec_code} vs {acs_avec_nom}")

            acs_finaux = sorted(list(set(acs_avec_code + acs_avec_nom)))
            if acs_finaux:
                dico["RT" + str(comp + 1)] = acs_finaux

        self.apprentissages = dico  # Mise à jour du champ

    def nettoie_mots_cles(self):
        mots = self.mots  # .encode('utf8', 'ignore').decode('utf8')
        mots = mots.replace(".", "").replace(";", ",")
        liste_mots = mots.split(",")
        liste_mots = [l.strip() for l in liste_mots if l.strip()] # supprime les espaces inutiles et les lignes vides
        mots = ", ".join(liste_mots)
        self.mots = mots

    def nettoie_titre(self, data_titres):
        """Nettoie le titre d'une ressource ou d'une SAE en utilisant les titres officiels
        fournis dans le yaml (via le dictionnaire DATA_RESSOURCES)"""

        def devine_nom(champ):
            champ_purge = officiel.supprime_accent_espace(champ)
            for sem in data_titres:
                for code in data_titres[sem]:
                    nom_purge = officiel.supprime_accent_espace(data_titres[sem][code]["nom"])
                    if champ_purge.startswith(nom_purge):
                        return data_titres[sem][code]["nom"]  # le bon nom

        old = self.nom
        titre = devine_nom(self.nom)
        if titre and titre != old:
            Docx.__LOGGER.warning(f"nettoie_titre : {old} => titre deviné \"{titre}\"")
            self.nom = titre

    def nettoie_coeffs(self):
        coeffs_finaux = {}
        for (comp, chaine) in enumerate(self.coeffs):
            if "coef" in chaine: # s'il y a un coeff
                champ = chaine.split(" ")
                coeff = eval(champ[1])
                coeffs_finaux["RT" + str(comp + 1)] = coeff
            elif "X" in chaine:
                coeff = 0
                coeffs_finaux["RT" + str(comp + 1)] = coeff
        self.coeffs = coeffs_finaux

    def dico_to_yaml(self, dico):
        output = ruamel.yaml.dump(dico, Dumper=ruamel.yaml.RoundTripDumper,
                                  allow_unicode=True, width=100)
        # Purge les lignes vides en trop
        lignes = output.split("\n")
        lignes_finales = []
        for (i, ligne) in enumerate(lignes):
            if ligne.rstrip() == "":
                if i != len(lignes)-1 and lignes[i+1].rstrip() != "":
                    lignes_finales.append(ligne) # ajoute la ligne si la suivante n'est pas vide
            else:
                lignes_finales.append(ligne)
        output = "\n".join(lignes_finales)

        # Ajoute les espaces manquants dans les listes markdown
        # écrite sur plusieurs lignes
        lignes = output.split("\n") # pour vérif
        lignes_finales = []
        avec_marqueur = False
        last_marqueur = 0
        for (i, ligne) in enumerate(lignes):
            ligne = ligne.replace("\t", " "*2)
            if "    *" in ligne and avec_marqueur == False:
                avec_marqueur = True
                last_marqueur = "    *"
            elif "  *" in ligne and avec_marqueur == False:
                avec_marqueur = True
                last_marqueur = "  *"
            else: # pas de marqueur
                if ligne.strip() == "" or ligne[0] != " ":
                    avec_marqueur = False # fin du marqueur
                elif ligne.strip() != "" and avec_marqueur == True:
                    if last_marqueur == "  *":
                        ligne = " "*4 + ligne.lstrip()
                    else:
                        ligne = " "*6 + ligne.lstrip()
            lignes_finales.append(ligne)

        output = "\n".join(lignes_finales)

        # Remplace http(s) URLs pour markdown
        # if "12" in self.code:
        #    print("ici")
        output = re.sub( r"(http(s)?://[\w\d:#@%/;~_?\+-=\\\.&]*[\w/])", r"[\1](\1)", output )
        # Remplace les guillemets
        # ne traite pas tous les cas, mais arrange la majorité
        output = re.sub( r"\"(.*?)\"", r"«\1»", output, flags=re.DOTALL)
        # On utilise les guillements français (ajout automatique des bons espaces)
        #output = output.replace("«", r"\og ").replace("»", r"\fg{}")
        
        return output

class RessourceDocx(Docx):
    """Classe modélisant les ressources, lorsqu'elles sont extraites du docx"""
    __LOGGER = logging.getLogger(__name__)

    def charge_informations(self, code, semestre, heures_encadrees, tp, sae, prerequis,
                            description, mots):
        self.code = code
        self.semestre = semestre # <--
        self.heures_encadrees = heures_encadrees
        self.tp = tp
        self.sae = sae
        self.prerequis = prerequis
        self.description = description
        self.contexte = None
        self.contenu = None
        self.mots = mots


    def nettoie_titre_ressource(self):
        """Nettoie le titre d'une ressource ou d'une SAE en utilisant les titres officiels
        fournis dans le yaml (via le dictionnaire DATA_RESSOURCES)"""
        old = self.nom
        DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
        self.nettoie_titre(DATA_RESSOURCES)
        titre2 = officiel.get_officiel_ressource_name_by_code(self.code)
        if titre2 != self.nom:
            self.nom = titre2
            RessourceDocx.__LOGGER.warning(f"nettoie_titre : {old} => titre d'après PN \"{titre2}\"")

    def nettoie_code(self):
        """Recherche le code de la forme RXXX"""
        DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
        if self.code:
            codes = devine_ressources_by_code(self.code)

            if len(codes) == 1:
                self.code = codes[0]
            else:
                code_devine = officiel.get_code_from_nom_using_dict(self.nom, DATA_RESSOURCES)
                if code_devine:
                    RessourceDocx.__LOGGER.warning(f"nettoie_code : \"{self.nom}\" => code {code_devine}")
                    self.code = code_devine
                else:
                    self.code = None

        if not self.code:
            RessourceDocx.__LOGGER.warning(f"nettoie_code : \"{self.nom}\" => code manquant")

    def nettoie_prerequis(self):
        """Nettoie les prérequis"""
        if not self.prerequis or officiel.AUCUN_PREREQUIS.lower() in self.prerequis.lower():
            self.prerequis = officiel.AUCUN_PREREQUIS
        else:
            ressources = nettoie_liste_ressources(self.prerequis)
            if ressources:
                self.prerequis = ressources

    def nettoie_sae(self):
        """Nettoie le champ SAe d'une ressource en détectant les codes"""
        SAE_avec_code = devine_sae_by_code(self.sae)
        liste = [l.rstrip() for l in SAE_avec_code]
        self.sae = liste
        if not self.sae:
            RessourceDocx.__LOGGER.warning(f"nettoie_sae: dans {self.nom} pas de SAE (:")

    def nettoie_heures(self):
        """Nettoie le champ (horaire) (de la forme 46h ou 33...) pour en extraire la valeur numérique :
        le champ peut contenir 2 volumes (heures formation puis heures tp), auquel cas les 2 valeurs sont renvoyées
        dans un tuple"""
        volumes = None
        if self.heures_encadrees:  # si les heures encadrées sont renseignées
            volumes = nettoie_champ_heure(self.heures_encadrees)
        if self.tp:
            self.tp = nettoie_champ_heure(self.tp)

        if isinstance(volumes, int):
            self.heures_encadrees = volumes
        elif isinstance(volumes, tuple):
            self.heures_encadrees = volumes[0]
            if not self.tp:
                self.tp = volumes[1]
            elif self.tp != volumes[1]:
                RessourceDocx.__LOGGER.warning(r"nettoie_heure: ans {self.nom}, pb dans les heures tp/td")
        else:
            self.heures_encadrees = None

    def split_description(self):
        """Découpe le champ description en un contexte+un contenu ; si pas possible """
        # if self.code == "R110":
        #    print("ici")
        champs = self.description.split("\n")
        champs = [c for c in champs if c]  # supprime les lignes vides

        indicea = 0  # la ligne mentionnant le contexte
        if True in [ligne.startswith("Contexte et ") for ligne in champs]:  # la ligne commençant par Contenus
            indicea = [ligne.startswith("Contexte et ") for ligne in champs].index(True)

        indicec = 0
        contexte = []
        marqueur = False
        identifiants = ["Contenus", "Objectifs visés"] # Identifiant marquant la ligne des contenus
        for id in identifiants:
            presence = [ligne.startswith(id) for ligne in champs]
            if True in presence and not marqueur: # la ligne commençant par l'identifiant
                indicec = presence.index(True)
                marqueur = True
        if True in [ligne.startswith("Contexte et ") for ligne in champs]:
            contexte = champs[indicea + 1:indicec]
        else:
            contexte = champs[:indicec]
        # suppression des lignes vides
        contexte = "\n".join(remove_ligne_vide(contexte))
        # suppression des liens

        contexte = remove_link(contexte)
        if not contexte:
            contexte = "Aucun"
        contenu = "\n".join(champs[indicec + 1:])

        # sauvegarde des champs
        self.contexte = contexte
        self.contenu = contenu

    def nettoie_contenu(self):
        """Partant du contenu détaillé d'une ressource, la transforme
        en markdown en générant les listes à puces"""
        contenu = self.contenu.replace(" / ", "/")
        self.contenu = convert_to_markdown(contenu)

    def nettoie_contexte(self):
        """Partant du contexte détaillé d'une ressource, la transforme
        en markdown en générant les listes à puces"""
        contexte = self.contexte.replace(" / ", "/")
        self.contexte = convert_to_markdown(contexte)

    def nettoie_champ(self):
        """Lance le nettoyage des champs"""
        self.nettoie_code()
        self.nettoie_titre_ressource()
        self.nettoie_heures()

        self.nettoie_semestre()
        self.nettoie_acs()
        self.nettoie_sae()
        self.nettoie_prerequis()
        self.nettoie_mots_cles()
        self.nettoie_coeffs()

        # Remet en forme le descriptif
        self.split_description()
        self.nettoie_contexte()
        self.nettoie_contenu()
        print(f"{self.code} {self.semestre}")

    def to_yaml(self):
        """Exporte la ressource en yaml"""
        dico = {"nom": self.nom,
                "code": self.code,
                "semestre" : int(self.semestre[1]),
                "heures_formation": self.heures_encadrees if self.heures_encadrees else "???",
                "heures_tp": self.tp if self.tp or self.tp == 0 else "???",
                "coeffs": self.coeffs,
                "acs": self.apprentissages,
                "sae": self.sae,
                "prerequis": self.prerequis,
                "contexte": folded(self.contexte),
                "contenu": folded(self.contenu),
                "motscles": self.mots if self.mots else ""
                }
        return self.dico_to_yaml(dico)

def nettoie_champ_heure(champ):
    try: # champ contenant uniquement un nbre d'heure
        volumes = int(champ)
        return volumes
    except:
        volumes = re.findall("(\d{2}\D|\d{1}\D)", champ)
        if len(volumes) == 1:
            return int(volumes[0][:-1])
        elif len(volumes) == 2:
            volumes = sorted(volumes, reverse=True)
            return (int(volumes[0][:-1]), int(volumes[1][:-1]))


def nettoie_liste_ressources(contenu):
    """Nettoie un contenu contenant une liste ressources, en extrayant les codes ressources
    et en les fournissant les codes extraits dans une liste
    """
    DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
    R_avec_code = devine_ressources_by_code(contenu)
    R_avec_nom = officiel.devine_code_by_nom_from_dict(contenu, DATA_RESSOURCES)
    liste = R_avec_code + R_avec_nom
    liste = [l.strip().replace(",", "").replace(".", "") for l in liste] # supprime les espaces et les ponctuations restantes
    return sorted(list(set(liste)))


def devine_acs_by_code(champ):
    """Recherche les codes ressources de la forme ACXXX ou AC0XXX dans champ ;
    ramène les codes AC0XXX à 3 chiffres.
    """
    codes3 = re.findall(r"(AC[0-9][0-9][0-9]\D)", champ) # de code à 3 chiffres
    codes4 = re.findall(r"(AC0[0-9][0-9][0-9])", champ)

    codes3 = [c.rstrip() for c in codes3]
    codes4 = [c.rstrip() for c in codes4]
    codes4 += [ "AC0" + c[-3:] for c in codes3] # ajoute les 0 manquants des acs (codage AC0111)
    codes4 = [c.strip() for c in codes4]
    return sorted(list(set(codes4)))


def devine_ressources_by_code(champ):
    """Recherche les codes ressources de la forme RXXX dans champ ;
    """
    codes1 = re.findall(r"(R\d{3})", champ) # de code à 3 chiffres
    codes2 = re.findall(r"(R\d{3}\D)", champ)
    codes = codes1 + [c.strip() for c in codes2 if "|" not in c]
    return sorted(list(set(codes)))

def devine_ressources_by_nom(donnees):
    """Partant d'une chaine de caractères, détermine les ressources
    présentes dans la donnée, en utilisant les infos officielles de
    ressources.yml"""
    donnees_purge = officiel.supprime_accent_espace(donnees)
    codes = []
    DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
    for sem in DATA_RESSOURCES:
        for code in DATA_RESSOURCES[sem]:
            nom_purge = officiel.supprime_accent_espace(DATA_RESSOURCES[sem][code])
            if nom_purge in donnees_purge:
                codes += [code]
    return sorted(list(set(codes)))

def devine_sae_by_code(donnees):
    """Partant d'une chaine de caractères, détermine les codes des SAE"""
    codes = re.findall(r"(SAE\d\d)", donnees)
    codes += re.findall(r"(SAÉ\d\d)", donnees)# de code à 3 chiffres
    for (i, code) in enumerate(codes):
        codes[i] = codes[i].replace("E", "É")
    return sorted(list(set(codes)))

def remove_link(contenu):
    #liens = re.findall("(<a\s.*\">)", contenu)
    liens = re.findall(r"(<a\shref=\"[\w\./:-]*\">)", contenu)
    for m in liens:
        contenu = contenu.replace(m, "")
    contenu = contenu.replace("</a>", "")
    return contenu

def remove_ligne_vide(contenus):
    """Supprime les lignes vides"""
    if isinstance(contenus, list):
        return [c for c in contenus if c.rstrip()]
    else: # contenu = chaine
        if get_marqueurs(contenus):
            temp = contenus.split("\n")
            temp = [t for t in temp if t.replace("\t", "").rstrip()]
            return "\n".join(temp)
        else: # pas de marqueur => respect des paragraphes
            contenus = contenus.replace("\n\n", "\\\\\n")
            temp = contenus.split("\n")
            temp = [t for t in temp if t.replace("\t", "").rstrip()]
            return "\n".join(temp)

def get_marqueur_numerique(contenu):
    """Revoie la liste des marqueurs numériques"""
    m = re.findall(r"(\d/|\d\s/)", contenu)
    #m += re.findall(r"(\d\s\)|\d\))", contenu) # les marqueurs de la forme 1)
    m += re.findall(r"(\d\s\))", contenu)
    m += re.findall(r"(--)\s", contenu)
    m += re.findall(r"(--)\t", contenu)
    return m

def get_marqueurs(contenu):
    """Renvoie la liste des marqueurs (à 1 caractère) partant d'un contenu - splitable en plusieurs lignes
    (éventuellement vide)"""
    contenus = [ligne.rstrip() for ligne in contenu.split("\n")]  # les contenus

    marqueurs = []
    for ligne in contenus:
        m = re.search(r"(\t)*", ligne) # y a-t-il des tabulations ?
        if m.group() != "":
            ajout = m.group()
        else:
            ajout = ""
        ligne = ligne.replace("\t","").rstrip() # supprime les tabulations pour rapatrier le marqueur en début de ligne
        if ligne: # si la ligne n'est pas vide, cherche le marqueur en début de ligne (si 1 caractère)
            if ligne[0] not in string.ascii_letters and ligne[0] != "É" and ligne[0] != "/":
                marqueurs += [ajout + ligne[0]] # tous les symboles

    marqueurs_finaux = [] # tri les marqueurs en supprimant les doublons et en gardant un ordre (pour détecter les sous listes)
    for m in marqueurs:
        if m not in marqueurs_finaux:
            marqueurs_finaux.append(m)
    return marqueurs_finaux

def get_marqueur_from_liste(ligne, marqueurs):
    """Renvoie le marqueur qui marque le début d'une ligne parmi une liste de marqueurs recherchés"""
    for m in marqueurs:
        if ligne.startswith(m):
            return m


def remplace_marqueur_numerique_with_caracteres(contenu):
    """Remplace les marqueurs numériques par des marqueurs > lorsque présents dans un contenu"""
    marqueurs_numeriques = get_marqueur_numerique(contenu)
    for m in marqueurs_numeriques: # remplace les marqueurs numériques
        contenu = contenu.replace(m, ">")
    return contenu

def convert_to_markdown(contenu):
    """Convertit un contenu avec des marqueurs en markdown"""
    contenu = remove_link(contenu) # supprime les liens

    contenu = remplace_marqueur_numerique_with_caracteres(contenu)
    marqueurs_finaux = get_marqueurs(contenu)
    lignes = contenu.split("\n")
    contenus_fin =  lignes[:] # copie des ligne
    for (i, ligne) in enumerate(lignes):
        m = get_marqueur_from_liste(ligne, marqueurs_finaux) # identifie la présence d'un marqueur dans la ligne
        if m:
            pos = marqueurs_finaux.index(m)
            ligne = "\t" * (pos) + "* " + ligne.replace(m, "").replace("\t", "").rstrip()
            # corrige les espaces après les marqueurs
            champ = re.findall(r"(\*\s+)\w", ligne)
            for c in champ:
                ligne = ligne.replace(c, "* ")
        contenus_fin[i] = ligne

    contenu = "\n\n".join(contenus_fin)

    return contenu


class SAEDocx(Docx):
    """Classe modélisant un chapeau de SAé relu dans les docx"""
    __LOGGER = logging.getLogger(__name__)

    def charge_informations(self, code, semestre, heures_encadrees, tp, projet, description, ressources, livrables, mots):
        self.code = code
        self.semestre = semestre  # <--
        self.heures_encadrees = heures_encadrees
        self.tp = tp
        self.projet = projet
        self.description = description
        self.ressources = ressources
        self.livrables = livrables
        self.mots = mots

    def nettoie_titre_sae(self):
        """Nettoie le titre d'une SAE en utilisant les titres officiels
        fournis dans le yaml (via le dictionnaire DATA_RESSOURCES)"""
        old = self.nom
        DATA_SAES = officiel.get_DATA_SAES()
        self.nettoie_titre(DATA_SAES)
        titre2 = officiel.get_officiel_sae_name_by_code(self.code)
        if titre2 != self.nom:
            self.nom = titre2
            SAEDocx.__LOGGER.warning(f"nettoie_titre : {old} => titre d'après PN \"{titre2}\"")

    def nettoie_code(self):
        """Recherche les codes de la forme SAE|éXX """
        DATA_SAES = officiel.get_DATA_SAES()
        if self.code:
            codes = devine_sae_by_code(self.code)
            if len(codes) == 1:
                self.code = codes[0]
            else:
                code_devine = officiel.get_code_from_nom_using_dict(self.nom, DATA_SAES)
                if code_devine:
                    SAEDocx.__LOGGER.warning(f"nettoie_code : \"{self.nom}\" => code {code_devine}")
                    self.code = code_devine
                else:
                    self.code = None
        if not self.code:
            SAEDocx.__LOGGER.warning(f"nettoie_code : \"{self.nom}\" => code manquant")

    def nettoie_heures_sae(self):
        """Nettoie les champs (horaires) des saes"""
        if self.heures_encadrees:  # si les heures encadrées sont renseignées
            self.heures_encadrees = nettoie_champ_heure(self.heures_encadrees)
        else:
            SAEDocx.__LOGGER.warning(f"nettoie_heures_sae: dans {self.nom}, manque les heures de formation")
            self.heures_encadrees = "???"
        if self.tp or self.tp == 0:
            self.tp = nettoie_champ_heure(self.tp)
        else:
            SAEDocx.__LOGGER.warning(f"nettoie_heures_sae: dans {self.nom}, manque les heures de tp")
            self.tp = "???"

        if self.projet:
            if self.code == "SAÉ16":
                self.projet = 0
                SAEDocx.__LOGGER.warning("SAÉ16 : heures projet mise à 0")
            else:
                self.projet = nettoie_champ_heure(self.projet)
        else:
            SAEDocx.__LOGGER.warning(f"nettoie_heures_sae: dans {self.nom}, manque les heures de projet")
            self.projet = "???"

        try:
            if self.heures_encadrees < self.tp:
                SAEDocx.__LOGGER.warning(f"nettoie_heures_sae: dans {self.nom}, pb dans les heures formations/tp")
        except:
            pass

    def nettoie_livrables_sae(self):
        """Partant du contenu détaillé d'une ressource, la transforme
        en markdown en générant les listes à puces"""
        self.livrables = convert_to_markdown(self.livrables)

    def nettoie_ressources(self):
        """Nettoie le champ ressource d'une sae en détectant les codes"""
        self.ressources = nettoie_liste_ressources(self.ressources)
        if not self.ressources:
            SAEDocx.__LOGGER.warning(f"nettoie_ressources: dans {self.nom} pas de ressources (:")

    def nettoie_description(self):
        """Nettoie le champ description"""
        if self.description:
            self.description = convert_to_markdown(self.description)
        else:
            self.description = ""

    def nettoie_champs(self):
        """Lance le nettoyage de tous les champs de la saé"""
        self.nettoie_heures_sae()
        self.nettoie_semestre()
        self.nettoie_acs()
        self.nettoie_ressources()
        self.nettoie_description()
        self.nettoie_livrables_sae()
        self.nettoie_mots_cles()
        self.nettoie_coeffs()

    def to_yaml(self):
        """Exporte la saé en yaml"""
        dico = {"titre": self.nom,
                "code": self.code,
                "semestre": int(self.semestre[1]),
                "heures_encadrees": self.heures_encadrees if self.heures_encadrees != ""
                                    else "???",
                "tp": self.tp if self.tp != "" else "???",
                "projet": self.projet if self.projet != "" else "???",
                "description": folded(self.description),
                "coeffs": self.coeffs,
                "acs": self.apprentissages,
                "ressources": self.ressources,
                "livrables": folded(self.livrables),
                "motscles": self.mots if self.mots else ""
                }
        return self.dico_to_yaml(dico)


class ExempleSAEDocx(Docx):
    """Classe modélisant les exemples de SAE tel que relu dans les Docx"""

    def __init__(self, nom, brut, code):
        self.nom = nom.rstrip()
        self.brut = brut  # les données brutes de la ressource
        self.code = code # code de la SAE à laquelle l'exemple est raccroché
        # Ajoute le semestre de la SAE
        self.semestre = int(officiel.get_officiel_sem_sae_by_code(code)[1])

    def charge_informations(self, description, formes, problematique, modalite):
        self.description = description
        self.formes = formes  # <--
        self.problematique = problematique
        self.modalite = modalite

    def nettoie_description(self):
        """Nettoie la description d'un exemple de SAE"""
        self.description = convert_to_markdown(self.description)

    def nettoie_problematique(self):
        """Nettoie la description d'un exemple de SAE"""
        if self.problematique:
            self.problematique = convert_to_markdown(self.problematique)
        else:
            self.problematique = ""

    def nettoie_modalite(self):
        """Nettoie les modalités (d'évaluation) d'un exemple de SAE"""
        if self.modalite:
            self.modalite = convert_to_markdown(self.modalite)
        else:
            self.modalite = ""

    def nettoie_formes(self):
        """Nettoie les modalités (d'évaluation) d'un exemple de SAE"""
        if self.formes:
            self.formes = convert_to_markdown(self.formes)
        else:
            self.formes = ""


    def nettoie_champs(self):
        """Déclenche le nettoyage des champs de l'exemple"""
        self.nom = self.nom.strip()
        self.nettoie_modalite()
        self.nettoie_description()
        self.nettoie_problematique()
        self.nettoie_formes()

    def to_yaml(self):
        """Exporte la ressource en yaml"""
        dico = {"titre": self.nom,
                "code": self.code,
                "semestre": self.semestre,
                "description": folded(self.description),
                "formes": folded(self.formes),
                "problematique": folded(self.problematique) if self.problematique !="" else "",
                "modalite": folded(self.modalite),
                }
        return self.dico_to_yaml(dico)

if __name__=="__main__":
    # Eléments de test
    DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
    for sem in DATA_RESSOURCES:
        for code in DATA_RESSOURCES[sem]:
            nom_data = officiel.supprime_accent_espace(DATA_RESSOURCES[sem][code])
            print(nom_data)
