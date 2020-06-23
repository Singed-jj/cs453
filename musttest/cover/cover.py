from typing import List, Dict
from coverage.control import Coverage
from coverage.execfile import PyRunner
from coverage.report import get_analysis_to_report
from musttest.diff.hashcash import hexdigest
from collections import defaultdict
from coverage.misc import NoSource, CoverageException
import os


class Line:
    def __init__(self, file_path: str, line_no: int, text: str):
        self.file_path = file_path
        self.line_no = line_no
        self.text = text[:-1]

    def __repr__(self):
        return "%s(%d): %s" % (self.file_path, self.line_no, self.text)

    def getHash(self):
        return hexdigest(f"{self.file_path}{self.line_no}{self.text}")

    def __str__(self):
        return self.text

    def __int__(self):
        return self.line_no

    def get_file_path(self):
        return self.file_path


class Cover:

    @staticmethod
    def get_coverage(args: list, root_path: str, module_use=False) -> Dict[str, Line]:
        """
        Returns Dict of covered line's Line object.
         :param args: list of module name and target testcase want to get coverage
         :param root_path: target src root want to get coverage
         :return: {
             Line1_hash: {file_path, line_no, line_text},
             Line2_hash: {file_path, line_no, line_text}
         }
        1. cover 한 라인 (file path, line no, line text)
        2. file path 가 root 에 포함되는가.
        2. Line(line text, line no, file path)
        3. res_dict[Line.getHash()] = Line
        4. return res_dict
        """

        regular_path = os.path.abspath(root_path)
        covered = defaultdict(Line)
        # path 에 해당하는 .py file run.
        # report 에 covered line 정보 담겨있음.
        cov = Coverage()
        # args = args[:1] + [root_path] + args[1:]
        runner = PyRunner(args, as_module=module_use)
        runner.prepare()

        cov.start()
        code_ran = True
        try:
            runner.run()
        except NoSource:
            code_ran = False
            raise
        finally:
            cov.stop()
            if code_ran:
                cov.save()

            # testcase.py args 없다고 가정.
            report = get_analysis_to_report(cov, [])
            try:
                for fr, analysis in report:
                    # report : [(file1, [line1, line2, ...]), (), ...]
                    fn = fr.filename
                    if regular_path not in fn:
                        continue

                    if os.path.splitext(fn)[-1] != ".py":
                        continue

                    with open(fn, 'r', encoding="UTF8") as f:
                        lines = f.readlines()
                        if lines:
                            for line_no in analysis.executed:
                                lo = Line(fr.filename, line_no, lines[line_no-1])
                                covered[lo.getHash()] = lo
                        f.close()
            except CoverageException:
                print("There is no Test ran")

            return covered
