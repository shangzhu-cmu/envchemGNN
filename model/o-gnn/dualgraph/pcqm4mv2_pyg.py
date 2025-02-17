import os
import os.path as osp
import shutil
from ogb.utils import smiles2graph
from ogb.utils.torch_util import replace_numpy_with_torchtensor
from ogb.utils.url import decide_download, download_url, extract_zip
import pandas as pd
import numpy as np
from tqdm import tqdm
import torch

from torch_geometric.data import InMemoryDataset
from torch_geometric.data import Data

class PygPCQM4Mv2Dataset(InMemoryDataset):
    def __init__(self, root = 'dataset', file_name='pcqm4m-v2', smiles2graph = smiles2graph, transform=None, pre_transform = None):
        '''
            Pytorch Geometric PCQM4Mv2 dataset object
                - root (str): the dataset folder will be located at root/pcqm4m_kddcup2021
                - smiles2graph (callable): A callable function that converts a SMILES string into a graph object
                    * The default smiles2graph requires rdkit to be installed
        '''

        self.original_root = root
        self.smiles2graph = smiles2graph
        self.folder = osp.join(root, file_name)
        self.version = 1
        
        # # Old url hosted at Stanford
        # # md5sum: 65b742bafca5670be4497499db7d361b
        # # self.url = f'http://ogb-data.stanford.edu/data/lsc/pcqm4m-v2.zip'
        # # New url hosted by DGL team at AWS--much faster to download
        # self.url = 'https://dgl-data.s3-accelerate.amazonaws.com/dataset/OGB-LSC/pcqm4m-v2.zip'

        # # check version and update if necessary
        # if osp.isdir(self.folder) and (not osp.exists(osp.join(self.folder, f'RELEASE_v{self.version}.txt'))):
        #     print('PCQM4Mv2 dataset has been updated.')
        #     if input('Will you update the dataset now? (y/N)\n').lower() == 'y':
        #         shutil.rmtree(self.folder)

        super(PygPCQM4Mv2Dataset, self).__init__(self.folder, transform, pre_transform)

        print(self.processed_paths[0])
        self.data, self.slices = torch.load(self.processed_paths[0])

    @property
    def raw_file_names(self):
        return 'data.csv'

    @property
    def processed_file_names(self):
        return 'geometric_data_processed.pt'

    # def download(self):
    #     if decide_download(self.url):
    #         path = download_url(self.url, self.original_root)
    #         extract_zip(path, self.original_root)
    #         os.unlink(path)
    #     else:
    #         print('Stop download.')
    #         exit(-1)

    def process(self):
        data_df = pd.read_csv(osp.join(self.raw_dir, 'data.csv'))
        smiles_list = data_df['smiles']
        homolumogap_list = data_df['label']

        print('Converting SMILES strings into graphs...')
        data_list = []
        for i in tqdm(range(len(smiles_list))):
            data = Data()

            smiles = smiles_list[i]
            homolumogap = homolumogap_list[i]
            graph = self.smiles2graph(smiles)
            
            assert(len(graph['edge_feat']) == graph['edge_index'].shape[1])
            assert(len(graph['node_feat']) == graph['num_nodes'])

            data.__num_nodes__ = int(graph['num_nodes'])
            data.edge_index = torch.from_numpy(graph['edge_index']).to(torch.int64)
            data.edge_attr = torch.from_numpy(graph['edge_feat']).to(torch.int64)
            data.x = torch.from_numpy(graph['node_feat']).to(torch.int64)
            data.y = torch.Tensor([homolumogap]).to(torch.int64)

            data_list.append(data)

        if self.pre_transform is not None:
            data_list = [self.pre_transform(data) for data in data_list]

        data, slices = self.collate(data_list)

        print('Saving...')
        torch.save((data, slices), self.processed_paths[0])

if __name__ == '__main__':
    PygPCQM4Mv2Dataset().process()
    dataset = PygPCQM4Mv2Dataset()
    print(dataset)
    print(dataset.data.edge_index)
    print(dataset.data.edge_index.shape)
    print(dataset.data.x.shape)
    print(dataset[100])
    print(dataset[100].y)