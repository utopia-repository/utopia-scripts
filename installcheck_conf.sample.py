# A list of known repositories.
REPOS = {'debian': 'http://httpredir.debian.org/debian',
         'urepo': 'https://deb.utopia-repository.org',
         'urepo-nightlies': 'https://ni.deb.utopia-repository.org',
         'ubuntu': 'http://archive.ubuntu.com/ubuntu'}

# A list of architectures to test.
TARGET_ARCHS = ['amd64', 'i386']

# This defines the repos that we want to test. Keys are test target pairs (repo, distribution, suite),
# and values are a list of (repo, distribution, suite) pairs that each test target depends on.
# e.g. Utopia Repository targets declare either Debian main or Ubuntu main+universe in their dependencies.
TARGET_DISTS = {
    ('urepo', 'sid', 'main'): [('debian', 'sid', 'main')],
    ('urepo', 'sid', 'imports'): [('debian', 'sid', 'main'),
                                  ('debian', 'sid', 'contrib'),
                                  ('debian', 'sid', 'non-free'),
                                  ('urepo', 'sid', 'main')],
    ('urepo', 'sid', 'forks'): [('debian', 'sid', 'main'),
                                ('urepo', 'sid', 'main')],
    ('urepo-nightlies', 'sid-nightlies', 'main'): [('debian', 'sid', 'main'),
                                                   ('urepo', 'sid', 'main')],

    ('urepo', 'stretch', 'main'): [('debian', 'stretch', 'main'),
                                   ('debian', 'stretch-backports', 'main'),
                                   ('urepo', 'stretch', 'imports'),
                                  ],
    ('urepo', 'stretch', 'imports'): [('debian', 'stretch', 'main'),
                                      ('debian', 'stretch', 'contrib'),
                                      ('debian', 'stretch', 'non-free'),
                                      ('urepo', 'stretch', 'main'),
                                     ],
    ('urepo', 'stretch', 'forks'): [('debian', 'stretch', 'main'),
                                    ('urepo', 'stretch', 'main'),
                                   ],

    ('urepo', 'buster', 'main'): [('debian', 'buster', 'main'),
                                   ('debian', 'buster-backports', 'main'),
                                   ('urepo', 'buster', 'imports'),
                                 ],
    ('urepo', 'buster', 'imports'): [('debian', 'buster', 'main'),
                                      ('debian', 'buster', 'contrib'),
                                      ('debian', 'buster', 'non-free'),
                                      ('urepo', 'buster', 'main'),
                                    ],
    ('urepo', 'buster', 'forks'): [('debian', 'buster', 'main'),
                                    ('urepo', 'buster', 'main'),
                                  ],

    ('urepo', 'xenial', 'main'): [('ubuntu', 'xenial', 'main'),
                                  ('ubuntu', 'xenial', 'universe')],

    ('urepo', 'bionic', 'main'): [('ubuntu', 'bionic', 'main'),
                                  ('ubuntu', 'bionic', 'universe')],
    ('urepo', 'bionic', 'imports'): [('ubuntu', 'bionic', 'main'),
                                      ('ubuntu', 'bionic', 'universe'),
                                      ('ubuntu', 'bionic', 'restricted'),
                                      ('ubuntu', 'bionic', 'multiverse'),
                                      ('urepo', 'bionic', 'main')],
    ('urepo', 'bionic', 'forks'): [('ubuntu', 'bionic', 'main'),
                                   ('ubuntu', 'bionic', 'universe'),
                                   ('urepo', 'bionic', 'main')],
}
