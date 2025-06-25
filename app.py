import base64
import os
import zipfile
import mimetypes
import re
import numpy as np
import dash
from io import BytesIO, StringIO
from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.dependencies import ALL
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.io as pio

pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_width = 1200
pio.kaleido.scope.default_height = 800
pio.kaleido.scope.default_scale = 2

DEFAULTS = {
    "xmin": -30,
    "xmax": 30,
    "ymin": -8,
    "ymax": 2,
    "legend_y": 0.26,
}

DEMO_FILE = "CeCoAl4.zip"

app = Dash(__name__)

def subscript_numbers(text):
    sub_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return re.sub(r'(\d+)', lambda m: m.group(0).translate(sub_map), text)

app.layout = html.Div([
    html.H1("COHP & COOP Plotter", style={
        "fontSize": "32px", "fontWeight": "bold", "fontFamily": "DejaVu Sans, Arial, sans-serif",
        "textAlign": "center", "marginBottom": "20px", "color": "#333"
    }),

    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload ZIP file with COHPCAR and/or COOPCAR.lobster', style={
            "backgroundColor": "#007BFF", "color": "white", "padding": "12px 20px",
            "border": "none", "borderRadius": "5px", "cursor": "pointer",
            "fontSize": "16px", "fontWeight": "bold", "fontFamily": "DejaVu Sans, Arial, sans-serif",
            "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
        }),
        multiple=False
    ),

    html.Div([
        html.Button("Reset axes", id="reset-axes", n_clicks=0, style={
            "backgroundColor": "#FF5733", "color": "white", "padding": "10px 20px",
            "border": "none", "borderRadius": "5px", "cursor": "pointer",
            "fontSize": "16px", "fontWeight": "bold", "fontFamily": "DejaVu Sans, Arial, sans-serif",
            "marginRight": "10px", "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
        }),
        html.Button("Demo file", id="demo-file", n_clicks=0, style={
            "backgroundColor": "#28a745", "color": "white", "padding": "10px 20px",
            "border": "none", "borderRadius": "5px", "cursor": "pointer",
            "fontSize": "16px", "fontWeight": "bold", "fontFamily": "DejaVu Sans, Arial, sans-serif",
            "marginRight": "10px", "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
        }),
        html.Button("Save COHP plot", id="save-plot", n_clicks=0, style={
            "backgroundColor": "#007BFF", "color": "white", "padding": "10px 20px",
            "border": "none", "borderRadius": "5px", "cursor": "pointer",
            "fontSize": "16px", "fontWeight": "bold", "fontFamily": "DejaVu Sans, Arial, sans-serif",
            "marginRight": "10px",
            "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
        }),
        html.Button("Save COOP plot", id="save-coop-plot", n_clicks=0, style={
            "backgroundColor": "#007BFF", "color": "white", "padding": "10px 20px",
            "border": "none", "borderRadius": "5px", "cursor": "pointer",
            "fontSize": "16px", "fontWeight": "bold", "fontFamily": "DejaVu Sans, Arial, sans-serif",
            "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
        }),
    ], style={"marginTop": "15px"}),

    html.Div([
        html.Div([
            html.Div(id='cohp-warning'),
            dcc.Graph(id='cohp-plot', style={
                "height": "950px",
                "width": "575px",
                "backgroundColor": "#fff",
                "borderRadius": "10px",
                "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.08)"
            }),
        ]), 
        html.Div([
            html.Div(id='coop-warning'),
            dcc.Graph(id='coop-plot', style={
                "height": "950px",
                "width": "575px",
                "backgroundColor": "#fff",
                "borderRadius": "10px",
                "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.08)"
            }),
            html.Div(id='coop-xlimits-display', style={"marginTop": "8px", "fontSize": "16px", "color": "#333"}),
        ], style={"flex": "5", "marginRight": "30px", "display": "flex", "flexDirection": "column", "alignItems": "flex-start"}),

        html.Div([
            # COHP adjustments
            html.H3("COHP graph adjustments", style={
                "fontFamily": "DejaVu Sans, Arial, sans-serif", "color": "#333",
                "marginBottom": "10px", "textDecoration": "underline", "fontSize": "20px"
            }),
            html.Div([
                html.Label("X-axis limits:", style={"fontWeight": "bold", "marginBottom": "5px"}),
                dcc.Input(id='xmin-cohp', type='number', value=None, style={
                    "marginRight": "10px", "padding": "8px", "borderRadius": "5px", "border": "1px solid #ccc",
                    "width": "40px"
                }),
                dcc.Input(id='xmax-cohp', type='number', value=None, style={
                    "padding": "8px", "borderRadius": "5px", "border": "1px solid #ccc",
                    "width": "40px"
                }),
            ], style={"marginBottom": "15px"}),

            html.Div([
                html.Label("Y-axis limits:", style={"fontWeight": "bold", "marginBottom": "5px"}),
                dcc.Input(id='ymin-cohp', type='number', value=DEFAULTS["ymin"], style={
                    "marginRight": "10px", "padding": "8px", "borderRadius": "5px", "border": "1px solid #ccc",
                    "width": "40px"
                }),
                dcc.Input(id='ymax-cohp', type='number', value=DEFAULTS["ymax"], style={
                    "padding": "8px", "borderRadius": "5px", "border": "1px solid #ccc",
                    "width": "40px"
                }),
            ], style={"marginBottom": "15px"}),

            html.Div([
                dcc.Checklist(
                    id='show-titles-cohp',
                    options=[
                        {'label': 'Plot title', 'value': 'plot_title'},
                        {'label': 'X axis title', 'value': 'x_title'},
                        {'label': 'Y axis title', 'value': 'y_title'},
                    ],
                    value=['plot_title', 'x_title', 'y_title'],
                    inline=True,
                    style={"fontFamily": "DejaVu Sans, Arial, sans-serif", "marginLeft": "10px"}
                ),
            ], style={"marginBottom": "15px", "marginLeft": "auto"}),

            html.Div([
                dcc.Checklist(
                    id='show-axis-scale-cohp',
                    options=[
                        {'label': 'Show X axis scale', 'value': 'x_scale'},
                        {'label': 'Show Y axis scale', 'value': 'y_scale'},
                    ],
                    value=['x_scale', 'y_scale'],
                    inline=True,
                    style={"fontFamily": "DejaVu Sans, Arial, sans-serif", "marginLeft": "10px"}
                ),
            ], style={"marginBottom": "15px", "marginLeft": "auto"}),

            html.Hr(),
            # COOP adjustments
            html.H3("COOP graph adjustments", style={
                "fontFamily": "DejaVu Sans, Arial, sans-serif", "color": "#333",
                "marginBottom": "10px", "textDecoration": "underline", "fontSize": "20px"
            }),
            html.Div([
                html.Label("X-axis limits:", style={"fontWeight": "bold", "marginBottom": "5px"}),
                dcc.Input(id='xmin-coop', type='number', value=None, style={
                    "marginRight": "10px", "padding": "8px", "borderRadius": "5px", "border": "1px solid #ccc",
                    "width": "40px"
                }),
                dcc.Input(id='xmax-coop', type='number', value=None, style={
                    "padding": "8px", "borderRadius": "5px", "border": "1px solid #ccc",
                    "width": "40px"
                }),
            ], style={"marginBottom": "15px"}),

            html.Div([
                html.Label("Y-axis limits:", style={"fontWeight": "bold", "marginBottom": "5px"}),
                dcc.Input(id='ymin-coop', type='number', value=DEFAULTS["ymin"], style={
                    "marginRight": "10px", "padding": "8px", "borderRadius": "5px", "border": "1px solid #ccc",
                    "width": "40px"
                }),
                dcc.Input(id='ymax-coop', type='number', value=DEFAULTS["ymax"], style={
                    "padding": "8px", "borderRadius": "5px", "border": "1px solid #ccc",
                    "width": "40px"
                }),
            ], style={"marginBottom": "15px"}),

            html.Div([
                dcc.Checklist(
                    id='show-titles-coop',
                    options=[
                        {'label': 'Plot title', 'value': 'plot_title'},
                        {'label': 'X axis title', 'value': 'x_title'},
                        {'label': 'Y axis title', 'value': 'y_title'},
                    ],
                    value=['plot_title', 'x_title', 'y_title'],
                    inline=True,
                    style={"fontFamily": "DejaVu Sans, Arial, sans-serif", "marginLeft": "10px"}
                ),
            ], style={"marginBottom": "15px", "marginLeft": "auto"}),

            html.Div([
                dcc.Checklist(
                    id='show-axis-scale-coop',
                    options=[
                        {'label': 'Show X axis scale', 'value': 'x_scale'},
                        {'label': 'Show Y axis scale', 'value': 'y_scale'},
                    ],
                    value=['x_scale', 'y_scale'],
                    inline=True,
                    style={"fontFamily": "DejaVu Sans, Arial, sans-serif", "marginLeft": "10px"}
                ),
            ], style={"marginBottom": "15px", "marginLeft": "auto"}),

        ], style={
            "flex": "3",
            "minWidth": "250px",
            "maxWidth": "300px",
            "height": "550px",
            "backgroundColor": "#fff",
            "borderRadius": "10px",
            "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",
            "padding": "20px",
            "fontFamily": "DejaVu Sans, Arial, sans-serif",
            "fontSize": "16px",
            "color": "#333",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "flex-start",
            "marginRight": "30px"
        }),

        html.Div(
            id='element-pair-table',
            style={
                "flex": "3",
                "minWidth": "300px",
                "maxWidth": "400px",
                "height": "550px",
                "backgroundColor": "#fff",
                "borderRadius": "10px",
                "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",
                "padding": "20px",
                "fontFamily": "DejaVu Sans, Arial, sans-serif",
                "fontSize": "16px",
                "color": "#333",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "flex-start"
            }
        ),
    ], style={
        "display": "flex",
        "flexDirection": "row",
        "justifyContent": "center",
        "alignItems": "stretch",
        "gap": "0px",
        "marginTop": "30px",
        "marginBottom": "0px",
        "width": "100%"
    }),

    html.Div(id="save-confirmation", style={
        "marginTop": "10px", "color": "#4CAF50", "fontFamily": "DejaVu Sans, Arial, sans-serif"
    }),

    dcc.Store(id='uploaded-contents'),
    dcc.Store(id='element-pair-defaults'),
    html.Div(id='folder-name', style={"display": "none"}),
    dcc.Download(id='download-plot'),
    dcc.Download(id='download-coop-plot'),
    html.Div(id="save-coop-confirmation", style={
        "marginTop": "10px", "color": "#4CAF50", "fontFamily": "DejaVu Sans, Arial, sans-serif"
    }),
])

