import torch.utils.data as data
import numpy as np
import torch
import pandas as pd 
import h5py
from torchvision import transforms as tf
from torchvision.transforms import functional as F
import PIL
import random
import scipy
import os
try:
    from .helper import Augmentation
except Exception: #ImportError
    from helper import Augmentation
__all__ = ['NYUv2']

class NYUv2(data.Dataset):
    def __init__(self, root='/media/scratch1/jonfrey/datasets/NYU_v2', 
                 mode='train', scenes=[], output_trafo = None, 
                 output_size=400, degrees = 10, flip_p = 0.5, jitter_bcsh=[0.3, 0.3, 0.3, 0.05], load_all=True):
        """
        Each dataloader loads the full .mat file into memory. 
        For the small dataset size this is perfect.
        Both should work when file is located on SSD!
        
        Parameters
        ----------
        root : str, path to .mat file
        mode : str, option ['train','val]
        scenes : [] if empty is is not filtered otherwise provide list of sceneType names 

            'basement', 'bathroom', 'bedroom', 'bookstore', 'cafe',
            'classroom', 'computer_lab', 'conference_room', 'dinette',
            'dining_room', 'excercise_room', 'foyer', 'furniture_store',
            'home_office', 'home_storage', 'indoor_balcony', 'kitchen',
            'laundry_room', 'living_room', 'office', 'office_kitchen',
            'playroom', 'printer_room', 'reception_room', 'student_lounge',
            'study', 'study_room'
        """
        self._output_size = output_size
        self._mode = mode
        self._load_all = load_all
        
        if self._load_all:
            self._load(root, mode)
            self._filter_scene(scenes)
        else:
            self._load_sparse(root, mode)
            self._filter_scene_sparse(scenes)
        
        self._augmenter = Augmentation(output_size,
                                       degrees,
                                       flip_p,
                                       jitter_bcsh)
        
        self._output_trafo = output_trafo
            
        # full training dataset with all objects
        self._weights = pd.read_csv(f'cfg/dataset/nyu/test_dataset_pixelwise_weights.csv').to_numpy()[:,0]
    
    @staticmethod
    def get_classes(mode):
        index = pd.read_csv(f'cfg/dataset/nyu/{mode}_indexes.csv').to_numpy()[:,0]-1 # from matlab to python
        sceneTypes = pd.read_csv('cfg/dataset/nyu/sceneTypes.csv').to_numpy()[index,0]
        return np.unique(sceneTypes, return_index=True)
            
    def __getitem__(self, index):
        if self._load_all:
            img = torch.from_numpy(self.images[index]/255) # C H W 
            label = torch.from_numpy(np.array( self.labels[index]) )[None,:,:] # C H W 
        else:
            idx = self.filtered_index[index]
            
            label = (torch.from_numpy(self.labels[index])[None,:,:]).permute(0,2,1) # C H W 
            img =  np.asarray( self._file['images'][idx], dtype=np.float32)
            
            img = torch.from_numpy(img/255).permute(0,2,1)
            
            # label = torch.from_numpy(label)[None,:,:]
        
        if self._mode == 'train':
            img, label = self._augmenter.apply(img, label)
        elif self._mode == 'val' or self._mode == 'test':
            img, label = self._augmenter.apply(img, label, only_crop=True)
        else:
            raise Exception('Invalid Dataset Mode')
        
        img_ori = img.clone()
        if self._output_trafo is not None:
            img = self._output_trafo(img)
        
        # add standard data augmentation options
        return img, label.type(torch.int64)[0,:,:]-1, img_ori
        
    def __len__(self):
        return self.length

    def _load(self, root, mode):
        
        
        index = pd.read_csv(f'cfg/dataset/nyu/{mode}_indexes.csv').to_numpy()[:,0]-1 # from matlab to python
        with h5py.File(os.path.join( root, 'nyu_depth_v2_labeled.mat'), 'r') as f:
            #self.labels = np.asarray( f['labels'], dtype=np.float32 )[index]
            #self.labels = np.moveaxis( self.labels,1,2) # NR,H,W
            self.images =  np.asarray( f['images'], dtype=np.float32)[index]
            self.images = np.moveaxis( self.images,2,3) # NR,C,H,W
            self.labels = np.load( os.path.join( root, 'labels40.npy') )
            self.labels = (np.moveaxis( self.labels,2,0)[index]).astype(np.float32)# NR,H,W
        
        
        self.names = pd.read_csv('cfg/dataset/nyu/names.csv').to_numpy()[:,0]
        self.scenes = pd.read_csv('cfg/dataset/nyu/scenes.csv').to_numpy()[index,0]
        self.sceneTypes = pd.read_csv('cfg/dataset/nyu/sceneTypes.csv').to_numpy()[index,0]
        self.length = self.images.shape[0]
        
    def _load_sparse(self, root, mode):
        index = pd.read_csv(f'cfg/dataset/nyu/{mode}_indexes.csv').to_numpy()[:,0]-1 # from matlab to python
        self._file = h5py.File(os.path.join( root,'nyu_depth_v2_labeled.mat'), 'r')
        
        self.labels = np.load( os.path.join( root, 'labels40.npy') )
        self.labels = (np.moveaxis( self.labels,2,0)[index]).astype(np.float32)
        
        self.names = pd.read_csv('cfg/dataset/nyu/names.csv').to_numpy()[:,0]
        self.scenes = pd.read_csv('cfg/dataset/nyu/scenes.csv').to_numpy()[index,0]
        self.sceneTypes = pd.read_csv('cfg/dataset/nyu/sceneTypes.csv').to_numpy()[index,0]
        self.length = self.sceneTypes.shape[0]
        self.filtered_index = index
    
    def _filter_scene(self, scenes):
        if len( scenes ) == 0:
            return
        else:
            for s in scenes:
                arr = np.where( self.sceneTypes == s)[0]
                try:
                    idx = np.concatenate( [idx, arr], axis=0)
                except:
                    idx = arr
            # by overriding the datamaps it is ensured that no indexing error happens!
            self.labels = self.labels[idx]
            self.images = self.images [idx]
            self.names = self.names[idx]
            self.scenes = self.scenes[idx]
            self.sceneTypes = self.sceneTypes[idx]
            self.length = self.images.shape[0]
    
    def _filter_scene_sparse(self, scenes):
        if len( scenes ) == 0:
            return
        else:
            for s in scenes:
                arr = np.where( self.sceneTypes == s)[0]
                try:
                    idx = np.concatenate( [idx, arr], axis=0)
                except:
                    idx = arr
            self.filtered_index = self.filtered_index[idx]
            self.names = self.names[idx]
            self.scenes = self.scenes[idx]
            self.sceneTypes = self.sceneTypes[idx]
            self.length = self.sceneTypes.shape[0]
        
    def __del__(self):
        if not self._load_all:
            try:
                self._file.close()    
            except:
                pass
                
            
