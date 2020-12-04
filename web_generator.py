import requests
import json
import random
from browser import document, html

# TODO
# 
#  add title generation
#  add variable rhymeschemes (AABB, ABBA)
#  mess around with topics
#  some bugs around capitalizing words after periods
#  optimize the words it puts periods after


# NOTE: the various 'prior' or 'prev' parameters usually actually refer to a word that will come /after/ the sought word in the poem, but before in the generation process -- the verses are built backwards

# INPUTS
topics = ['ocean', 'mystery', 'speed']
uncommonality_factor = 0.25 # ignore first x percentage of results 


printmode = False

def lastIndexOf(arr, term):
	arr.reverse()
	last_index = len(arr) - arr.index(term) - 1
	arr.reverse()
	return last_index

# randomly disperses commas, periods, and dashes throughout the json list
def add_punctuation(json_list):
    #punctuation
    capitalize = False

    for x in range(len(json_list)):
        if capitalize: # capitalizes word if last one ended in a period
            json_list[x]['word'] = json_list[x]['word'].capitalize()
            capitalize = False

        part_of_speech = json_list[x]['tags'][0]
        if part_of_speech == 'n' and len(json_list[x]['word']) > 2: # only place punctuation after nouns (?)
            if random.randint(1, 4) == 4: # 1/15 chance
                punc = random.choice([',', ',', '.', ' --', ':', '!', ','])
                json_list[x]['word'] = json_list[x]['word'] + punc # add a comma, period, or dash
                if punc == '.' or punc == '!':
                    capitalize = True # tells next cycle to capitalize its word bc this one ends in a period
        



def cull_words_from_json(json_list):
	words = []
	for x in json_list:
		words.append(x['word'])
	return words

# sends a request with the given parameters, returning a random word if successful or -1 if not
def get_word(prior, rhyme, topics, extra):
    prior_url_term = ('&rel_bgb=' + prior) if not(prior is None) else ''
    rhyme_url_term = ('&rel_rhy=' + rhyme) if not(rhyme is None) else ''
    extra_url_term = extra if not(extra is None) else ''
    topic_url_term = ''

    if not(topics is None) and len(topics) > 0:
        topic_url_term = '&topics='
        for x in topics:
            topic_url_term += x + ','

    url = 'https://api.datamuse.com/words?md=spf&' + prior_url_term + rhyme_url_term + topic_url_term + extra_url_term

    results = requests.get(url).json()
    num_results = len(results)

    if(num_results == 0):
        return -1

    handicap = int((num_results-1) * uncommonality_factor) # ignore this many first results (to avoid over-common/simple words)
    index = random.randint(handicap, num_results - 1)
    return results[index]


def phrase_helper_get_first_word(prev, rhyme):
    first_word = get_word(prev, rhyme, topics, None)
    
    # give it five tries to find a rhyming word that's not the given one
    i = 0
    while(first_word == rhyme and i < 5):
        first_word = get_word(prev, rhyme, topics, None)
        i+=1

    if first_word == -1:
        first_word = get_word(None, rhyme, topics, None)
    if first_word == -1:
        print("six_syllable_phrase: Failure. We can't find a starting word.")
        return -1

    return first_word


#task: generate a six-syllable phrase that precedes the param-word prev and rhymes with the param-word rhyme
def six_syllable_phrase(prev, rhyme):
	# find the rhyme first, try to fill in backwards, and if it won't fit restart
	
	# choosing a rhymeword
    first_word = phrase_helper_get_first_word(prev, rhyme)
    phrase_data = [first_word]
    init_syllables = phrase_data[0]['numSyllables']

    # try to fill in backwards to exactly six syllables
    syl_ctr = init_syllables
    num_retries = 0
    retry_limit = 30

    while (syl_ctr < 6) and (num_retries < retry_limit):
    	phrase_len = len(phrase_data)

    	prior_word = phrase_data[phrase_len - 1]['word']
        prior_word = prior_word if prior_word.count(' ') == 0 else prior_word[:prior_word.index(' ')] # stops at first space if any in prev word
        right_context = phrase_data[phrase_len-2]['word'] if phrase_len > 2 else None # if right context available gets word

        candidate = get_word(prior_word, None, topics, right_context)

        if candidate == -1: # to do: ty other url commands, like jjb for nouns or jja for adjectives, or trg
            if printmode:
                print("six_syllable_phrase: Retry. No matches, going back one word...")
    	    if phrase_len == 1:
    	        if printmode:
                    print("actually, there's only one word - so we're recalling the function...")
    	        return six_syllable_phrase(prev, rhyme)
    	    else:
                num_retries+=1
    	        syl_ctr -= phrase_data[phrase_len-1]['numSyllables']
    	        phrase_data.pop(phrase_len-1)
    	        continue

        candidate_syls = candidate['numSyllables']

        if syl_ctr + candidate_syls > 6:
            error_str = 'six_syllable_phrase: Retry. Syllable count overloaded by \"' + candidate['word'] + '\"...'
            if printmode:
                print(error_str)
    	    num_retries+=1
    	    continue

        phrase_data.append(candidate)
        syl_ctr += candidate_syls

    if num_retries < retry_limit:
        phrase_data.reverse()
        add_punctuation(phrase_data)
        return cull_words_from_json(phrase_data)
    else:
    	print("six_syllable_phrase: Too many retries. Re-calling the function...")
    	return six_syllable_phrase(prev, rhyme)

