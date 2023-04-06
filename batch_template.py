import argparse
from abc import ABC, abstractmethod
from .quality_classifier import QualityClassifer
from .text_cleaner import TextCleaner
from .batch_processor_utils import BatchProcessorUtils
import os,json

class BatchProcessor(ABC):
    def __init__(self, indir, outdir, normalize=True, language='cn'):
        self.indir = indir
        self.outdir = outdir
        self.text_cleaner = TextCleaner()
        self.classifier = QualityClassifer(language=language)
        self.normalize = normalize
        self.language = language
    
    @abstractmethod
    def preprocess(self, line):
        pass
    
    def process(self):
        def single_func(line):
            line = self.preprocess(line)
            dic = json.loads(line)
            if self.normalize:
                cleaned_text = self.text_cleaner.clean(dic['text'], language=self.language)
            else:
                cleaned_text = dic['text']
            if len(cleaned_text) == 0:
                return
            dic['text'] = cleaned_text
            dir_choice, score_dict = self.classifier.classify_and_pareto(cleaned_text)
            dic['score'] = score_dict
            out_path = os.path.join(self.outdir, dir_choice)
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            indir = os.path.basename(self.indir)
            with open(os.path.join(out_path, f'{dir_choice}.{indir}.jsonl'), 'w') as fo:
                # print(dic)
                fo.write(json.dumps(dic, ensure_ascii=False)+'\n')
        batch_processor_utils = BatchProcessorUtils(single_func=single_func, process_dir=self.indir, log_dir='logs')   
        batch_processor_utils.batch_process()
