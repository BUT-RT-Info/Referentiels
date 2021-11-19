import re, logging
import officiel
from modeles import *
import ruamel.yaml
from ruamel.yaml.scalarstring import FoldedScalarString as folded


__LOGGER = logging.getLogger(__name__)

class Docx():
    """Classe de base servant à l'héritage pour modéliser les ressources/saé/exemples lues dans les docx
    et réaliser le parsing et le nettoyage des informations.

    Les informations sont stockées dans les attributs suivants :

    * nom : le nom officiel de l'activité (d'après les données officielles du yaml)
    * code : le code officiel de l'activité (d'après le yaml) en notation pointée
    * code_docx : le code lu dans le docx (a priori en notation non pointée)
    * brut : les données brutes de la ressource/saé (contenu du docx)
    * semestre : le semestre de la ressource/saé déduit du code
    * annee : l'année (déduite du semestre)
    * apprentissages : les acs tels que décrit dans le docx
    * acs : les acs finaux après analyse des apprentissages et comparés aux données officiels (yaml)
    * mots : les mots-clés chargés ultérieurement
    * competences : les compétences tels que décrites dans le docx
    * coeffs : les coeffs décrits dans le docx pour des activités de BUT1 (old version)
    * officiel : les éléments officiels du pn (yaml)
    * parcours : les parcours concernés

    """
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, nom, code, brut, pnofficiel):
        self.nom = nom
        self.code = code
        self.codeRT = None # chargé ultérieurement
        self.brut = brut  # les données brutes de la ressource/saé
        self.semestre = None # le semestre de la ressource/saé (chargé ultérieurement)
        self.annee = None # l'année en fonction du semestre
        self.apprentissages = None # les acs tels que décrit dans le docx (chargés ultérieurement)
        self.acs = None # les acs après analyse des apprentissages
        self.mots = None # les mots-clés chargés ultérieurement
        self.competences = None # chargé ultérieurement
        self.coeffs = None # chargés ultérieurement
        self.officiel = pnofficiel # les éléments du templates officiel
        self.parcours = None # chargé ultérieurement


    def charge_ac(self, apprentissages):
        """Mutateur pour les apprentissages"""
        self.apprentissages = apprentissages


    def charge_competences(self, competences):
        """Mutateur pour les compétences"""
        self.competences = competences


    def charge_coeffs(self, coeffs):
        """Mutateur pour les coefficients"""
        self.coeffs = coeffs


    def __str__(self):
        """Affichage d'une activité"""
        print(self.nom + " " + self.code)


    def nettoie_semestre(self):
        """Pour une ressource, ou une SAE, nettoie le champ semestre"""
        old = self.semestre # le semestre indiqué dans la ressource
        semestre = self.officiel.get_sem_ressource_by_code(self.code)
        if not semestre:
            raise(f"Pb: le code {self.code} n'est rattaché à aucun semestre")
        elif semestre not in old:
            Docx.__LOGGER.warning(f"nettoie_semestre : dans {self.code} | {self.nom}, PAS de semestre ou mal détecté => rattaché à {semestre}")
        elif semestre != old:
            Docx.__LOGGER.warning(f"nettoie_semestre : dans {self.code} | {self.nom}, semestre nettoyé en {semestre}")
        self.semestre = semestre[1] # ne prend que le chiffre


    def nettoie_acs(self):
        """Nettoie les acs d'une ressource ou d'une saé,
        en les remplaçant par leur code pour les 3 compétences"""

        if self.annee == "BUT1": # vieux modèle
            if len(self.apprentissages) != 3:
                Docx.__LOGGER.warning(f"nettoie_acs : Problème dans le nombre de compétences de {self.code} | {self.nom}")

            dico = {}
            for comp in range(3): # seulement 3 comp en BUT1
                donnees = self.apprentissages[comp]  # chaine de caractères listant les ACS

                acs_avec_code = devine_acs_by_code(donnees) # récupère les codes des acs
                acs_avec_code = [ac.replace(" ", "") for ac in acs_avec_code]  # supprime les espaces inutiles

                acs_avec_nom = officiel.devine_code_acs_by_nom_from_dict(donnees, self.officiel.DATA_ACS) # récupère les codes en utilisant les noms
                acs_avec_nom = [ac.replace(" ", "") for ac in acs_avec_nom]  # supprime les espaces inutiles

                if acs_avec_code and set(acs_avec_nom).intersection(set(acs_avec_code)) != set(acs_avec_nom):
                    Docx.__LOGGER.warning(f"Dans {self.nom}, revoir les ACS : {acs_avec_code} vs {acs_avec_nom}")

                acs_finaux = sorted(list(set(acs_avec_code + acs_avec_nom)))
                if acs_finaux:
                    dico["RT" + str(comp + 1)] = acs_finaux

            self.acs = dico  # Mise à jour du champ
        else: # Cas du BUT2/BUT3 dans lequel les ACS ne sont pas rangés par compétence
            acs_avec_code = []
            for val in self.apprentissages:
                acs_avec_code.extend( devine_acs_by_code(val) )
            # Trie les acs par compétences (dans l'année du BUT concernée)
            if self.code == "R5.01":
                print("ici")
            acs = {comp: [] for comp in self.officiel.DATA_ACS[self.annee]}
            for ac in acs_avec_code:
                comp = self.officiel.get_comp_from_acs_code(ac)
                if not comp:
                    self.__LOGGER.warning(f"Pb l'{ac} n'est rattaché à aucune comp")
                else:
                    acs[comp].append(ac)
            self.acs = acs

        # supprime les champs vides
        comp_a_supprimer = [comp for comp in self.acs if not self.acs[comp]]
        for comp in comp_a_supprimer:
            del self.acs[comp]

        if not self.acs:
            self.__LOGGER.warning(f"Dans {self.code}/{self.codeRT}, pas d'ACS !!")


    def nettoie_competences(self):
        """Nettoie les compétences d'une ressource ou d'une saé,
        en les remplaçant par leur code pour les 3 compétences"""
        competences = ",".join(self.competences)
        codes = re.findall("RT\d", competences)
        for p in officiel.PARCOURS:
            codes += re.findall( p + "\d", competences)
        liste = sorted(list(set(codes)))
        self.competences = liste

        # supprime les champs vides
        comp_a_supprimer = [comp for comp in self.acs if not self.acs[comp]]
        for comp in comp_a_supprimer:
            del self.acs[comp]

        if not self.acs:
            self.__LOGGER.warning(f"Dans {self.code}/{self.codeRT}, pas d'ACS !!")


    def compare_acs_competences(self):
        """Compare les compétences déduites des acs de celles listées dans la rubrique compétence"""
        comp_des_acs = sorted(list(self.acs.keys()))
        comp = sorted(self.competences)
        if comp != comp_des_acs:
            self.__LOGGER.warning(f"Dans {self.code}/{self.codeRT} : Pb des compétences relevant d'ACs indiqués ne correspondent pas aux compétences listés (champ compétences)")


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
                    nom_purge = officiel.supprime_accent_espace(data_titres[sem][code])
                    if champ_purge.startswith(nom_purge):
                        return data_titres[sem][code] # le bon nom

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


    def nettoie_liste_ressources(self, contenu):
        """Nettoie un contenu contenant une liste ressources, en extrayant les codes ressources
        et en les fournissant les codes extraits dans une liste
        """
        DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
        R_avec_code = devine_ressources_by_code_RXXX(contenu) # les codes RXXX
        R_avec_code = [l.replace(",", "").replace(".", "").replace(" ", "") for l in R_avec_code]
        mapping_R_avec_code = [officiel.mapping_code_RXXX_vers_code_pointe(l) for l in R_avec_code]

        R_avec_code_pointe = devine_ressources_by_code_RXpXX(contenu)
        R_avec_nom = officiel.devine_code_activite_by_nom_from_dict(contenu, DATA_RESSOURCES)

        liste = mapping_R_avec_code + R_avec_code_pointe + R_avec_nom
        # liste = [l.replace(",", "").replace(".", "").replace(" ", "") for l in liste] # supprime les espaces et les ponctuations restantes
        if liste:
            if self.code == "R4.12":
                print("ici")
            return sorted(list(set(liste)))
        else:
            return []

