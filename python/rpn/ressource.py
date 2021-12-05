import logging

import rpn.latex
from config import Config
import rpn.activite
import modeles, string
import rofficiel.officiel

class Ressource(rpn.activite.ActivitePedagogique):
    """Modélise une ressource."""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        """Initialise les informations sur la ressource à partir du ``fichieryaml``
        et stocke les données ``officiel``les
        """
        super().__init__(fichieryaml, officiel)
        self.nom = self.yaml["nom"]
        self.acs = self.yaml["acs"]
        self.annee = self.yaml["annee"]
        self.parcours = self.yaml["parcours"]
        # self.competences = self.yaml["competences"]

        # Les heures
        self.heures_formation = self.yaml["heures_formation"]
        self.heures_formation_pn = self.yaml["heures_formation_pn"]
        self.details_heures_formation = self.yaml["details_heures_formation"]
        self.details_heures_formation_pn = self.yaml["details_heures_formation_pn"]
        self.heures_projet = 0
        self.heures_projet_pn = 0

        # L'adaptation locale
        self.type = self.yaml["type"]
        self.adaptation_locale = self.yaml["type"]["adaptation_locale"]



    def prepare_prerequis(self):
        """Prépare l'affichage des pré-requis"""
        if self.yaml["prerequis"] == rofficiel.officiel.AUCUN_PREREQUIS:
            latex_prerequis = "\\textit{Aucun}"
        else:
            # est-une liste de ressources
            if not self.yaml["prerequis"][0].startswith("R"):
                latex_prerequis = self.yaml["prerequis"]
            else:
                latex_prerequis = self.to_latex_liste_fiches(self.yaml["prerequis"])
        return latex_prerequis

    def prepare_contexte(self):
        """Prépare le contexte/contenu/objectifs/prolongements)"""
        if not self.yaml["contexte"] or self.yaml["contexte"] == "Aucun":
            contexte = "Aucun"
        else:
            contexte = self.yaml["contexte"]
        return rpn.latex.md_to_latex(contexte, self.officiel.DATA_MOTSCLES)

    def prepare_description(self):
        """Prépare les contenus"""
        champ = []

        # contexte obligatoire
        contexte = self.yaml["contexte"]
        latex_contexte = ""
        if contexte:
            latex_contexte = self.to_latex_champ_titre("Contexte et ancrage professionnel", contexte)

        contenus = self.yaml["contenus"]
        latex_contenus = ""
        if contenus:
            latex_contenus = self.to_latex_champ_titre("Contenus", contenus)
            if latex_contenus.endswith("\n"):
                latex_contenus = latex_contenus[:-1]  # supprime le dernier passage à la ligne

        # optionnel
        prolongement = self.yaml["prolongements"]
        latex_prolongement = ""
        if prolongement:
            latex_prolongement = self.to_latex_champ_titre("Prolongements", prolongement)

        champ.append(latex_contexte)
        champ.append(latex_contenus)
        if latex_prolongement:
            champ.append(latex_prolongement)
        return "\n\n\\vspace{0.2cm}\n".join(champ)


    def prepare_exemple(self):
        """Prépare l'exemple de mise en oeuvre"""
        if self.yaml["exemple"]:
            latex_exemple = "\\begin{tabular}{|G|}\n"
            latex_exemple += "\\hline\n"
            latex_exemple += "\\textcolor{ressourceC}{\\bfseries Exemple de mise en \\oe{}uvre} \\\\\n"
            latex_exemple += "\\hline\n"
            latex_exemple += rpn.latex.md_to_latex(self.yaml["exemple"], self.officiel.DATA_MOTSCLES)
            latex_exemple += "\\\\\n\\hline\n"
            latex_exemple += "\\end{tabular}\n"
        else:
            latex_exemple = ""
        return latex_exemple


    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_tableau_ressource.tex"):
        """Génère le code latex décrivant la fiche de la ressource avec une mise en forme
        sous forme de tableau, en utilisant le template latex donné dans ``modele``.
        """
        modlatex = modeles.get_modele(modele)

        # Préparation des compétences, des ACs et des coeffs \ajoutRcomp + \ajoutRcoeff + boucle \ajoutRacs
        latex_competences = self.to_latex_competences_et_acs()

        # Préparation des sae
        latex_sae = self.to_latex_liste_fiches(self.yaml["sae"])

        # Préparation des prérequis
        latex_prerequis = self.prepare_prerequis()

        # préparation de la description
        latex_description = self.prepare_description()

        # Prépare les parcours
        latex_parcours = ", ".join(self.yaml["parcours"])

        # Prépare les infos sur le cursus
        latex_cursus = self.prepare_cursus()

        # Prépare l'exemple
        latex_exemple = self.prepare_exemple()

        # Prépare les heures du tableur
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
            cursus= latex_cursus,
            heures_formation=self.heures_formation if isinstance(self.heures_formation, int) else "???",
            heures_acd= heures_acd,
            #heures_tp=self.details_heures_formation["tp"],
            #heures_cm=self.details_heures_formation["cm"],
            #heures_td=self.details_heures_formation["td"],
            # heures_formation_pn=self.heures_formation_pn,
            # heures_tp_pn=self.details_heures_formation_pn["tp"],
            # heures_cm_pn=self.details_heures_formation_pn["cm"],
            # heures_td_pn=self.details_heures_formation_pn["td"],
            tableur_heures_formation=tableur_heures_formation_encadree,
            tableur_heures_cm_td=self.yaml["tableur_heures_formation"]["cm/td"],
            tableur_heures_tp=self.yaml["tableur_heures_formation"]["tp"],
            tableur_heures_formation_pn=tableur_heures_formation_encadree_pn,
            tableur_heures_cm_td_pn=self.yaml["tableur_heures_formation_pn"]["cm/td"],
            tableur_heures_tp_pn=self.yaml["tableur_heures_formation_pn"]["tp"],
            parcours=latex_parcours,
            description=latex_description,
            exemple=rpn.latex.nettoie_latex(latex_exemple,
                                             self.officiel.DATA_ABBREVIATIONS),
            competences_et_acs=latex_competences, # les compétences
            listeSAE=latex_sae,
            listePreRequis=latex_prerequis,
            motsCles=rpn.latex.nettoie_latex(self.yaml["motscles"] + ".",
                                             self.officiel.DATA_ABBREVIATIONS) if self.yaml["motscles"] else ""
        )
        # contenu=rpn.latex.nettoie_latex(latex_contenu, self.officiel.DATA_ABBREVIATIONS),
        # chaine = chaine.replace("&", "\&")
        # chaine = rpn.latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)

        # Insère les abbréviations
        return chaine

