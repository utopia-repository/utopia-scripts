# A list of known repositories.
REPOS = {
    'debian': 'http://deb.debian.org/debian',
    'urepo': 'https://deb.utopia-repository.org'
}

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

    ('urepo', 'bookworm', 'main'): [('debian', 'bookworm', 'main')],
    ('urepo', 'bookworm', 'meta'): [('debian', 'bookworm', 'main'),
                                    ('urepo', 'bookworm', 'main'),
                                  ],
    ('urepo', 'bookworm', 'imports'): [('debian', 'bookworm', 'main'),
                                      ('debian', 'bookworm', 'contrib'),
                                      ('debian', 'bookworm', 'non-free'),
                                      ('urepo', 'bookworm', 'main'),
                                  ],
}
