import fasttext
import numpy as np

default_config = {
    'en_model_path': '/share/project/bowen/dev_data/norm_corpus/save_model/fasttext-mergeHL_en-2epoch.bin',
    'zh_model_path': '/share/project/zxq/model/fasttext-checkpoint-mergeNewWuDao-2epoch.bin',
}

class QualityClassifer(object):
    def __init__(self, config=None, language='cn'):
        self.config = config if config else default_config
        if language == 'en':
            self.model = fasttext.load_model(self.config['en_model_path'])
        elif language == 'cn':
            self.model = fasttext.load_model(self.config['zh_model_path'])

    def classify(self, text):
        text = text.replace('\n', '')
        if len(text)>0:
            label_pred = self.model.predict(text)
        else:
            label_pred = None
        if label_pred[0][0] == '__label__1':
            return label_pred[1][0]
        else:
            return 1.0 - label_pred[1][0]
        return prob
    
    def classify_and_pareto(self, text):
        prob = self.classify(text)
        pareto_list = [np.random.pareto(i) for i in [9, 8, 7, 6, 5, 4, 3, 2, 1, 0.5]]
        pareto_choice = -1
        for i in range(len(pareto_list)):
            if pareto_list[i] > 1 - prob:
                pareto_choice = i
                break
        if pareto_choice == -1:
            dir_choice = '0.5_less'
        elif pareto_choice == 10:
            dir_choice = '0.5'
        else:
            dir_choice = str(9-i)
        score_dict = {
            "proba_float" : prob,
            "pareto(9)": pareto_list[0],
            "pareto(8)": pareto_list[1],
            "pareto(7)": pareto_list[2],
            "pareto(6)": pareto_list[3],
            "pareto(5)": pareto_list[4],
            "pareto(4)": pareto_list[5],
            "pareto(3)": pareto_list[6],
            "pareto(2)": pareto_list[7],
            "pareto(1)": pareto_list[8],
            "pareto(0.5)": pareto_list[9],
            "pareto(9)>1-score": bool(pareto_list[0] > 1 - prob),
            "pareto(8)>1-score": bool(pareto_list[1] > 1 - prob),
            "pareto(7)>1-score": bool(pareto_list[2] > 1 - prob),
            "pareto(6)>1-score": bool(pareto_list[3] > 1 - prob),
            "pareto(5)>1-score": bool(pareto_list[4] > 1 - prob),
            "pareto(4)>1-score": bool(pareto_list[5] > 1 - prob),
            "pareto(3)>1-score": bool(pareto_list[6] > 1 - prob),
            "pareto(2)>1-score": bool(pareto_list[7] > 1 - prob),
            "pareto(1)>1-score": bool(pareto_list[8] > 1 - prob),
            "pareto(0.5)>1-score": bool(pareto_list[9] > 1 - prob)
        }
        return dir_choice, score_dict


if __name__ == "__main__":
    qc = QualityClassifer(language='en')
    raw_text = """Riders Field is a baseball park in Frisco, Texas, United States. The home of the Frisco RoughRiders, a Double-A team of the Texas League, it opened on April 3, 2003, and can seat 10,216 people. Primarily a venue for Minor League Baseball games, the facility also hosts high school and college baseball tournaments and other public and private events. It has been the site of three Texas League All-Star Games. In his design, park architect David M. Schwarz desired the creation of a village-like "park within a (ball)park". The stadium received the 2003 Texas Construction award for Best Architectural Design. Attendance for RoughRiders games at the stadium has consistently placed first or second in the Texas League and at the Double-A classification since its opening. After having the second-highest attendance in its first two seasons, it had the highest in the league and classification from 2005 to 2019. (Full article...)"""
    label = qc.classify_and_pareto(raw_text)
    print(label)
