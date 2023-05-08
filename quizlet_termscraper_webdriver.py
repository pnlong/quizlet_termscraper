# README
# This program is meant to scrape quizlet.com for a set of terms provided in stdin
# May 26, 2021
# Phillip Long

# cat terms | awk '{$1=$1};1' | python quizlet_termscraper_webdriver.py chrome_driver_path course_name prioritize_definitions_method maximum_number_of_definitions > terms_definitions.md


# sys.argv[1] = path to chrome web driver, download at:
#              (https://chromedriver.chromium.org/downloads -->
#               https://chromedriver.storage.googleapis.com/index.html?path=91.0.4472.101/ --> *
#               chromedriver_mac64.zip)
#               or at /Users/philliplong/Desktop/Coding/quizlet_termscraper/chromedriver on my Mac
#               * note that chrome driver version needs to match the version of chrome installed on the computer
#              [REQUIRED]

# sys.argv[2] = name of course (that will be used in search queries), preferably in acronym form [REQUIRED]

# sys.argv[3] = method for prioritizing definitions found on various quizlet sites for a term; either "long" (for longer definitions first) or "short" (for shorter definitions first) [REQUIRED]

# sys.argv[4] = maximum number of definitions to output per term (-1 to output all definitions found) [NOT REQUIRED]


import sys
from time import sleep
from time import perf_counter
from random import uniform
from re import sub
from re import match
import numpy

from selenium import webdriver


# SET UP FUNCTIONS AND IMPORTANT VARIABLES --------------------------------------------------------

# sys.argv = ("quizlet_termscraper_webdriver.py", "/Users/philliplong/Desktop/Coding/quizlet_termscraper/chromedriver", "apush", "short", -1) # for testing
# sys.stdin = ['Albany Congress', 'Anne Hutchinson', 'Antinomianism', "Bacon's Rebellion", 'Benjamin Franklin', 'Bible Commonwealth', 'Black legend', 'Calvinism', 'Christopher Columbus', 'Conquistadors', 'Conversion', 'Covenant', 'Doctrine of a calling', 'Dominion of New England', 'Dutch West India Company', 'Edward Braddock', 'Enclosure', 'Franchise', 'Francisco Pizarro', 'Freemen', 'Fundamental Orders', 'General Court', 'George Whitefield', 'Glorious Revolution', 'Great Puritan Migration', 'Half-Way Covenant', 'headright system', 'Henry Hudson', 'Hernado Cortes', 'House of Burgesses', 'Huguenots', 'Humphrey Gilbert', 'Indentured servitude', 'Institutes of the Christian Religion', 'James Oglethorpe', 'James Wolfe', 'Jeremiads', 'John Calvin', 'John Cotton', 'John Peter Zenger', 'John Rolfe', 'John Smith', 'John Winthrop', 'Joint-stock company', 'Jonathan Edwards', 'King Philip', 'Lord Baltimore', 'Marco Polo', 'Maryland Act of Toleration', 'Massachusetts Bay Company', 'Mayflower', 'Mayflower Compact', 'mestizos', 'Middle passage', 'Molasses Act', 'Nathaniel Bacon', 'Nation-state', 'Navigation Laws', 'New England Confederation', 'Old and new lights', 'Oliver Cromwell', 'patronship', 'Paxton Boys', 'Peter Stuyvesant', 'Phyllis Wheatley', 'Pilgrims', 'Pontiac', 'Predestination', 'Primogeniture', 'Proclamation of 1763', 'Proprietor', 'Protestant ethic', 'Protestant Reformation', 'Puritans', 'Quakers', 'Regulator movement', 'Renaissance', 'Restoration', 'Robert de la Salle', 'Roger Williams', 'Royal charter', 'Samuel de Champlain', 'Separatists', 'Sir Edmund Andros', 'Slave codes', 'Slavery', 'Spanish Armada', 'Squatter', 'The "elect"', 'The Great Awakening', 'Thomas Hooker', 'Treaty of Tordesillas', 'Vasco da Gama', 'Virginia Company', '"Visible saints"', 'Walter Raleigh', 'William Berkeley', 'William Bradford', 'William Laud', 'William Penn', 'William Pitt', 'Yeoman']