# --- Demo file callback ---
@app.callback(
    Output('upload-data', 'contents', allow_duplicate=True),
    Input('demo-file', 'n_clicks'),
    prevent_initial_call=True
)
def load_demo_file(n_clicks):
    if n_clicks:
        demo_path = os.path.join(os.path.dirname(__file__), DEMO_FILE)
        if not os.path.exists(demo_path):
            return dash.no_update
        with open(demo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        mime_type = mimetypes.guess_type(demo_path)[0] or "application/zip"
        contents = f"data:{mime_type};base64,{encoded}"
        return contents
    return dash.no_update

# --- Upload handler: parse ZIP, extract COHPCAR, parse element pairs ---
@app.callback(
    Output('uploaded-contents', 'data'),
    Output('folder-name', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def handle_upload(contents, filename):
    if not contents:
        raise PreventUpdate
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    with zipfile.ZipFile(BytesIO(decoded), 'r') as zip_ref:
        files = zip_ref.namelist()
        cohp_file = next((f for f in files if "COHPCAR" in f), None)
        coop_file = next((f for f in files if "COOPCAR" in f), None)
        cohp_data = zip_ref.read(cohp_file).decode('utf-8') if cohp_file else None
        coop_data = zip_ref.read(coop_file).decode('utf-8') if coop_file else None

        # Use DEMO_FILE name if filename is None or "COHP"
        if not filename or filename == "COHP":
            folder_name = os.path.splitext(os.path.basename(DEMO_FILE))[0]
        else:
            folder_name = os.path.splitext(os.path.basename(filename))[0]

        # Parse unique element pairs (from whichever file exists)
        unique_pairs = set()
        for file_data in [cohp_data, coop_data]:
            if file_data:
                for line in file_data.splitlines():
                    if line.startswith("No."):
                        match = re.search(r":([A-Za-z]+)\d+->([A-Za-z]+)\d+\(", line)
                        if match:
                            atom1, atom2 = match.groups()
                            pair = (atom1, atom2) if atom1 == atom2 else tuple(sorted([atom1, atom2]))
                            unique_pairs.add(pair)
        return {
            "cohp_data": cohp_data,
            "coop_data": coop_data,
            "unique_pairs": sorted(list(unique_pairs)),
            "folder_name": folder_name,
        }, folder_name

# --- Build element pair color table ---
@app.callback(
    Output('element-pair-table', 'children'),
    Input('uploaded-contents', 'data'),
    prevent_initial_call=True
)
def build_element_pair_table(data):
    if not data or "unique_pairs" not in data:
        return ""
    color_options = [
        {'label': html.Span([
            html.Div(style={
                "backgroundColor": c, "width": "15px", "height": "15px",
                "display": "inline-block", "marginRight": "8px"
            }), c
        ], style={"display": "flex", "alignItems": "center"}), "value": c}
        for c in ['blue', 'red', 'green', 'gray', 'black', 'orange', 'purple', 'pink', 'silver']
    ]
    table_header = html.Tr([
        html.Th("Element pair", style={"textAlign": "center", "padding": "10px", "fontWeight": "bold"}),
        html.Th("Color", style={"textAlign": "center", "padding": "10px", "fontWeight": "bold"}),
        html.Th("Show", style={"textAlign": "center", "padding": "10px", "fontWeight": "bold"}),
        html.Th("ICOHP/ICOOP", style={"textAlign": "center", "padding": "10px", "fontWeight": "bold"}),
    ], style={"backgroundColor": "#f2f2f2"})
    table_rows = []
    color_cycle = ['red', 'green', 'blue', 'orange']
    for i, pair in enumerate(data["unique_pairs"]):
        pair_str = f"{pair[0]}-{pair[1]}"
        default_color = color_cycle[i % len(color_cycle)]
        table_rows.append(html.Tr([
            html.Td(pair_str, style={"textAlign": "center", "padding": "10px"}),
            html.Td(
                dcc.Dropdown(
                    id={'type': 'color-dropdown', 'index': pair_str},
                    options=color_options,
                    value=default_color,
                    clearable=False,
                    style={"width": "100px"}
                ),
                style={"textAlign": "center", "padding": "10px"}
            ),
            html.Td(
                dcc.Checklist(
                    id={'type': 'toggle-pair', 'index': pair_str},
                    options=[{'label': '', 'value': 'show'}],
                    value=['show'],
                    inline=True
                ),
                style={"textAlign": "center", "padding": "10px"}
            ),
            html.Td(
                dcc.Checklist(
                    id={'type': 'toggle-icohp', 'index': pair_str},
                    options=[{'label': '', 'value': 'icohp'}],
                    value=[],  # Not shown by default
                    inline=True
                ),
                style={"textAlign": "center", "padding": "10px"}
            ),
        ], style={"borderBottom": "1px solid #ddd"}))
    table = html.Table([table_header] + table_rows, style={
        "width": "100%", "borderCollapse": "collapse", "marginTop": "20px"
    })
    return table

def get_dynamic_xrange(energy, y_min, y_max, traces):
    # traces: list of np.arrays, each is a pCOHP or pCOOP sum
    mask = (energy >= y_min) & (energy <= y_max)
    max_abs = 0
    for arr in traces:
        if arr is not None and arr.shape == energy.shape:
            arr_in_window = arr[mask]
            if arr_in_window.size > 0:
                max_abs = max(max_abs, np.max(np.abs(arr_in_window)))
    if max_abs == 0:
        max_abs = 1  # fallback to avoid zero width
    buffer = max_abs * 0.05
    return -max_abs - buffer, max_abs + buffer

# --- Plot callback ---
@app.callback(
    Output('cohp-plot', 'figure'),
    Input('uploaded-contents', 'data'),
    Input({'type': 'color-dropdown', 'index': ALL}, 'value'),
    Input({'type': 'toggle-pair', 'index': ALL}, 'value'),
    Input({'type': 'toggle-icohp', 'index': ALL}, 'value'),
    Input('xmin-cohp', 'value'), Input('xmax-cohp', 'value'),
    Input('ymin-cohp', 'value'), Input('ymax-cohp', 'value'),
    Input('show-titles-cohp', 'value'),
    Input('show-axis-scale-cohp', 'value'),
    prevent_initial_call=True
)
def update_plot(data, colors, toggles, icohp_toggles, xmin, xmax, ymin, ymax, show_titles, show_axis_scale):    
    if not data or "cohp_data" not in data:
        return go.Figure()
    pairs = [f"{p[0]}-{p[1]}" for p in data["unique_pairs"]]
    color_map = {pair: colors[i] if i < len(colors) else 'blue' for i, pair in enumerate(pairs)}
    show_map = {pair: ('show' in toggles[i] if i < len(toggles) else True) for i, pair in enumerate(pairs)}
    icohp_map = {pair: ('icohp' in icohp_toggles[i] if i < len(icohp_toggles) else False) for i, pair in enumerate(pairs)}
    lines = data["cohp_data"].splitlines()
    header_idx = next(i for i, line in enumerate(lines) if line.strip().startswith("No.1"))
    data_start_idx = header_idx + 1
    numeric_lines = []
    for line in lines[data_start_idx:]:
        tokens = line.strip().split()
        if tokens and re.match(r'^-?\d+\.?\d*([eE][-+]?\d+)?$', tokens[0]):
            numeric_lines.append(line)
    data_arr = np.genfromtxt(StringIO("\n".join(numeric_lines)))
    energy = data_arr[:, 0]
    interaction_to_pair = []
    for line in lines:
        if line.startswith("No."):
            match = re.search(r":([A-Za-z]+)\d+->([A-Za-z]+)\d+\(", line)
            if match:
                atom1, atom2 = match.groups()
                pair = (atom1, atom2) if atom1 == atom2 else tuple(sorted([atom1, atom2]))
                interaction_to_pair.append(pair)
    # --- Dynamic x-range calculation ---
    y_min, y_max = -8, 2
    pcohp_traces = []
    for i, pair in enumerate(data["unique_pairs"]):
        pair_str = f"{pair[0]}-{pair[1]}"
        if not show_map.get(pair_str, True):
            continue
        indices = [j for j, p in enumerate(interaction_to_pair) if p == tuple(pair)]
        pcohp_sum = np.zeros_like(energy)
        for idx in indices:
            pcohp_col = 3 + 2 * idx
            pcohp_sum += -data_arr[:, pcohp_col]
        pcohp_traces.append(pcohp_sum)
    auto_xmin, auto_xmax = get_dynamic_xrange(energy, y_min, y_max, pcohp_traces)
    xmax_val = xmax if xmax is not None else auto_xmax
    xmin_val = xmin if xmin is not None else auto_xmin
    ymax_val = ymax if ymax is not None else y_max
    ymin_val = ymin if ymin is not None else y_min
    fig = go.Figure()
    for i, pair in enumerate(data["unique_pairs"]):
        pair_str = f"{pair[0]}-{pair[1]}"
        if not show_map.get(pair_str, True):
            continue
        indices = [j for j, p in enumerate(interaction_to_pair) if p == tuple(pair)]
        pcohp_sum = np.zeros_like(energy)
        icohp_sum = np.zeros_like(energy)
        for idx in indices:
            pcohp_col = 3 + 2 * idx
            icohp_col = 4 + 2 * idx
            pcohp_sum += -data_arr[:, pcohp_col]
            icohp_sum += -data_arr[:, icohp_col]
        # pCOHP line
        fig.add_trace(go.Scatter(
            x=pcohp_sum, y=energy,
            mode='lines',
            name=pair_str,
            line=dict(width=4, color=color_map.get(pair_str, 'blue'))
        ))
        # ICOHP dashed line if toggled
        if icohp_map.get(pair_str, False):
            fig.add_trace(go.Scatter(
                x=icohp_sum, y=energy,
                mode='lines',
                name=f"ICOHP",
                line=dict(width=4, color=color_map.get(pair_str, 'blue'), dash='dash'),
                showlegend=True
            ))
    fig.update_layout(
        xaxis=dict(title="-COHP", range=[xmin_val, xmax_val], tickfont=dict(size=22)),
        yaxis=dict(title="Energy (eV)", range=[ymin_val, ymax_val], tickfont=dict(size=22)),
        legend=dict(font=dict(size=18)),
        margin=dict(l=80, r=80, t=80, b=80),
        height=1000,
        title=dict(text=f"{data.get('folder_name', '')} COHP", font=dict(size=22)),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=3)
    fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=3)

    # --- Layout and annotation for the graph ---
    # Set defaults if not provided
    #show_titles = ['plot_title', 'x_title', 'y_title']
    #show_axis_scale = ['x_scale', 'y_scale']
    legend_y = data.get('legend_y', 0.26) if isinstance(data, dict) else 0.26
    folder_name_unicode = data.get('folder_name', '') if isinstance(data, dict) else ''

    # --- Title formatting ---
    folder_name = data.get('folder_name', '') if isinstance(data, dict) else ''
    folder_name_unicode = subscript_numbers(folder_name)
    zip_title = f"{folder_name_unicode} COHP"
    plot_title = zip_title if 'plot_title' in show_titles else None

    # --- Axis titles ---
    x_title = '-COHP' if 'x_title' in show_titles else ''
    y_title = 'Energy (eV)' if 'y_title' in show_titles else ''

    # --- Axis scale (ticks and labels) ---
    show_x_scale = 'x_scale' in show_axis_scale
    show_y_scale = 'y_scale' in show_axis_scale

    # --- Layout ---
    fig.update_layout(
        font=dict(family="DejaVu Sans, Arial, sans-serif", size=30, color='black'),
        title=dict(
            text=plot_title,
            x=0.5,
            xanchor='center',
            y=0.99,
            font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            pad=dict(t=20)
        ) if plot_title else None,
        xaxis=dict(
            title=dict(
                text=x_title,
                font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            ),
            range=[xmin_val, xmax_val],
            showgrid=False,
            zeroline=True,
            zerolinewidth=3,
            zerolinecolor='black',
            tickfont=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            tickwidth=3,
            ticklen=10,
            ticks='outside' if show_x_scale else '',
            automargin=True,
            showticklabels=show_x_scale
        ),
        yaxis=dict(
            title=dict(
                text=y_title,
                font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            ),
            range=[ymin_val, ymax_val],
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            tickwidth=3,
            ticklen=10,
            ticks='outside' if show_y_scale else '',
            showticklabels=show_y_scale
        ),
        legend=dict(
            font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            borderwidth=0,
            orientation="v",
            x=0.01,
            y=0.01,
            xanchor='left',
            yanchor='bottom',
            itemwidth=30,
            itemsizing='constant',
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            traceorder="normal"
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=100, t=70, b=60),
        height=925,
        width=575,
    )

    # --- Fermi level annotation ---
    fig.add_annotation(
        x=xmax_val,
        y=0,
        text="<i>E</i><sub><i>F</i></sub>",
        showarrow=False,
        font=dict(size=30, family="DejaVu Sans, Arial, sans-serif", color="black"),
        xanchor="left",
        yanchor="middle",
        xshift=10,
        yshift=0,
        align="left"
    )

    # --- Optional: Add border rectangle ---
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=1, y1=1,
        xref="paper", yref="paper",
        line=dict(color="black", width=3),
        fillcolor='rgba(0,0,0,0)'
    )

    # --- Optional: Add Fermi level line ---
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=3)

    return fig

