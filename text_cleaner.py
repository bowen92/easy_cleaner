# Copyright © 2023 BAAI. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License")
from collections import OrderedDict
import re
import unicodedata
import json
import html
from urlextract import URLExtract
import string
from .ruleset import URLRuleSet, UserPrivacyRuleSet, TextIntegrityRuleSet
import opencc
import pathlib
import re

default_config = {
    "trad2simple": True,
    "filter_emoji": True,
    "filter_control": True,
    "filter_personal": True,
    "filter_url": True,
    "filter_extraspace": True,
    "min_length": 16,
    "length_check": True,
    "do_end_clip": True,
    "end_mark_check": True,
    "double_mark_check": True
}

class TextCleaner(object):
    def __init__(self, config=None, language='cn'):
        self.config = default_config
        self.language = language
        if config:
            self.config.update(config)
        if language!='cn':
            self.config['trad2simple'] = False
        self.build_pipeline(self.config)
        
    def build_pipeline(self, config):
        self.pipeline = [self.check_ratio]
        if config['trad2simple']:
            try:
                self.t2s_converter = opencc.OpenCC('t2s.json')
            except:
                self.t2s_converter = opencc.OpenCC('t2s')
            self.pipeline.append(self.trad2simple)
        
        if config['filter_emoji']:
            self.emoji_set = self._build_emoji_set()
            self.emoji_regex = self._build_emoji_regex()
            self.pipeline.append(self.filter_emoji)
        
        if config['filter_control']:
            self.pipeline.append(self.filter_control)
        
        if config['filter_personal']:
            self.privacy_regex_set = UserPrivacyRuleSet()
            self.pipeline.append(self.filter_personal)

        if config['filter_url']:
            self.url_regex_set = URLRuleSet()
            self.url_extractor = URLExtract()
            self.pipeline.append(self.filter_url)
        
        if config['filter_extraspace']:
            self.pipeline.append(self.filter_extraspace)
        
        if config['do_end_clip']:
            self.ALL_LANGUAGE_END_CLIP_REGEX = TextIntegrityRuleSet().ALL_LANGUAGE_END_CLIP_REGEX
            self.pipeline.append(self.do_end_clip)

        if config['end_mark_check']:
            self.ALL_LANGUAGE_END_PUNCTION = TextIntegrityRuleSet().ALL_LANGUAGE_END_PUNCTION
            self.pipeline.append(self.end_mark_check)
        
        if config['double_mark_check']:
            self.ALL_LANGUAGE_WHOLE_SENTENCE_MARK = TextIntegrityRuleSet().ALL_LANGUAGE_WHOLE_SENTENCE_MARK
            self.pipeline.append(self.double_mark_check)

        if config['length_check'] and config['min_length']:
            self.min_length = config['min_length']
            self.pipeline.append(self.length_check)

    def check_ratio(self, text):
        if len(text) == 0:
            return ''
        if self.language == 'cn':
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        else:
            chinese_chars = ''
        english_chars = re.findall(r'[a-zA-Z]', text)
        digit_chars = re.findall(r'\d', text)
        total_chars = len(chinese_chars) + len(english_chars) + len(digit_chars)
        total_ratio = total_chars/len(text)
        return text if total_ratio>0.5 else ""

    def _build_emoji_set(self):
        import os
        emoji_path = os.path.join(os.path.dirname(__file__), "emojis.json")
        with open(emoji_path, 'r') as fr:
            data = json.load(fr)
        emojis = [eval(repr(emoji_code).replace("\\\\", "\\"))
                  for emoji_code in data.keys()]
        emojis = [emoji_code for emoji_code in emojis if len(emoji_code) == 1]
        return set(emojis)

    def _build_emoji_regex(self):
        regex_msg = re.compile(
            '[\U0001F600-\U0001F92F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F190-\U0001F1FF\U00002702-\U000027B0\U0001F926-\U0001FA9F\u200d\u2640-\u2642\u2600-\u2B55\u23cf\u23e9\u231a\ufe0f\u23ee\U0000200D' + ']+')
        return regex_msg

    def trad2simple(self, text):
        assert self.t2s_converter
        return self.t2s_converter.convert(text)
    
    def filter_emoji(self, text):
        assert self.emoji_regex
        assert self.emoji_set
        cleaned_text = self.emoji_regex.sub(u'', text)
        cleaned_chars = [
            char for char in cleaned_text if char not in self.emoji_set]
        return ''.join(cleaned_chars).strip()
    
    def _is_control(self, char):
        """Checks whether `chars` is a control character."""
        # skip the following control chars
        if char == "\t" or char == "\n" or char == "\r":
            return False
        cat = unicodedata.category(char)
        if cat.startswith("C"):
            return True
        return False

    def filter_control(self, text):
        norm_text = ''
        for idx, char in enumerate(text):
            if not self._is_control(char):
                norm_text += char
        return norm_text

    def filter_personal(self, text):
        assert self.privacy_regex_set
        cleaned_article = html.unescape(text)
        for regex_exp in self.privacy_regex_set.REGEX_PIPELINE:
            cleaned_article = re.sub(regex_exp, "", cleaned_article, 500)
        return cleaned_article
    
    def _contain_url(self, text):
        url_hits_num = [
            True for hit in self.url_regex_set.URL_HITS if hit in text]
        if len(url_hits_num) > 0:
            return True
        else:
            return False
    
    def filter_url(self, text):
        assert self.url_regex_set
        assert self.url_extractor
        if not self._contain_url(text):
            return text
        article = html.unescape(text)
        urls = [re.escape(url) for url in self.url_extractor.find_urls(article)]
        patternsRegex = '(' + '|'.join(urls) + ')'
        article = re.sub(patternsRegex, '', article).strip()
        urls = re.findall(self.url_regex_set.URL_REGEX, article)
        all_regex_urls_temp = [y for y in list(set(sum([re.split(r'http:|https:|ftp:|HTTP:|HTTPS:|FTP:', ''.join(
            x for x in url if x in string.printable)) for url in urls], []))) if len(y) > 1]
        all_regex_urls = list(map(lambda x: 'http:' + x, all_regex_urls_temp)) + list(map(lambda x: 'https:' + x, all_regex_urls_temp)) + list(map(lambda x: 'ftp:' + x, all_regex_urls_temp)) + \
            list(map(lambda x: 'HTTP:' + x, all_regex_urls_temp)) + list(map(lambda x: 'HTTPS:' + x, all_regex_urls_temp)) + list(map(lambda x: 'FTP:' + x, all_regex_urls_temp))
        patterns_regex = '|'.join(all_regex_urls).replace(',', '').replace(':', '\:').replace('?', '\?').replace(
            '=', '\=').replace('&', '\&').replace('.', '\.').replace('#', '\#').replace('/', '\/')
        cleaned_article = re.sub(
            re.escape(patterns_regex), '', article, 1000, flags=re.I).strip()
        if 'http' in cleaned_article:
            urls_further = re.findall(
                self.url_regex_set.URL_REGEX_FURTHER, cleaned_article)
            all_regex_urls_temp_further = [y for y in list(set(sum([re.split(r'http:|https:|ftp:|HTTP:|HTTPS:|FTP:', ''.join(
                x for x in url if x in string.printable)) for url in urls_further], []))) if len(y) > 1]
            all_regex_urls_further = list(map(lambda x: 'http:' + x, all_regex_urls_temp_further)) + list(map(lambda x: 'https:' + x, all_regex_urls_temp_further)) + list(map(lambda x: 'ftp:' + x, all_regex_urls_temp_further)) + list(
                map(lambda x: 'HTTP:' + x, all_regex_urls_temp_further)) + list(map(lambda x: 'HTTPS:' + x, all_regex_urls_temp_further)) + list(map(lambda x: 'FTP:' + x, all_regex_urls_temp_further))
            patterns_regex_further = '|'.join(all_regex_urls_further).replace(',', '').replace(':', '\:').replace(
                '?', '\?').replace('=', '\=').replace('&', '\&').replace('.', '\.').replace('#', '\#').replace('/', '\/')
            cleaned_article = re.sub(
                patterns_regex_further, '', cleaned_article, 1000, flags=re.I).strip()
        return cleaned_article
    
    def filter_extraspace(self, article):
        article = re.sub("[\t\u3000\s]+", " ", article)
        article = re.sub("[\r\n]+", "\n", article).strip()
        return article
    
    def do_end_clip(self, text):
        assert self.ALL_LANGUAGE_END_CLIP_REGEX
        clip_ret = re.search(self.ALL_LANGUAGE_END_CLIP_REGEX, text)
        if clip_ret:
            return clip_ret.group()
        else:
            return ""
    
    def length_check(self, text):
        num_chars = len(re.findall("\S", text))
        if num_chars >= self.min_length:
            return text
        else:
            return ""

    def end_mark_check(self, article):
        '''
            make sure at least one sentence exists in this article, otherwise drop it
        '''
        assert self.ALL_LANGUAGE_END_PUNCTION
        new_article = [
            x for x in self.ALL_LANGUAGE_END_PUNCTION if x in article]
        if len(new_article) >= 1:
            return article
        else:
            return ""

    def double_mark_check(self, article):
        '''
            double-mark validation
        '''
        assert self.ALL_LANGUAGE_WHOLE_SENTENCE_MARK
        new_article = [x for x in self.ALL_LANGUAGE_WHOLE_SENTENCE_MARK if (
            (x[0] in article) and (x[1] in article))]
        if len(new_article) >= 1:
            return article
        else:
            return ""

    def clean(self, text):
        assert len(self.pipeline)>0
        for func in self.pipeline:
            text = func(text)
            if len(text)==0:
                break
        return text.strip()
    
