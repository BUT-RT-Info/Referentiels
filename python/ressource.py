import logging

import pypandoc
import ruamel.yaml

from modeles import get_modele, TemplateLatex
from officiel import DATA_ACS, get_officiel_sae_name_by_code, get_officiel_ressource_name_by_code
from ressourcedocx import caracteres_recalcitrants, remove_ligne_vide


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

    def str_to_latex(self, modele="pn/modele_ressource.tex"):
        """Génère le code latex décrivant la ressource"""
        modlatex = get_modele(modele) #"pn/modele_ressource.tex")


        if self.ressource["code"] == "R107":
            print("ici")

        # Préparation des ac
        ajoutac = "\\ajoutac{%s}{%s}"
        compRT = []
        for accomp in self.ressource["acs"]:
            comps = []

            for no_ac in range(len(self.ressource["acs"][accomp])): # les ac de la comp
                code_ac = self.ressource["acs"][accomp][no_ac]
                comps.append( ajoutac % (code_ac, DATA_ACS[accomp][code_ac]) )
            compRT.append("\n".join(comps))

        # Préparation des sae
        ajoutsaes = "\\ajoutsae{%s}{%s}"
        saesRT = []
        for (i, sae) in enumerate(self.ressource["sae"]): # in range(len(self.apprentissages)):
            saesRT.append(ajoutsaes % (sae, get_officiel_sae_name_by_code(sae)))
        saes = "\n".join(saesRT)

        ajoutprerequis = "\\ajoutprerequis{%s}{%s}"
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