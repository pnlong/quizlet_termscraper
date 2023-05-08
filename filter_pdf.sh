#!/bin/bash

# sh ~/Desktop/Coding/quizlet_termscraper/filter_pdf.sh output_directory software_directory i

output=${1}
software=${2}
i=${3}


subsets="$output/subsets"
mkdir -p $subsets

pandocs="$output/pandocs"
mkdir -p $pandocs


output_md_prefix="unit${i}_terms_definitions"
output_md_subset="${subsets}/${output_md_prefix}.subset.md"

# create the subsetted list, with the 3 top definitions per term
cat "${output}/${output_md_prefix}.md" | python ${software}/change_maximum_number_of_definitions.py 3 > $output_md_subset

# convert md -> pdf
pandoc --pdf-engine=xelatex -s $output_md_subset -o "${pandocs}/${output_md_prefix}.pdf"