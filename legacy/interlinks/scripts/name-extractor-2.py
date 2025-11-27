import collections

props = ["gndo:forename", "gndo:surname"]
cooc = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
tmp = collections.defaultdict(set)


def extract_literal(line):
    start = line.index('"')
    end = line.index('"', start + 1)
    return line[start + 1:end]


def bad_name(name):
    return " " in name or "." in name or "-" in name


def extract_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        count = 0
        for p in props:
            tmp[p] = set()
        for line in f:
            if "gndo:gndIdentifier" in line:
                for p in props:
                    if len(tmp[p]) > 1:
                        for name in tmp[p]:
                            cooc[p][name].update(tmp[p])
                    tmp[p] = set()
                # id = line.split(' ')[2].strip('"')
                count += 1
                if count % 10000 == 0:
                    print('.', end='')
                if count % 1000000 == 0:
                    print(' {}'.format(count))
            for p in props:
                if p in line:
                    name = extract_literal(line)
                    if not bad_name(name):
                        tmp[p].add(name)


def get_coocs(prop, name):
    return collections.Counter(cooc[prop][name]).most_common()


import json


def save_cooc(filename):
    with open(filename, 'w', encoding='utf-8') as fp:
        json.dump(cooc, fp)


def load_cooc(filename):
    with open(filename, 'r', encoding='utf-8') as fp:
        return json.load(fp)


# extract_from_file('authorities-name_lds.ttl')
# extract_from_file('authorities-person_lds.ttl')
# save_cooc('cooc.json')
cooc = load_cooc('cooc.json')
len(cooc['gndo:forename'])

get_coocs('gndo:surname', 'Abeles')
