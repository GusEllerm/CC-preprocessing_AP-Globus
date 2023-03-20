from gladier import GladierBaseTool

# custom transfer tool which takes output of previous tool as source path of file for transfer
class CC_Process(GladierBaseTool):
    

    """
    DEFINITION
    """
    
    flow_definition = {
        'Comment': 'TODO',
        'StartAt': 'CC_Process',
        'States': {
            'CC_Process': {
                'Comment': 'TODO',
                'Type': 'Action',
                'ActionUrl': 'http://localhost:5000/cc',
                'Parameters': {
                    'cc_file_path.$': '$.input.cc_file_path',
                    'prefix_list.$': '$.input.prefix_list',
                },
                'ResultPath': '$.CC_Process',
                'WaitTime': 600,
                'End': True,
                'ActionScope': 'https://auth.globus.org/scopes/27c72d0c-9a46-4a5d-a6a5-bd2cd35bc574/action_all'
            },
        }
    }

    funcx_functions = []
    
    flow_input = {}

    required_input = [
        'cc_file_path',
        'prefix_list',
    ]