class RessourceDocx(Docx):
    """Classe modélisant les ressources, lorsqu'elles sont extraites du docx"""
    __LOGGER = logging.getLogger(__name__)


    def charge_informations(self, codeRT, semestre, heures_encadrees, tp,
                            sae, prerequis,
                            description, mots, parcours):
        self.codeRT = codeRT.strip()
        self.semestre = semestre # <--
        self.heures_encadrees = heures_encadrees
        self.tp = tp
        self.sae = sae
        self.prerequis = prerequis
        self.description = description
        self.contexte = None # <= inutilisé à partir du BUT2/3
        self.contenu = None # <= inutilisé à partir du BUT2/3
        self.mots = mots
        self.parcours = parcours


    def nettoie_titre_ressource(self):
        """Nettoie le titre d'une ressource ou d'une SAE en utilisant les titres officiels
        fournis dans le yaml (via le dictionnaire DATA_RESSOURCES)"""
        old = self.nom

        self.nettoie_titre(self.officiel.DATA_RESSOURCES)
        titre2 = self.officiel.get_ressource_name_by_code(self.code)

        if titre2 != self.nom:
            self.nom = titre2
            RessourceDocx.__LOGGER.warning(f"nettoie_titre : {old} => titre d'après PN \"{titre2}\"")


    def nettoie_code(self):
        """Recherche le code de la forme RXXX => ne sert plus qu'à vérifier le mapping"""
        DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
        if self.codeRT:
            codes = devine_ressources_by_code_RXXX(self.codeRT)

            if len(codes) == 1: # 1 code deviné
                if codes[0] != self.codeRT:
                    raise Exception(f"Probleme dans le mapping {self.code} <-> {self.codeRT}")
            else:
                code_devine = officiel.get_code_from_nom_using_dict(self.nom, self.officiel.DATA_RESSOURCES)

                if code_devine:
                    RessourceDocx.__LOGGER.warning(f"nettoie_code : \"{self.nom}\" => code {code_devine}")
                    if code_devine != self.code:
                        raise Exception(f"Probleme dans le mapping de {self.code} <-> {self.codeRT}")

        if not self.codeRT:
            RessourceDocx.__LOGGER.warning(f"nettoie_code : \"{self.codeRT}\" => code manquant")


    def nettoie_prerequis(self):
        """Nettoie les prérequis"""
        if not self.prerequis or officiel.AUCUN_PREREQUIS.lower() in self.prerequis.lower():
            self.prerequis = officiel.AUCUN_PREREQUIS
        else:
            ressources = self.nettoie_liste_ressources(self.prerequis)
            if ressources:
                self.prerequis = ressources


    def nettoie_sae(self):
        """Nettoie le champ SAe d'une ressource en détectant les codes"""
        SAE_avec_code = devine_sae_by_code_SXX(self.sae) # <- les codes RT
        SAE_avec_code2 = devine_sae_by_code_SXpXX(self.sae) # <- les codes en notation pointé
        liste = [l.replace(".", "").replace(" ", "") for l in SAE_avec_code + SAE_avec_code2] # supprime les points
        # passe en notation pointée
        liste = [officiel.get_sae_notation_pointe(code) for code in liste]
        liste = sorted(list(set(liste))) # élimine les doublons
        self.sae = liste
        if not self.sae:
            RessourceDocx.__LOGGER.warning(f"nettoie_sae: dans {self.code} pas de SAE (:")


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


    def nettoie_parcours(self):
        PARCOURS = officiel.PARCOURS
        if self.parcours:
            self.parcours = "Tronc commun"
            self.__LOGGER.warning(f"Dans {self.code}, ajout de la mention Tronc commun")
        liste = self.parcours.split(",")
        if not liste:
            self.__LOGGER.warning(f"Dans {self.code}, PB: pas de parcours détectés")
        parcours = []
        for (i, p) in enumerate(liste):
            if p.lower() in [par.lower() for par in PARCOURS]:
                i = [par.lower() for par in PARCOURS].index(p.lower())
                parcours.append(PARCOURS[i])
            elif "tronc" in p.lower():
                parcours.extend(PARCOURS)
        self.parcours = sorted(list(set(parcours)))


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


    def nettoie_description(self):
        """Partant du contexte détaillé d'une ressource, la transforme
        en markdown en générant les listes à puces"""
        if not self.contenu or not self.contexte: # <= pas de contexte/contenu
            champs = self.description.split("\n")
            champs = [c.replace(" / ", "/") for c in champs if c]
            contenu = convert_to_markdown("\n".join(champs))
            self.description = contenu
        else:
            self.description = self.contexte + "\n" + self.contenu


    def nettoie_champ(self):
        """Lance le nettoyage des champs"""
        self.nettoie_code()
        self.nettoie_titre_ressource()
        self.nettoie_heures()

        self.nettoie_semestre()
        self.annee = officiel.Officiel.get_annee_from_semestre(self.semestre)
        self.nettoie_acs()
        self.nettoie_sae()
        self.nettoie_prerequis()
        self.nettoie_mots_cles()
        self.nettoie_coeffs()
        self.nettoie_parcours()

        # Remet en forme le descriptif
        self.split_description()
        self.nettoie_contexte()
        self.nettoie_contenu()
        self.nettoie_description()
        # print(f"{self.code} {self.semestre}")


    def to_yaml(self):
        """Exporte la ressource en yaml"""
        dico = {"nom": self.nom,
                "code": self.code,
                "libelle": self.codeRT,
                "semestre" : int(self.semestre),
                "heures_formation": self.heures_encadrees if self.heures_encadrees else "???",
                "heures_tp": self.tp if self.tp or self.tp == 0 else "???",
                "coeffs": self.coeffs,
                "acs": self.acs,
                "sae": self.sae,
                "prerequis": self.prerequis,
                "description": folded(self.description),
                "motscles": self.mots if self.mots else "",
                "parcours": self.parcours
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



def devine_acs_by_code(champ):
    """Recherche les codes des ACs dans champ ;
    ramène les codes AC0XXX à 3 chiffres.
    """
    # Recherche les codes des fiches du BUT1 de la forme ACXXX ou AC0XXX et les transforme en la nomenclature AC11
    codes3 = re.findall("AC0{0,1}[0-9][0-9][0-9]", champ) # de code à 3 chiffres (dans BUT1)

    # Supprime le 0 initial
    codes_old_modele = sorted(list(set(codes3)))
    codes_renumerote = [officiel.mapping_code_AC0XXX_vers_code_pointe(c) for c in codes_old_modele]

    # Recherche des codes des ACs de tronc commun de la forme ACXX.XX avec X<=3
    codes = re.findall(r"AC\s{0,1}\d\.{0,1}[123]\.0\d", champ)
    codes = [c.replace(" ", "").replace(".", "") for c in codes]
    codes = [officiel.ACs.get_acs_notation_pointe(c) for c in codes]

    # Recherche les codes de la forme ACXX.XXParcours
    PARCOURS = officiel.PARCOURS
    codes_parcours = []
    for p in PARCOURS:
        codes = re.findall("ACAC\s{0,1}\d\.{0,1}[123]\.0\d\s{0,1}" + p, champ)
        codes += re.findall("ACAC\s{0,1}\d\.{0,1}[123]\.0\d\s{0,1}" + p.capitalize(), champ)
        codes += re.findall("ACAC\s{0,1}\d\.{0,1}[123]\.0\d\s{0,1}" + p.upper(), champ)
        codes = sorted(list(set(codes)))

    codes = [officiel.ACs.get_acs_notation_pointe(c) for c in codes]

    return sorted(list(set(codes + codes_renumerote)))


def devine_ressources_by_code_RXXX(champ):
    """Recherche les codes ressources de la forme RXXX ou R-XXX-XXX dans champ ;
    """
    # Sans notation pointée
    codes1 = re.findall(r"R\d{3}", champ) # de code à 3 chiffres
    codes2 = re.findall(r"R\d{3}[:\|\D]", champ) # est-ce encore utile ?
    codes3 = re.findall(r"R-[a-zA-Z]{0,9}-\d{3}", champ)
    codes = codes1 + [c[:-1] for c in codes2] + codes3
    return sorted(list(set(codes)))

def devine_ressources_by_code_RXpXX(champ):
    """Recherche les codes en notation pointé"""
    # Avec notation pointee
    codes1 = re.findall(r"R\d\.\d{2}", champ)
    return sorted(list(set(codes1)))


def devine_sae_by_code_SXX(donnees):
    """Partant d'une chaine de caractères, détermine les codes des SAE (ancienne version) de la forme SAEXX"""
    codes = re.findall(r"(SA[EÉ]\s{0,1}\d\d)", donnees) # de code à 3 chiffres
    for (i, code) in enumerate(codes):
        codes[i] = codes[i].replace("E", "É")
    return sorted(list(set(codes)))


def devine_sae_by_code_SXpXX(donnees):
    """Partant d'une chaine de caractères, détermine les codes des SAE (en notation pointee) de la forme SAEXpXX"""
    codes = re.findall(r"SA[EÉ]\d\.\d\d", donnees)
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

        self.nettoie_titre(self.officiel.DATA_SAES)
        titre2 = self.officiel.get_sae_name_by_code(self.code)

        if titre2 != self.nom:
            self.nom = titre2
            SAEDocx.__LOGGER.warning(f"nettoie_titre : {old} => titre d'après PN \"{titre2}\"")

    def nettoie_code(self):
        """Recherche les codes de la forme SAE|éXX """
        DATA_SAES = officiel.get_DATA_SAES()
        if self.code:
            codes = devine_sae_by_code_SXX(self.code)
            if len(codes) == 1:
                self.code = codes[0]
            else:
                code_devine = officiel.get_code_from_nom_using_dict(self.nom, self.officiel.DATA_SAES)
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
        self.ressources = nettoie_liste_ressources(self.ressources, self.officiel.DATA_RESSOURCES)
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
        self.nettoie_competences()
        self.compare_acs_competences()
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

    def __init__(self, nom, brut, code, pnofficiel):
        self.nom = nom.rstrip()
        self.brut = brut  # les données brutes de la ressource
        self.code = code # code de la SAE à laquelle l'exemple est raccroché
        self.officiel = pnofficiel
        # Ajoute le semestre de la SAE
        self.semestre = int(self.officiel.get_sem_sae_by_code(code)[1])

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

def get_code_RXpXX_from_mapping_RXXX(code_RXXX):
    DATA_R = officiel.get_DATA_R_DOCX() # le mapping
    for sem in DATA_R:
        for code in DATA_R[sem]:
            if DATA_R[sem][code].startswith(code_RXXX):
                return code
    return None

if __name__=="__main__":
    # Eléments de test
    pass
