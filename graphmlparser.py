import xmltodict

def flatten(mixed_data: list, key: str) -> list:
    """
    function separates data nodes using key
    Example:
        >>>flatten([{'data':[info1, info2]}], 'data')
        [info1, info2]
    :param data: list of nodes with data
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

def is_edge_correct(edge: dict, type: str) -> bool:
    """
    checks if edge contains all necessary data to be a correct edge with label
    :param edge: dict with edge data
    :param type: type of edge:generic or curve
    :return: true if edge is generic false otherwise
    """
    if not type in edge.keys():
        return False;
    if not 'y:EdgeLabel' in edge[type].keys():
        return False;
    return True;

def edge_label_cleaner(label: str) -> str:
    """
    cleans edge_label of signal from extra data
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

def get_edge_labels(edges: list) -> list:
    """
    gets edge labels from edges in edges list and cleans them from extra data
    :param edges: list with data
    :return: list of cleaned labels
    """
    flattened_edges = flatten(edges, 'data')
    cleaned_labels = []
    for type in ['y:GenericEdge', 'y:QuadCurveEdge']:
        edges = list(filter(lambda x: is_edge_correct(x, type), flattened_edges))
        edges = [edge[type] for edge in edges]
        edges = flatten(edges, 'y:EdgeLabel')
        edges = list(filter(lambda x: "#text" in x.keys(), edges))
        edge_labels = [edge["#text"] for edge in edges]
        cleaned_labels.extend(list(map(edge_label_cleaner, edge_labels)))
    return cleaned_labels

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

def get_sub_nodes(nodes: list) -> list:
    """
    gets all sub-nodes from groupnodes (detects in node has subnodes (has "graph' key) and gets all nodes in node['graph']
    item, flattened by node and by data fields
    :param nodes: list of nodes
    :return: list of nodes
    """

    sub = [node['graph'] for node in nodes if 'graph' in node.keys()]
    sub = flatten(sub, 'node')
    sub = flatten(sub, 'data')
    return sub

def clean_node_label(label: str) -> [str]:
    """
    this function gets event labels from node label (using information that / always follows event label)
    exludind entry/ and exit/ events. Strings are separated with \n symbol
    Examples:
        >>>clean_node_label("entry/\nsomesunction()\nEVENT1/\nsomefunction2()\nEVENT2/\nsomefunction3()\nexit/\nsome_function4()")
        ["entry","EVENT1", "EVENT2", "exit"]
    :param label: label with events and functions data
    :return: list of events
    """
    events = label.split('/')
    events = [s.split('\n')[-1].strip() for s in events]
    return events[:-1]

def get_simple_nodes_data(flattened_nodes: dict) -> [str]:
    """
    gets labels from list of nodes and cleans them from extra data using clean_node_label function
    :param flattened_nodes: list of nodes with data
    :return: list of labels with event sygnals
    """
    simple_nodes = list(filter(lambda x: not is_node_empty(x) and not is_node_group(x), flattened_nodes))
    simple_nodes = [x['y:GenericNode'] for x in simple_nodes]
    simple_nodes = flatten(simple_nodes, 'y:NodeLabel')
    simple_nodes = list(filter(lambda x: '#text' in x.keys(), simple_nodes))
    node_labels = [x['#text'] for x in simple_nodes]
    node_labels = list(map(clean_node_label, node_labels))
    return [e for node in node_labels for e in node]

def get_group_nodes_data(flattened_nodes: list) -> [str]:
    """
    gets labels from list of group nodes (gets them from list of all nodes)
    and cleans them from extra data using clean_node_label function
    :param flattened_nodes: list of all nodes
    :return: list of cleaned labels
    """

    group_nodes = list(filter(lambda x: is_node_group(x), flattened_nodes))
    group_nodes = [x['y:ProxyAutoBoundsNode']['y:Realizers'] for x in group_nodes]
    group_nodes = flatten(group_nodes, 'y:GroupNode')
    group_nodes = flatten(group_nodes, 'y:NodeLabel')
    group_nodes = list(filter(lambda x: '#text' in x.keys(), group_nodes))
    node_labels = [x['#text'] for x in group_nodes]
    node_labels = list(map(clean_node_label, node_labels))
    return [e for node in node_labels for e in node]

def clean_list(labels: list) -> [str]:
    """
    cleans labels list of empty labels, non-unique labels, "enrty" and "exit" labels
    :param labels: list of uncleaned labels
    :return: list of cleaned labels
    """
    res = []
    for label in labels:
        if label and not label in res and label != 'entry' and label != 'exit':
            res.append(label)
    return res

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
    filename = 'dogan.graphml'
    data = xmltodict.parse(open(filename).read())

    all_labels = get_edge_labels(data['graphml']['graph']['edge'])

    nodes = data['graphml']['graph']['node']
    flattened_nodes = flatten(nodes, 'data')
    flattened_nodes.extend(get_sub_nodes(nodes))
    all_labels.extend(get_simple_nodes_data(flattened_nodes))
    all_labels.extend(get_group_nodes_data(flattened_nodes))
    all_labels = clean_list(all_labels)
    enum = get_enum(all_labels)
    keystrokes = get_keystrokes(all_labels)


    res = open(filename + '_res.txt', "w")
    res.write(enum)
    res.write('\n\n')
    res.write(keystrokes)
    res.write('\n\n')
    res.close()


if __name__ == '__main__':
    main()