chrome_driver_path = str(sys.argv[1])
try:
    driver_test = webdriver.Chrome(executable_path = chrome_driver_path)
    driver_test.quit()
    del driver_test
except:
    print(f"Error: faulty chrome_driver_path argument provided to {sys.argv[0]}")
    quit()

course_name = str(sys.argv[2])
if course_name.replace(" ", "") == "": # if course_name argument is empty
    course_name = "" # set course_name to empty

prioritize_definitions_method = str(sys.argv[3]).strip().lower()
if prioritize_definitions_method not in ("long", "short"):
    print(f"Error: faulty prioritize_definitions_method argument provided to {sys.argv[0]}")
    quit()
if prioritize_definitions_method == "long":
    prioritize_definitions_method_scalar = 1
elif prioritize_definitions_method == "short":
    prioritize_definitions_method_scalar = -1 # will reverse the order of DEFINITION_LENGTH column so that large fractions of shared words will come first, but short definition lengths come first as well

try:
    maximum_number_of_definitions = int(sys.argv[4])
    if maximum_number_of_definitions < -1:
        print(f"Error: faulty maximum_number_of_definitions argument provided to {sys.argv[0]}")
        quit()
except:
    maximum_number_of_definitions = -1 # default if no maximum_number_of_definitions argument provided



search_source_priority = "https://quizlet.com" # I want defintions from quizlet.com
time_scalar = 1
number_of_seconds_if_caught_by_recaptcha = 60
characters_to_substitute = r"○|˚|•"
no_definition_found_text = "No definition found"
maximum_time_per_site = 3 * 60 # in seconds
percent_shared_words_threshold = 0.50
percent_shared_characters_threshold = 0.73
minimum_definition_length = 10 # in characters
chunk_size = 15000
term_definition_delimiter = ": "



# a function to remove extra spaces and whitespace from text
def remove_whitespace(text):
    return(" ".join(text.strip().split()))

# a function to simplify terms and definitions for better comparison
def simplify_text(text):
    return(remove_whitespace(sub(r"\([^()]*\)", "", sub("[^\w ]+", "", text.lower().replace("/", " ").replace("-", " ")))))

# a function that removes duplicates while retaining order (like R's unique() function); default behavior is to return a list
def unique(data_structure):
    return(list(dict.fromkeys(list(data_structure)))) # returns a list

# a function to remove unimportant words, like "the" or "and", from a sample of text
def extract_important_words(text):
    unimportant_words = ("a", "the", "and", "of")

    important_words = []
    for word in text.split():
        if simplify_text(word) not in unimportant_words:
            important_words.append(word)
    
    return(" ".join(important_words))

# a function that calculates the words shared between two given samples of text
def words_shared_between(text_a, text_b):
    text_a_words = set(text_a.split())
    text_b_words = set(text_b.split())
    
    share_count = 0
    for word in text_a_words:
        if word in text_b_words:
            share_count += 1
            
    return(share_count)

# a function that calculates the characters shared between two given samples of text, and generates a percentage (0 -> 1) of how similar the texts are
def chars_shared_between(text_a, text_b):
    # sort out so that text_a is the shorter string and text_b is the longer string in case that is not already the case
    if len(text_a) > len(text_b):
        text_a, text_b = text_b, text_a # switch them
        
    # just check if making the comparison is worthwhile by checking the difference in lengths
    if (len(text_a) / len(text_b)) < percent_shared_characters_threshold:
        return(None)
    
    
    text_b_len_original = len(text_b)
    for letter in text_a:
        if letter in text_b:
            i = text_b.index(letter)
            if i == 0:
                text_b = text_b[1: ]
            else:
                text_b = text_b[ :i] + text_b[(i + 1): ]
            del i
    
    # generate score by dividing the number of characters left in text_b (those not in text_a) by the original number of characters in text_b
    score = 1 - (len(text_b) / text_b_len_original)
    return(score)
    

