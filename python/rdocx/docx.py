import logging
import re
import string

import ruamel.yaml

import rofficiel.officiel
import rofficiel.competences

import rdocx.tools
import tools
import copy

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

    def __init__(self, nom, code, brut, pnofficiel, complementaire=False):
        self.nom = nom
        self.code = code
        self.codeRT = None # chargé ultérieurement
        self.brut = brut  # les données brutes de la ressource/saé
        self.numero_semestre = None # le semestre de la ressource/saé (chargé ultérieurement sous forme d'une str)
        self.nom_semestre = None
        self.annee = None # l'année en fonction du semestre
        self.parcours = None  # chargé ultérieurement

        # les compétences et apprentissages critiques
        self.apprentissages = None # les acs tels que décrit dans le rdocx (chargés ultérieurement)
        self.acs = {} # les acs après analyse des apprentissages
        self.competences = {}  # chargé ultérieurement

        # les heures
        self.heures_encadrees = None
        self.details_heures_encadrees = {'cm': None, 'td': None, 'tp': None}
        self.heures_encadrees_pn = None
        self.details_heures_encadrees_pn = {'cm': None, 'td': None, 'tp': None}
        self.tableur_heures_formation = {'cm/td': None, 'tp': None, 'projet': None} # les heures du tableur
        self.tableur_heures_formation_pn = {'cm/td': None, 'tp': None} # les heures du tableur

        # adaptation locale
        self.type = {"adaptation_locale": False,
                     "complementaire": complementaire}

        # les listes de ressources ou saés associés
        self.ressources = None
        self.saes = None
        self.prerequis = None

        # les éléments descriptifs

        # {"Contexte" : '',
        # avec découpage
        self.contexte = None
        self.contenu = None
        self.prolongation = None

        self.mots = None # les mots-clés chargés ultérieurement

        self.coeffs = None # chargés ultérieurement
        self.officiel = pnofficiel # les éléments du templates officiel

        # Les info venant du tableur
        self.url = None

    def __str__(self):
        """Affichage d'une activité"""
        chaine = self.code + "/" + self.codeRT
        if self.nom:
            chaine += " : " + self.nom
        return chaine


    def __repr__(self):
        """Chaine de caractère représentant une ressource ou une SAE"""
        return self.code + "/" + self.codeRT

    def charge_infos_tableur(self, url, tableur_heures_formation, tableur_heures_formation_pn):
        self.url = url
        # charge et nettoie
        self.tableur_heures_formation = tableur_heures_formation
        self.tableur_heures_formation_pn = tableur_heures_formation_pn
        for cle in self.tableur_heures_formation:
            try:
                self.tableur_heures_formation[cle] = int(self.tableur_heures_formation[cle])
            except:
                self.tableur_heures_formation[cle] = None
                self.__LOGGER.warning(f"{self}: charge_infos_tableur: pas d'heures formation pour {cle} dans le tableur BUT-RT-S1-S6")
        for cle in self.tableur_heures_formation_pn:
            try:
                self.tableur_heures_formation_pn[cle] = int(self.tableur_heures_formation_pn[cle])
            except:
                self.tableur_heures_formation_pn[cle] = None
                self.__LOGGER.warning(f"{self}: charge_infos_tableur: pas d'heures formation pn pour {cle} dans le tableur BUT-RT-S1-S6")

    def charge_ac(self, apprentissages):
        """Mutateur pour les apprentissages"""
        self.apprentissages = apprentissages


    def charge_competences(self, competences):
        """Mutateur pour les compétences"""
        self.competences = competences


    def charge_coeffs(self, coeffs):
        """Mutateur pour les coefficients"""
        self.coeffs = coeffs


    def nettoie_semestre(self):
        """Pour une ressource ou une SAE, nettoie le champ semestre
        étant donné le semestre_officiel_decode"""
        semestre = self.officiel.get_sem_activite_by_code(self.code)
        self.nettoie_semestre_from_decode(semestre)


    def nettoie_acs(self):
        """Nettoie les acs d'une ressource ou d'une saé,
        en les remplaçant par leur code pour les 3 compétences"""

        if "Tous les AC" in "\n".join(self.apprentissages):
            self.__LOGGER.warning(f"{self}: nettoie_acs: Injecte tous les AC")
            self.acs = copy.deepcopy(self.officiel.DATA_ACS[self.annee])
            return

        if self.annee == "BUT1": # vieux modèle
            if len(self.apprentissages) != 3:
                self.__LOGGER.warning(f"{self}: nettoie_acs : Problème dans le nombre de compétences")

            dico = {}
            for comp in range(3): # seulement 3 comp en BUT1
                donnees = self.apprentissages[comp]  # chaine de caractères listant les ACS

                acs_avec_code = devine_acs_by_code(donnees) # récupère les codes des acs
                acs_avec_code = [ac.replace(" ", "") for ac in acs_avec_code]  # supprime les espaces inutiles

                acs_avec_nom = rofficiel.competences.devine_code_acs_by_nom_from_dict(donnees, self.officiel.DATA_ACS) # récupère les codes en utilisant les noms
                acs_avec_nom = [ac.replace(" ", "") for ac in acs_avec_nom]  # supprime les espaces inutiles

                if acs_avec_code and set(acs_avec_nom).intersection(set(acs_avec_code)) != set(acs_avec_nom):
                    Docx.__LOGGER.warning(f"{self.code}/{self.codeRT}, revoir les ACS : {acs_avec_code} vs {acs_avec_nom}")

                acs_finaux = sorted(list(set(acs_avec_code + acs_avec_nom)))
                if acs_finaux:
                    dico["RT" + str(comp + 1)] = acs_finaux

            self.acs = dico  # Mise à jour du champ
        else: # Cas du BUT2/BUT3 dans lequel les ACS ne sont pas rangés par compétence
            # Lecture des ACs
            acs_avec_code = []
            for val in self.apprentissages:
                acs_avec_code.extend(devine_acs_by_code(val))
            acs_avec_code = sorted(list(set(acs_avec_code)))  # supprime les doublons

            if not self.type["complementaire"]: # semestre classique
                # Trie les acs par compétences (dans l'année du BUT concernée)
                acs = {comp: [] for comp in self.officiel.DATA_ACS[self.annee]} # les compétences tout parcours
            else:
                acs = {comp: [] for comp in self.officiel.DATA_ACS["BUT2"]}

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
        for p in rofficiel.officiel.PARCOURS:
            codes += re.findall( p + "\d", competences)
        # Cherche les compétences par leur nom
        codes_par_nom = rofficiel.competences.devine_code_comp_by_nom_from_dict(competences)

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


    def nettoie_heures_cm_td(self, champ=None, type="cm"):
        """Nettoie les champs (horaires) cm/td"""
        if not champ:
            champ = self.details_heures_encadrees
        if champ[type] or champ[type] == 0:  # si les heures encadrées sont renseignées
            volumes = self.nettoie_champ_heure(champ[type])
            if isinstance(volumes, int):
                return volumes
            elif isinstance(volumes, tuple):
                return volumes[0]
            else:
                self.__LOGGER.warning(f"{self}: nettoie_heures_cm: pas d'heures {type}")


    def nettoie_adaptation_locale(self):
        """Nettoie le champ adapation locale"""
        adaptation = self.type["adaptation_locale"]
        if self.type["complementaire"]: # module complémentaire
            self.type["adaptation_locale"] = True
            self.__LOGGER.debug(f"{self}: nettoie_adaptation_locale: forcée à oui/True")
        elif adaptation and adaptation.strip() != "":
            if "oui" in adaptation.lower():
                self.type["adaptation"] = True
            else:
                self.type["adaptation"] = False
        else:
            self.type["adaptation"] = False
            self.__LOGGER.warning(f"{self}: nettoie_adaptation_locale: pas d'info sur l'adaptation locale => fixe à non")


    def nettoie_codes_dans_champ(self, contenu_md):
        """Cherche les codes de SAE ou de ressources (au format code RT) pour les remplacer par les codes Orébut"""
        # Recherche les codes de SAE
        SAE_avec_code = devine_sae_by_code_SXX(contenu_md)  # <- les codes RT
        # SAE_avec_code3 = devine_sae_by_code_SPXX(contenu_md)  # les codes avec mention du parcours
        SAE_avec_code4 = devine_sae_by_code_SAEPXX(contenu_md)

        for codeRT in SAE_avec_code + SAE_avec_code4:  # supprime les points
            code = rdocx.tools.mapping_code_SAEXX_vers_code_pointe(codeRT)
            if code:
                contenu_md = contenu_md.replace(codeRT, code)

        # Recherche des codes ressources
        R_avec_code = devine_ressources_by_code_RXXX(contenu_md)  # les codes RXXX
        R_avec_code2 = devine_ressource_by_code_RPXX(contenu_md) # les codes R-Parcours-XXX
        for codeRT in R_avec_code + R_avec_code2:
            code = rdocx.tools.mapping_code_RXXX_vers_code_pointe(codeRT)
            if code:
                contenu_md = contenu_md.replace(codeRT, code)
        return contenu_md


    def nettoie_description(self):
        """Nettoie le champ description après l'avoir splité"""
        for cle in self.description:
            if self.description[cle]:
                contenu = self.description[cle].replace(" / ", "/")
                contenu_md = convert_to_markdown(contenu)
                contenu_md = self.nettoie_codes_dans_champ(contenu_md)
                self.description[cle] = contenu_md


    def nettoie_mots_cles(self):
        """Nettoie les mots_clés (dans ressource ou SAE de BUT1)"""
        if self.mots:
            mots = self.mots  # .encode('utf8', 'ignore').decode('utf8')
            mots = mots.replace(".", "").replace(";", ",").replace(":", ",")
            liste_mots = mots.split(",")
            liste_mots = [l.strip() for l in liste_mots if l.strip()] # supprime les espaces inutiles et les lignes vides
            liste_mots = [l.capitalize()[0] + l[1:] for l in liste_mots] # mise en majuscule du 1er caractère
            mots = ", ".join(liste_mots)
            self.mots = mots
        else:
            self.mots = ""

    def nettoie_titre(self, data_titres):
        """Nettoie le titre d'une ressource ou d'une SAE en utilisant les titres officiels
        fournis dans le yaml (via le dictionnaire DATA_RESSOURCES)"""

        def devine_nom(champ, nom_semestre):
            champ_purge = tools.supprime_accent_espace(champ)
            # for sem in data_titres:
            for code in data_titres[nom_semestre]:
                nom_purge = tools.supprime_accent_espace(data_titres[nom_semestre][code])
                if champ_purge.startswith(nom_purge):
                    return data_titres[nom_semestre][code] # le bon nom

        old = self.nom # .replace(":", "-") # supprime les -
        if not self.type["complementaire"]:
            titre = devine_nom(self.nom, self.nom_semestre)
        else:
            titre = devine_nom(self.nom, "SC")
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


    def prepare_heures_yaml(self, champ):
        """Renvoie le dictionnaire affichant les heures en partant du champ donné (self.detail_heures_formation par exemple)"""
        dico = {}
        for cle in champ:
            if champ[cle] or champ[cle] == 0:
                dico[cle] = champ[cle]
            else:
                dico[cle] = "???"
        return dico



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
        old = self.nom_semestre # le semestre indiqué dans la ressource

        if not semestre_officiel_decode:
            raise Exception(f"{self}: nettoie_semestre: n'est rattaché à aucun semestre")
        else:
            if self.type["complementaire"]: # liste de semestre autorise
                semestres_decodes = []
                for no_sem in string.digits[1:7]:
                    if "S"+no_sem in self.nom_semestre:
                        semestres_decodes.append(no_sem)
                if not semestres_decodes:
                    self.numero_semestre = "C"
                    self.nom_semestre = "SC"
                else:
                    self.numero_semestre = semestres_decodes
                    self.nom_semestre = ["S" + sem for sem in semestres_decodes]
            else: # les ressources non complémentaires => mention du semestre obligatoire
                try:
                    old = "S" + str(int(old)) # lorsque le semestre a déjà été nettoyé
                except:
                    pass
                if semestre_officiel_decode not in old:
                    self.__LOGGER.warning(f"{self}: nettoie_semestre: PAS de semestre ou mal détecté => rattaché à {semestre_officiel_decode}")
                self.numero_semestre = semestre_officiel_decode[1] # ne prend que le chiffre
                self.nom_semestre = "S" + semestre_officiel_decode[1]

    def nettoie_liste_ressources(self, contenu):
        """Nettoie un contenu contenant une liste ressources, en extrayant les codes ressources
        et en les fournissant les codes extraits dans une liste
        """
        DATA_RESSOURCES = self.officiel.DATA_RESSOURCES

        # Recherche des codes
        R_avec_code = devine_ressources_by_code_RXXX(contenu) # les codes RXXX
        # R_avec_code = [l.replace(",", "").replace(".", "").replace(" ", "") for l in R_avec_code]
        R_avec_parcours = devine_ressource_by_code_RPXX(contenu)
        mapping_R_avec_code = [rdocx.tools.mapping_code_RXXX_vers_code_pointe(l) for l in R_avec_code + R_avec_parcours]

        # R_avec_code_pointe = [] # devine_ressources_by_code_RXpXX(contenu)

        # Ne conserve que les ressources d'un semestre antérieur
        #R_avec_nom = rofficiel.officiel.devine_code_activite_by_nom_from_dict(contenu, DATA_RESSOURCES)
        # R_anterieur_avec_nom = []
        # for r in mapping_R_avec_code:
        #    try:
        #        sem = int(r[1])
        #        int(self.semestre)
        #        if sem <= int(self.semestre):
        #            R_anterieur_avec_nom.append(r)
        #        else:
        #            self.__LOGGER.warning(
        #                f"{self}: nettoie_liste_ressource: des ressources postérieures au semestre sont cités")
        #    except:
        #        print("pb formattage")

        liste = [l for l in mapping_R_avec_code if l] # supprime les champs None
        # liste = [l.replace(",", "").replace(".", "").replace(" ", "") for l in liste] # supprime les espaces et les ponctuations restantes
        if liste:
            return sorted(list(set(liste)))
        else:
            return []


    def nettoie_liste_sae(self, liste):
        """Nettoie une liste de SAE"""
        SAE_avec_code = rdocx.docx.devine_sae_by_code_SXX(liste)  # <- les codes RT
        # SAE_avec_code2 = rdocx.docx.devine_sae_by_code_SXpXX(liste)  # <- les codes en notation pointé (sans parcours)
        SAE_avec_code3 = rdocx.docx.devine_sae_by_code_SAEPXX(liste) # les codes avec mention du parcours
        code = SAE_avec_code + SAE_avec_code3
        # passe en notation pointée
        liste = [rdocx.tools.mapping_code_SAEXX_vers_code_pointe(c) for c in code]
        liste = [l for l in liste if l] # supprime les champs None
        liste = sorted(list(set(liste)))  # élimine les doublons
        return liste


    def nettoie_champ_heure(self, champ):
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
        PARCOURS = rofficiel.officiel.PARCOURS
        if not parcours:
            parcours = "Tronc commun"
            self.__LOGGER.warning(f"{self.code}/{self.codeRT}: ajout en tant que \"Tronc commun\"")

        parcours = parcours.lower().strip() # mise en minuscule pour faciliter la détection

        # self.__LOGGER.warning(f"{self.code}/{self.codeRT}: PB: pas de parcours détectés")
        if parcours == "tronc commun":
            parcours = ["Tronc commun"] # corrige éventuellement l'orthographe
        else:
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

