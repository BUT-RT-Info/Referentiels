import logging

import pypandoc
import ruamel.yaml

from modeles import get_modele, TemplateLatex
from officiel import DATA_ACS, get_officiel_sae_name_by_code, get_officiel_ressource_name_by_code
from ressourcedocx import remove_ligne_vide
from tools import caracteres_recalcitrants


class Ressource():
    """Modélise une ressource lorsqu'elle est extraite d'un yaml"""
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.ressource = yaml.load(fid.read())
            except:
                Ressource.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")

    def to_latex(self, modele="pn/modele_ressource.tex"):
        """Génère le code latex décrivant la ressource"""
        modlatex = get_modele(modele) #"pn/modele_ressource.tex")


        if self.ressource["code"] == "R107":
            print("ici")

        # Préparation des ac
        ajoutac = "\\ajoutRac{%s}{%s}"
        compRT = []
        for accomp in self.ressource["acs"]:
            comps = []

            for no_ac in range(len(self.ressource["acs"][accomp])): # les ac de la comp
                code_ac = self.ressource["acs"][accomp][no_ac]
                comps.append( ajoutac % (code_ac, DATA_ACS[accomp][code_ac]) )
            compRT.append("\n".join(comps))

        # Préparation des sae
        ajoutsaes = "\\ajoutRsae{%s}{%s}"
        saesRT = []
        for (i, sae) in enumerate(self.ressource["sae"]): # in range(len(self.apprentissages)):
            saesRT.append(ajoutsaes % (sae, get_officiel_sae_name_by_code(sae)))
        saes = "\n".join(saesRT)

        ajoutprerequis = "\\ajoutRprerequis{%s}{%s}"
        prerequis = ""
        if self.ressource["prerequis"] == "Aucun":
            prerequis = ""
        else:
            liste = []
            for (no, mod) in enumerate(self.ressource["prerequis"]):
                liste.append(ajoutprerequis % (mod, get_officiel_ressource_name_by_code(mod)))
            prerequis = "\n".join(liste)

        # préparation du contexte
        contexte = self.ressource["contexte"]
        if contexte == "Aucun":
            contexte = ""
            Ressource.__LOGGER.warning(f"{self.ressource['nom']} n'a pas de contexte")

        else:
            contexte = contexte.replace("\n", "\n\n").replace("\n" * 4,
                                                            "\n")  # corrige les suppressions de ligne à la relecture du yaml

            output = pypandoc.convert_text(contexte, 'tex', format='md',
                                           extra_args=['--atx-headers'])
            output = output.replace("\r\n", "\n")
            contexte = caracteres_recalcitrants(output)
            contexte = remove_ligne_vide(contexte)

        # contexte = remove_ligne_vide(contexte)
        # préparation du contenu

        contenu = self.ressource["contenu"] #supprime les passages à la ligne
        contenu = contenu.replace("\n", "\n\n").replace("\n"*4, "\n") # corrige les suppressions de ligne à la relecture du yaml

        output = pypandoc.convert_text(contenu, 'tex', format='md',
            extra_args=['--atx-headers'])
        output = output.replace("\r\n", "\n")
        contenu = caracteres_recalcitrants(output)
        contenu = remove_ligne_vide(contenu)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(code=self.ressource["code"],
                                                       nom=self.ressource["nom"],
                                                       heures_formation=self.ressource["heures_formation"],
                                                       heures_tp=self.ressource["heures_tp"],
                                                       compRT1=compRT[0],
                                                       compRT2=compRT[1],
                                                       compRT3=compRT[2],
                                                       saes=saes,
                                                       motscles=caracteres_recalcitrants(self.ressource["motscles"]),
                                                       prerequis=prerequis,
                                                       contexte=caracteres_recalcitrants(contexte),
                                                       contenu=contenu,
                                                   )
        # chaine = chaine.replace("&", "\&")

        chaine = chaine.replace("\\tightlist\n", "")
        return chaine


