from musttest.cover.cover import Cover
from musttest.diff.manager import DiffReport, Manager
from musttest.util.format import unittest_formatter
import os
import pickle

class CoverObject:
    # TODO delete this class and change src.cover.cover
    def __init__(self, file_path: str, covered: dict):
        self.file_path = file_path
        self.covered = covered

    def get_file_path(self):
        return self.file_path


class Georeum:
    def __init__(self, root_directory: str, test_directory: str, rel_cache_directory: str = ".cache"):
        """
        Initializes Georeum instance.
        :param root_directory: Absolute path of root directory of project want to examine.
        :param test_directory: Absolute path Directory that has tests. It's commonly \"root_directory\"/tests/
        :param rel_cache_directory: Relative path of cache directory that Georeum uses. Default is \"root_directory\"/.cache
        """
        self.root_directory = root_directory
        self.test_directory = test_directory
        self.cache_directory = os.path.join(
            root_directory, rel_cache_directory)
        self.manager = Manager(self.root_directory, self.cache_directory)
        self.selected = None

    @staticmethod
    def search_py_file(target_directory: str) -> list:
        """
        Search all .py files in target directory.
        :param target_directory: Absolute path of directory that want to examine.
        :return: List of pathes of .py files.
        """
        # find all of py file in target_directory recursively
        target_file_list = []
        try:
            filenames = os.listdir(target_directory)
            for filename in filenames:
                full_filename = os.path.join(target_directory, filename)
                if os.path.isdir(full_filename):
                    target_file_list.extend(
                        Georeum.search_py_file(full_filename))
                else:
                    ext = os.path.splitext(full_filename)[-1]
                    if ext == '.py' and 'test' in filename.lower() :
                        target_file_list.append(full_filename)
        except PermissionError:
            pass

        return target_file_list

    def save(self):
        """
        Saves current coverage and diff cache.
        """
        # TODO should manage dir_path for real tool release
        # 1. hash latest update code and save
        self.manager.update_cache()

        # 2. searh py file at target_directory & select target test file
        test_file_list = Georeum.search_py_file(self.test_directory)
        # 2.1 Select only files with name test_*
        test_file_list = [testfile for testfile in test_file_list if os.path.basename(testfile).find("test") != -1]
        covered_list = []
        for test_file in test_file_list:
            # 3. get coverage for each file
            from termcolor import cprint
            cprint(unittest_formatter(test_file, self.root_directory), 'cyan')

            is_unittest = False if unittest_formatter(test_file, self.root_directory)[-1] == "." else True
            if not is_unittest:
                covered = Cover.get_coverage(
                    args=['pytest', test_file], root_path=self.root_directory, module_use=True)
            else:
                covered = Cover.get_coverage(
                    args=['unittest', unittest_formatter(test_file, self.root_directory)], root_path=self.root_directory, module_use=True)

            covered_list.append(CoverObject(test_file, covered))

        # 4. save coverage object list to data
        pickle.dump(covered_list,
                    open(os.path.join(self.cache_directory, "coverage.bin"), 'wb'))

    def __contains_line(self, cover_object: CoverObject, report: DiffReport) -> bool:
        """
        A function that finds whether diff exists in coverage
        :param cover_object: Coverage to examine.
        :param report: DiffReport typed class that has diff information.
        :return: A boolean value indicates whether diff exists in coverage
        """
        for covered in cover_object.covered.values():
            # relative path of covered file with respect to root directory
            rel_path = os.path.relpath(covered.file_path, self.root_directory)
            for df in report.modified_files():
                # if coverage is in modified files:
                if df.name == rel_path and \
                        (covered.line_no in df.added or covered.line_no in df.removed):
                    return True

        return False

    def select_test_case(self) -> list:
        """
        Selects test cases that are needed to be run.
        :return: A list of path of test cases.
        """
        # TODO should manage dir_path for real tool release

        # get latest code coverage
        cover_object_list = pickle.load(
            open(os.path.join(self.cache_directory, "coverage.bin"), 'rb'))

        # find diff of all update code
        # TODO: this does not covers the case where modified lines are at the edge of the coverage
        diff_report = self.manager.analyze()
        selected_tests = []
        for cover_object in cover_object_list:
            # if the coverage of a test has diff, add its path to selected_tests list
            if self.__contains_line(cover_object, diff_report):
                selected_tests.append(cover_object.file_path)

        self.selected = selected_tests
        print(self.selected)
        return selected_tests

    def test_run(self):
        """
        Runs test cases that are selected
        :return: A list of test cases ran
        """
        # ran : test file ran
        # updated : updated CoverObject
        ran = []
        updated = []

        # 1. hash latest update code and save
        self.manager.update_cache()

        # 2. get latest code coverage
        coverd_object_list = pickle.load(
            open(os.path.join(self.cache_directory, "coverage.bin"), 'rb'))

        # 3. traverse self.selected and update Coverage

        for test_file in self.selected:
            is_unittest = False if unittest_formatter(test_file, self.root_directory)[-1] == "." else True
            if not is_unittest:
                covered = Cover.get_coverage(
                    args=['pytest', test_file], root_path=self.root_directory, module_use=True)
            else:
                covered = Cover.get_coverage(
                    args=['unittest', unittest_formatter(test_file, self.root_directory)], root_path=self.root_directory, module_use=True)
            
            for i, co in enumerate(coverd_object_list):
                if co.get_file_path() == test_file:
                    updated.append(i)
            coverd_object_list.append(CoverObject(test_file, covered))
            ran.append(test_file)

        # for test_file in self.selected:
        #     covered = Cover.get_coverage(
        #         args=['pytest', test_file], root_path=self.root_directory, module_use=True)
        #     for i, co in enumerate(coverd_object_list):
        #         if co.get_file_path() == test_file:
        #             updated.append(i)
        #     coverd_object_list.append(CoverObject(test_file, covered))
        #     ran.append(test_file)

        # 4. old CoverObject remove
        for i in sorted(updated, reverse=True):
            del coverd_object_list[i]

        # 5. save new coverage object list to data
        pickle.dump(coverd_object_list,
                    open(os.path.join(self.cache_directory, "coverage.bin"), 'wb'))
        return ran
