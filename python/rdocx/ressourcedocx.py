import logging

from ruamel.yaml.scalarstring import FoldedScalarString as folded

import officiel
import rdocx.docx
import tools


class RessourceDocx(rdocx.docx.Docx):
    """Classe modélisant les ressources, lorsqu'elles sont extraites du rdocx"""
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
        self.nettoie_titre(self.officiel.DATA_RESSOURCES)


    def nettoie_semestre(self):
        """Pour une ressource, ou une SAE, nettoie le champ semestre
        étant donné le semestre_officiel_decode"""
        semestre = self.officiel.get_sem_ressource_by_code(self.code)
        self.nettoie_semestre_from_decode(semestre)


    def nettoie_code(self):
        """Recherche le code de la forme RXXX => ne sert plus qu'à vérifier le mapping"""
        if self.codeRT:
            codes = rdocx.docx.devine_ressources_by_code_RXXX(self.codeRT)

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
            RessourceDocx.__LOGGER.warning("{self.code}: nettoie_code: code/libellé court manquant")


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
        SAE_avec_code = rdocx.docx.devine_sae_by_code_SXX(self.sae) # <- les codes RT
        SAE_avec_code2 = rdocx.docx.devine_sae_by_code_SXpXX(self.sae) # <- les codes en notation pointé
        liste = [l.replace(".", "").replace(" ", "") for l in SAE_avec_code + SAE_avec_code2] # supprime les points
        # passe en notation pointée
        liste = [officiel.get_sae_notation_pointe(code) for code in liste]
        liste = sorted(list(set(liste))) # élimine les doublons
        self.sae = liste
        if not self.sae:
            RessourceDocx.__LOGGER.warning(f"{self.code}/{self.codeRT}: nettoie_sae:  pas de SAE (:")


    def nettoie_heures(self):
        """Nettoie le champ (horaire) (de la forme 46h ou 33...) pour en extraire la valeur numérique :
        le champ peut contenir 2 volumes (heures formation puis heures tp), auquel cas les 2 valeurs sont renvoyées
        dans un tuple"""
        volumes = None
        if self.heures_encadrees:  # si les heures encadrées sont renseignées
            volumes = self.nettoie_champ_heure(self.heures_encadrees)
        if self.tp:
            self.tp = self.nettoie_champ_heure(self.tp)

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
        if True in [ligne.startswith("Contexte ") for ligne in champs]:  # la ligne commençant par Contenus
            indicea = [ligne.startswith("Contexte ") for ligne in champs].index(True)

        indicec = -1
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
            if indicec >= 0:
                contexte = champs[:indicec]
            else:
                contexte = "" # Pas de contexte
        # suppression des lignes vides
        contexte = "\n".join(tools.remove_ligne_vide(contexte))
        # suppression des liens

        contexte = rdocx.docx.remove_link(contexte)
        if not contexte:
            contexte = "Aucun"
        if indicec == -1:
            contenu = "\n".join(champs[indicec + 1:])
        else:
            contenu = "\n".join(champs[indicec + 1:])

        # sauvegarde des champs
        self.contexte = contexte
        self.contenu = contenu


    def nettoie_contenu(self):
        """Partant du contenu détaillé d'une ressource, la transforme
        en markdown en générant les listes à puces"""
        contenu = self.contenu.replace(" / ", "/")
        self.contenu = rdocx.docx.convert_to_markdown(contenu)


    def nettoie_contexte(self):
        """Partant du contexte détaillé d'une ressource, la transforme
        en markdown en générant les listes à puces"""
        contexte = self.contexte.replace(" / ", "/")
        self.contexte = rdocx.docx.convert_to_markdown(contexte)


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
        self.parcours = self.nettoie_parcours(self.parcours)

        # Remet en forme le descriptif
        self.split_description()
        self.nettoie_contexte()
        self.nettoie_contenu()
        # self.nettoie_description()
        # print(f"{self.code} {self.semestre}")


    def to_yaml(self):
        """Exporte la ressource en yaml"""
        dico = {"nom": self.nom,
                "code": self.code,
                "codeRT": self.codeRT,
                "libelle": self.codeRT,
                "semestre" : int(self.semestre),
                "annee": self.annee,
                "heures_formation": self.heures_encadrees if self.heures_encadrees else "???",
                "heures_tp": self.tp if self.tp or self.tp == 0 else "???",
                "coeffs": self.coeffs,
                "acs": self.acs,
                "sae": self.sae,
                "prerequis": self.prerequis,
                "contexte": folded(self.contexte),
                "contenu": folded(self.contenu),
                "motscles": self.mots if self.mots else "",
                "parcours": self.parcours
                }
        return self.dico_to_yaml(dico)


