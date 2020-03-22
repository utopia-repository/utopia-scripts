#!/usr/bin/env python3
"""
Generates static package lists for an aptly repository.
Given a list of distribution/component targets, this script will auto-resolve which repos
or snapshots they point to.
"""
import argparse
import enum
import html
import json
import time

# External modules
import requests
import requests_unixsocket
import yaml

class PackageEntry():
    """
    Represents a package entry.
    """
    def __init__(self, name, version, architecture, source_name, component, files, description=None, depends=None, recommends=None, suggests=None, vcs_browser=None):
        self.name = name
        self.version = version
        self.arch = architecture  # Architecture
        self.source_name = source_name  # Corresponding source package name
        self.component = component
        self.files = files
        self.description = description
        # Optional fields
        self.depends = depends
        self.recommends = recommends
        self.suggests = suggests
        self.vcs_browser = vcs_browser

    def _resolve_pool_url(self, pool_root_url, filename):
        """Resolves the download URL for a filename."""
        # For Debian repos this uses the following format:
        #    https://deb.debian.org/debian/pool/<component>/<prefix>/<source package name>/<filename>
        # e.g.
        #    https://deb.debian.org/debian/pool/main/v/variety/variety_0.8.3-1_all.deb
        #    https://deb.debian.org/debian/pool/main/liba/libayatana-indicator/libayatana-indicator_0.6.2-3.dsc
        # Note: Debian convention uses the first character of the source package name to split
        # the URL, or the first four letters (libX) if the source package starts with "lib"
        if self.source_name.startswith('lib'):
            prefix = self.source_name[:4]
        else:
            prefix = self.source_name[0]
        return f'{pool_root_url}/{self.component}/{prefix}/{self.source_name}/{filename}'

    def get_download_url(self, pool_root_url):
        """Resolves a download URL for the package given the root URL of the pool/ folder."""
        if self.arch == 'source':
            filename = [entry for entry in self.files if entry.endswith('.dsc')]
        else:
            filename = self.files
        filename = filename[0]

        return self._resolve_pool_url(pool_root_url, filename)

    def __repr__(self):
        return f'<PackageEntry object for {self.name}_{self.version}_{self.arch}>'

class AptlySourceType(enum.Enum):
    SNAPSHOT = 0
    REPO = 1

