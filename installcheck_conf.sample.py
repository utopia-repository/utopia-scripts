# A list of known repositories.
REPOS = {'debian': 'http://deb.debian.org/debian',
         'urepo': 'https://deb.utopia-repository.org',}

# A list of architectures to test.
TARGET_ARCHS = ['amd64', 'i386']

# This defines the repos that we want to test. Keys are test target pairs (repo, distribution, suite),
# and values are a list of (repo, distribution, suite) pairs that each test target depends on.
# e.g. Utopia Repository targets declare either Debian main or Ubuntu main+universe in their dependencies.
TARGET_DISTS = {
    ('urepo', 'sid', 'main'): [('debian', 'sid', 'main')],
    ('urepo', 'sid', 'meta'): [('debian', 'sid', 'main'), ('urepo', 'sid', 'main')],
    ('urepo', 'sid', 'imports'): [('debian', 'sid', 'main'),
                                  ('debian', 'sid', 'contrib'),
                                  ('debian', 'sid', 'non-free'),
                                  ('urepo', 'sid', 'main')],

    ('urepo', 'bullseye', 'main'): [('debian', 'bullseye', 'main'),
                                   ('debian', 'bullseye-backports', 'main'),
                                 ],
    ('urepo', 'bullseye', 'meta'): [('debian', 'bullseye', 'main'),
                                    ('debian', 'bullseye-backports', 'main'),
                                    ('urepo', 'bullseye', 'main'),
                                  ],
    ('urepo', 'bullseye', 'imports'): [('debian', 'bullseye', 'main'),
                                      ('debian', 'bullseye', 'contrib'),
                                      ('debian', 'bullseye', 'non-free'),
                                      ('urepo', 'bullseye', 'main'),
                                  ],

    ('urepo', 'buster', 'main'): [('debian', 'buster', 'main'),
                                   ('debian', 'buster-backports', 'main'),
                                 ],
    ('urepo', 'buster', 'imports'): [('debian', 'buster', 'main'),
                                      ('debian', 'buster', 'contrib'),
                                      ('debian', 'buster', 'non-free'),
                                      ('urepo', 'buster', 'main'),
                                    ],
    ('urepo', 'buster', 'forks'): [('debian', 'buster', 'main'),
                                    ('urepo', 'buster', 'main'),
                                  ],
}
