import logging

import rpn.latex
from config import Config
import rpn.activite
import modeles

class SAE(rpn.activite.ActivitePedagogique):
    """Modélise une SAé (chapeau) en chargeant les données provenant du ``fichieryaml``
    et stocke les données ``officiel``les.
    """

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        super().__init__(fichieryaml, officiel)
        self.nom = self.yaml["nom"]
        self.acs = self.yaml["acs"]

        # self.competences = self.yaml["competences"]
        self.annee = self.yaml["annee"]
        # self.heures_encadrees = self.yaml["heures_encadrees"]
        self.parcours = self.yaml["parcours"]

        self.heures_formation = self.yaml["heures_formation"]
        self.heures_formation_pn = self.yaml["heures_formation_pn"]
        self.details_heures_formation = self.yaml["details_heures_formation"]
        self.details_heures_formation_pn = self.yaml["details_heures_formation_pn"]
        self.heures_projet = self.yaml["heures_projet"]
        self.heures_projet_pn = self.yaml["heures_projet_pn"]

        # L'adaptation locale
        self.adaptation_locale = self.yaml["adaptation_locale"]

        self.exemples = [] # la liste des exemples


    def charge_exemple(self, e):
        """Charge un exemple"""
        self.exemples.append(e)


    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_tableau_sae.tex"):
        """Génère le code latex décrivant la saé en utilisant le template latex donné
        dans ``modele``
        """
        modlatex = modeles.get_modele(modele)  # "templates/modele_ressource.tex")

        # La liste des compétences, des acs (et des coeffs)
        latex_competences = self.to_latex_competences_et_acs()

        # Préparation des ressources
        latex_ressource = self.to_latex_liste_fiches(self.yaml["ressources"])

        # Préparation des objectifs
        objectifs = self.yaml["objectifs"]
        if not objectifs:
            latex_objectifs = ""
        else:
            latex_objectifs = rpn.latex.md_to_latex(objectifs, self.officiel.DATA_MOTSCLES)

        # préparation de la description générique
        latex_descriptif = self.prepare_descriptif()

        # Prépare les parcours
        latex_parcours = ", ".join(self.yaml["parcours"])

        # Prépare les infos sur le cursus
        latex_cursus = self.prepare_cursus()


        # Prépare les heures du tableur de Frédéric
        if isinstance(self.yaml["tableur_heures_formation"]["cm/td"], int) and isinstance(self.yaml["tableur_heures_formation"]["tp"], int):
            tableur_heures_formation_encadree = self.yaml["tableur_heures_formation"]["cm/td"] + self.yaml["tableur_heures_formation"]["tp"]
        else:
            tableur_heures_formation_encadree = "???"
        if isinstance(self.yaml["tableur_heures_formation_pn"]["cm/td"], int) and isinstance(self.yaml["tableur_heures_formation_pn"]["tp"], int):
            tableur_heures_formation_encadree_pn = self.yaml["tableur_heures_formation_pn"]["cm/td"] + self.yaml["tableur_heures_formation_pn"]["tp"]
        else:
            tableur_heures_formation_encadree_pn = "???"

        # Prépare les heures des fiches (aec éventuel détail CM/TD/TP)
        heures_acd = []
        for cle in ["cm", "td", "tp"]:
            if self.details_heures_formation[cle] != "???" and isinstance(self.details_heures_formation[cle], int):
                heures_acd.append(str(self.details_heures_formation[cle]) + "h " + cle.upper())
        heures_acd = ", ".join(heures_acd)

        # Injection dans le template
        chaine = modeles.TemplateLatex(modlatex).substitute(
            codelatex=self.get_code_latex_hyperlink(self.code),
            code=self.code,
            codeRT=self.codeRT,
            url=rpn.latex.md_to_latex(self.yaml["url"] if "url" in self.yaml else "", self.officiel.DATA_MOTSCLES),
            nom=self.prepare_nom(),
            cursus=latex_cursus,
            heures_formation=self.heures_formation,
            heures_acd=heures_acd,
            # heures_tp=self.details_heures_formation["tp"],
            # heures_cm=self.details_heures_formation["cm"],
            # heures_td=self.details_heures_formation["td"],
            # heures_formation_pn=self.heures_formation_pn,
            # heures_tp_pn=self.details_heures_formation_pn["tp"],
            # heures_cm_pn=self.details_heures_formation_pn["cm"],
            # heures_td_pn=self.details_heures_formation_pn["td"],
            heures_projet=self.heures_projet,
            # heures_projet_pn=self.heures_projet_pn,
            tableur_heures_formation=tableur_heures_formation_encadree,
            tableur_heures_cm_td=self.yaml["tableur_heures_formation"]["cm/td"],
            tableur_heures_tp=self.yaml["tableur_heures_formation"]["tp"],
            tableur_heures_formation_pn=tableur_heures_formation_encadree_pn,
            tableur_heures_cm_td_pn=self.yaml["tableur_heures_formation_pn"]["cm/td"],
            tableur_heures_tp_pn=self.yaml["tableur_heures_formation_pn"]["tp"],
            tableur_heures_projet=self.yaml["tableur_heures_formation"]["projet"],
            parcours=latex_parcours,
            objectifs=rpn.latex.nettoie_latex(latex_objectifs, self.officiel.DATA_ABBREVIATIONS),
            description=latex_descriptif,
            competences_et_acs=latex_competences,
            listeRessources=latex_ressource
            # listeExemples = A FAIRE
        )
        # chaine = chaine.replace("&", "\&")
        # Ajoute à la chaine les exemples
        if self.exemples: # le tableau donnant la liste des exemples
            chaine += "\n"
            chaine += self.to_latex_tableau_exemples()

        contenu = []
        for (i, e) in enumerate(self.exemples):
            contenu.append(e.to_latex(i+1))
        chaine += "\n\n".join(contenu)

        return chaine

    def to_latex_tableau_exemples(self):
        chaine = ""
        if self.exemples:
            chaine += "\\begin{tabular}[t]{|P|T|}\n"
            chaine += "\\hline\n"
            chaine += "\\begin{tabular}[t]{@{}P@{}}\n"
            chaine += " \\bfseries \\textcolor{saeC}{Exemples de} \\tabularnewline\n"
            chaine += " \\bfseries \\textcolor{saeC}{mise en \oe{}uvre}\n"
            chaine += "\end{tabular}\n"
            chaine += " & \n"
            chaine += ""
            chaine += "\\begin{tabular}[t]{@{}T@{}}\n"
            aff = []
            for (i, e) in enumerate(self.exemples):
                aff.append(e.get_titre_numerote(i+1, option="hyperlink"))
            chaine += "\n\\tabularnewline\n".join(aff)
            chaine += "\n\\tabularnewline\n"
            chaine += "\\end{tabular}\n"
            chaine += "\\\\\n"
            chaine += "\\hline\n"
            chaine += "\\end{tabular}\n"
        return chaine

    def prepare_descriptif(self):
        """Prépare le descriptif, avec dans le cas des SAEs de BUT1, fusion des livrables et des mots-clés"""

        champs = []

        descriptif = self.yaml["description"]
        latex_description = ""
        if descriptif:
            latex_description = rpn.latex.md_to_latex(descriptif, self.officiel.DATA_MOTSCLES)

        # préparation des livrables
        livrables = self.yaml["livrables"]
        latex_livrables = ""
        if livrables and livrables != "Aucun":
            latex_livrables = self.to_latex_champ_titre("Type de livrables ou de productions", self.yaml["livrables"])

        # préparation des prolongements
        latex_prolongements = ""
        if self.yaml["motscles"]:
            latex_prolongements = self.to_latex_champ_titre("Prolongements possibles", self.yaml["prolongements"] + ".")

        # préparation des mots-clés
        latex_mots = ""
        if self.yaml["motscles"]:
            latex_mots = self.to_latex_champ_titre("Mots-clés", self.yaml["motscles"] + ".")

        if not latex_livrables and not latex_mots:
            return latex_description
        else:
            champs = []
            if latex_description:
                latex_description = self.to_latex_champ_titre("Description", self.yaml["description"])
                champs.append(latex_description)
            if latex_livrables:
                champs.append(latex_livrables)
            if latex_prolongements:
                champs.append(latex_prolongements)
            if latex_mots:
                champs.append(latex_mots)
            return "\n\n\\vspace{0.2cm}\n".join(champs)
