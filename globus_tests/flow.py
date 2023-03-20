import os

from gladier import GladierBaseClient, generate_flow_definition

# from cc_process import Process_CC
from pprint import pprint
from cc_process import CC_Process

# UUID's for globus endpoints
I1_GB = 'e0af0a40-b193-11ed-ae06-bfc1a406350a'
C1_GB = 'a8eff728-b179-11ed-ae06-bfc1a406350a'

# funcx endpoints
I1_FX = 'fdfaf897-4e44-4a70-9b18-e6017c8fb51a'

# Dataset
data = 'CC-MAIN-2022-40'
download_dir =  "./common_crawl_download"

# Test vars
cc_file_path = "/Users/eller/Projects/Action_Provider_V2/common_crawl_download/CC-MAIN-2022-40/CC-MAIN-2022-40-wet.paths.gz"
prefix_list = "CC-MAIN-2022-40"

@generate_flow_definition
class TestClient(GladierBaseClient):
    gladier_tools = [
        CC_Process
    ]
    

if __name__ == '__main__':
    flow_input = {
        'input': {
          'cc_file_path': cc_file_path,
          'prefix_list': prefix_list
        }
    }

    cc_process = TestClient()
    pprint(cc_process.flow_definition)

    flow = cc_process.run_flow(flow_input=flow_input)

    # Track the progress
    action_id = flow['action_id']
    cc_process.progress(action_id)
    pprint(cc_process.get_status(action_id))