def nettoie_marqueurs(contenu):
    """Nettoie les marqueurs utilisés pour baliser les listes à puces dans les contenus et les convertir en
    marqueur markdown"""
    contenu = tools.remplace_marqueur_numerique_with_caracteres(contenu)
    marqueurs_finaux = tools.get_marqueurs(contenu)
    lignes = contenu.split("\n")
    contenus_fin =  lignes[:] # copie des ligne
    for (i, ligne) in enumerate(lignes):
        ligne = ligne[tools.indice_premier_caractere(ligne):].rstrip() # retire les espaces du début
        m = tools.get_marqueur_from_liste(ligne, marqueurs_finaux) # identifie la présence d'un marqueur dans la ligne
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

def convert_to_markdown(contenu):
    """Convertit un contenu avec des marqueurs en markdown"""
    contenu = remove_link(contenu) # supprime les liens
    contenu = nettoie_marqueurs(contenu)
    contenu = nettoie_reference_SAE_ou_ressources(contenu) # nettoie les références à des ressources et des SAEs avec codeRT
    return contenu

def nettoie_reference_SAE_ou_ressources(contenu):
    """Recherche des références à des contenus ou à des SAEs et les nettoie"""
    # recherche la référence à des SAEs (codeRT)
    codes = re.findall(r"[sS][aA][éÉeE]", contenu)
    for code in codes:
        contenu = contenu.replace(code, "SAÉ") # remplace les Saé par des majuscules

    codes = get_code_SXX(contenu)

    # recherche des références à des ressources (codeRT)
    codes += devine_ressources_by_code_RXXX(contenu)

    for (i, code) in enumerate(codes):
        code_final = mapping_code_pointe_from_codeRT(code)
        if code_final:
            contenu = contenu.replace(code, code_final)
        else:
            __LOGGER.warning(f"nettoie_reference_SAE_ou_ressources: {code} trouvé mais non mappé en notation pointé")
    return contenu


