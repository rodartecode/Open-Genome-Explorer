from py4web import action, __version__, redirect, URL


@action("index")
@action.uses("index.html")
def index():
    redirect(URL('OpenGenomeExplorer'))
    return dict(version=__version__)
