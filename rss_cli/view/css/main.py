from rss_cli.utils.default_config import Colors


SCREEN_STYLE = f"""
    Screen {{
        background: {Colors.BACKGROUND}
    }}

    ArticlesGrid {{
        height: 150w;
        width: 100%;
        grid-size: 3;
    }}
    
    ArticleCard {{
        border: round {Colors.BORDER_DIM} 25%;
        padding: 1;
        height: 150w;
        width: 100%;
        content-align: center middle;
    }}

    ArticleCard:focus {{
        border-title-background: {Colors.BORDER_DIM} 75%;
        border-title-color: {Colors.BACKGROUND};
        border: round white 75%;
    }}

    QuitScreen {{
        align: center middle;
    }}

    #dialog {{
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }}

    #question {{
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }}

    Button {{
        width: 100%;
    }}
"""
