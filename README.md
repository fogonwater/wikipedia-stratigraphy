# Wikipedia Stratigraphy

Some code for extracting and visualising [Wikipedia article histories](http://fogonwater.com/blog/2015/11/wikipedia-edit-history-stratigraphy/). This code is a bit of a mess and would benefit from a serious tidy. Fails on articles with a very large number of edits. I also suspect there is something funky about the way the most recent edit displays.

Written in Python 2.x. Untested with Python 3.x.

## Installation

1. Create and activate a virtual environment (e.g. `virtualenv venv` then `source venv/bin/activate`)
2. Install modules with the requirements file: `pip install -r requirements.txt`

## Basic usage

Test the script is working by running `wikistrat.py` in a directory that contains folders named `wikixml` and `img`.

`$ python wikistrat.py`

The script should download the Tirau article's history to `wikixml` and create three visualisations in the `img` directory.

Set up a Wikipedia stratigraphy object.

`wikistrat = WikiStrat()`

WikiStrat retrieves xml histories from Wikipedia and stores them in a data directory. Images are written to an image directory. By default these are expected to be `wikixml` and `img` respectively. You can configure them.

`wikistrat = WikiStrat(data_dir='special_data_folder', img_dir='nice_images_folder)`

Extract and visualise Wikipedia article histories with the parse method.
`wikistrat.parse('Tirau')`

By default the parse method will only download an article's history if there is no local copy. To force a refresh, set `refresh=True`.
`wikistrat.parse('Tirau', refresh=True)`