def devine_acs_by_code(champ):
    """Recherche les codes des ACs dans champ ; ramène les codes AC0XXX à 3 chiffres.
    """
    # Recherche les codes des fiches du BUT1 de la forme ACXXX ou AC0XXX et les transforme en la nomenclature AC11
    codes3 = re.findall("AC0{0,1}[0-9]{3}", champ) # de code à 3 chiffres (dans BUT1)

    # Supprime le 0 initial
    codes_old_modele = sorted(list(set(codes3)))
    codes_renumerote = [rdocx.tools.mapping_code_AC0XXX_vers_code_pointe(c) for c in codes_old_modele]

    # Recherche des codes des ACs de tronc commun de la forme ACXX.XX avec X<=3
    codes = re.findall(r"AC\s*\d\.{0,1}[123]\.0\d", champ)
    codes = [c.replace(" ", "").replace(".", "") for c in codes]
    codes_renumerote += [rofficiel.competences.ACs.get_acs_notation_pointe(c) for c in codes]

    # Recherche les codes de la forme ACXX.XXParcours
    PARCOURS = rofficiel.officiel.PARCOURS
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
    """Recherche les codes ressources de la forme RXXX ou R-XXX-XXX ou RCXX dans champ ;
    """
    # Sans notation pointée
    codes1 = re.findall(r"R\s*\d{3}", champ) # de code à 3 chiffres
    codes2 = re.findall(r"R\s*\d{3}[:\|\D]", champ) # est-ce encore utile ?
    codes3 = re.findall(r"RC\s*\d{2}", champ) # le code des modules complémentaires
    # codes3 = re.findall(r"R-[a-zA-Z]{0,9}-\d{3}", champ)
    codes = codes1 + [c[:-1] for c in codes2] + codes3
    return sorted(list(set(codes)))


