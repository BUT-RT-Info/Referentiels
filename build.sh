#!/bin/bash

# Reconstruit tout !
# Avec --ccn edition "ministère"
usage() {
  echo "$0 [--ccn] doc_ressources doc_sae"
  exit 1
}
[ $# != 2 ] || [ $# != 3 ] || usage
CCN="--acd"
if [ "$1" == "--ccn" ]
then
  CCN="--ccn"
  shift
fi

ressources="$1"
saes="$2"

die() {
  echo 
  echo "Erreur: $1"
  echo
  exit 1
}

[ "$ressources" ] || usage
[ "$saes" ] || usage
[ -d python ] || die "repertoire manquant: python"
[ -d latex ] || die "repertoire manquant: latex"

[ -d python/export ] || mkdir "python/export" || die "creating python/export directory"

python python/export_ressources_docx_to_yaml.py "$ressources" -o "python/export" -r . || die "echec de export_docx_to_yaml.py"
python python/export_sae_docx_to_yaml.py "$saes" -o "python/export" -r . || die "echec de export_sae_docx_to_yaml.py"
python python/export_yaml_to_latex.py "$CCN" -a -r . || die "echec de export_yaml_to_latex.py"

cd latex || die "repertoire manquant: latex"
lualatex pn_formation
lualatex pn_formation

lualatex pn_formation_ccn
lualatex pn_formation_ccn

echo "Done."
echo "Resultat: latex/pn_formation.pdf, latex/pn_formation_ccn.pdf"