# --- Save plot callback ---
@app.callback(
    Output('download-plot', 'data'),
    Output('save-confirmation', 'children'),
    Input('save-plot', 'n_clicks'),
    State('cohp-plot', 'figure'),
    State('folder-name', 'children'),
    prevent_initial_call=True
)
def save_plot(n_clicks, figure, folder_name):
    if n_clicks:
        fig = pio.from_json(pio.to_json(figure))
        # --- Ensure white background and consistent legend for saved plot ---
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
                borderwidth=0,
                orientation="v",
                x=0.01,
                y=0.01,
                xanchor='left',
                yanchor='bottom',
                itemwidth=30,
                itemsizing='constant',
                bgcolor='rgba(0,0,0,0)',
                bordercolor='rgba(0,0,0,0)',
                traceorder="normal"
            ),
        )
        filename = f"{folder_name}_COHP_plot.png"
        def write_image_to_bytesio(output_buffer):
            fig.write_image(output_buffer, format="png", scale=4)
        return dcc.send_bytes(write_image_to_bytesio, filename), html.Span(
            f"Plot downloaded as '{filename}'!",
            style={"fontWeight": "bold", "fontSize": "18px"}
        )
    return dash.no_update, ""

@app.callback(
    Output('download-coop-plot', 'data'),
    Output('save-coop-confirmation', 'children'),
    Input('save-coop-plot', 'n_clicks'),
    State('coop-plot', 'figure'),
    State('folder-name', 'children'),
    prevent_initial_call=True
)
def save_coop_plot(n_clicks, figure, folder_name):
    if n_clicks:
        fig = pio.from_json(pio.to_json(figure))
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
                borderwidth=0,
                orientation="v",
                x=0.01,
                y=0.01,
                xanchor='left',
                yanchor='bottom',
                itemwidth=30,
                itemsizing='constant',
                bgcolor='rgba(0,0,0,0)',
                bordercolor='rgba(0,0,0,0)',
                traceorder="normal"
            ),
        )
        filename = f"{folder_name}_COOP_plot.png"
        def write_image_to_bytesio(output_buffer):
            fig.write_image(output_buffer, format="png", scale=4)
        return dcc.send_bytes(write_image_to_bytesio, filename), html.Span(
            f"Plot downloaded as '{filename}'!",
            style={"fontWeight": "bold", "fontSize": "18px"}
        )
    return dash.no_update, ""

