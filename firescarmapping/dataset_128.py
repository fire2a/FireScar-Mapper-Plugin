import numpy as np
import torch

from torchvision import transforms
from .parameters import LS_max128, LI_min128, mean_128, std_128
import rasterio as rio 
from osgeo import gdal
from scipy.interpolate import NearestNDInterpolator
        


# +
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

            imgdata (object: ndarray): Matrix composed of the 16 concatenated matrices of a pre and post-fire image' bands

            """
            for k in range(1,17):
                if (imgdata[k-1]>LS_max128[k-1]).any():
                    if imgdata[k-1].mean()<LS_max128[k-1]:
                        imgdata[k-1][imgdata[k-1]>LS_max128[k-1]]=imgdata[k-1].mean()
                    else:
                        imgdata[k-1][imgdata[k-1]>LS_max128[k-1]]=mean_128[k-1]
                elif (imgdata[k-1]<LI_min128[k-1]).any():
                    if imgdata[k-1].mean()>LI_min128[k-1]:
                        imgdata[k-1][imgdata[k-1]<LI_min128[k-1]]=imgdata[k-1].mean()
                    else: 
                        imgdata[k-1][imgdata[k-1]<LI_min128[k-1]]=mean_128[k-1]
            return imgdata
        #imgfile = rio.open(self.imgfiles[idx])
        #imgpre=rio.open(self.imgprefiles[idx])
        imgdata1 =  self.imgfiles[idx]
        imgdatapre = self.imgprefiles[idx]
        imgdata=np.concatenate((imgdata1, imgdatapre), axis=0)
        imgdata[imgdata==0]=np.nan
        if (np.isfinite(imgdata)==False).any():                               #Replace nan for the neighbours mean values
            mask=np.where(np.isfinite(imgdata))
            interp=NearestNDInterpolator(np.transpose(mask), imgdata[mask])
            imgdata=interp(*np.indices(imgdata.shape))
        """
        ds = gdal.Open(imgdata)
        myarray = np.array(ds.GetRasterBand(1).ReadAsArray())

        x=imgdata1.shape[1]
        y=imgdata1.shape[2]
        
    #FireScar padding to 128 in case is not that size
        x,y=myarray.shape
                                                                            #only to equalize to 128x128 images or it could be to image size 
        #ulx_i, lry_i, lrx_i, uly_i=imgfile.bounds
        ulx_i, lry_i, lrx_i, uly_i=rio.open(imgdata1).bounds
        ulx, xres, xskew, uly, yskew, yres  = ds.GetGeoTransform()
        lrx = ulx + (ds.RasterXSize * xres)
        lry = uly + (ds.RasterYSize * yres)
        left=round((ulx-ulx_i)/xres)    #np.pad(a, up, down, left, right)
        right=round((lrx_i-lrx)/xres)
        up=round((uly-uly_i)/yres)
        down=round((lry_i-lry)/yres)
        myarray=np.pad(myarray,((up, down),(left,right)),"constant")
        """
        imgdata=preprocessing(imgdata)                               #preprocessing to the data when there are values off range (i.e outliers)

        sample = {'idx': idx,
            'img': imgdata,
            'imgfile': self.imgfiles[idx]}
        if self.transform:
            sample = self.transform(sample)
        return sample
    
class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""
    def __call__(self, sample):
        """
        :param sample: sample to be converted to Tensor
        :return: converted Tensor sample
        """
        out = {'idx': sample['idx'],
        'img': torch.from_numpy(sample['img'].copy()),
        'imgfile': sample['imgfile']}

        return out
class Randomize(object):
    """Randomize image orientation including rotations by integer multiples of
    90 deg, (horizontal) mirroring, and (vertical) flipping."""

    def __call__(self, sample):
        """
        :param sample: sample to be randomized
        :return: randomized sample
        """
        imgdata = sample['img']
        idx=sample["idx"]
        # mirror horizontally
        mirror = np.random.randint(0, 2)
        if mirror:
            imgdata = np.flip(imgdata, 2)
            fptdata = np.flip(fptdata, 1)
        # flip vertically
        flip = np.random.randint(0, 2)
        if flip:
            imgdata = np.flip(imgdata, 1)
            fptdata = np.flip(fptdata, 0)
        # rotate by [0,1,2,3]*90 deg
        rot = np.random.randint(0, 4)
        if rot:
            imgdata = np.rot90(imgdata, rot, axes=(1,2))
            fptdata = np.rot90(fptdata, rot, axes=(0,1))

        return {'idx': sample['idx'],
                'img': imgdata.copy(),
                'imgfile': sample['imgfile']}

class Normalize(object):
    """Normalize pixel values to the range [0, 1] measured using minmax-scaling"""
    def __init__(self):
        #the limits are determined according to the Dataset's nature
        self.channel_means=np.array(mean_128)
        self.channel_std=np.array(std_128)
    def __call__(self, sample):
        """
        :param sample: sample to be normalized
        :return: normalized sample"""
#         sample['img'] = (sample['img']-self.channel_min.reshape(
#             sample['img'].shape[0], 1, 1))/(self.channel_max.reshape(
#             sample['img'].shape[0], 1, 1)-self.channel_min.reshape(
#             sample['img'].shape[0], 1, 1))
        sample['img'] = (sample['img']-self.channel_means.reshape(
        sample['img'].shape[0], 1, 1))/self.channel_std.reshape(
        sample['img'].shape[0], 1, 1)
        return sample 

def create_dataset128(*args, apply_transforms=True, **kwargs):
        """Create a dataset; uses same input parameters as PowerPlantDataset.
        :param apply_transforms: if `True`, apply available transformations
        :return: data set"""
        if apply_transforms:
            data_transforms = transforms.Compose([
                Normalize(),
                ToTensor()
            ])
        else:
            data_transforms = None

        data = firescardataset(*args, **kwargs,
                                            transform=data_transforms)
        return data