def devine_ressources_by_code_RXpXX(champ):
    """Recherche les codes en notation pointé"""
    # Avec notation pointee
    codes1 = re.findall(r"R\d\.\d{2}", champ)
    return sorted(list(set(codes1)))


def mapping_code_pointe_from_codeRT(code_RXXX):
    """Partant d'un code RT (ressource ou SAE), renvoie le code pointé attribué à l'activité"""
    DATA_R = rofficiel.officiel.get_DATA_R_DOCX() # le mapping
    code_RXXX = code_RXXX.replace("É", "E").replace(" ", "")
    for sem in DATA_R:
        for code in DATA_R[sem]:
            if DATA_R[sem][code].startswith(code_RXXX):
                return code
    return None


def get_code_SXX(donnees):
    """Renvoie les codes de SAEXX trouvé"""
    codes = re.findall(r"[sS][aA][éÉeE]\s{0,1}\d\d", donnees)
    return codes

def devine_sae_by_code_SXX(donnees):
    """Partant d'une chaine de caractères, détermine les codes des SAE (ancienne version) de la forme SAEXX"""
    # codes = re.findall(r"(SA[EÉ]\s{0,1}\d\d)", donnees) # de code à 3 chiffres
    codes = get_code_SXX(donnees)
    for (i, code) in enumerate(codes):
        codes[i] = codes[i].upper().replace("E", "É")
    return sorted(list(set(codes)))