@app.callback(
    Output('xmin-cohp', 'value', allow_duplicate=True),
    Output('xmax-cohp', 'value', allow_duplicate=True),
    Output('ymin-cohp', 'value', allow_duplicate=True),
    Output('ymax-cohp', 'value', allow_duplicate=True),
    Output('xmin-coop', 'value', allow_duplicate=True),
    Output('xmax-coop', 'value', allow_duplicate=True),
    Output('ymin-coop', 'value', allow_duplicate=True),
    Output('ymax-coop', 'value', allow_duplicate=True),
    Input('reset-axes', 'n_clicks'),
    prevent_initial_call=True
)
def reset_axes(n_clicks):
    if n_clicks:
        return (
            DEFAULTS["xmin"], DEFAULTS["xmax"], DEFAULTS["ymin"], DEFAULTS["ymax"],
            DEFAULTS["xmin"], DEFAULTS["xmax"], DEFAULTS["ymin"], DEFAULTS["ymax"]
        )
    raise PreventUpdate

# --- COOP plot callback ---
@app.callback(
    Output('coop-plot', 'figure'),
    Input('uploaded-contents', 'data'),
    Input({'type': 'color-dropdown', 'index': ALL}, 'value'),
    Input({'type': 'toggle-pair', 'index': ALL}, 'value'),
    Input({'type': 'toggle-icohp', 'index': ALL}, 'value'),
    Input('xmin-coop', 'value'), Input('xmax-coop', 'value'),
    Input('ymin-coop', 'value'), Input('ymax-coop', 'value'),
    Input('show-titles-coop', 'value'),
    Input('show-axis-scale-coop', 'value'),
    prevent_initial_call=True
)
def update_coop_plot(data, colors, toggles, icohp_toggles, xmin, xmax, ymin, ymax, show_titles, show_axis_scale):
    if not data or "coop_data" not in data or not data["coop_data"]:
        return go.Figure()
    pairs = [f"{p[0]}-{p[1]}" for p in data["unique_pairs"]]
    color_map = {pair: colors[i] if i < len(colors) else 'blue' for i, pair in enumerate(pairs)}
    show_map = {pair: ('show' in toggles[i] if i < len(toggles) else True) for i, pair in enumerate(pairs)}
    icohp_map = {pair: ('icohp' in icohp_toggles[i] if i < len(icohp_toggles) else False) for i, pair in enumerate(pairs)}
    lines = data["coop_data"].splitlines()
    header_idx = next(i for i, line in enumerate(lines) if line.strip().startswith("No.1"))
    data_start_idx = header_idx + 1
    numeric_lines = []
    for line in lines[data_start_idx:]:
        tokens = line.strip().split()
        if tokens and re.match(r'^-?\d+\.?\d*([eE][-+]?\d+)?$', tokens[0]):
            numeric_lines.append(line)
    data_arr = np.genfromtxt(StringIO("\n".join(numeric_lines)))
    energy = data_arr[:, 0]
    interaction_to_pair = []
    for line in lines:
        if line.startswith("No."):
            match = re.search(r":([A-Za-z]+)\d+->([A-Za-z]+)\d+\(", line)
            if match:
                atom1, atom2 = match.groups()
                pair = (atom1, atom2) if atom1 == atom2 else tuple(sorted([atom1, atom2]))
                interaction_to_pair.append(pair)
    # --- Dynamic x-range calculation ---
    y_min, y_max = -8, 2
    pcoop_traces = []
    for i, pair in enumerate(data["unique_pairs"]):
        pair_str = f"{pair[0]}-{pair[1]}"
        if not show_map.get(pair_str, True):
            continue
        indices = [j for j, p in enumerate(interaction_to_pair) if p == tuple(pair)]
        pcoop_sum = np.zeros_like(energy)
        for idx in indices:
            pcoop_col = 3 + 2 * idx
            pcoop_sum += data_arr[:, pcoop_col]
        pcoop_traces.append(pcoop_sum)
    auto_xmin, auto_xmax = get_dynamic_xrange(energy, y_min, y_max, pcoop_traces)
    xmax_val = xmax if xmax is not None else auto_xmax
    xmin_val = xmin if xmin is not None else auto_xmin
    ymax_val = ymax if ymax is not None else y_max
    ymin_val = ymin if ymin is not None else y_min
    fig = go.Figure()
    for i, pair in enumerate(data["unique_pairs"]):
        pair_str = f"{pair[0]}-{pair[1]}"
        if not show_map.get(pair_str, True):
            continue
        indices = [j for j, p in enumerate(interaction_to_pair) if p == tuple(pair)]
        pcoop_sum = np.zeros_like(energy)
        icoop_sum = np.zeros_like(energy)
        for idx in indices:
            pcoop_col = 3 + 2 * idx
            icoop_col = 4 + 2 * idx
            pcoop_sum += data_arr[:, pcoop_col]
            icoop_sum += data_arr[:, icoop_col]
        # pCOOP line
        fig.add_trace(go.Scatter(
            x=pcoop_sum, y=energy,
            mode='lines',
            name=pair_str,
            line=dict(width=4, color=color_map.get(pair_str, 'blue'))
        ))
        # ICOHP dashed line if toggled
        if icohp_map.get(pair_str, False):
            fig.add_trace(go.Scatter(
                x=icoop_sum, y=energy,
                mode='lines',
                name=f"ICOOP",
                line=dict(width=4, color=color_map.get(pair_str, 'blue'), dash='dash'),
                showlegend=True
            ))
    fig.update_layout(
        xaxis=dict(title="COOP", range=[xmin_val, xmax_val], tickfont=dict(size=22)),
        yaxis=dict(title="Energy (eV)", range=[ymin_val, ymax_val], tickfont=dict(size=22)),
        legend=dict(font=dict(size=18)),
        margin=dict(l=80, r=80, t=80, b=80),
        height=1000,
        title=dict(text=f"{data.get('folder_name', '')} COOP", font=dict(size=22)),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=3)
    fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=3)

    # --- Layout and annotation for the graph ---
    legend_y = data.get('legend_y', 0.26) if isinstance(data, dict) else 0.26
    folder_name_unicode = data.get('folder_name', '') if isinstance(data, dict) else ''

    # --- Title formatting ---
    folder_name = data.get('folder_name', '') if isinstance(data, dict) else ''
    folder_name_unicode = subscript_numbers(folder_name)
    zip_title = f"{folder_name_unicode} COOP"
    plot_title = zip_title if 'plot_title' in show_titles else None

    # --- Axis titles ---
    x_title = 'COOP' if 'x_title' in show_titles else ''
    y_title = 'Energy (eV)' if 'y_title' in show_titles else ''

    # --- Axis scale (ticks and labels) ---
    show_x_scale = 'x_scale' in show_axis_scale
    show_y_scale = 'y_scale' in show_axis_scale

    # --- Layout ---
    fig.update_layout(
        font=dict(family="DejaVu Sans, Arial, sans-serif", size=30, color='black'),
        title=dict(
            text=plot_title,
            x=0.5,
            xanchor='center',
            y=0.99,
            font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            pad=dict(t=20)
        ) if plot_title else None,
        xaxis=dict(
            title=dict(
                text=x_title,
                font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            ),
            range=[xmin_val, xmax_val],
            showgrid=False,
            zeroline=True,
            zerolinewidth=3,
            zerolinecolor='black',
            tickfont=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            tickwidth=3,
            ticklen=10,
            ticks='outside' if show_x_scale else '',
            automargin=True,
            showticklabels=show_x_scale
        ),
        yaxis=dict(
            title=dict(
                text=y_title,
                font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            ),
            range=[ymin_val, ymax_val],
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            tickwidth=3,
            ticklen=10,
            ticks='outside' if show_y_scale else '',
            showticklabels=show_y_scale
        ),
        legend=dict(
            font=dict(size=30, family="DejaVu Sans, Arial, sans-serif"),
            borderwidth=0,
            orientation="v",
            x=0.01,
            y=0.01,
            xanchor='left',
            yanchor='bottom',
            itemwidth=30,
            itemsizing='constant',
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            traceorder="normal"
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=100, t=70, b=60),
        height=925,
        width=575,
    )

    # --- Fermi level annotation ---
    fig.add_annotation(
        x=xmax_val,
        y=0,
        text="<i>E</i><sub><i>F</i></sub>",
        showarrow=False,
        font=dict(size=30, family="DejaVu Sans, Arial, sans-serif", color="black"),
        xanchor="left",
        yanchor="middle",
        xshift=10,
        yshift=0,
        align="left"
    )

    # --- Optional: Add border rectangle ---
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=1, y1=1,
        xref="paper", yref="paper",
        line=dict(color="black", width=3),
        fillcolor='rgba(0,0,0,0)'
    )

    # --- Optional: Add Fermi level line ---
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=3)

    return fig