class AptlyList():
    def __init__(self, config_path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def aptly_call(self, path):
        """Runs a GET request on aptly using the given path."""
        endpoint = self.config['api']['endpoint']
        with requests_unixsocket.monkeypatch():
            url = f'{endpoint}/{path}'
            r = requests.get(url)
            return r.json()

    def get_published_dists(self):
        """
        Return a mapping of published (distribution, component) pairs to their source repo/snapshot.
        """
        results = {}

        data = self.aptly_call('publish')
        for entry in data:
            dist = entry['Distribution']
            source_type = AptlySourceType.REPO if entry['SourceKind'] == 'local' else AptlySourceType.SNAPSHOT
            for component_entry in entry['Sources']:
                component = component_entry['Component']
                source_name = component_entry['Name']
                results[(dist, component)] = (source_type, source_name)
        return results

    def get_packages(self, source_type, source_name, component):
        """
        Returns a list of PackageEntry representing the packages in the given source repo / snapshot.
        """
        if source_type == AptlySourceType.SNAPSHOT:
            package_list = self.aptly_call(f'snapshots/{source_name}/packages?format=details')
        else:
            package_list = self.aptly_call(f'repos/{source_name}/packages?format=details')

        results = []
        for package in package_list:
            name = package['Package']
            is_source = 'Binary' in package
            if is_source:
                # The Files field for a source package looks like the following:
                # " 97fdc50df9688f7bfa5e108236cbded2 2080 numix-icon-theme-square_19.05.07-0utopia1.debian.tar.xz\n 0a87d8bf45f72f2bf1637c37ecb505c1 2114 numix-icon-theme-square_19.05.07-0utopia1.dsc\n 3b8e0e83ec5f40d034f6e752f527cdeb 1978947 numix-icon-theme-square_19.05.07.orig.tar.gz\n"
                files = [file_entry.split()[-1] for file_entry in package['Files'].splitlines()]
                source_name = name
                description = None
            else:
                files = [package['Filename']]
                # aptly seems to only include the 'Source' field if binary package name != source
                source_name = package.get('Source', name)
                # Also some packages are formatted "source (version)" - we should remove the version tag
                source_name = source_name.split()[0]

                # Get the first line of the package description
                description = package['Description'].splitlines()[0].strip()

            entry = PackageEntry(
                name=name,
                architecture='source' if is_source else package['Architecture'],
                version=package['Version'],
                source_name=source_name,
                component=component,
                description=description,
                depends=package['Build-Depends'] if is_source else package.get('Depends'),
                files=files,
                # Only set for binary packages
                recommends=package.get('Recommends'),
                suggests=package.get('Suggests'),
                # Only set for source packages
                vcs_browser=package.get('Vcs-Browser')
            )
            results.append(entry)
        return results

    def write_package_list(self, dist, component, packages):
        """
        Write a package list for the given distribution+component given a list of PackageEntry.
        """
        html_opts       = self.config['html']
        repo_name       = html_opts['repo_name']
        extra_headers   = html_opts.get('extra_headers', '')
        output_filename = html_opts['output_filename']
        pool_root_url   = html_opts.get('pool_root_url')

        extractor_opts     = self.config['extractors']
        extract_changelogs = extractor_opts.get('changelogs', False)
        run_uscan          = extractor_opts.get('uscan', False)

        filename = output_filename.format(distribution=dist, component=component)

        packages.sort(key=lambda entry: entry.name)

        with open(filename, 'w') as outf:
            outf.write(f"""<!DOCTYPE HTML>
<html>
<head><title>Package List for {dist}/{component} - {repo_name}</title>
<meta charset="UTF-8">
<meta name=viewport content="width=device-width">
{extra_headers}
</head>
<body>
<a href="/">Back to root</a>
<br><br>
<table class="sortable">
<tr>
<th>Package Name</th>
<th>Version</th>
<th>Architecture</th>""")
            if extract_changelogs:
                outf.write("""<th>Changelog</th>""")
            if run_uscan:
                outf.write("""<th>Watch Status</th>""")
            outf.write("""<th>Vcs-Browser</th>
<th>Package Relations</th>""")

            for entry in packages:
                # For the name field, include the first line of the package description as a tooltip if available
                if entry.description:
                    name_field = """<span title="{0} - {1}" class="tooltip">{0}</span>""".format(entry.name, html.escape(entry.description))
                else:
                    name_field = entry.name

                # The architecture column will be a link pointing to the package file if resolving pool URLs is enabled
                if pool_root_url:
                    download_link = entry.get_download_url(pool_root_url)
                    arch_field = f"""<a href="{download_link}">{entry.arch}</a>"""
                else:
                    arch_field = entry.arch

                # Name, version, architecture/download URL columns
                outf.write(f"""<tr id="{entry.name}_{entry.version}">
<td>{name_field}</td>
<td>{entry.version}</td>
<td>{arch_field}</td>
""")
                # Changelog column
                if extract_changelogs:
                    # STUB: not implemented yet
                    #f.write("""<td><a href="{}">Changelog</a></td>""".format(os.path.relpath(changelog_path, OUTDIR)))
                    outf.write("""<td>N/A</td>""")

                # uscan / Watch Status column
                if run_uscan:
                    # STUB: not implemented yet
                    outf.write("""<td>N/A</td>""")

                # Vcs-Browser column
                if entry.vcs_browser:
                    outf.write(f"""<td><a href="{entry.vcs_browser}">{entry.vcs_browser}</a>""")
                else:
                    outf.write("""<td>N/A</td>""")

                # Package Relations column
                dependency_text = ''
                if entry.depends:
                    heading = 'Build-Depends' if entry.arch == 'source' else 'Depends'
                    dependency_text += f"""<span class="dependency deptype-depends">{heading}:</span> {html.escape(entry.depends)}<br>"""
                if entry.recommends:
                    heading = 'Recommends'
                    dependency_text += f"""<span class="dependency deptype-recommends">{heading}:</span> {html.escape(entry.recommends)}<br>"""
                if entry.suggests:
                    heading = 'Suggests'
                    dependency_text += f"""<span class="dependency deptype-suggests">{heading}:</span> {html.escape(entry.suggests)}<br>"""
                outf.write(f"""<td>{dependency_text}</td>
</tr>""")

            curr_time = time.strftime("%I:%M:%S %p, %b %d %Y +0000", time.gmtime())
            outf.write(f"""</table>
<p><b>Total items:</b> {len(packages)}</p>
<p>Last updated {curr_time}</p>
</body>
</html>""")

    def process_targets(self, targets):
        """
        Process a list of "distribution" or "distribution/component" targets. Component defaults to "main" if not set.
        """
        known_dists = self.get_published_dists()
        for target in targets:
            if '/' in target:
                dist, component = target.split('/', 1)
            else:
                dist = target
                component = 'main'
            try:
                source_type, source_name = known_dists[(dist, component)]
                print(f'Using {source_type} {source_name} for target {dist}/{component}')
            except KeyError:
                print(f"ERROR: unknown distribution/component: {dist}/{component}")
                continue
            else:
                packages = self.get_packages(source_type, source_name, component)
                self.write_package_list(dist, component, packages)

                # FOR DEBUGGING
                #for pkg in packages:
                #    print(json.dumps(pkg.__dict__))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    #parser.add_argument("-V", "--version", action='version', version=f'aptlylist {__version__}')
    parser.add_argument("-c", "--config", type=str, help=f'path to config file (defaults to aptlylist2.yaml)', default='aptlylist2.yaml')
    parser.add_argument("targets", nargs='+', help='targets to process - can be in the form "distribution" or "distribution/component"')
    args = parser.parse_args()

    list_engine = AptlyList(args.config)
    list_engine.process_targets(args.targets)

if __name__ == '__main__':
    main()
