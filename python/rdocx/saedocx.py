import logging

from ruamel.yaml.scalarstring import FoldedScalarString as folded

import rofficiel.officiel
import rdocx.docx
import tools

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
        self.details_heures_encadrees = {'cm': cm, 'td': td, 'tp': tp}

        self.adaptation_locale = adaptation_locale
        self.projet = projet
        self.objectifs = objectifs
        self.descr = description # la description
        ## pour les saes
        self.description = {"description": "",
                            "type de livrables": "",
                            "prolongements": "",
                            "mots": ""}
        self.ressources = ressources
        self.livrables = livrables # => à renvoyer dans self.description
        self.mots = mots # => à renvoyer dans self.description
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
            codes += rdocx.docx.devine_sae_by_code_SAEPXX(self.codeRT) # code type SAE-IOM-53
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
            SAEDocx.__LOGGER.warning(f"{self}: nettoie_heures_sae: manque les heures de formation")
            self.heures_encadrees = "???"

        if self.details_heures_encadrees["tp"] or self.details_heures_encadrees["tp"] == 0:
            self.details_heures_encadrees["tp"] = self.nettoie_champ_heure(self.details_heures_encadrees["tp"])
        else:
            SAEDocx.__LOGGER.warning(f"{self}: nettoie_heures_sae:  manque les heures de tp")
            self.details_heures_encadrees["tp"] = "???"

        try:
            if self.heures_encadrees < self.details_heures_encadrees["tp"]:
                SAEDocx.__LOGGER.warning(f"{self}: nettoie_heures_sae: pb dans les heures formations/tp")
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
            livrables = rdocx.docx.convert_to_markdown(self.livrables)
            livrables = self.nettoie_codes_dans_champ(livrables)
            self.description["type de livrables"] += livrables # injecte dans description



    def nettoie_ressources(self):
        """Nettoie le champ ressource d'une sae en détectant les codes"""
        if self.ressources:
            liste_ressources = self.nettoie_liste_ressources(self.ressources)
            self.ressources = liste_ressources
        else:
            self.ressources = []
        if not self.ressources:
            SAEDocx.__LOGGER.warning(f"{self.code}/{self.codeRT}: nettoie_ressources: pas de ressources (:")


    def nettoie_objectifs(self):
        """Nettoie le champ objectifs"""
        if self.objectifs:
            self.objectifs = rdocx.docx.convert_to_markdown(self.objectifs)
        else:
            self.objectifs = ""


    def split_description(self):
        """Découpe le champ description en description/type livrable/prolongement/mots-clés;
        si pas possible place dans contenu"""
        # if self.code == "R110":
        #    print("ici")
        description = {**self.description} # copie du dictionnaire description

        if self.descr:
            lignes = self.descr.split("\n")
            lignes = [c for c in lignes if c]  # supprime les lignes vides

            indices = {cle: -1 for cle in description}
            for id in description:
                presence = [ligne.lower().startswith(id) for ligne in lignes]
                if True in presence: # la ligne commençant par l'identifiant
                    indices[id] = presence.index(True)

            champs_ordonnes = sorted(indices, key=lambda cle: indices[cle]) # tri par indice croissant

            # -1 -1 -1 -1 => tout dans contenu
            if list(indices.values()).count(-1) == len(description):
                description["description"] = lignes[:]
            # sinon 1 marqueur a été trouvé
            else:
                for (i, cle) in enumerate(champs_ordonnes):
                    if indices[cle] >= 0: # si la clé est trouvée
                        if i < len(champs_ordonnes) -1: # pas le dernier champ
                            champ_suivant = champs_ordonnes[i+1]
                            description[cle] = lignes[indices[cle]+1:indices[champ_suivant]]
                        else:
                            description[cle] = lignes[indices[cle]+1:]

            # suppression des lignes vides
            for cle in description:
                lignes_conservees = tools.remove_ligne_vide(description[cle])
                chaine = "\n".join(lignes_conservees)
                description[cle] = rdocx.docx.remove_link(chaine)
                if not description[cle]:
                    self.__LOGGER.warning(f"{self}: split_description: description > {cle} manquant")
            # sauvegarde
            self.description = {"description": description["description"],
                            "type de livrables": description["type de livrables"],
                            "prolongements": description["prolongements"],
                            "mots": description["mots"]}
        # sinon self.descr vide



    def nettoie_champs(self):
        """Lance le nettoyage de tous les champs de la SAé"""
        self.nettoie_code()
        self.nettoie_titre_sae()

        for type in ["cm", "td", "tp"]:
            self.details_heures_encadrees[type] = self.nettoie_heures_cm_td(self.details_heures_encadrees, type)
        self.nettoie_heures_sae()
        self.nettoie_heures_projets()

        self.nettoie_adaptation_locale()

        self.nettoie_semestre()
        self.annee = rofficiel.officiel.Officiel.get_annee_from_semestre(self.semestre)

        self.nettoie_acs()
        self.nettoie_competences()
        self.compare_acs_competences()

        self.nettoie_ressources()

        self.nettoie_objectifs()

        # La description
        self.split_description() # découpe le champ descr en 4
        self.nettoie_description()

        self.nettoie_livrables_sae() # injecte les livrables si exi
        self.nettoie_mots_cles()
        if self.mots:
            self.description["mots"] += self.mots


        self.nettoie_coeffs()

        self.parcours = self.nettoie_parcours(self.parcours)

    def to_yaml(self):
        """Exporte la saé en yaml"""
        dico = {"nom": self.nom,
                "code": self.code,
                "codeRT": self.codeRT,
                "libelle": self.codeRT,
                "url": folded(self.url),
                "semestre": int(self.semestre),
                "annee": self.annee,
                "parcours": self.parcours,
                "heures_formation": self.heures_encadrees if self.heures_encadrees != "" else "???",
                "details_heures_formation": self.prepare_heures_yaml(self.details_heures_encadrees),
                "heures_formation_pn": self.heures_encadrees_pn if self.heures_encadrees_pn else "???",
                "details_heures_formation_pn": self.prepare_heures_yaml(self.details_heures_encadrees_pn),
                "tableur_heures_formation": self.prepare_heures_yaml(self.tableur_heures_formation),
                "tableur_heures_formation_pn": self.prepare_heures_yaml(self.tableur_heures_formation_pn),
                "heures_projet": self.projet if self.projet != "" else "???",
                "heures_projet_pn": "???",
                "adaptation_locale": "oui" if self.adaptation_locale.lower() == "oui" else "non",
                "coeffs": self.coeffs,
                "competences": self.competences,
                "acs": self.acs,
                "ressources": self.ressources,
                "objectifs": folded(self.objectifs),
                "description": folded(self.description["description"]) if self.description["description"] else "",
                "livrables": folded(self.description["type de livrables"]) if self.description["type de livrables"] else "",
                "prolongements" : folded(self.description["prolongements"]) if self.description["prolongements"] else "",
                "motscles": folded(self.description["mots"]) if self.description["mots"] else "",
                }
        return self.dico_to_yaml(dico)


