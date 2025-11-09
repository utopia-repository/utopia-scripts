#!/usr/bin/env python3
"""
Installability checker for Apt repositories, using dose-debcheck as a backend.

By default, this downloads Packages files for the relevant distributions into a temporary folder
(as Packages_REPO_DIST_SUITE_ARCH) and outputs results as Installcheck_REPO_DIST_SUITE_ARCH.txt
in the current folder.
"""

import argparse
import collections
import concurrent.futures
import gzip
import lzma
import os
import shutil
import subprocess
import tempfile
import traceback

import requests
import yaml

RepoTarget = collections.namedtuple('RepoTarget', [
    'repo_name',
    'distribution',
    'suite',
    'architecture'
])

_ARCHIVE_FORMATS = {
    'xz': lzma.decompress,
    'gz': gzip.decompress,
}
def try_download_packages_file(link, filename, extension):
    link = f'{link}.{extension}'
    print('Getting packages link', link)
    try:
        r = requests.get(link, timeout=10)
        r.raise_for_status()  # raise if not success
    except requests.exceptions.RequestException:
        return False

    #print(link, r, len(r.content))
    extract_func = _ARCHIVE_FORMATS[extension]
    try:
        data = extract_func(r.content)
        with open(filename, 'wb') as out_f:
            out_f.write(data)
    except ValueError:
        traceback.print_exc()
        return False
    return True

class InstallCheck():

    def __init__(self, config_path: str):
        with open(config_path, encoding='utf8') as f:
            self.config = yaml.safe_load(f)

    @staticmethod
    def get_packages_filename(target: RepoTarget) -> str:
        """Get the temporary filename for a RepoTarget instance's Packages file"""
        # pylint: disable=consider-using-f-string
        return 'Packages_%s_%s_%s_%s' % target

    def download_packages_file(self, target: RepoTarget, skip_download=False):
        """
        Gets the Packages file given the repository, distribution, suite, and
        architecture.
        """
        url = self.config["repos"][target.repo_name]
        # Example: http://deb.debian.org/debian/dists/sid/main/binary-amd64/
        link = f'{url}/dists/{target.distribution}/{target.suite}/binary-{target.architecture}/Packages'
        filename = self.get_packages_filename(target)

        if not skip_download:
            for ext in _ARCHIVE_FORMATS:
                if try_download_packages_file(link, filename, ext):
                    break
            else:
                print(f'Failed to download any package file for {filename}')
        else:
            if os.path.isfile(filename):
                print('Reusing Packages file %s' % filename)
            else:
                print('Missing Packages file %s; some tests may be skipped!' % filename)

    def get_deps(self, target: RepoTarget) -> set[RepoTarget]:
        """Get dependencies for a RepoTarget"""
        deps = self.config["suite_dependencies"][f"{target.repo_name}/{target.suite}"]
        results = set()
        for dep in deps:
            try:
                dep_repo_name, dep_suite = dep.split('/', 1)
            except ValueError as e:
                raise ValueError(f'Invalid dependency name {dep}') from e
            results.add(RepoTarget(
                dep_repo_name,
                target.distribution,
                dep_suite,
                target.architecture,
            ))
        return results

    def test_dist(self, target: RepoTarget, outfilename: str):
        """
        Runs dose-debcheck on a repo, dist, suite, and arch pair.
        """
        target_filename = self.get_packages_filename(target)
        if not os.path.exists(target_filename):
            print(f"Skipping unavailable dist {target}")
            return

        deps = self.get_deps(target)
        # What we what to run is:
        #  dose-debcheck -fe Packages_of_target --bg Packages_of_dependency_1
        #  --bg Packages_of_dependency_2 ...
        cmd = ['dose-debcheck', '-fe', target_filename]
        for dep_target in deps:
            dep_target_filename = self.get_packages_filename(dep_target)
            if not os.path.exists(dep_target_filename):
                print(f"Skipping dist {target} due to unavailable dependency {dep_target}")
                return

            cmd += ['--bg', dep_target_filename]

        print('Running command', cmd)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        # Read stdout as dose-debcheck runs instead of only returning results at the end.
        lines = []  # XXX: is storing the output text this way this efficient?
        for line in process.stdout:
            line = line.decode()
            print(line, end='')
            lines.append(line)

        process.wait()
        print('process returncode: %s' % process.returncode)
        if process.returncode:
            with open(outfilename, 'w', encoding='utf8') as outfile:
                # Only write reports for combinations that fail testing.
                if lines:
                    outfile.write(f'Results for {target}:\n')
                outfile.writelines(lines)

    def run(self, outdir: str, skip_download=False, max_workers=1, tmpdir=None):
        to_download = set()
        targets = set()
        for target_dist_info in self.config["target_dists"]:
            for suite in target_dist_info["suites"]:
                for arch in self.config["target_archs"]:
                    target = RepoTarget(
                        target_dist_info["repo"],
                        target_dist_info["distribution"],
                        suite,
                        arch
                    )
                    targets.add(target)
                    to_download.add(target)
                    to_download |= self.get_deps(target)

        if tmpdir:
            os.chdir(tmpdir)

        print('targets:', targets)
        print('to_download:', to_download)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            download_futures = {
                executor.submit(self.download_packages_file, target, skip_download=skip_download)
                for target in to_download
            }
            concurrent.futures.wait(download_futures)

            test_dist_futures = {
                # pylint: disable=consider-using-f-string
                executor.submit(self.test_dist, target,
                                os.path.join(outdir, 'Installcheck_%s_%s_%s_%s.txt' % target))
                for target in targets
            }
            concurrent.futures.wait(test_dist_futures)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-t", "--tempdir", help="sets the temporary directory to download Packages files into", type=str, default=tempfile.mkdtemp())
    parser.add_argument("-o", "--outdir", help="sets the output directory to write results to", type=str, default=os.getcwd())
    parser.add_argument("-s", "--skip-download", help="skips downloading new Packages file (most useful with a custom tempdir)", action='store_true')
    parser.add_argument("-p", "--processes", help="amount of processes to use (defaults to amount of CPU cores)", type=int, default=os.cpu_count() or 1)
    parser.add_argument("-c", "--config", help="path to config file", default='installcheck.yml')
    args = parser.parse_args()

    if not shutil.which('dose-debcheck'):
        raise OSError("Could not find 'dose-debcheck' in the PATH!")

    print('Using %s as tempdir' % args.tempdir)
    print('Using %s as outdir' % args.outdir)

    runner = InstallCheck(args.config)
    runner.run(args.outdir, skip_download=args.skip_download, max_workers=args.processes, tmpdir=args.tempdir)

if __name__ == '__main__':
    main()
