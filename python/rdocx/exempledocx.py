from ruamel.yaml.scalarstring import FoldedScalarString as folded

import rdocx.docx
import logging

__LOGGER = logging.getLogger(__name__)

class ExempleSAEDocx(rdocx.docx.Docx):
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
        self.description = rdocx.docx.convert_to_markdown(self.description)

    def nettoie_problematique(self):
        """Nettoie la description d'un exemple de SAE"""
        if self.problematique:
            self.problematique = rdocx.docx.convert_to_markdown(self.problematique)
        else:
            self.problematique = ""

    def nettoie_modalite(self):
        """Nettoie les modalités (d'évaluation) d'un exemple de SAE"""
        if self.modalite:
            self.modalite = rdocx.docx.convert_to_markdown(self.modalite)
        else:
            self.modalite = ""

    def nettoie_formes(self):
        """Nettoie les modalités (d'évaluation) d'un exemple de SAE"""
        if self.formes:
            self.formes = rdocx.docx.convert_to_markdown(self.formes)
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