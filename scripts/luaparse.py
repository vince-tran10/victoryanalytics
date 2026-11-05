"""Data-only parser for Lua table literals (no code execution)."""
import json, re, sys
TOK = re.compile(r'''\s+|--\[\[.*?\]\]|--[^\n]*|(?P<str>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|(?P<num>-?\d+(?:\.\d+)?)|(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<p>[{}\[\]=,;])''', re.S)


def tokens(s):
    pos = 0
    out = []
    while pos < len(s):
        m = TOK.match(s, pos)
        if not m:
            raise ValueError(f'bad char at {pos}: {s[pos:pos+40]!r}')
        pos = m.end()
        if m.group('str') is not None:
            v = m.group('str')[1:-1]
            v = re.sub(r'\\(.)', lambda x: {'n': '\n', 't': '\t'}.get(x.group(1), x.group(1)), v)
            out.append(('s', v))
        elif m.group('num') is not None:
            n = m.group('num')
            out.append(('v', float(n) if '.' in n else int(n)))
        elif m.group('name') is not None:
            n = m.group('name')
            if n in ('true', 'false', 'nil'):
                out.append(('v', {'true': True, 'false': False, 'nil': None}[n]))
            else:
                out.append(('n', n))
        elif m.group('p') is not None:
            out.append(('p', m.group('p')))
    return out


class P:
    def __init__(s, t):
        s.t = t
        s.i = 0

    def peek(s, k=0):
        return s.t[s.i + k] if s.i + k < len(s.t) else (None, None)

    def take(s):
        x = s.t[s.i]
        s.i += 1
        return x

    def expect(s, v):
        x = s.take()
        if x[1] != v:
            raise ValueError(f'expected {v} got {x} at {s.i}')

    def value(s):
        k, v = s.peek()
        if (k, v) == ('p', '{'):
            return s.table()
        s.take()
        if k in ('s', 'v'):
            return v
        raise ValueError(f'unexpected {k, v} at {s.i}')

    def table(s):
        s.expect('{')
        d = {}
        arr = []
        while True:
            k, v = s.peek()
            if (k, v) == ('p', '}'):
                s.take()
                break
            if (k, v) == ('p', '['):
                s.take()
                key = s.value()
                s.expect(']')
                s.expect('=')
                d[key] = s.value()
            elif k == 'n' and s.peek(1) == ('p', '='):
                s.take()
                s.take()
                d[v] = s.value()
            else:
                arr.append(s.value())
            if s.peek() in (('p', ','), ('p', ';')):
                s.take()
        if d and arr:
            for i, a in enumerate(arr, 1):
                d[i] = a
            return {str(k): v for k, v in d.items()}
        if arr:
            return arr
        return {str(k): v for k, v in d.items()}


def parse_module(src):
    t = tokens(src)
    i = next(j for j, x in enumerate(t) if x == ('p', '{'))
    return P(t[i:]).table()


if __name__ == '__main__':
    for inp, outp in zip(sys.argv[1::2], sys.argv[2::2]):
        d = parse_module(open(inp, encoding='utf-8').read())
        json.dump(d, open(outp, 'w'), ensure_ascii=False)
        print(inp, len(d))
