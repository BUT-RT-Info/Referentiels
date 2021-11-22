import logging
import re
import string

import ruamel.yaml

import officiel
# import rdocx.saedocx, rdocx.ressourcedocx

__LOGGER = logging.getLogger(__name__)



class Docx():
    """Classe de base servant à l'héritage pour modéliser les ressources/saé/exemples lues dans les rdocx
    et réaliser le parsing et le nettoyage des informations.

    Les informations sont stockées dans les attributs suivants :

    * nom : le nom officiel de l'activité (d'après les données officielles du yaml)
    * code : le code officiel de l'activité (d'après le yaml) en notation pointée
    * code_docx : le code lu dans le rdocx (a priori en notation non pointée)
    * brut : les données brutes de la ressource/saé (contenu du rdocx)
    * semestre : le semestre de la ressource/saé déduit du code
    * annee : l'année (déduite du semestre)
    * apprentissages : les acs tels que décrit dans le rdocx
    * acs : les acs finaux après analyse des apprentissages et comparés aux données officiels (yaml)
    * mots : les mots-clés chargés ultérieurement
    * competences : les compétences tels que décrites dans le rdocx
    * coeffs : les coeffs décrits dans le rdocx pour des activités de BUT1 (old version)
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
        self.apprentissages = None # les acs tels que décrit dans le rdocx (chargés ultérieurement)
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



    def nettoie_acs(self):
        """Nettoie les acs d'une ressource ou d'une saé,
        en les remplaçant par leur code pour les 3 compétences"""
        if self.code == "SAÉ1.1":
            print("ici")

        if self.annee == "BUT1": # vieux modèle
            if len(self.apprentissages) != 3:
                self.__LOGGER.warning(f"nettoie_acs : Problème dans le nombre de compétences de {self.code} | {self.nom}")

            dico = {}
            for comp in range(3): # seulement 3 comp en BUT1
                donnees = self.apprentissages[comp]  # chaine de caractères listant les ACS

                acs_avec_code = devine_acs_by_code(donnees) # récupère les codes des acs
                acs_avec_code = [ac.replace(" ", "") for ac in acs_avec_code]  # supprime les espaces inutiles

                acs_avec_nom = officiel.devine_code_acs_by_nom_from_dict(donnees, self.officiel.DATA_ACS) # récupère les codes en utilisant les noms
                acs_avec_nom = [ac.replace(" ", "") for ac in acs_avec_nom]  # supprime les espaces inutiles

                if acs_avec_code and set(acs_avec_nom).intersection(set(acs_avec_code)) != set(acs_avec_nom):
                    Docx.__LOGGER.warning(f"{self.code}/{self.codeRT}, revoir les ACS : {acs_avec_code} vs {acs_avec_nom}")

                acs_finaux = sorted(list(set(acs_avec_code + acs_avec_nom)))
                if acs_finaux:
                    dico["RT" + str(comp + 1)] = acs_finaux

            self.acs = dico  # Mise à jour du champ
        else: # Cas du BUT2/BUT3 dans lequel les ACS ne sont pas rangés par compétence
            acs_avec_code = []
            for val in self.apprentissages:
                acs_avec_code.extend( devine_acs_by_code(val) )
            acs_avec_code = sorted(list(set(acs_avec_code))) # supprime les doublons
            # Trie les acs par compétences (dans l'année du BUT concernée)
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
            self.__LOGGER.warning(f"{self.code}/{self.codeRT}: pas d'ACS !!")


    def nettoie_competences(self):
        """Nettoie les compétences d'une ressource ou d'une saé,
        en les remplaçant par leur code pour les 3 compétences"""
        competences = ",".join(self.competences)
        codes = re.findall("RT\d", competences)
        for p in officiel.PARCOURS:
            codes += re.findall( p + "\d", competences)
        # Cherche les compétences par leur nom
        codes_par_nom = officiel.devine_code_comp_by_nom_from_dict(competences)

        # MaJ des compétences
        liste = sorted(list(set(codes + codes_par_nom)))
        self.competences = liste

        if not self.competences:
            self.__LOGGER.warning(f"{self.code}/{self.codeRT}: pas de compétences !!")


    def compare_acs_competences(self):
        """Compare les compétences déduites des acs de celles listées dans la rubrique compétence"""
        comp_des_acs = sorted(list(self.acs.keys()))
        comp = sorted(self.competences)
        if comp != comp_des_acs:
            self.__LOGGER.warning(f"{self.code}/{self.codeRT}:: Pb des compétences relevant d'ACs indiqués ne correspondent pas aux compétences listés (champ compétences)")


    def nettoie_mots_cles(self):
        """Nettoie les mots_clés (dans ressource ou SAE de BUT1)"""
        if self.mots:
            mots = self.mots  # .encode('utf8', 'ignore').decode('utf8')
            mots = mots.replace(".", "").replace(";", ",").replace(":", ",")
            liste_mots = mots.split(",")
            liste_mots = [l.strip() for l in liste_mots if l.strip()] # supprime les espaces inutiles et les lignes vides
            mots = ", ".join(liste_mots)
            self.mots = mots
        else:
            self.mots = ""

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

        old = self.nom.replace(":", "-") # supprime les -
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
        if "nom" in dico:
            dico["nom"] = ruamel.yaml.scalarstring.SingleQuotedScalarString(dico["nom"]) # force les guillemets pour autoriser les ":"

        output = ruamel.yaml.dump(dico, Dumper=ruamel.yaml.RoundTripDumper,
                                  allow_unicode=True, width=100,
                                  )
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

        output = re.sub( r"(http(s)?://[\w\d:#@%/;~_?\+-=\\\.&]*[\w/])", r" [\1](\1)", output )
        # Remplace les guillemets
        # ne traite pas tous les cas, mais arrange la majorité
        output = re.sub( r"\"(.*?)\"", r"«\1»", output, flags=re.DOTALL)
        # On utilise les guillements français (ajout automatique des bons espaces)
        #output = output.replace("«", r"\og ").replace("»", r"\fg{}")
        # output = tools.check_espace(output)
        # output = output.replace("https ://", "https://")

        return output


    def nettoie_semestre_from_decode(self, semestre_officiel_decode):
        """Pour une ressource, ou une SAE, nettoie le champ semestre
        étant donné le semestre_officiel_decode"""
        old = self.semestre # le semestre indiqué dans la ressource

        if not semestre_officiel_decode:
            raise Exception(f"{self.code}/{self.codeRT}: nettoie_semestre: n'est rattaché à aucun semestre")
        else:
            if semestre_officiel_decode not in old and semestre_officiel_decode.replace("S", "Semestre ") not in old:
                if semestre_officiel_decode not in old:
                    self.__LOGGER.warning(f"{self.code}/{self.codeRT}: nettoie_semestre: PAS de semestre ou mal détecté => rattaché à {semestre_officiel_decode}")
                elif semestre_officiel_decode != old:
                    self.__LOGGER.warning(f"{self.code}/{self.codeRT}: nettoie_semestre: semestre nettoyé en {semestre_officiel_decode}")
        self.semestre = semestre_officiel_decode[1] # ne prend que le chiffre


    def nettoie_liste_ressources(self, contenu):
        """Nettoie un contenu contenant une liste ressources, en extrayant les codes ressources
        et en les fournissant les codes extraits dans une liste
        """
        DATA_RESSOURCES = self.officiel.DATA_RESSOURCES
        R_avec_code = devine_ressources_by_code_RXXX(contenu) # les codes RXXX
        R_avec_code = [l.replace(",", "").replace(".", "").replace(" ", "") for l in R_avec_code]
        mapping_R_avec_code = [officiel.mapping_code_RXXX_vers_code_pointe(l) for l in R_avec_code]

        R_avec_code_pointe = devine_ressources_by_code_RXpXX(contenu)

        # Ne conserve que les ressources d'un semestre antérieur
        R_avec_nom = officiel.devine_code_activite_by_nom_from_dict(contenu, DATA_RESSOURCES)
        R_anterieur_avec_nom = []
        for r in R_avec_nom:
            sem = int(r[1])
            try:
                int(self.semestre)
            except:
                print("pb formattage")
            if sem <= int(self.semestre):
                R_anterieur_avec_nom.append(r)



        R_code = mapping_R_avec_code + R_avec_code_pointe
        if R_code:
            if set(R_anterieur_avec_nom).intersection(set(R_code)) != set(R_code):
                self.__LOGGER.warning(f"{self.code}/{self.codeRT}: nettoie_liste_ressource: les ressources devinées avec leur nom ne sont pas compatibles dans les codes :(")

        liste = R_code + R_anterieur_avec_nom
        # liste = [l.replace(",", "").replace(".", "").replace(" ", "") for l in liste] # supprime les espaces et les ponctuations restantes
        if liste:
            return sorted(list(set(liste)))
        else:
            return []


    def nettoie_champ_heure(self, champ):
        if "R3.05" in self.code:
            print("ici")
        try: # champ contenant uniquement un nbre d'heure
            volumes = int(champ)
            return volumes
        except:
            volumes = re.findall("\d{1,2}\s*\D", champ)
            if len(volumes) == 1:
                return int(volumes[0][:-1])
            elif len(volumes) == 2:
                volumes = sorted(volumes, reverse=True)
                return (int(volumes[0][:-1]), int(volumes[1][:-1]))

    def nettoie_parcours(self, parcours):
        PARCOURS = officiel.PARCOURS
        if not parcours:
            parcours = "Tronc commun"
            self.__LOGGER.warning(f"{self.code}/{self.codeRT}: ajout en tant que \"Tronc commun\"")
        parcours = parcours.lower() # mise en minuscule pour faciliter la détection

        # self.__LOGGER.warning(f"{self.code}/{self.codeRT}: PB: pas de parcours détectés")

        parcours_officiel = []
        for p in PARCOURS:
            if p.lower() in parcours:
                parcours_officiel.append(p)
        if len(parcours_officiel) == len(PARCOURS):
            parcours = ["Tronc commun"]
            self.__LOGGER.warning(f"{self.code}/{self.codeRT}: 5 parcours => Tronc commun")
        elif len(parcours_officiel) == 0: # pas de parcours => TC
            parcours = ["Tronc commun"]
            self.__LOGGER.warning(f"{self.code}/{self.codeRT}: 0 parcours => Tronc commun")
        else:
            parcours = parcours_officiel
        return sorted(list(set(parcours)))

def remove_link(contenu):
    #liens = re.findall("(<a\s.*\">)", contenu)
    if "Cybermalveillance" in contenu:
        print("ici")
    liens = re.findall(r"(<a\shref=[\"«][\w\s\./:-]*[\"»]>)", contenu)
    for m in liens:
        contenu = contenu.replace(m, "")
    contenu = contenu.replace("</a>", "")

    # supprime les espaces dans les liens
    return contenu


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
    contenus = [ligne.strip() for ligne in contenu.split("\n")]  # les contenus

    marqueurs = []
    for ligne in contenus:
        m = re.search(r"(\t)*", ligne) # y a-t-il des tabulations ?
        if m.group() != "":
            ajout = m.group()
        else:
            ajout = ""
        ligne = ligne.replace("\t","").strip() # supprime les tabulations pour rapatrier le marqueur en début de ligne
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
    # contenu = tools.check_espace(contenu)

    contenu = remplace_marqueur_numerique_with_caracteres(contenu)
    marqueurs_finaux = get_marqueurs(contenu)
    lignes = contenu.split("\n")
    contenus_fin =  lignes[:] # copie des ligne
    for (i, ligne) in enumerate(lignes):
        ligne = ligne.lstrip() # retire les espaces du début
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


def devine_acs_by_code(champ):
    """Recherche les codes des ACs dans champ ;
    ramène les codes AC0XXX à 3 chiffres.
    """
    # Recherche les codes des fiches du BUT1 de la forme ACXXX ou AC0XXX et les transforme en la nomenclature AC11
    codes3 = re.findall("AC0{0,1}[0-9]{3}", champ) # de code à 3 chiffres (dans BUT1)

    # Supprime le 0 initial
    codes_old_modele = sorted(list(set(codes3)))
    codes_renumerote = [officiel.mapping_code_AC0XXX_vers_code_pointe(c) for c in codes_old_modele]

    # Recherche des codes des ACs de tronc commun de la forme ACXX.XX avec X<=3
    codes = re.findall(r"AC\s*\d\.{0,1}[123]\.0\d", champ)
    codes = [c.replace(" ", "").replace(".", "") for c in codes]
    codes_renumerote += [officiel.ACs.get_acs_notation_pointe(c) for c in codes]

    # Recherche les codes de la forme ACXX.XXParcours
    PARCOURS = officiel.PARCOURS
    mapping_parcours = {'Cyber': ['Cyber'],
                        'PilPro': ['PilPro', 'PPR'],
                        'DevCloud': ['DevCloud', 'DSC'],
                        'ROM': ['ROM'],
                        'IOM': ['IOM']}
    codes_parcours = []
    p_detecte = []
    minuscule = champ.lower()
    for p in PARCOURS:
        for map in mapping_parcours[p]:
            codes = re.findall("ac\s*\d\.{0,1}[45]\.0\d\s*" + map.lower(), minuscule)
            if codes:
                p_detecte += [p] # ajout du parcours
                codes = [c.replace(" ", "").replace("ac", "AC").replace(map.lower(), p) for c in codes] # recode les acs
                codes_parcours += codes
    codes_parcours = sorted(list(set(codes_parcours)))

    return sorted(list(set(codes_renumerote + codes_parcours)))


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


def get_code_RXpXX_from_mapping_RXXX(code_RXXX):
    DATA_R = officiel.get_DATA_R_DOCX() # le mapping
    for sem in DATA_R:
        for code in DATA_R[sem]:
            if DATA_R[sem][code].startswith(code_RXXX):
                return code
    return None


def devine_sae_by_code_SXX(donnees):
    """Partant d'une chaine de caractères, détermine les codes des SAE (ancienne version) de la forme SAEXX"""
    codes = re.findall(r"(SA[EÉ]\s{0,1}\d\d)", donnees) # de code à 3 chiffres
    for (i, code) in enumerate(codes):
        codes[i] = codes[i].replace("E", "É")
    return sorted(list(set(codes)))