if __name__=="__main__":
    tc = TextCleaner()
    raw_text = """-a lo que ha derivado este especial velorio de guaguas-.\\"invitaban a hombres de mi familia y yo me colaba entre med
io. me iba oculta. pero a la gente de campo le llamaba la atencion. ahora no tanto, aunque si antiguamente. cuando comence, era
 novedoso que cantara una mujer\\", rememora. desde la poesia popular, rosa araneda fue una grande que le abrio paso en el tema
. de acuerdo con el portal memoriachilena.cl, ella nacio alrededor de 0000. segun otros sitios web, llego al mundo en 0000, nad
a menos que en las tierras de san vicente de tagua tagua. sus versos abordaron diversos topicos e incluso escribio unos en hono
r a machali, donde se visualiza su amplio conocimiento de la cultura campesina. otros los dedico a la guerra civil de 0000, res
altando su compromiso con la contingencia politica. se llamo a si misma la \\"poetisa cronista\\", titulo considerado como just
o por diversos expertos, al haber descrito las circunstancias en que vivieron obreros, mujeres e indigenas.sangre nuevajuan bus
tamante tiene cuatro hijos. dos de ellos estan imbuidos en el mundo de la musica, pero ninguno en la poesia cantada que cultiva
 su padre desde el canto a lo divino, a lo humano y en la paya. \\"a lo mejor, todavia no ha llegado su tiempo\\", esboza. no o
bstante, el ve interes en las nuevas generaciones.\\"es mucha la cantidad de poetas y de payadores jovenes que hay, en comparac
ion con cuando yo recien conoci el tema. es a raiz de los talleres que se han dado, gracias a los fondos concursables. toda una
 cadena, hace que este arte se desarrolle mejor. pero es algo practicamente escondido. porque si le hablas al comun de la gente
 de esto, no sabe. sin embargo hay un publico cautivo, siempre alerta respecto a que pasa o donde hay un encuentro\\", asegura.
en sus palabras, tampoco faltan los que asisten por primera vez a un """
    print(tc.clean(raw_text))