# a function that formats actual quizlet terms used and their definitions for printing later
def format_quizlet_term_and_definition(term_definition):
    # if term_definition is no_definition_found_text
    if (type(term_definition) == str) and (term_definition == no_definition_found_text):
        return(str(no_definition_found_text))
    
    # if term_definition is a list or tuple in the format (term, definition)
    elif (type(term_definition) is list or type(term_definition) is tuple) and (len(term_definition) == 2):
        formatted_term = remove_whitespace(sub(characters_to_substitute, "", remove_whitespace(term_definition[0]).replace("′", "'")))
        formatted_definition = remove_whitespace(sub(characters_to_substitute, "", remove_whitespace(term_definition[1]).replace("\n", "; ").replace("′", "'")))
        return(str(f"*{formatted_term}*{term_definition_delimiter}{formatted_definition}"))
    
# a function to wait a random amount of time within a given range
def wait(lower_limit, upper_limit, scalar = True):
    if scalar:
        limit_difference = upper_limit - lower_limit
        upper_limit = time_scalar * upper_limit
        lower_limit = abs(upper_limit - limit_difference)
        del limit_difference
    
    sleep(uniform(lower_limit, upper_limit))
    
# a function that checks if the currently loaded page is a recaptcha page, and if it is, enter a while sleep that checks every once in a while if the page has been resolved
def check_for_recaptcha_page(chrome_driver):
    recaptcha_page_address_prefix = "https://www.google.com/sorry/index"
    is_recaptcha_page = chrome_driver.current_url.startswith(recaptcha_page_address_prefix)
    while is_recaptcha_page:
        sleep(number_of_seconds_if_caught_by_recaptcha) # wait some time for human intervention and pass the "I'm not a Robot" test to fix it
        is_recaptcha_page = chrome_driver.current_url.startswith(recaptcha_page_address_prefix)

# a function that types in a given text into a given text entry element like an actual human (one letter at a time)
def simulate_typing(text_entry_element, text):
    for letter in text:
        text_entry_element.send_keys(letter)
        wait(0.05, 0.2, False)
    del letter
    
# a function that scrolls to the bottom, and back to the top, of a webpage
def scroll_down_up(chrome_driver):
    chrome_driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    wait(0.5, 1, False)
    chrome_driver.execute_script("window.scrollTo(document.body.scrollHeight, 0)")



# SET UP WEB DRIVER -------------------------------------------------------------------------------
# create a new Chrome session
driver = webdriver.Chrome(executable_path = chrome_driver_path)
del chrome_driver_path
driver.maximize_window() # maximize the driver window



# LOG INTO QUIZLET --------------------------------------------------------------------------------
# go to quizlet.com
driver.get("https://quizlet.com")
wait(3, 5, False)


# INCASE OF COOKIES POPUP AT BOTTOM, CLICK AWAY
try:
    if len(driver.find_elements_by_xpath("//button[@class='cookie-setting-link']")) > 0:
        cookies_popup = driver.find_element_by_xpath("//button[@id='onetrust-accept-btn-handler']")
        cookies_popup.click()
        del cookies_popup
        wait(0.5, 1.5, False)
except:
    pass

# click login button, get sent to new page
login = driver.find_element_by_xpath("//button[@aria-label='Log in']")
login.click()
del login
wait(3, 5, False)


# scroll to bottom to load in everything
# driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", driver.find_element_by_xpath('//div[@class="a1cdxe01"]'))
wait(0.5, 1.5, False)


# enter username
simulate_typing(driver.find_element_by_id("username"), "phillipl915")
wait(0.5, 1.5, False)


# enter password
simulate_typing(driver.find_element_by_id("password"), "090105PNL")
wait(0.5, 1.5, False)


# click login button
login = driver.find_element_by_xpath("//button[@type='submit']")
login.click()
del login
wait(1, 3)



# GET TERMS FROM SYS.IN ---------------------------------------------------------------------------

