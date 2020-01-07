# J2 Renderer

Bulk template renderer based on Jinja2.

## Launch params

```
  -h, --help            show this help message and exit
  -s SOURCE, --source=SOURCE
                        Valid path to template folder
  -d DESTINATION, --destination=DESTINATION
                        Path to destination folder
  -t TEMPLATE, --template=TEMPLATE
                        Filename of yml scenario in template folder
```

## Template file format

```yaml
css:
  # Catch files in templates/css folder matches by mask `*`
  src: templates/css/*
  dst: css/
  # This will work if any of environment variables is equal
  when all:
    $MODE: html
    $STYLE: bootstrap

js:
  src: templates/js/*
  dst: js/
  # This will work if all of environment variables is equal
  when any:
    $MODE: html
    $STYLE: bootstrap

index:
  src: templates/index.html
  # Destination file name can contain environment variable reference
  dst: $INDEX_OUT_NAME.html
  env:
    # Values to pass into Jinja2 template 
    title: "Index page"
    sections: ["home", "about", "sitemap"]
```