def devine_sae_by_code_SPXX(donnees):
    # Inclut la présence d'un parcours dans le code de la SAE
    PARCOURS = officiel.PARCOURS
    mapping_parcours = {'Cyber': ['Cyber'],
                        'PilPro': ['PilPro', 'PPR'],
                        'DevCloud': ['DevCloud', 'DSC'],
                        'ROM': ['ROM'],
                        'IOM': ['IOM']}
    codes_parcours = []
    p_detecte = []
    minuscule = donnees.lower().replace("é", "e")
    for p in PARCOURS:
        for map in mapping_parcours[p]:
            codes = re.findall("sae\s*-" + map.lower() + "-\d\d", minuscule)
            if codes:
                p_detecte += [p]  # ajout du parcours
                codes = [c.replace(" ", "").replace("sae", "SAÉ").replace(map.lower(), p) for c in
                         codes]  # recode les acs
                codes_parcours += codes
    codes_parcours = sorted(list(set(codes_parcours)))

    return sorted(list(set(codes_parcours)))


def devine_sae_by_code_SXpXX(donnees):
    """Partant d'une chaine de caractères, détermine les codes des SAE (en notation pointee) de la forme SAEXpXX"""
    codes = re.findall(r"SA[EÉ]\d\.\d\d", donnees)
    for (i, code) in enumerate(codes):
        codes[i] = codes[i].replace("E", "É")
    return sorted(list(set(codes)))