# Navigate to the bing home page, since BING search engine does not have Recaptcha
driver.get("https://www.bing.com/")


terms = []
quizlet_links = []
for line in sys.stdin:
    # get rid of new line character at the end of line, we only want the vocab term
    term = remove_whitespace(sub(characters_to_substitute, "", str(line).replace("′", "'")))
    # add term to terms list
    terms.append(term)
    # get rid of text inside of parentheses within the term
    term = remove_whitespace(sub(r"\([^()]*\)", "", term))
    
    
    # SEARCH GOOGLE -------------------------------------------------------------------------------  
    # get the search textbox
    search_field = driver.find_element_by_name("q")
    # delete any previous text from search box
    search_field.clear()
    # enter search query
    search_field.send_keys((term + " " + course_name.lower() + " site:" + search_source_priority))
    # submit search query
    search_field.submit()
    scroll_down_up(driver)
    wait(0.25, 0.75, False)

    # Get the urls generated by the Google Search Result
    # get the list of <a></a> which are displayed after the search
    # extract "href" attribute (the url) and link text (which can be used to identify it later)
    search_links_all = tuple(map(lambda a: a.get_attribute("href"), driver.find_elements_by_tag_name("a"))) 
    
    
    
    # FILTER GOOGLE SEARCH RESULT PAGE TO DESIRED WEBSITE -----------------------------------------
    
    search_links_filter = []
    for link in search_links_all:
        if link == None:
            continue
        if match("^" + search_source_priority + "/\\d+/", link): # the website starts with search_source_priority followed by a series of numbers (the pattern found in the address of a NORMAL quizlet site)
            # if a link in the Google Search Results comes from the desired website,
            # add to the search_links filter list
            search_links_filter.append(link)
    del link
    
    # Now, I have a list of urls from a Google Search (hopefully) containing definitions from a desired website
    # of the current term
    # Add links to my list of quizlet links
    for link in search_links_filter:
        quizlet_links.append(link)
    del link


    del term, search_field, search_links_all, search_links_filter
    

del line, search_source_priority



# ORDER QUIZLET LINKS IN THE ORDER I WANT TO SCRAPE THEM, SET UP MATRIX FOR DEFINITIONS -----------
# this will be done by seeing how many times each website popped up in my google searching above,
# and the websites that were suggested as a result the most are given priority


# the columns of quizlet_links_filtered are: LINK, NUMBER_OF_APPEARANCES
quizlet_links_filtered = numpy.array(tuple((link, quizlet_links.count(link)) for link in set(quizlet_links)))
quizlet_links_filtered = (quizlet_links_filtered[quizlet_links_filtered[:, 1].argsort()])[::-1] # arrange in descending order by counts of link appearance
quizlet_links_filtered = unique(list(quizlet_links_filtered[:, 0])) # extract the column of links (already in correct order)
# remove wierd google webcaches or related google searches if the link they are referencing is already in the list
number_deleted = 0
for i in range(1, len(quizlet_links_filtered)):
    is_dulpicate_of_previous_link = tuple(quizlet_link in quizlet_links_filtered[i - number_deleted] for quizlet_link in quizlet_links_filtered[:(i - 1 - number_deleted)])
    if any(is_dulpicate_of_previous_link):
        del quizlet_links_filtered[i - number_deleted]
        number_deleted += 1
del number_deleted, is_dulpicate_of_previous_link, i

del quizlet_links



terms_lower = tuple(map(simplify_text, terms))
# create empty 2d array for terms and definitions
# the first column is the term as it is in the vocab list
# the next columns are for each website that will be visited. They will be filled in by the actual term used and definition found, formatted by a helper function above
terms_definitions = [[term] + ([no_definition_found_text] * len(quizlet_links_filtered)) for term in terms]

wait(1, 1.5, False)



