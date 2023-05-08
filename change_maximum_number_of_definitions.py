# README
# This program is associated with quizlet_termscraper_webdriver.py
# It subsets the amount of definitions found per term to a given maximum_number_of_definitions argument
# This program is useful if you want to change the maximum_number_of_definitions argument
# given to quizlet_termscraper_webdriver.py, but the termscraper had already been run, and you dont want to rerun it.
# August 4, 2021
# Phillip Long

# cat quizlet_termscraper_output | python ~/quizlet_termscraper/change_maximum_number_of_definitions.py maximum_number_of_definitions > terms_definitions_filtered.md
# Ex. : cat quizlet_termscraper_output | python ~/quizlet_termscraper/change_maximum_number_of_definitions.py 3 > terms_definitions_filtered.md


# sys.argv[1] = maximum number of definitions to output per term (-1 to output all definitions found) [REQUIRED]

import sys
import numpy
import re

# sys.argv = ("change_maximum_number_of_definitions.py", "1")
maximum_number_of_definitions = int(sys.argv[1])
if maximum_number_of_definitions < -1:
    print(f"Error: faulty maximum_number_of_definitions argument provided to {sys.argv[1]}")
    quit()

term_definition_delimiter = ": "


# a helper function to remove extra spaces and whitespace from text
def remove_whitespace(text):
    return(" ".join(text.strip().split()))

# a helper function to simplify terms and definitions for better comparison
def simplify_text(text):
    return(remove_whitespace(re.sub("[^\w ]+", "", text.lower().replace("/", " ").replace("-", " "))))


# a function that deals with the current chunk to make it into what we want
def subset_current_term_chunk(current_term_chunk):
    current_term_chunk_definitions_lower = numpy.array(list(remove_whitespace(simplify_text(term_definition.split(term_definition_delimiter)[1])) for term_definition in current_term_chunk))
    current_term_chunk = list(numpy.array(current_term_chunk)[numpy.sort((numpy.unique(current_term_chunk_definitions_lower, return_index=True)[1]))])
    
    if maximum_number_of_definitions >= 1:
        if len(current_term_chunk) >= maximum_number_of_definitions:
            number_of_definitions = maximum_number_of_definitions
        else:
            number_of_definitions = len(current_term_chunk)
        
        current_term_chunk = current_term_chunk[0:number_of_definitions]
        del number_of_definitions
            
    elif maximum_number_of_definitions == 0: # basically if I want just the term
        current_term_chunk = [(current_term_chunk[0].split(term_definition_delimiter))[0]]
            
    # if maximum_number_of_definitions == -1, nothing needs to be done to current term chunk
    
    return(list(current_term_chunk))




term_chunks = []
current_term_chunk = []

is_introductory_lines = True
for line in sys.stdin:
    
    line = re.sub(r"○|˚|•", "", line.rstrip().replace("\n", "; ").replace("′", "'"))
    
    if line == "**********":
        is_introductory_lines = False
        print("**********", end = "\n")
        continue
    # change the heading which tells how many definitions the program filtered to
    elif is_introductory_lines and (("filtered to a maximum of" in line) or ("containing all definitions found" in line)):
        line_starter = line[ :(line.index("(") + 1)]
        prioritize_definitions_method_used = line[line.index(","): ]
        if maximum_number_of_definitions == -1:    
            line = f"{line_starter}containing all definitions found{prioritize_definitions_method_used}"
        elif maximum_number_of_definitions > -1:
            line = f"{line_starter}filtered to a maximum of {maximum_number_of_definitions} definition(s){prioritize_definitions_method_used}"
    
    # if is_introductory_lines, print the line and skip the rest of the iteration
    if is_introductory_lines:
        print(line, end = "\n")
        continue

    
    # if the line is the start of a new term chunk, add current_term_chunk (if it's not empty) to term_chunks
    if re.match(re.compile("[0-9]+. "), line) and current_term_chunk != []:
        current_term_chunk = subset_current_term_chunk(current_term_chunk)
        
        term_chunks.append(current_term_chunk)
        
        del current_term_chunk
        current_term_chunk = [line]
    
    
    # elsewise, just add the current line to the current_term_chunk
    else:
        current_term_chunk.append(line)

# add the last current_term_chunk to term chunks
current_term_chunk = subset_current_term_chunk(current_term_chunk)
term_chunks.append(current_term_chunk)


del line, current_term_chunk



# flatten term_chunks for printing
term_chunks = [definition for chunk in term_chunks for definition in chunk]

for line in term_chunks:
    print(line, end = "\n")

del line, term_chunks
