from musttest.diff.diff import Diff, DiffFormat, DiffReport, DiffError
from musttest.diff import hashcash as hashcash
import os
import glob
import pickle


class Manager:
    def __init__(self, dir_path: str, rel_cache_path: str = ".cache"):
        """
        An instance of diff management module.
        :param dir_path: Absolute path of target path to analyze.
        :param rel_cache_path: Relative path of cache files. (default = ./.cache)
        """
        self.dir_path = dir_path
        # self.dir_path = "/Users/fovjfozk/.pyenv/versions/3.7.1/envs/pytorch/lib/python3.7/site-packages/Flask-2.0.0.dev0-py3.7.egg/flask/"
        self.cache_path = os.path.join(dir_path, rel_cache_path)

    def analyze(self) -> DiffReport:
        # analyzing does not update the file yet.
        """
        Diff analyzer between cache and current.
        How it works:
        1. 우선 모든 파일의 복사본을 준비한다.
        2. 각 라인을 해시하여 정보를 array 등에 담는다.
        3. 전체 라인을 해시하여 파일의 정보를 대표한다.
        4. 기존에 있던 복사본의 각 파일과 해시값을 비교하여 파일 단위에 변화가 있는지 알아낸다.
        5. 변화가 있는 파일에 대해 라인 단위로 변화가 있는지 알아낸다.
        :return: A src.diff.diff.DiffReport instance.
        """
        if not os.path.isdir(self.dir_path):
            raise DiffError("Project path is empty: %s" % self.dir_path)

        if not os.path.isdir(self.cache_path):
            os.mkdir(self.cache_path)

        # dict: key = file directory, value = hashcash list
        hashcashdic = dict()
        for filename in glob.iglob(self.dir_path + '**/**', recursive=True):
            if os.path.isfile(filename) and os.path.splitext(filename)[-1] == ".py":
                with open(filename, 'r', encoding="UTF8") as file:
                    rel_path = os.path.relpath(filename, self.dir_path)
                    try:
                        hashcashdic[rel_path] = hashcash.hashcash(file.readlines())
                    except:
                        continue
        # dict: key = file directory (relative), value = hashcash list
        # What if cache file does not exists?
        prev_cache = pickle.load(
            open(os.path.join(self.cache_path, "cache.pkl"), "rb"))

        diff_formats = []
        for f in hashcashdic.keys():
            df = DiffFormat(f)
            # if previous cache exists for the file, use Diff.analyze to find difference.
            if f in prev_cache.keys():
                Diff.analyze(df, hashcashdic[f], prev_cache[f])

            # if no previous cache for the file was found, add all lines to added.
            else:
                with open(os.path.join(self.dir_path, f), 'r', encoding="UTF8") as fl:
                    df.added = range(1, len(fl.readlines()))
            diff_formats.append(df)
        return DiffReport(diff_formats)

    def update_cache(self) -> None:
        # dump as dictionary with its key is relative path of the file with respect to root directory
        hashcashdic = dict()
        for filename in glob.iglob(os.path.join(self.dir_path, '**/**'), recursive=True):
            if os.path.isfile(filename) and os.path.splitext(filename)[-1] == ".py":
                with open(filename, 'r', encoding="UTF8") as file:
                    rel_path = os.path.relpath(filename, self.dir_path)
                    hashcashdic[rel_path] = hashcash.hashcash(file.readlines())

        if not os.path.isdir(self.cache_path):
            os.mkdir(self.cache_path)
        pickle.dump(hashcashdic, open(os.path.join(
            self.cache_path, "cache.pkl"), "wb"))
