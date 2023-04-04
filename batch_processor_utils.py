import os,json

class BatchProcessorUtils(object):
    def __init__(self, single_func=None, process_dir=None, log_dir=None):
        self.single_func = single_func
        self.process_dir = process_dir
        self._process_dir = os.path.basename(process_dir)
        self.log_dir = log_dir

    def batch_process(self):
        assert self.single_func
        for file in os.listdir(self.process_dir):
            abspath = os.path.join(self.process_dir, file)
            with open(abspath, 'r') as f:
                self.logging_directory_init()
                num_lines = -1
                ready_lines = self.load_log_file(path=abspath)
                for line in f:
                    num_lines += 1
                    if ready_lines >= num_lines:
                        continue
                    line = f.readline().strip()
                    self.single_func(line)
                    self.logging(file, num_lines)

    def logging_directory_init(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        with open(os.path.join(self.log_dir, f'log.{self._process_dir}'), 'w+') as f:
            dic = {path: -1 for path in os.listdir(self.process_dir)}
            f.write(json.dumps(dic, ensure_ascii=False))
    
    def load_log_file(self, path=None):
        log_file = os.path.join(self.log_dir, f'log.{self._process_dir}')
        f = open(log_file, 'r')
        dic = json.loads(f.read())
        f.close()
        if not path:
            return dic
        return dic.get(path, -1)
        
    def logging(self, path, num_lines):
        log_file = os.path.join(self.log_dir, f'log.{self._process_dir}')
        if not os.path.exists(log_file):
            self.logging_directory_init()
        dic = self.load_log_file()
        dic[path] = num_lines
        with open(log_file, 'w+') as fo:
            fo.write(json.dumps(dic, ensure_ascii=False))