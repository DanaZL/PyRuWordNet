#!/home/ubuntu/anaconda2/bin/python
# -*- coding: utf-8

import dash_cytoscape
import dash
import dash_core_components as dcc
import dash_html_components as html

from ruwordnet import RuWordNet


def create_graph(root_synset_ids):

    child_ids = set()
    for idx, root_id in enumerate(root_synset_ids):
        child_ids.update(ruwordnet.get_child_ids(root_id))

    print("Agregate vertex for leaf nodes...")
    #agregate vertex for leaf nodes
    vert_labels = {}
    vert_leaf_labels = {}
    for synset_id in root_synset_ids + list(child_ids):
        synset = ruwordnet.id2synset[synset_id]
        if synset.hypernym_for or len(synset.hyponym_for) != 1:
            vert_labels[synset_id] = synset.ruthes_name
        else:
            for hypernym_id in synset.hyponym_for:
                if hypernym_id + '_leaf' not in vert_leaf_labels:
                    vert_leaf_labels[hypernym_id + '_leaf'] = synset.ruthes_name
                else:
                    vert_leaf_labels[hypernym_id + '_leaf'] += ",\n" + synset.ruthes_name


    print("Collect relations...")
    relations = []
    for synset_id in vert_labels:
        synset = ruwordnet.id2synset[synset_id]
        for hyponem_id in synset.hypernym_for:
            if hyponem_id in vert_labels:
                relations.append((synset.id, hyponem_id))

    for synset_id in vert_leaf_labels:
        relations.append((synset_id.split("_")[0], synset_id))

    vertex_synsets = [
        {
            'data': {'id': synset_id, 'label': vert_labels[synset_id]}, 
            'position': {'x': 0, 'y': 0},
            'style': {
                'text-rotation': '270deg',
                'text-valign': 'bottom',
                'text-halign': 'left',
                'text-wrap': 'wrap'
                # 'text-rotation':'autorotate'
            },

        }
        for synset_id in vert_labels
    ]

    vertex_synsets += [
        {
            'data': {'id': synset_id, 'label': vert_leaf_labels[synset_id]}, 
            'position': {'x': 0, 'y': 0},
            'style': {
                # 'text-rotation': '270deg',
                'text-valign': 'bottom',
                'text-halign': 'left',
                'text-wrap': 'wrap'
                # 'text-rotation':'autorotate'
            },

        }
        for synset_id in vert_leaf_labels
    ]

    vertex_relations = [
        {'data': {'source': source, 'target': target}}
        for source, target in relations
    ]

    # elements = nodes + edges
    # print(vertex_synsets[:20])
    # print(vertex_relations[:20])
    print len(vertex_synsets), len(vertex_relations)
    elements = vertex_synsets[:] + vertex_relations[:]
    return elements

ruwordnet = RuWordNet("../rwn-xml-2017-05-13/")

root_synsets = ruwordnet.get_roots()
root_synset_ids = [synset.id for synset in root_synsets]
root_synset_names = [synset.ruthes_name for synset in root_synsets]

print("Loading connect components...")
all_connect_component_roots = ruwordnet.get_connect_components()
print("Finish, connect components: {}".format(len(all_connect_component_roots)))

component_root_synset_ids = [list(connect_component_roots) 
                                for connect_component_roots in all_connect_component_roots]
# print(component_root_synset_ids[0][:10], len(component_root_synset_ids))
component_root_synset_names = [",".join([ruwordnet.id2synset[synset_id].ruthes_name 
    for synset_id in component_roots[:5]]) + "..." for component_roots in component_root_synset_ids]


dropdown_component_list = [{'label':x, 'value':i} for i, x in enumerate(component_root_synset_names)]
dropdown_root_synset_list = [{'label':root_synset.ruthes_name, 'value':root_synset.id} \
    for root_synset in root_synsets]

ruwordnet_stat = "Статистика тезауруса: Всего синсетов: {}, ".format(len(ruwordnet.id2synset))
ruwordnet_stat += "Всего компонент связности: {}".format(len(all_connect_component_roots))

cur_value_root = ''
cur_value_component = ''

