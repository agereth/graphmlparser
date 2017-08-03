import xmltodict

def label_cleaner(label: str) -> str:
    """
    cleans label of signal from extra data
    Removes extra spases, comments(symbols after \), conditions (symbols after [), actions (symbols after /)
    Examples:
        >>> label_cleaner("NEUTRALIZE")
        "NEUTRALIZE"
        >>> label_cleaner("BUTTON_PRESSED // some action")
        "BUTTON_PRESSED"
        >>> label_cleaner("\\COMMENT")
        ""
        >>> label_cleaner("SIGNAL [flag == 1]")
        "SIGNAL"
        :param label:
        :return: string
        """
    dividers = "[/\\"
    for divider in dividers:
        label = label.split(divider)[0]
    return label.strip()


def get_label_text(label: dict, edge_labels: list):
    """
    gets label_text from special data dictionary "label"
    edges may have two types: GenericEdge and  QuadCurveEdge so label text is either
     label['y:GenericEdge']['y:EdgeLabel']['#text']
    or
     label[''y:QuadCurveEdge']['y:EdgeLabel']['#text']
    after getting a label we delete extra label data with label_cleaner function
    and store label_lext to edge_labels list (labels are to be unique)

    :param label, edge_labels:
    """

    edgetypes = ['y:GenericEdge', 'y:QuadCurveEdge']
    for etype in edgetypes:
        if (etype in label.keys()) and ('y:EdgeLabel' in label[etype].keys()) and (
                    '#text' in label[etype]['y:EdgeLabel'].keys()):
            label_text = label[etype]['y:EdgeLabel']['#text']
            text = label_cleaner(label_text)
            if text and edge_labels.count(text) == 0:
                edge_labels.append(text)

def flatten(mixed_data: list, key: str) -> list:
    """
    function separates data nodes using key
    Example: 
        >>>flatten([{'data':[info1, info2]}], 'data')
        [info1, info2]
    :param data: list of nodes ith data
    :param key: dictionary key to get list with data 
    :return: list with data items
    """
    flattened_data = []
    for node in mixed_data:
        node_data = node[key]
        if isinstance(node_data, dict):
            flattened_data.append(node_data)
        else:
            for e in node_data:
                flattened_data.append(e)
    return flattened_data


def is_node_empty(node: dict) -> bool:
    """
    function checks  node has text label (checks all necessary dictionary keys are present)
    returns True if any key is absent and False otherwise
    :param node: dictionary structure
    :return: bool
    """
    if not ('y:GenericNode') in node.keys():
        return True
    if not ('y:NodeLabel') in node['y:GenericNode'].keys():
        return True
    return False


def is_node_group(node: dict) -> bool:
    """
    checks using node dictionary keys if this node is group
    :param node: dict
    :return: bool
    """
    return 'y:ProxyAutoBoundsNode' in node.keys()

def clean_node_label(label: str) -> str:
    """
    :param label:
    :return:
    """
    events = label.split('/')
    events = [s.split('\n')[-1].strip() for s in events]
    return events[:-1]

def get_simple_nodes_data(flattened_nodes, all_labels):
    simple_nodes = list(filter(lambda x: not is_node_empty(x) and not is_node_group(x), flattened_nodes))
    simple_nodes = [x['y:GenericNode'] for x in simple_nodes]
    simple_nodes = flatten(simple_nodes, 'y:NodeLabel')
    simple_nodes = list(filter(lambda x: '#text' in x.keys(), simple_nodes))
    node_labels = [x['#text'] for x in simple_nodes]
    for label in node_labels:
        for e in clean_node_label(label):
            if (not e == 'entry' and not e == 'exit' and not e in all_labels):
                all_labels.append(e)

def get_group_node_text(group_node, node_label):
    node_labels.append(group_node['data']['y:ProxyAutoBoundsNode']['y:Realizers'][ 'y:GroupNode']['#text'])

def get_enum(text_labels: list) -> str:
    """
    gets enum structure for c language from list of sygnals
    adds _SYG to each sygnal and adds special text in the end and beginning of the text)
    Example:
        >>> get_enum(["EVENT1", "EVENT2"])
        "enum PlayerSignals {
            TICK_SEC_SIG = Q_USER_SIG,

            EVENT1_SIG,
            EVENT2_SIG

        LAST_USER_SIG
        };"
    :param text_labels:
    :return: string
    """
    enum_labels = [label + '_SIG' for label in text_labels]
    enum = ',\n'.join(enum_labels)
    enum = 'enum PlayerSignals {\nTICK_SEC_SIG = Q_USER_SIG,\n\n' + enum + ',\n\nLAST_USER_SIG\n};'
    return enum

def get_keystrokes(text_labels: list) -> str:
    """
    gets enum structure for c language from list of sygnals
    Example:
        >>> get_keystrokes(["EVENT1", "EVENT2"])
        "const KeyStroke KeyStrokes[]= {
        {EVENT1_SIG, "EVENT1", ""},
        {EVENT2_SIG, "EVENT2", ""},

        { TERMINATE_SIG, "TERMINATE", 0x1B }
        };"
    :param text_labels:
    :return: string
    """
    new_labels = ['{' + label + '_SIG, ' +'\"' + label + '\", \'\'}'  for label in text_labels]
    keystrokes = ',\n'.join(new_labels)
    return 'const KeyStroke KeyStrokes[]={\n' + keystrokes + '\n\n{ TERMINATE_SIG, "TERMINATE", 0x1B }\n\n}'


def main():
    filename = 'lightsaber.graphml'
    data = xmltodict.parse(open(filename).read())

    edges = data['graphml']['graph']['edge']
    all_labels = []
    for edge in edges:
        labels = edge['data']
        if isinstance(labels, dict):
            labels = [labels]
        for label in labels:
            get_label_text(label, all_labels)

    nodes = data['graphml']['graph']['node']
    flattened_nodes = flatten(nodes, 'data')
    sub = []
    for node in nodes:
        if 'graph' in node.keys():
            sub.append(node['graph'])
    sub = flatten(sub, 'node')
    sub = flatten(sub, 'data')
    flattened_nodes.extend(sub)

    get_simple_nodes_data(flattened_nodes, all_labels)

    group_nodes = list(filter(lambda x: is_node_group(x), flattened_nodes))
    group_node_labels = []
    group_nodes = [x['y:ProxyAutoBoundsNode']['y:Realizers'] for x in group_nodes]
    group_nodes = flatten(group_nodes, 'y:GroupNode')
    group_nodes = flatten(group_nodes, 'y:NodeLabel')
    group_nodes = list(filter(lambda x: '#text' in x.keys(), group_nodes))
    node_labels = [x['#text'] for x in group_nodes]
    for label in node_labels:
        for e in clean_node_label(label):
            if (not e == 'entry' and not e == 'exit' and not e in all_labels):
                all_labels.append(e)






    res = open(filename + '_res.txt', "w")
    res.write(get_enum(all_labels))
    res.write('\n\n')
    res.write(get_keystrokes(all_labels))
    res.write('\n\n')
    res.close()


if __name__ == '__main__':
    main()