@app.callback(
    Output('cohp-warning', 'children'),
    Input('uploaded-contents', 'data')
)
def cohp_warning(data):
    if not data or not data.get("cohp_data"):
        return html.Div(
            "No COHPCAR found in ZIP.",
            style={
                "fontFamily": "DejaVu Sans, Arial, sans-serif",
                "color": "red",
                "fontSize": "18px",
                "fontWeight": "bold",
                "marginBottom": "8px",
                "textAlign": "left",
                "marginLeft": "200px",
                "width": "100%",
            }
        )
    return ""

@app.callback(
    Output('coop-warning', 'children'),
    Input('uploaded-contents', 'data')
)
def coop_warning(data):
    if not data or not data.get("coop_data"):
        return html.Div(
            "No COOPCAR.lobster found in ZIP.",
            style={
                "fontFamily": "DejaVu Sans, Arial, sans-serif",
                "color": "red",
                "fontSize": "18px",
                "fontWeight": "bold",
                "marginBottom": "8px",
                "textAlign": "left",
                "marginLeft": "200px",
                "width": "100%",
            }
        )
    return ""

@app.callback(
    Output('xmin-cohp', 'value'),
    Output('xmax-cohp', 'value'),
    Output('xmin-coop', 'value'),
    Output('xmax-coop', 'value'),
    Input('uploaded-contents', 'data'),
    prevent_initial_call=True
)
def set_auto_x_limits_on_upload(data):
    if not data:
        raise PreventUpdate

    # --- COHP ---
    auto_xmin_cohp, auto_xmax_cohp = None, None
    if data.get("cohp_data"):
        lines = data["cohp_data"].splitlines()
        header_idx = next(i for i, line in enumerate(lines) if line.strip().startswith("No.1"))
        data_start_idx = header_idx + 1
        numeric_lines = []
        for line in lines[data_start_idx:]:
            tokens = line.strip().split()
            if tokens and re.match(r'^-?\d+\.?\d*([eE][-+]?\d+)?$', tokens[0]):
                numeric_lines.append(line)
        data_arr = np.genfromtxt(StringIO("\n".join(numeric_lines)))
        energy = data_arr[:, 0]
        y_min, y_max = -8, 2
        # Build pCOHP traces for all pairs
        interaction_to_pair = []
        for line in lines:
            if line.startswith("No."):
                match = re.search(r":([A-Za-z]+)\d+->([A-Za-z]+)\d+\(", line)
                if match:
                    atom1, atom2 = match.groups()
                    pair = (atom1, atom2) if atom1 == atom2 else tuple(sorted([atom1, atom2]))
                    interaction_to_pair.append(pair)
        pcohp_traces = []
        for i, pair in enumerate(data["unique_pairs"]):
            indices = [j for j, p in enumerate(interaction_to_pair) if p == tuple(pair)]
            pcohp_sum = np.zeros_like(energy)
            for idx in indices:
                pcohp_col = 3 + 2 * idx
                pcohp_sum += -data_arr[:, pcohp_col]
            pcohp_traces.append(pcohp_sum)
        from math import floor, ceil
        auto_xmin_cohp, auto_xmax_cohp = get_dynamic_xrange(energy, y_min, y_max, pcohp_traces)
        auto_xmin_cohp = int(round(auto_xmin_cohp))
        auto_xmax_cohp = int(round(auto_xmax_cohp))

    # --- COOP ---
    auto_xmin_coop, auto_xmax_coop = None, None
    if data.get("coop_data"):
        lines = data["coop_data"].splitlines()
        header_idx = next(i for i, line in enumerate(lines) if line.strip().startswith("No.1"))
        data_start_idx = header_idx + 1
        numeric_lines = []
        for line in lines[data_start_idx:]:
            tokens = line.strip().split()
            if tokens and re.match(r'^-?\d+\.?\d*([eE][-+]?\d+)?$', tokens[0]):
                numeric_lines.append(line)
        data_arr = np.genfromtxt(StringIO("\n".join(numeric_lines)))
        energy = data_arr[:, 0]
        y_min, y_max = -8, 2
        # Build pCOOP traces for all pairs
        interaction_to_pair = []
        for line in lines:
            if line.startswith("No."):
                match = re.search(r":([A-Za-z]+)\d+->([A-Za-z]+)\d+\(", line)
                if match:
                    atom1, atom2 = match.groups()
                    pair = (atom1, atom2) if atom1 == atom2 else tuple(sorted([atom1, atom2]))
                    interaction_to_pair.append(pair)
        pcoop_traces = []
        for i, pair in enumerate(data["unique_pairs"]):
            indices = [j for j, p in enumerate(interaction_to_pair) if p == tuple(pair)]
            pcoop_sum = np.zeros_like(energy)
            for idx in indices:
                pcoop_col = 3 + 2 * idx
                pcoop_sum += data_arr[:, pcoop_col]
            pcoop_traces.append(pcoop_sum)
        auto_xmin_coop, auto_xmax_coop = get_dynamic_xrange(energy, y_min, y_max, pcoop_traces)
        auto_xmin_coop = int(round(auto_xmin_coop))
        auto_xmax_coop = int(round(auto_xmax_coop))

    return auto_xmin_cohp, auto_xmax_cohp, auto_xmin_coop, auto_xmax_coop

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)