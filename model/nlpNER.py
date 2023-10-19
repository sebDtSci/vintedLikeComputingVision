""" Python file"""
import spacy
from spacy import displacy, tokenizer
nlp = spacy.load('en_core_web_sm')
from summa import keywords

def extOrg(text):

    # text = [e.capitalize() for e in text]
    # text2 = text.title()
    # print(text2)
    # ner_categories = ["PERSON","ORG","GPE","GRP","PRODUCT"]
    ner_categories = ["GRP","ORG","GPE"]

    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        if ent.label_ in ner_categories:
            # entities.append({ent.text, ent.label_})
            entities.append(ent.text)
    
    key = keywords.keywords(text)
    print(key)

    return entities, key