# SEARCH QUIZLET LINKS FOR TERMS AND DEFINITIONS --------------------------------------------------
for i in range(len(quizlet_links_filtered)):    
    try:
        
        # GET TO QUIZLET SITE -------------------------------------------------------------------------

        # Navigate to the google home page
        driver.get(quizlet_links_filtered[i])
        wait(0.5, 2)
        # check if recaptcha page has popped up (and if it has, wait for user intervention)
        check_for_recaptcha_page(driver)
        # I am now on the page which (hopefully) has the definition
    
    
    
        # SEARCH QUIZLET SITE FOR DEFINITIONS -----------------------------------------------------
            
        # INCASE OF POPUP, CLICK AWAY
        if len(driver.find_elements_by_xpath("//button[@class='UILink UILink--revert']")) > 0:
            popup = driver.find_element_by_xpath("//button[@class='UILink UILink--revert']")
            popup.click()
            del popup
            wait(0.5, 1, False)
        # INCASE OF COOKIES POPUP AT BOTTOM, CLICK AWAY
        if len(driver.find_elements_by_xpath("//button[@class='cookie-setting-link']")) > 0:
            cookies_popup = driver.find_element_by_xpath("//button[@id='onetrust-accept-btn-handler']")
            cookies_popup.click()
            del cookies_popup
            wait(0.5, 1, False)
            


    
        # BEGIN PARSING WEBSITE FOR TERMS
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        # # INCASE OF "SEE MORE" BUTTON, CLICK IT TO SEE MORE
        # if len(driver.find_elements_by_xpath("//button[@class='UIButton UIButton--fill' and @aria-label='See more']")) > 0:
        #     see_more = driver.find_element_by_xpath("//button[@class='UIButton UIButton--fill' and @aria-label='See more']")
        #     see_more.click()
        #     del see_more
        #     wait(1, 2, False)
        #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        # 
        # 
        # # GET TERMS AND DEFINITIONS (IF THERE ARE ANY)
        # quizlet_terms = quizlet_definitions = []
        # 
        # quizlet_terms_classes = driver.find_elements_by_class_name("SetPageTerm-wordText")
        # quizlet_definitions_classes = driver.find_elements_by_class_name("SetPageTerm-definitionText")
        # if (len(quizlet_terms_classes) > 0) and (len(quizlet_definitions_classes) > 0):
        #     
        #     quizlet_terms = list(map(lambda term: remove_whitespace(term.text), quizlet_terms_classes))
        #     quizlet_definitions = list(map(lambda definition: remove_whitespace(definition.text), quizlet_definitions_classes))
        #     
        # del quizlet_terms_classes, quizlet_definitions_classes


        # BEGIN PARSING WEBSITE FOR TERMS
        scroll_down_up(driver)
        quizlet = quizlet_previous = numpy.empty(shape = (0, 2), dtype = "str")
        
        start_time = perf_counter()
        # done in while loop so that terms and definitions can be extracted while scrolling (while making sure there are no duplicate entries)
        while ((len(quizlet) != len(quizlet_previous)) or (len(quizlet) == 0 or len(quizlet_previous) == 0) or (sum((quizlet == quizlet_previous).flatten()) < len((quizlet == quizlet_previous).flatten()))) and (perf_counter() - start_time < maximum_time_per_site): # so while quizlet array is changing
            quizlet_previous = quizlet
        
        
            # INCASE OF "SEE MORE" BUTTON, CLICK IT TO SEE MORE
            if len(driver.find_elements_by_xpath("//button[@class='UIButton UIButton--fill' and @aria-label='See more']")) > 0:
                see_more = driver.find_element_by_xpath("//button[@class='UIButton UIButton--fill' and @aria-label='See more']")
                see_more.click()
                del see_more
                wait(0.5, 1, False)
        
        
            # CHECK IF THERE ARE TERMS
            quizlet_terms_classes = driver.find_elements_by_class_name("SetPageTerm-wordText")
            quizlet_definitions_classes = driver.find_elements_by_class_name("SetPageTerm-definitionText")
            if (len(quizlet_terms_classes) > 0) and (len(quizlet_definitions_classes) > 0):
            
                # append current iteration terms and definitions to full quizlet terms and definitions
                quizlet = numpy.vstack((quizlet, numpy.transpose([list(map(lambda term: remove_whitespace(term.text), quizlet_terms_classes)),
                                                                  list(map(lambda definition: remove_whitespace(definition.text), quizlet_definitions_classes))])))
                # get unique rows
                quizlet = numpy.unique(quizlet, axis = 0)
        
            del quizlet_terms_classes, quizlet_definitions_classes
        
            driver.execute_script(f"window.scrollBy(0, {chunk_size})")    
        
        
        
        quizlet_terms = tuple(map(remove_whitespace, quizlet[:, 0]))
        quizlet_definitions = tuple(map(remove_whitespace, quizlet[:, 1]))
        del quizlet, quizlet_previous, start_time
    
    
    
        # terms in lower case and removed special characters for better comparison
        quizlet_terms_lower = tuple(map(simplify_text, quizlet_terms))

    
        wait(0.25, 0.75, False)
    
    
    
        # ITERATE THROUGH LIST OF PROVIDED VOCABULARY TERMS -------------------------------------------
        for k in range(len(terms_lower)):
            term_lower = terms_lower[k]
        
        
            # columns: INDEX_QUIZLET_TERM_LOWER, LENGTH_OF_QUIZLET_TERM_LOWER, IS_TERM_IN_QUIZLET_TERM, LENGTH_OF_QUIZLET_DEFINITION_LOWER
            term_within_quizlet_terms = numpy.array(tuple((i, len(quizlet_terms_lower[i]), (term_lower in quizlet_terms_lower[i]), len(quizlet_definitions[i])) for i in range(len(quizlet_terms_lower))), dtype = object)
            term_within_quizlet_terms = term_within_quizlet_terms[numpy.logical_and((term_within_quizlet_terms[:, 2] == True), (term_within_quizlet_terms[:, 3] > minimum_definition_length))] # filter so that there are only rows where the term is within the quizlet term, and definition lengths are longer than a set minimum
            term_within_quizlet_terms = term_within_quizlet_terms[term_within_quizlet_terms[:, 1].argsort()] # sort so quizlet term length is ascending
            
            
            # columns: INDEX_QUIZLET_TERM_LOWER, FRACTION_SHARED, LENGTH_OF_QUIZLET_DEFINITION_LOWER
            term_shares_words_with_quizlet_terms = numpy.array(tuple((i, (words_shared_between(extract_important_words(term_lower), extract_important_words(quizlet_terms_lower[i])) / len(set(extract_important_words(term_lower).split()))), len(quizlet_definitions[i])) for i in range(len(quizlet_terms_lower))), dtype = object)
            term_shares_words_with_quizlet_terms = term_shares_words_with_quizlet_terms[numpy.logical_and((term_shares_words_with_quizlet_terms[:, 1] >= percent_shared_words_threshold), (term_shares_words_with_quizlet_terms[:, 2] > minimum_definition_length))] # filter so that only quizlet terms sharing 50% of words with the actual term are left, and definition lengths are longer than a set minimum
            term_shares_words_with_quizlet_terms = (term_shares_words_with_quizlet_terms[term_shares_words_with_quizlet_terms[:, 1].argsort()])[::-1] # filter so that percentage of words shared is descending (highest percentage on top)
            
            
            # columns: INDEX_QUIZLET_TERM_LOWER, FRACTION_SHARED, LENGTH_OF_QUIZLET_DEFINITION_LOWER
            term_shares_chars_with_quizlet_terms = numpy.array(tuple((i, chars_shared_between(extract_important_words(term_lower), extract_important_words(quizlet_terms_lower[i])), len(quizlet_definitions[i])) for i in range(len(quizlet_terms_lower))), dtype = object)
            term_shares_chars_with_quizlet_terms = term_shares_chars_with_quizlet_terms[numpy.logical_and((term_shares_chars_with_quizlet_terms[:, 1] != None), (term_shares_chars_with_quizlet_terms[:, 2] > minimum_definition_length))] # filter so that only quizlet terms sharing 75% of characters with the actual term are left, and definition lengths are longer than a set minimum
            term_shares_chars_with_quizlet_terms = term_shares_chars_with_quizlet_terms[term_shares_chars_with_quizlet_terms[:, 1] >= percent_shared_characters_threshold]
            term_shares_chars_with_quizlet_terms = (term_shares_chars_with_quizlet_terms[term_shares_chars_with_quizlet_terms[:, 1].argsort()])[::-1] # filter so that percentage of words shared is descending (highest percentage on top)
            


            j = None
            # CHECK FOR STRAIGHTUP MATCH BETWEEN TERM AND QUIZLET TERM
            if term_lower in quizlet_terms_lower:
                j = quizlet_terms_lower.index(term_lower)
            
                # i + 1 because of the first column, TERM
                # input the actual term used and definition (in tuple form: (actual_term_used, definition)) into terms_definitions
                if len(quizlet_definitions[j]) > minimum_definition_length:
                    terms_definitions[k][i + 1] = (quizlet_terms[j], quizlet_definitions[j])
            
        
            # CHECK FOR TERM WITHIN QUIZLET TERMS
            elif len(term_within_quizlet_terms) > 0:
                j = term_within_quizlet_terms[0, 0] # choose the quizlet term that contains the term that is the closest in length to the term
                # and none of the quizlet terms will be exact matches, since the previous if() would have succeeded if that was the case, skipping this elif()
            
                # i + 1 because of the first column, TERM
                # input the actual term used and definition (in tuple form: (actual_term_used, definition)) into terms_definitions
                terms_definitions[k][i + 1] = (quizlet_terms[j], quizlet_definitions[j])
            
        
            # CHECK FOR THE AMOUNT OF WORDS SHARED BETWEEN TERM AND QUIZLET TERMS
            elif len(term_shares_words_with_quizlet_terms) > 0:
                j = term_shares_words_with_quizlet_terms[0, 0] # choose the word with the highest percentage shared words
            
                # i + 1 because of the first column, TERM
                # input the actual term used and definition (in tuple form: (actual_term_used, definition)) into terms_definitions
                terms_definitions[k][i + 1] = (quizlet_terms[j], quizlet_definitions[j])
        
            
            # CHECK FOR THE AMOUNT OF CHARACTERS SHARED BETWEEN TERM AND QUIZLET TERMS
            elif len(term_shares_chars_with_quizlet_terms) > 0:
                j = term_shares_chars_with_quizlet_terms[0, 0] # choose the word with the highest percentage shared words
            
                # i + 1 because of the first column, TER M
                # input the actual term used and definition (in tuple form: (actual_term_used, definition)) into terms_definitions
                terms_definitions[k][i + 1] = (quizlet_terms[j], quizlet_definitions[j])
            
            del term_lower, term_within_quizlet_terms, term_shares_words_with_quizlet_terms, term_shares_chars_with_quizlet_terms, j



        del quizlet_terms, quizlet_terms_lower, quizlet_definitions, k

    
    
    # if there is an error in parsing the quizlet site, skip this site (with built-in pass function)
    except:
        pass
    
    

