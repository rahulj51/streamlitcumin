

upload_box_style = {
    'width': '100%',
    'height': '60px',
    'lineHeight': '60px',
    'borderWidth': '1px',
    'borderStyle': 'dashed',
    'borderRadius': '5px',
    'textAlign': 'center',
    'margin': '10px'
}

def fill_color(pct):
    color = "#afa"
    if 50 <= pct <= 75:
        color = "#fea"
    elif pct < 50:
        color = "#faa"
    return color


def progress_bar(pct):
    max_width = 150
    width = round((pct / 100) * max_width) + 1  #plus 1 to show a small bar for zero pct
    bar = f'<div><svg width="{max_width}" height="15"><rect width="{width}" height="100" style="fill:{fill_color(pct)};stroke-width:1;stroke:rgb(0,0,0)" /></svg> {pct}%</div>'
    return bar

