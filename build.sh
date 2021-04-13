#!/bin/bash

# Reconstruit tout !

ressources="$1"
saes="$2"

die() {
  echo 
  echo "Erreur: $1"
  echo
  exit 1
}

[ "$ressources" ] || die "Usage: $0 doc_ressources doc_sae"
[ "$saes" ] || die "Usage: $0 doc_ressources doc_sae"
[ -d python ] || die "repertoire manquant: python"
[ -d latex ] || die "repertoire manquant: latex"

[ -d python/export ] || mkdir "python/export" || die "creating python/export directory"

python python/export_docx_to_yaml.py "$ressources" -o "python/export" -r . || die "echec de export_docx_to_yaml.py"
python python/export_sae_docx_to_yaml.py "$saes" -o "python/export" -r . || die "echec de export_sae_docx_to_yaml.py"
python python/export_yaml_to_latex.py -a -r . || die "echec de export_yaml_to_latex.py"

cd latex || die "repertoire manquant: latex"
lualatex pn_formation
lualatex pn_formation

echo "Done."
echo "Resultat: latex/pn_formation.pdf"