del terms, terms_lower, quizlet_links_filtered, i




# FILTER AND TIDY TERMS_DEFINITIONS  --------------------------------------------------------------
for i in range(len(terms_definitions)):
    # get rid of duplicate entries (as in multiple "No definition found")
    terms_definitions_row = unique(terms_definitions[i])
    term = terms_definitions_row[0]
    definitions = terms_definitions_row[1:]
    del terms_definitions_row
    
    # if definition(s) were found
    if definitions != [no_definition_found_text, ]: 
        # since definition(s) were found, remove any no_definition_found_text
        definitions.remove(no_definition_found_text)
        
        # perform unique(), but on the simplified version of definitions (so definitions with minute differences are removed)
        definitions_lower = list(simplify_text(term_definition[1]) for term_definition in definitions)
        definitions = list(definitions[index] for index in numpy.unique(definitions_lower, return_index = True)[1])
        del definitions_lower
        
        
        # if there are more definitions found than the acceptable maximum_number_of_definitions, we will set the number of definitions to be printed to the maximum
        
                    
        if maximum_number_of_definitions == -1:
            number_of_definitions = len(definitions)
            
        elif maximum_number_of_definitions > -1:
            if len(definitions) >= maximum_number_of_definitions:
                number_of_definitions = maximum_number_of_definitions
            else:
                number_of_definitions = len(definitions)
        
        
        
        # how we will order the definitions is
        # first, by how well the term used matches the actual term
        # secondly, by the length of the definition
        
        # columns: TERM, TERMUSED_DEFINITION, FRACTION_OF_SHARED_WORDS, DEFINITION_LENGTH
        prioritized_definitions = numpy.array(tuple((term, term_definition, words_shared_between(extract_important_words(simplify_text(term)), extract_important_words(simplify_text(term_definition[0]))) / len(set(extract_important_words(simplify_text(term_definition[0])).split())), len(term_definition[1])) for term_definition in definitions), dtype = object)
        
        # arrange primarily by FRACTION_OF_SHARED_WORDS then DEFINITION_LENGTH, then reverse the order so that the largest FRACTION_OF_SHARED_WORDS and shortest/longest DEFINITION_LENGTH are at the top (depending on prioritize_definitions_method)
        prioritized_definitions = list(prioritized_definitions[numpy.lexsort((prioritize_definitions_method_scalar * prioritized_definitions[:, 3], prioritized_definitions[:, 2]))][:, 1][::-1])
        prioritized_definitions = list(format_quizlet_term_and_definition(term_definition) for term_definition in prioritized_definitions)
        

        terms_definitions[i] = [term] + prioritized_definitions[0:number_of_definitions] # keep the amount of defintions we want (number_of_definitions) from the top
    
    
    
        del number_of_definitions, prioritized_definitions
        
        
    elif definitions == [no_definition_found_text, ]:
        terms_definitions[i] = [term, no_definition_found_text]
    
    
    
    del term, definitions
    
    
    
