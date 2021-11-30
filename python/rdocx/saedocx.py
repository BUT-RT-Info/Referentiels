import logging

from ruamel.yaml.scalarstring import FoldedScalarString as folded

import rofficiel.officiel
import rdocx.docx


class SAEDocx(rdocx.docx.Docx):
    """Classe modélisant un chapeau de SAé relu dans les rdocx"""
    __LOGGER = logging.getLogger(__name__)

    def charge_informations(self, codeRT, semestre, heures_encadrees, tp, cm, td,
                            adaptation_locale,
                            projet, objectifs, description, ressources,
                            livrables, mots, parcours):
        self.codeRT = codeRT
        self.semestre = semestre  # <--
        self.heures_encadrees = heures_encadrees
        self.tp = tp
        self.cm = cm
        self.td = td
        self.adaptation_locale = adaptation_locale
        self.projet = projet
        self.objectifs = objectifs
        self.description = description
        self.ressources = ressources
        self.livrables = livrables
        self.mots = mots
        self.parcours = parcours


    def nettoie_titre_sae(self):
        """Nettoie le titre d'une SAE en utilisant les titres officiels
        fournis dans le yaml (via le dictionnaire DATA_RESSOURCES)"""
        self.nettoie_titre(self.officiel.DATA_SAES)


    def nettoie_code(self):
        """Recherche les codes de la forme SAE|éXX """
        self.codeRT = self.codeRT.replace("SAE", "SAÉ") # ajoute les é éventuellement manquants
        if self.codeRT:
            codes = rdocx.docx.devine_sae_by_code_SXX(self.codeRT)
            codes += rdocx.docx.devine_sae_by_code_SPXX(self.codeRT) # code type SAE-IOM-53
            if len(codes) == 1:
                if codes[0].lower() != self.codeRT.lower():
                    raise Exception(f"Problème dans le mapping {self.code} <-> {self.codeRT}")

            else:
                code_devine = rofficiel.officiel.get_code_from_nom_using_dict(self.nom, self.officiel.DATA_SAES)
                if code_devine:
                    SAEDocx.__LOGGER.warning(f"nettoie_code : \"{self.nom}\" => code {code_devine}")
                    if code_devine != self.code:
                        raise Exception(f"Probleme dans le mapping de {self.code} <-> {self.codeRT}")

        if not self.codeRT:
            SAEDocx.__LOGGER.warning(f"{self.code}: nettoie_code: code/libellé court manquant")


    def nettoie_heures_sae(self):
        """Nettoie les champs (horaires) des saes"""
        if self.heures_encadrees:  # si les heures encadrées sont renseignées
            self.heures_encadrees = self.nettoie_champ_heure(self.heures_encadrees)
        else:
            SAEDocx.__LOGGER.warning(f"nettoie_heures_sae: dans {self.nom}, manque les heures de formation")
            self.heures_encadrees = "???"

        if self.tp or self.tp == 0:
            self.tp = self.nettoie_champ_heure(self.tp)
        else:
            SAEDocx.__LOGGER.warning(f"nettoie_heures_sae: dans {self.nom}, manque les heures de tp")
            self.tp = "???"

        try:
            if self.heures_encadrees < self.tp:
                SAEDocx.__LOGGER.warning(f"nettoie_heures_sae: dans {self.nom}, pb dans les heures formations/tp")
        except:
            pass


    def nettoie_heures_projets(self):
        """Nettoie les heures projets"""
        if self.projet:
            if self.code == "SAÉ16":
                self.projet = 0
                SAEDocx.__LOGGER.warning("SAÉ16 : heures projet mise à 0")
            else:
                self.projet = self.nettoie_champ_heure(self.projet)
        else:
            SAEDocx.__LOGGER.warning(f"nettoie_heures_sae: dans {self.nom}, manque les heures de projet")
            self.projet = "???"



    def nettoie_livrables_sae(self):
        """Partant du contenu détaillé d'une ressource, la transforme
        en markdown en générant les listes à puces"""
        if self.livrables:
            self.livrables = rdocx.docx.convert_to_markdown(self.livrables)
        else:
            self.livrables = ""


    def nettoie_ressources(self):
        """Nettoie le champ ressource d'une sae en détectant les codes"""
        if self.ressources:
            liste_ressources = self.nettoie_liste_ressources(self.ressources)
            self.ressources = liste_ressources
        else:
            self.ressources = []
        if not self.ressources:
            SAEDocx.__LOGGER.warning(f"{self.code}/{self.codeRT}: nettoie_ressources: pas de ressources (:")

    def nettoie_description(self):
        """Nettoie le champ description"""
        if self.description:
            self.description = rdocx.docx.convert_to_markdown(self.description)
        else:
            self.description = ""


    def nettoie_objectifs(self):
        """Nettoie le champ objectifs"""
        if self.objectifs:
            self.objectifs = rdocx.docx.convert_to_markdown(self.objectifs)
        else:
            self.objectifs = ""


    def nettoie_champs(self):
        """Lance le nettoyage de tous les champs de la SAé"""
        self.nettoie_code()
        self.nettoie_titre_sae()

        self.nettoie_heures_sae()
        self.nettoie_heures_cm_td()
        self.nettoie_heures_projets()

        self.nettoie_adaptation_locale()

        self.nettoie_semestre()
        self.annee = rofficiel.officiel.Officiel.get_annee_from_semestre(self.semestre)

        self.nettoie_acs()
        self.nettoie_competences()
        self.compare_acs_competences()

        self.nettoie_ressources()
        self.nettoie_description()
        self.nettoie_objectifs()
        self.nettoie_livrables_sae()
        self.nettoie_mots_cles()
        self.nettoie_coeffs()

        self.parcours = self.nettoie_parcours(self.parcours)

    def to_yaml(self):
        """Exporte la saé en yaml"""
        dico = {"nom": self.nom,
                "code": self.code,
                "codeRT": self.codeRT,
                "libelle": self.codeRT,
                "semestre": int(self.semestre),
                "annee": self.annee,
                "parcours": self.parcours,
                "heures_formation": self.heures_encadrees if self.heures_encadrees != "" else "???",
                "heures_cm": self.cm if self.cm or self.cm == 0 else "???",
                "heures_td": self.td if self.td or self.td == 0 else "???",
                "heures_tp": self.tp if self.tp != "" else "???",
                "heures_formation_pn": "???",
                "heures_cm_pn": "???",
                "heures_td_pn": "???",
                "heures_tp_pn": "???",
                "heures_projet": self.projet if self.projet != "" else "???",
                "heures_projet_pn": "???",
                "adaptation_locale": "oui" if self.adaptation_locale.lower() == "oui" else "non",
                "coeffs": self.coeffs,
                "competences": self.competences,
                "acs": self.acs,
                "ressources": self.ressources,
                "objectifs": folded(self.objectifs),
                "description": folded(self.description) if self.description else "",
                "livrables": folded(self.livrables),
                "motscles": self.mots
                }
        return self.dico_to_yaml(dico)