def devine_sae_by_code_SAEPXX(donnees):
    """Améliore la détection des codes de SAE de la forme SAE-Parcours-XX"""
    PARCOURS = rofficiel.officiel.PARCOURS
    mapping_parcours = {'Cyber': ['Cyber'],
                        'PilPro': ['PilPro', 'PPR'],
                        'DevCloud': ['DevCloud', 'DSC'],
                        'ROM': ['ROM'],
                        'IOM': ['IOM']}
    liste_codes = []
    for p in PARCOURS:
        for map in mapping_parcours[p]:
            reg_ex = ""
            for car in map:
                reg_ex += "[" + car.lower() + car.upper() + "]"
            codes = re.findall("[sS][aA][eéEÉ]\s*-{0,1}" + reg_ex + "-{0,1}\d\d", donnees)
            liste_codes += codes
    return sorted(list(set(liste_codes)))


def devine_ressource_by_code_RPXX(donnees):
    """Améliore la détection des codes de SAE de la forme SAE-Parcours-XX"""
    PARCOURS = rofficiel.officiel.PARCOURS
    mapping_parcours = {'Cyber': ['Cyber'],
                        'PilPro': ['PilPro', 'PPR'],
                        'DevCloud': ['DevCloud', 'DSC'],
                        'ROM': ['ROM'],
                        'IOM': ['IOM']}
    liste_codes = []
    for p in PARCOURS:
        for map in mapping_parcours[p]:
            reg_ex = ""
            for car in map:
                reg_ex += "[" + car.lower() + car.upper() + "]"
            codes = re.findall("[rR]\s*-" + reg_ex + "-\d{3}", donnees)
            liste_codes += codes
    return sorted(list(set(liste_codes)))


def devine_sae_by_code_SXpXX(donnees):
    """Partant d'une chaine de caractères, détermine les codes des SAE (en notation pointee) de la forme SAEXpXX"""
    codes = re.findall(r"SA[EÉ]\d\.\d\d", donnees)
    for (i, code) in enumerate(codes):
        codes[i] = codes[i].replace("E", "É")
    return sorted(list(set(codes)))