del i, prioritize_definitions_method_scalar


# PRINT INTRODUCTORY INFORMATION ------------------------------------------------------------------
# print YAML header, with information like margin size and author name
print("---", end = "\n")
print("author: Phillip Long", end = "\n")
print("geometry: margin=0.5in", end = "\n")
print("---", end = "\n")

# print title
print(f"# {course_name.upper()} Terms and Definitions", end = "\n")

# print maximum_number_of_definitions used
if maximum_number_of_definitions == -1:    
    print(f"##### (containing all definitions found", end = "")
elif maximum_number_of_definitions > -1:
    print(f"##### (filtered to a maximum of {maximum_number_of_definitions} definition(s)", end = "")

# print prioritize_definitions_method used
print(f", prioritizing {prioritize_definitions_method}er definitions)", end = "\n")

# print separator
print("**********", end = "\n")


# PRINT TERMS AND DEFINITIONS ---------------------------------------------------------------------
for row_number in range(len(terms_definitions)):
    row = terms_definitions[row_number]
    
    # print the provided vocab term first
    print(f"{row_number + 1}. **{row[0]}**", end = "")
    
    # if just the term is being printed (for some WIERD reason)
    if maximum_number_of_definitions == 0:
        print("", end = "\n")
        continue
    
    top_definition = row[1]
    # exract just the definition, and not the term used, from the top_definition (if statement needed in case no definition was found)
    if term_definition_delimiter in top_definition:
        top_definition = top_definition[(top_definition.index(term_definition_delimiter) + len(term_definition_delimiter)): ]
    print(f"{term_definition_delimiter}{top_definition}", end = "\n")
    
    
    # now print each definition as well as the actual quizlet term of that definition for each actualterm_definition combo
    line_starter = " " * (len(f"{row_number + 1}") + 2)
    del row[0:2]
    for termused_definition in row:
        print(f"{line_starter}- {termused_definition}", end = "\n")
        
    del top_definition, row
    
    
    
del row_number, terms_definitions


# once everything is done, quit the chromedriver
driver.quit()
del driver