elements = []

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H3(
                u'RuWordNet visualization',
                style = {
                    'position': 'relative',
                    'top': '0px',
                    'left': '40px',
                    'right': '20px',
                    'font-family': 'Dosis',
                    'display': 'inline',
                    'font-size': '4.0rem',
                    'color': '#4D637F'
                },
                className = 'five columns'
            )]
        ),
        html.Div([
            html.P(
                ruwordnet_stat,
                className = 'five columns'
            )
        ], 
            style = {
                'position': 'relative',
                'top': '0px',
                'left': '40px',
                'right': '20px',
                'font-family': 'Dosis',
                'display': 'inline',
                'font-size': '2.0rem',
                'color': '#4D637F'
            }
        )
    ],
        className = 'row'
    ),
    html.Div([
            html.P(u"Выберите компоненту связности для визуализации:"),
            html.Div(
                dcc.Dropdown(
                    id='dropdown_component',
                    options=dropdown_component_list,
                    placeholder="Select a componemt",
                    value = ""
                ),
                style = {
                    'font-size': '1.5rem',
                },
                className = 'six columns'
            ),
            html.P(u"Выберите корневой синсет для визуализации:"),
            html.Div(
                dcc.Dropdown(
                    id='dropdown_root_synset',
                    options=dropdown_root_synset_list,
                    placeholder="Select a root Synsets",
                    value = ""
                ),
                style = {
                    'font-size': '1.5rem',
                },
                className = 'six columns'
            ),
            html.Div(
                id = 'output-vis',
                style = {
                    'top': '1px',
                    'font-size': '1.5rem',
                    'font-weight': '5'
                },
                className = 'six columns'
            )
        ],
        style = {
            # 'position': 'relative',
            'font-size': '1.8rem',
            'top': '20px',
            'down': '5px',
            'left': '40px',
            'right': '120px'
        },
        className = 'row'
    ),
    html.Div([
        html.Div(
            children=["",""],
            id = 'selector_values',
            style = {
               'display': 'none'
            }
        ),
        dash_cytoscape.Cytoscape(
            id='cytoscape-layout',
            elements=elements,
            style={'width': '90%','height': '800px'},
            layout={
                'name': 'breadthfirst',
                'directed':'true',
                # 'spacingFactor': 2,
                "font": {
                  "size": 15,
                },
                'zoom':'minZoom',
                'roots': ', '.join(["#" + x for x in root_synset_ids])
            },
        )
    ],
        className = 'row'
    )
])

@app.callback(
    [dash.dependencies.Output('cytoscape-layout', 'elements'),
    dash.dependencies.Output('selector_values', 'children')],
    [dash.dependencies.Input('dropdown_root_synset', 'value'),
     dash.dependencies.Input('dropdown_component', 'value')],
     state = [dash.dependencies.State('selector_values', 'children')])
def update_output(value_root, value_component, selector_values):
    cur_value_root, cur_value_component = selector_values
    elements = None
    if value_component == '' and value_root == '':
        return [], selector_values

    if value_root != cur_value_root:
        if value_root != '':
            elements = create_graph([value_root])
            if len(elements) > 200:
                elements = []
        cur_value_root = value_root

    if value_component != cur_value_component:
        if value_component != '':
            elements = create_graph(component_root_synset_ids[int(value_component)])
            if len(elements) > 200:
                elements = []
            
        cur_value_component = value_component

    if elements is not None:
        return elements, [cur_value_root, cur_value_component]


@app.callback(
    dash.dependencies.Output('output-vis', 'children'),
    [dash.dependencies.Input('dropdown_root_synset', 'value'),
     dash.dependencies.Input('dropdown_component', 'value')],
     state = [dash.dependencies.State('selector_values', 'children')])
def update_output(value_root, value_component, selector_values):
    cur_value_root, cur_value_component = selector_values
    if value_component == '' and value_root == '':
        return ''

    if value_root != cur_value_root:
        if value_root != '':
            elements = create_graph([value_root])
            if len(elements) > 200:
                text = u"Иерархия корневого синсета слишком большая для визуализации"
                return text

    if value_component != cur_value_component:
        
        if value_component != '':
            elements = create_graph(component_root_synset_ids[int(value_component)])
            if len(elements) > 12:
                text = u"Эта компонента связности слишком большая для визуализации.\
                 Её корневые синсеты (Всего {}):\n".format(len(component_root_synset_ids[int(value_component)]))
                text += u",".join([ruwordnet.id2synset[synset_id].ruthes_name 
                            for synset_id in component_root_synset_ids[int(value_component)]])
                return text
    return ''

if __name__ == '__main__':
    app.run_server(debug=True)