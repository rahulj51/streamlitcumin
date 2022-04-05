

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

def progress_bar(pct):
    max_width = 50
    width = round((pct / 100) * 50)
    bar = f'<div><svg width="{max_width}" height="10"><rect width="{width}" height="100" style="fill:rgb(0,0,255);stroke-width:3;stroke:rgb(0,0,0)" /></svg> {pct}</div>'
    return bar

