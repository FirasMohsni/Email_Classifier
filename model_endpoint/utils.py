import re
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize




contractions_francaises = {
    r"\b(l')([aeiouhAEIOUH])": r"le \2",
    r"\b(L')([aeiouhAEIOUH])": r"Le \2",
    r"\b(d')([aeiouhAEIOUH])": r"de \2",
    r"\b(D')([aeiouhAEIOUH])": r"De \2",
    r"\b(j')([aeiouhAEIOUH])": r"je \2",
    r"\b(J')([aeiouhAEIOUH])": r"Je \2",
    r"\b(m')([aeiouhAEIOUH])": r"me \2",
    r"\b(M')([aeiouhAEIOUH])": r"Me \2",
    r"\b(n')([aeiouhAEIOUH])": r"ne \2",
    r"\b(N')([aeiouhAEIOUH])": r"Ne \2",
    r"\b(s')([aeiouhAEIOUH])": r"se \2",
    r"\b(S')([aeiouhAEIOUH])": r"Se \2",
    r"\b(t')([aeiouhAEIOUH])": r"te \2",
    r"\b(T')([aeiouhAEIOUH])": r"Te \2",
    r"\b(c')([aeiouhAEIOUH])": r"ce \2",
    r"\b(C')([aeiouhAEIOUH])": r"Ce \2",
    r"\b(qu')([aeiouhAEIOUH])": r"que \2",
    r"\b(Qu')([aeiouhAEIOUH])": r"Que \2"
}

def expand_french_contractions(text):
    for pattern, replacement in contractions_francaises.items():
        text = re.sub(pattern, replacement, text)
    return text

def remove_digits(text):
    text_no_digits = re.sub(r'\d+', '', text)
    text_no_digits_words = re.sub(r'\b\w*\d\w*\b', '', text_no_digits)
    return text_no_digits_words

def remove_punctuation(text):
    translator = str.maketrans('', '', string.punctuation)
    text_no_punctuation = text.translate(translator)
    return text_no_punctuation

stop_words = set(stopwords.words('french'))
stop_words.update(['un', 'une', 'stb', 'foulen', 'ben', 'bonjour', 'merci', '’', 'MR' , 'Mme'])

def remove_stopwords(text):
    words = word_tokenize(text)
    clean_words = [word for word in words if word.lower() not in stop_words]
    return ' '.join(clean_words)



def preprocess_text(text):
    text = expand_french_contractions(text)
    text = text.lower()
    text = remove_digits(text)
    text = remove_punctuation(text)
    text = remove_stopwords(text)
    
    return text

from flask import render_template_string

def render_search_filter_form():
    form_html = """
    <form method="GET" class="form-inline mb-3">
        <input type="text" class="form-control mr-2" name="search" placeholder="Rechercher..." value="{{ request.args.get('search', '') }}">
        <select class="form-control mr-2" name="status">
            <option value="">Tous les statuts</option>
            <option value="Non Traité" {% if request.args.get('status') == 'Non Traité' %}selected{% endif %}>Non Traité</option>
            <option value="Traité" {% if request.args.get('status') == 'Traité' %}selected{% endif %}>Traité</option>
            <option value="Suspendu" {% if request.args.get('status') == 'Suspendu' %}selected{% endif %}>Suspendu</option>
        </select>
        <button type="submit" class="btn btn-primary">Filtrer</button>
    </form>
    """
    return render_template_string(form_html)