class SAE():
    """Modélise une saé (chapeau) lorsqu'elle est extraite d'un yaml"""
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.sae = yaml.load(fid.read())
            except:
                Ressource.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")

    def to_latex(self, modele="pn/modele_sae.tex"):
        """Génère le code latex décrivant la ressource"""
        modlatex = get_modele(modele) #"pn/modele_ressource.tex")

        # Préparation des ac
        ajoutac = "\\ajoutSac{%s}{%s}"
        compRT = []
        for accomp in self.sae["acs"]:
            comps = []
            for no_ac in range(len(self.sae["acs"][accomp])): # les ac de la comp
                code_ac = self.sae["acs"][accomp][no_ac]
                comps.append( ajoutac % (code_ac, DATA_ACS[accomp][code_ac]) )
            compRT.append("\n".join(comps))

        # Préparation des ressources
        ajoutressources = "\\ajoutSressources{%s}{%s}"
        resRT = []
        for (i, res) in enumerate(self.sae["ressources"]): # in range(len(self.apprentissages)):
            resRT.append(ajoutressources % (res, get_officiel_ressource_name_by_code(res)))
        ressources = "\n".join(resRT)


        # préparation du descriptif
        descriptif = self.sae["description"]
        if descriptif == "Aucun":
            descriptif = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de description")
        else:
            descriptif = md_to_latex(descriptif)

        # préparation des livrables
        livrables = self.sae["livrables"]
        if livrables == "Aucun":
            livrables = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de livrables")
        else:
            livrables = md_to_latex(livrables)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(code=self.sae["code"],
                                                    titre=self.sae["titre"],
                                                    heures_encadrees=self.sae["heures_encadrees"],
                                                    heures_tp=self.sae["tp"],
                                                    heures_projet=self.sae["projet"],
                                                    compRT1=compRT[0],
                                                    compRT2=compRT[1],
                                                    compRT3=compRT[2],
                                                    description=caracteres_recalcitrants(descriptif),
                                                    ressources=ressources,
                                                    livrables= livrables,
                                                    motscles = caracteres_recalcitrants(self.sae["motscles"]),
                                                   )
        # chaine = chaine.replace("&", "\&")

        chaine = chaine.replace("\\tightlist\n", "")
        return chaine

class ExempleSAE():
    """Modélise un exemple de SAE lorsqu'elle est extraite d'un yaml"""
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.exemple = yaml.load(fid.read())
            except:
                Ressource.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")

    def to_latex(self, modele="pn/modele_exemple_sae.tex"):
        """Génère le code latex décrivant la ressource"""
        modlatex = get_modele(modele) #"pn/modele_ressource.tex")

        # préparation du descriptif
        description = self.exemple["description"]
        if not description:
            description = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de description")
        else:
            description = md_to_latex(description)

        # préparation de la forme
        formes = self.exemple["formes"]
        if not formes:
            formes = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de formes")
        else:
            formes = md_to_latex(formes)

        # préparation de la problématique
        problematique = self.exemple["problematique"]
        if not formes:
            problematique = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de problematique")
        else:
            problematique = md_to_latex(problematique)

        # préparation des modalites
        modalite = self.exemple["modalite"]
        if not formes:
            modalite = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de modalite")
        else:
            modalite = md_to_latex(modalite)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(titre=self.exemple["titre"],
                                                    description=description,
                                                    formes=formes,
                                                    problematique = problematique,
                                                    modalite=modalite
                                                    )
        # chaine = chaine.replace("&", "\&")

        chaine = chaine.replace("\\tightlist\n", "")
        return chaine

def md_to_latex(contenu):
    """Réalise la conversion markdown to latex avec pypandoc"""
    contenu = contenu.replace("\n", "\n\n")  # corrige les suppressions de ligne à la relecture du yaml

    contenu = pypandoc.convert_text(contenu, 'tex', format='md',
                                   extra_args=['--atx-headers'])
    contenu = contenu.replace("\r\n", "\n")
    contenu = caracteres_recalcitrants(contenu)
    contenu = remove_ligne_vide(contenu)
    lignes = contenu.split("\n") # pour debug

    if contenu.startswith("\\begin{itemize}"):
        contenu = "\\vspace{-5pt}\n" + contenu # ajout d'un offset en cas de liste à puces
    return contenu