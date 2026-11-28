#!/bin/sh
set -eu

if [ "$#" -ne 1 ] || [ -z "$1" ]; then
    echo "Usage: $0 OUTPUT_DIRECTORY" >&2
    exit 2
fi

report=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
root=$(dirname -- "$report")
mkdir -p -- "$1"
destination=$(CDPATH='' cd -- "$1" && pwd -P)
submitted="$root/archive/local/submitted"
if [ "$destination" = "$report" ] || [ "$destination" = "$submitted" ]; then
    echo 'Choose a separate directory for rebuilt reports.' >&2
    exit 2
fi
for name in combined.pdf combined.html; do
    if [ -e "$destination/$name" ] || [ -L "$destination/$name" ]; then
        echo "Render destination already contains $name. Choose an empty output directory." >&2
        exit 2
    fi
done

work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
mkdir "$work/report"
for name in combined.Rmd references.bib report.csl report.css report.tex; do
    cp -- "$report/$name" "$work/report/"
done
ln -s -- "$root/analysis" "$work/analysis"
ln -s -- "$root/outputs" "$work/outputs"
(
    cd "$work/report"
    Rscript --vanilla -e 'rmarkdown::render("combined.Rmd", output_format = "all")'
)
cp -- "$work/report/combined.pdf" "$work/report/combined.html" "$destination/"
printf 'Rebuilt report files are in %s\n' "$destination"
