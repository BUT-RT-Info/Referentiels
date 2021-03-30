"""
Gestion des modeles de question/reponses latex
"""
import string, os

def get_modele(fichier):
    # print(os.path.abspath(os.curdir))
    with open(fichier, "r", encoding="utf8") as fid:
        contenu = fid.read()

    return contenu

def effify(non_f_str: str):
    return eval(f'f"""{non_f_str}"""')

class TemplateLatex(string.Template):
    delimiter = '#'
