import codecs
import os
import re as regexp
from fnmatch import fnmatch
from functools import partial
from optparse import OptionParser
from os.path import isfile, isdir, dirname
from pathlib import Path
from shutil import copyfile

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateError
from lenses import lens


def match_files(root, mask):
    return filter(lambda s: fnmatch(s, mask) and isfile(s), map(str, Path(root).rglob("*")))


def render_template(env, name, vars):
    tmp = env.get_template(name)
    return tmp.render(vars)


def get_env_match_re():
    return regexp.compile(r"(\$(\b[A-Z0-9_]+\b))")


def get_env_val(n):
    if n not in os.environ:
        print(f"[WARNING] Not defined environment variable `{n}` found")

    return os.getenv(n)


def sub_env(x, s):
    return x.sub(lambda m: get_env_val(m.group(2)), s)


derefer_var = partial(sub_env, get_env_match_re())


def make_when_lens(key):
    return lens[1].Get(key, None).Recur(tuple).Iso(
        lambda i: len(set(map(derefer_var, i))) == 1, dict
    ).collect()


def make_filter_lens():
    return lens.Items(
    ).Prism(
        partial(
            lambda l_any, l_all, pred, i: i if pred(l_any(i), l_all(i)) else None,
            *(make_when_lens(key) for key in ("when any", "when all")),
            lambda any_l, all_l: (any_l and any(any_l)) or (all_l and all(all_l)) or not (any_l or all_l)
        ),
        dict, ignore_none=True
    )


def make_env_lens():
    return (make_filter_lens() & lens.Iso(
        partial(
            lambda k_src, k_dst, k_env, l_env, it: (k_src(it[1]), k_dst(it[1]), l_env(k_env(it[1]))),
            *(lens[key].get() for key in ("src", "dst")),
            lens.Get("env", {}).get(),
            lens.Recur(str).modify(derefer_var)
        ),
        dict
    )).collect()


def mkdir(path):
    return os.makedirs(path, exist_ok=True)


if __name__ == '__main__':
    cli = OptionParser()
    cli.add_option("-s", "--source", action="store", dest="source", help="Valid path to template folder")
    cli.add_option("-d", "--destination", action="store", dest="destination", help="Path to destination folder")
    cli.add_option("-t", "--template", action="store", default="template.yml", dest="template",
                   help="Filename of yml scenario in template folder")


    def help_out():
        cli.print_help()
        exit(1)


    opts, _ = cli.parse_args()

    source_path = opts.source
    destination_path = opts.destination

    if not (source_path and isdir(source_path)):
        help_out()

    template_path = os.path.join(source_path, opts.template)

    if not (template_path and isfile(template_path)):
        help_out()

    render = partial(render_template, Environment(loader=FileSystemLoader(source_path)))
    renderer = make_env_lens()

    try:
        with codecs.open(template_path, encoding="utf-8") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)

        for src, dst, vars in renderer(data):
            for f_in in match_files(source_path, "*" + src):
                p_out = os.path.join(destination_path, dst)
                mkdir(dirname(p_out))

                f_out = os.path.join(p_out, f_in.replace(dirname(src) + os.path.sep, "")) if isdir(p_out) else p_out
                mkdir(dirname(f_out))

                if vars:
                    with codecs.open(f_out, "w", encoding="utf-8") as f:
                        print(render(f_in, vars), file=f)
                else:
                    copyfile(f_in, f_out)
    except KeyError as e:
        print(f"[ERROR] Mandatory key not found: {e}")
    except TemplateError as e:
        print(f"[ERROR] Template error: {e}")
    except Exception as e:
        print(f"[RUNTIME ERROR] ({type(e)}): {e}")
