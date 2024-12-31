import numpy as np
import torch
from torchvision import transforms
from torchvision.transforms import Normalize
from scipy.interpolate import NearestNDInterpolator
from .parameters import LI_min_as, LS_max_as, mean_as, std_as


class firescardataset():
    def __init__(self, before_files, after_files, mult=1, transform=None):
        self.transform = transform
        # list of image files (pre and post fire), and labels
        # label vector edge coordinates
        self.imgfiles = after_files
        self.imgprefiles = before_files
               
        if mult > 1:
            self.imgfiles = np.array([*self.imgfiles] * mult)
            self.imgprefiles = np.array([*self.imgprefiles] * mult)
            
    def __len__(self):
        return len(self.imgfiles)
    
    def __getitem__(self, idx):
        """
        Accesses to the input's data and adapts the format to a matrix of the concatenated bands' values of both the pre and post-fire images. 
        Afterwards, also padding and preprocessing are applied to the data. 
        Returns a dictionary of the image's data and the values.

        idx (int): index of the input to access to. They are given iteratively for a given search.
        
        """
        def preprocessing(imgdata):
            """
            Preprocesses each image's data, removing outliers and values out of range. 

            imgdata (object: ndarray): Matrix composed of the 16 concatenated matrices of a pre and post-fire image' bands.

            """
            #the limits are determined according to the Dataset's 
            
            for k in range(1, 17):
                if (imgdata[k-1] > LS_max_as[k-1]).any():
                    if imgdata[k-1].mean() < LS_max_as[k-1]:
                        imgdata[k-1][imgdata[k-1] > LS_max_as[k-1]] = imgdata[k-1].mean()
                    else:
                        imgdata[k-1][imgdata[k-1] > LS_max_as[k-1]] = mean_as[k-1]
                elif (imgdata[k-1] < LI_min_as[k-1]).any():
                    if imgdata[k-1].mean() > LI_min_as[k-1]:
                        imgdata[k-1][imgdata[k-1] < LI_min_as[k-1]] = imgdata[k-1].mean()
                    else: 
                        imgdata[k-1][imgdata[k-1] < LI_min_as[k-1]] = mean_as[k-1]
            return imgdata
        
        imgdata1 = self.imgfiles[idx]
        imgdatapre = self.imgprefiles[idx]
        new_array = np.concatenate((imgdata1, imgdatapre), axis=0)  
        
        if not np.isfinite(new_array).all():  # Replace NaNs for the neighbors mean values
            mask = np.isfinite(new_array)
            interp = NearestNDInterpolator(np.transpose(mask.nonzero()), new_array[mask])
            new_array = interp(*np.indices(new_array.shape))
        
        new_array = preprocessing(new_array)
        x = imgdata1.shape[1]
        y = imgdata1.shape[2]
        size = 128

        # Calculate padding if necessary, making sure padding values are not negative
        pad_x = max(int((size - x) / 2), 0)
        pad_y = max(int((size - y) / 2), 0)

        # Apply padding to ensure the image is of size (size x size)
        if (x < size or y < size):
            new_array = np.pad(new_array, ((0, 0), (pad_x, pad_x), (pad_y, pad_y)), "constant")

        sample = {
            'idx': idx,
            'img': new_array,
            'imgfile': self.imgfiles[idx]
        }

        if self.transform:
            sample = self.transform(sample)

        return sample


class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""
    def __call__(self, sample):
        out = {
            'idx': sample['idx'],
            'img': torch.from_numpy(sample['img'].copy()),
            'imgfile': sample['imgfile']
        }
        return out
    

class Normalize(object):
    """Normalize pixel values to the range [0, 1] measured using minmax-scaling"""    
    def __init__(self):
        self.channel_means = np.array(mean_as)
        self.channel_std = np.array(std_as)

    def __call__(self, sample):
        sample['img'] = (sample['img'] - self.channel_means.reshape(
            sample['img'].shape[0], 1, 1)) / self.channel_std.reshape(
            sample['img'].shape[0], 1, 1)
        return sample 


def create_datasetAS(*args, apply_transforms=True, **kwargs):
    """
    Create a dataset; uses same input parameters as PowerPlantDataset.
    apply_transforms: if `True`, apply available transformation. Returns the data set
    """
    if apply_transforms:
        data_transforms = transforms.Compose([
            Normalize(),
            ToTensor()
        ])
    else:
        data_transforms = None

    data = firescardataset(*args, **kwargs, transform=data_transforms)
    
    return data
