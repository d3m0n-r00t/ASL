# 1. ASL Master Thesis 

- [1. ASL Master Thesis](#1-asl-master-thesis)
	- [1.1. Challenge](#11-challenge)
		- [1.1.1. Similar fields in semantic segmentation:](#111-similar-fields-in-semantic-segmentation)
	- [1.2. Use case](#12-use-case)
	- [1.3. First Step Dataset](#13-first-step-dataset)
	- [1.4. Implementation](#14-implementation)
		- [1.4.1. Project Structure](#141-project-structure)
	- [1.5. Getting started](#15-getting-started)
		- [1.5.1. Clone repo to home](#151-clone-repo-to-home)
		- [1.5.2. Setup conda env](#152-setup-conda-env)
		- [1.5.3. Experiment defintion](#153-experiment-defintion)
		- [1.5.4. Running the experiment](#154-running-the-experiment)
		- [1.5.5. Tasks and Evaluation](#155-tasks-and-evaluation)
	- [1.6. Supervision Options](#16-supervision-options)
	- [1.7. Continual Learning Options](#17-continual-learning-options)
	- [1.8. Scaling performance](#18-scaling-performance)
	- [1.9. Datasets](#19-datasets)
	- [1.10 NeptuneAI Logger](#110-neptuneai-logger)
	- [1.11 Uncertainty Estimation](#111-uncertainty-estimation)
- [2. Acknowledgement](#2-acknowledgement)

## 1.1. Challenge
Continual learning for semantic segmentation.  
We focus on adaptation to different environments.  


### 1.1.1. Similar fields in semantic segmentation:  
- **Unsupervised semantic segmentation:**  
> > >  In a lot of robotic application and especially semantic segmentation labeled data is expensive therefore employing unsupervised or semi-supervised methods is desirable to achieve the adaptation.
- **Domain adaptation:**  
> > > Semantic segmentation or optical flow training data is often generated using game engines or simulators (GTA 5 Dataset or Similar ones).
Here the challenge is how to deal with the domain shift between the target domain (real data) and training domain (synthetic data)- 

- **Class Incremental Continual Learning:**  
> > > To study catastrophic forgetting and algorithms on how to update a Neural Network class incremental learning is a nice toy task. 
There should be a clear carry over between tasks. The skill of classifying CARS and ROADS help each other. Also this scenario is easily set up. 

- **Knowledge Distillation:**  
> > > Extracting knowledge from a trained network to train an other one. Student Teacher models.  

- **Transfer Learning:**  
> > > Learning one task and transferring the learned knowledge to achieve other tasks. This is commonly done with auxillary training losses/tasks or pre-training on an other task/dataset.  

- **Contrastive Learning:**  
> > > Can be used to fully unsupervised learn meaningful embeddings.  

## 1.2. Use case
A simple use case can be a robot that is pre-trained on several indoor datasets but is deployed to a new indoor lab.  

Instead of generalizing to all indoor-environments in the world we tackle the challenge by continually integrating gathered knowledge of the robots environment in an unsupervised fashion in the semantic segmentation network.  

The problem of **GENERALIZATION**: NN are shown to work great when you are able to densely sample within the desired target distribution with provided training data.  
This is often not possible (lack of data). Generalization to a larger domain of inputs can be achieved by data augmentation or providing other suitable human designed priors. Non or the less these methods are intrinsically limited.  

Given this intrinsic limitation and the fact that data is nearly always captured in time-series and humans learn in the same fashion the continual learning paradigm arises.  

## 1.3. First Step Dataset
Given that there is now benchmark for continual learning for semantic segmentation we propose benchmark based on a existing semantic segmentation dataset. 

With additional metrics such as compute, inference time and memory consumption this allows for a comparison of different methods.  

Additionally we provide multiple baselines:  
1. Training in an non continual setting  
2. Training in a naive-way  
3. Our method  

## 1.4. Implementation
Implementation challenges:
- **Do we know that we are in a new scene** Measure of uncertainty might be interresting for this here. 

- Design considerations of replay buffer:
		- can be stored on GPU memory -> we don't need to touch and write a wrapper for each dataloader to integrate the buffer.  
		- we simply drop data in the Batch Generated by the dataloader and replace it with the replay buffer. 
		Also a different forward pass has to be performed for the replay buffer -> so an option is to perform two forward passed for each Batch  
		Forward pass for replay buffer.  
		Forward pass for real data.  
		This allows us to design batches with a certain distribution of replayed and new samples.  


Learning rate scheduling: 
- Since we are currently looking at the performance difference between naive learning and a smarter continual learning approach and we want to study the forgetting in the network we don't use a learning rate scheduler.  


### 1.4.1. Project Structure
The repository is organized in the following way:  


**root/**
- **src/**
	- **datasets/**
	- **loss/**
	- **models/**
	- **utils/**
	- **visu/**
- **cfg/**
	- **dataset/**: config files for dataset
	- **env/**: cluster workstation environment
	- **exp/**: experiment configuration
	- **setup/**: conda environment files
- **notebooks**
- **tools**
	- **leonhard/**
	- **natrix/**
- main.py

## 1.5. Getting started

### 1.5.1. Clone repo to home
```
cd ~
git clone https://github.com/JonasFrey96/ASL.git
```

### 1.5.2. Setup conda env  
The conda env file is located at `cfg/conda/track.yml`.  
This file is currently not a sparse version but includes all the packages I use for debugging.  
```
conda env create -f cfg/conda/track.yml
``` 
```
conda activate track3
```

### 1.5.3. Experiment defintion
Each experiment is defined by two files:  


1. ```env```
Contains all paths that are user depended for external datasets.

| key            | function                                                |
|----------------|---------------------------------------------------------|
| workstation    | Set true if no data needs to be transfered for training |
| base           | path to where to log the experiments                    |
| cityscapes     | path to dataset                                         |
| nyuv2          | path to dataset                                         |
| coco           | path to dataset                                         |
| mlhypersim     | path to dataset                                         |
| tramac_weights | path to pretrained weights fast_scnn_citys.pth          |

1. ```exp```
Contains all settings for the experiment.


### 1.5.4. Running the experiment
Simply pass the correct `exp` and `env` yaml files.  
```
python main.py --exp=cfg/exp/exp.yml --env=cfg/env/env.yml
```

If you develop on a workstation and want to easily push to leonhard i created a small script `tools/leonhard/push_and_run_folder.py`  
The script will schedule all experiment files located in the folder.  
```
python tools/leonhard/push_and_run_folder.py --exp=ml-hypersim --time=4 --gpus=4 --mem=10240 --workers=20 --ram=60 --scratch=300
```
It uses the `tools/leonhard/submit.sh` script to schedule the job.


### 1.5.5. Tasks and Evaluation
A **Task** is split partioned as follow:  
```
	1. Training Task  
		- Name  
		- Train/Val Dataset  
	N. Test Tasks  
		- Name  
		- Test Dataset  
```
A **Task** does not include any information about the training procedure itself.


**Logging**  
For each task a seperate tensorboard logfile is created.  
Also a logfile for tracking the joint results over the full training procedure is generated.  


## 1.6. Supervision Options  
To utilize the unlabeled data we have a look into the following aspects:

| Method                   | Description                                                         |
|--------------------------|---------------------------------------------------------------------|
| **Temporal Consistency** | Semantic segmentation should be consistent over time                |
| **Cross Consistency**    | Decoder should be invariant and consistent to Input transformations |
| **Optical Flow**         | Optical Flow directly relates semantic intra-frame segmentation     |
| **Depth Data**           | Semantic segmentation aligns with frames                            |

## 1.7. Continual Learning Options  
We will focus on latent memory replay to avoid catastrophic forgetting initially.

Other options:
- Regularization approach
- Increasing model complexity
- Generative replay

## 1.8. Scaling performance  
4 1080Ti GPUs 20 Cores BS 8 (effective BS 32)  
Rougly running at 1.8 it/s  
-> 57.6 Images/s  


## 1.9. Datasets  

| Dataset         | Parameters    | Values                                 |
|-----------------|---------------|----------------------------------------|
| **NYU_v2**      | Images Train: | 1449 (total)                           |
|                 | Images Val:   |                                        |
|                 | Annotations:  | NYU-40                                 |
|                 | Optical Flow: | True                                   |
|                 | Depth:        | True                                   |
| | Resolution: | 640 × 480 |
|                 | Total Size:   | 3.7GB                                  |
| **ML-Hypersim** | Images Train: | 74619 (total)                          |
|                 | Images Val:   |                                        |
|                 | Annotations:  | NYU-40                                 |
|                 | Optical Flow: | False                                  |
|                 | Depth:        | True                                   |
| | Resolution: | 1024×768 |
|                 | Total Size:   | 247GB                                  |
| **COCO 2014**   | Images Train: | 330K >200K labeled                     |
|                 | Images Val:   |                                        |
|                 | Annotations:  | Object cat 90 Classes (80 used)        |
|                 | Optical Flow: | False                                  |
|                 | Depth:        | False                                  |
|                 | Total Size:   | 20GB                                   |

## 1.10 NeptuneAI Logger
```
neptune tensorboard /PATH/TO/TensorBoard_logdir --project jonasfrey96/ASL
```

## 1.11 Uncertainty Estimation
![Uncertainty](https://github.com/JonasFrey96/ASL/blob/main/docs/handwritten_notes/Uncertainty.png)



# 2. Acknowledgement  
Special thanks to:  
People at <http://continualai.org> for the inspiration and feedback.  
The authors of Fast-SCNN: Fast Semantic Segmentation Network. ([arxiv](https://arxiv.org/pdf/1902.04502.pdf))  
TRAMAC <https://github.com/Tramac> for implementing Fast-SCNN in PyTorch [Fast-SCNN-pytorch](https://github.com/Tramac/Fast-SCNN-pytorch).  
