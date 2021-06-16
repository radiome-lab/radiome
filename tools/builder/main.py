import os
import re
from datetime import datetime
from pathlib import Path

import click


def initialize_template(src: Path, dst: Path, params: dict):
    if not src.exists():
        raise FileNotFoundError(f"Can't find the source directory {src}.")
    dst.mkdir(parents=True, exist_ok=True)
    for sub in src.iterdir():
        if sub.name in ['__pycache__', 'env', 'venv', 'dist', 'sdist', 'wheels', '.DS_Store'] or \
            re.match(r'.*.egg-info', sub.name):
            continue
        sub_dst = dst / sub.name.format(**params)
        if sub.is_dir():
            initialize_template(sub, sub_dst, params)
        else:
            if sub_dst.exists():
                sub_dst.unlink()
            with sub.open('r') as fr:
                with sub_dst.open('w') as fw:
                    fw.write(fr.read().format(**params))
                    # sub_dst.write_text(sub.read_text().format(**params))


@click.argument('destination', type=click.Path(), default='.')
def init(destination: Path):
    click.echo(f'Creating workflow at {destination}')
    package_name = click.prompt("Package name")
    package_description = click.prompt("A short description of your package")
    author = click.prompt("Author name")
    email = click.prompt("Author email")

    Path(destination).mkdir(parents=True, exist_ok=True)
    params = {
        'package_name': package_name,
        'package_description': package_description,
        'author': author,
        'email': email,
        'created_time': datetime.now().strftime('%Y-%m-%d')
    }
    initialize_template(Path(os.path.join(os.path.dirname(__file__), 'template')),
                        Path(destination),
                        params)


@click.group()
def main():
    pass


main.command()(init)

if __name__ == '__main__':
    main()
