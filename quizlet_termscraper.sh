#!/bin/bash

# sh ~/Desktop/Coding/quizlet_termscraper/quizlet_termscraper.sh output_directory software_directory termslist_prefix i course_name driver_address

output=${1}
software=${2}
termslist_prefix=${3}
i=${4}
course_name=${5}
driver_address=${6}

mkdir -p $output

output_md_prefix="unit${i}_terms_definitions"
output_md_full="${output}/${output_md_prefix}.md"

# generate full list, with shortest definitions prioritized and all definitions found being outputted
cat "${termslist_prefix}.${i}.txt" | awk '{$1=$1};1' | python "${software}/quizlet_termscraper_webdriver.py" ${driver_address} ${course_name} "short" "-1" > $output_md_full