def generate_title():
    return

# uses the topics to find a word with enough rhymes to sustain a verse
def get_rhyme_scheme_word():
    scheme_json = get_word(None, None, topics, '&max=200')
    if(scheme_json == -1):
        print("error")
        return -1
    scheme_word = scheme_json['word']

    scheme_word_frequency = float(scheme_json['tags'][len(scheme_json['tags']) - 1][2:])

    if scheme_word_frequency < 1:
        if printmode:
            print('get_rhyme_scheme_word: ' + scheme_word + ' was too rare: ' + str(scheme_word_frequency) + '. Trying again...')
        return get_rhyme_scheme_word()

    url = 'https://api.datamuse.com/words?md=sf&&rel_rhy=' + scheme_word
    num_rhymes = len(requests.get(url).json())
    if num_rhymes > 25:
        return scheme_word
    else:
        if printmode:
            print('get_rhyme_scheme_word: ' + scheme_word + ' had too few rhymes: ' + str(num_rhymes) + '. Trying again...')
        return get_rhyme_scheme_word()


def tester():
    url = 'https://api.datamuse.com/words?sp=he&qe=sp&md=p'
    word_json = requests.get(url).json()
    print(word_json)
    


# takes a number of verses generates them in french alexandrine, using the topic words chosen above
def generate_alexandrine(num_verses):
    print('serving up a ' + str(num_verses) + '-verse alexandrine...')
    verses = []
    for x in range(num_verses):
        #generate a verse
        rhyme_a = get_rhyme_scheme_word()
        rhyme_b = get_rhyme_scheme_word()
        rhyme_scheme = random.randint(0, 2)

        this_verse = []

        for y in range(4):
            rhyme = '' # ABAB scheme, should randomly pick between ABAB, ABBA, AABB
            if rhyme_scheme == 0:
                rhyme = rhyme_a if (y%2 == 0) else rhyme_b
            elif rhyme_scheme == 1:
                rhyme = rhyme_a if (y == 0 or y == 3) else rhyme_b
            else:
                rhyme = rhyme_a if (y < 2) else rhyme_b

            last_hemistich_prior = ''
            if x == 0 and y == 0:
                last_hemistich_prior = None
            elif y == 0:
                last_hemistich_prior = verses[x-1][0][0] # previous (in reality, next) verse, first line, first word
            else:
                last_hemistich_prior = this_verse[y-1][0]
           
            last_hemistich = six_syllable_phrase(last_hemistich_prior, rhyme)
            first_hemistich = six_syllable_phrase(last_hemistich[0], None)
            first_hemistich.extend(last_hemistich)
            first_hemistich[0] = first_hemistich[0].capitalize()
            first_hemistich.append('\n')

            this_verse.append(first_hemistich)

        this_verse.reverse()
        this_verse[3].append('\n')
        verses.append(this_verse)

    verses.reverse()

    poem = ' '
    for verse in verses:
        for line in verse:
            for word in line:
                poem += word + ' '
    poem 
    print('\n' + poem)
    
    return poem

def write_alexandrines_to_files(num_alexandrines, verse_length):
    for x in range(0, num_alexandrines):
        poem = generate_alexandrine(verse_length if not(verse_length is None) else random.randint(1, 5))
        file_index = str(x) + 'demo_alexandrine'
        poem_file = open(file_index + '.txt', "w")
        poem_file.write(poem)
        poem_file.close()

#tester()
#write_alexandrines_to_files(5, None)



document <= generate_alexandrine(1, 1)











