# A list of known repositories.
REPOS = {'debian': 'http://deb.debian.org/debian',
         'urepo': 'https://deb.utopia-repository.org',}

# A list of architectures to test.
TARGET_ARCHS = ['amd64']

# This defines the repos that we want to test. Keys are test target pairs (repo, distribution, suite),
# and values are a list of (repo, distribution, suite) pairs that each test target depends on.
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
}