if __name__ == '__main__':
    # Testing
    import imageio
    output_transform = tf.Compose([
      tf.Normalize([.485, .456, .406], [.229, .224, .225]),
    ])
    dataset = NYUv2(
        mode='train',
        scenes=['living_room', 'office'],
        output_trafo = None, 
        output_size=400, 
        degrees = 10, 
        flip_p = 0.5, 
        jitter_bcsh=[0.3, 0.3, 0.3, 0.05],
        load_all=True)
    
    img, label = dataset[0]    # C, H, W
    
    
    label = np.uint8( label.numpy() * (255/float(label.max())))[:,:]
    img = np.uint8( img.permute(1,2,0).numpy()*255 ) # H W C
    imageio.imwrite('/home/jonfrey/tmp/img.png', img)
    imageio.imwrite('/home/jonfrey/tmp/label.png', label)
    
    # dataset = NYUv2(
    #     mode='train',
    #     scenes=['living_room', 'office'],
    #     output_trafo = output_transform, 
    #     output_size=400, 
    #     degrees = 10, 
    #     flip_p = 0.5, 
    #     jitter_bcsh=[0.3, 0.3, 0.3, 0.05])
    # img, label = dataset[0]    
    
    # label = np.uint8( label.permute(2,1,0).numpy() * (255/float(label.max())))[:,:,0]
    # img = np.uint8( img.permute(2,1,0).numpy()*255 )
    # imageio.imwrite('/home/jonfrey/tmp/img_norm.png', img)
    # imageio.imwrite('/home/jonfrey/tmp/label.png', label)
    