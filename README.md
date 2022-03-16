# kifparser
Copyright (c) 2022 Quantori.

SUO-KIF ontology parser is a free open-source parser for [SUO-KIF language](https://github.com/ontologyportal/sigmakee/blob/master/suo-kif.pdf) for ontologies like [SUMO](https://www.ontologyportal.org) in Python based on and integrated with [AIIRE Natural Language Understanding Core parser](http://aiire.org).

This parser is tested with SUMO ontology files and can be used for
any other SUO-KIF files.

# KEY FEATURES
- Parse SUO-KIF ontology files
- Extract concepts with attributes from KIF formulas
- Apply implications, perform inference
- Export the extracted ontology to AIIRE and other formats

# Build instructions

To install, do:

    pip install https://github.com/quantori/kifparser

Please read [DEVNOTES.md](DEVNOTES.md) for details.

# Usage

- Command-line:

        kifparser < file.kif

- Python:

        from kifparser import KIFParser

# License

Kifparser is released under Apache License, Version 2.0
