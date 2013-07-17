#---------------------------------
#Forest
#Daniel Miron
#7/3/2013
#
#---------------------------------


import numpy as np
import sys
import h5py
import glob


import time
import gc

import pycuda
import pycuda.autoinit
import pycuda.tools
import pycuda.driver as cu
import pycuda.compiler as nvcc
import pycuda.gpuarray as gpuarray

class Forest:
    def __init__(self, nclass):
        self.nclass = nclass
        self.gpu_randomforest_train_source = """
        #include "curand_kernel.h"
        
        #define NODE_TERMINAL -1
        #define NODE_TOSPLIT  -2
        #define NODE_INTERIOR -3
        
        __device__ void movedata() {
        }
        
        __device__ void sampledata(const int nclass, const int* nsamples, const int* samplefrom,
       	const int maxnsamples, int* bagstart, curandState_t *randstate)
        {
       	//Select random samples
       	int iclass, isamp;
       	for (iclass=0; iclass < nclass; ++iclass) {
      		for (isamp=0; isamp < nsamples[iclass]; ++isamp) {
     			bagstart[isamp + iclass*maxnsamples] = curand(randstate) % samplefrom[iclass];
      		}
       	}
        }
        
        __device__ void sortbagbyx(
       	const float *baggedxstart, int totsamples, int mdim, int featurei, int *bagstart, int ndstart, int ndend, int *tempbagstart)
        {
       	//Sort elements of bagstart (from ndstart to ndend) according to x values
       	//Write results into bagstart
       	int length = ndend-ndstart+1;
       	if (length == 1)
       	{
      		return;
       	}
       	int xstart = featurei * totsamples;
       	int *inbag = bagstart;
       	int *outbag = tempbagstart;
        
       	//For-loop merge sort
       	int i = 1;
       	int start1, start2, end1, end2, p1, p2, output;
       	while (i < length)
       	{
        
      		for (start1 = ndstart; start1 <= ndend; start1 += i*2)
      		{
     			end1 = start1 + i - 1;
     			start2 = start1 + i;
     			end2 = start2 + i - 1;
     			p1 = start1; p2 = start2;
     			output = start1;
     			while (p1 <= end1 && p1 <= ndend && p2 <= end2 && p2 <= ndend && output <= ndend)
     			{
        				if (baggedxstart[xstart + inbag[p1]] < baggedxstart[xstart + inbag[p2]])
        				{
       					outbag[output] = inbag[p1];
       					++p1;
        				}
        				else
        				{
       					outbag[output] = inbag[p2];
       					++p2;
        				}
        				++output;
     			}
     			while (p1 <= end1 && p1 <= ndend)
     			{
        				outbag[output] = inbag[p1];
        				++p1;
        				++output;
     			}
     			while (p2 <= end2 && p2 <= ndend)
     			{
        				outbag[output] = inbag[p2];
        				++p2;
        				++output;
     			}
      		}
        
      		//swap for next run
      		if (inbag == bagstart)
      		{
     			inbag = tempbagstart;
     			outbag = bagstart;
      		}
      		else
      		{
     			inbag = bagstart;
     			outbag = tempbagstart;
      		}
        
      		//Loop again with larger chunks
      		i *= 2;
        
       	}
        
       	//Copy output to bagstart (if necessary)
       	if (inbag == tempbagstart)
       	{
      		for (p1 = ndstart; p1 <= ndend; ++p1)
      		{
     			bagstart[p1] = tempbagstart[p1];
      		}
       	}
        
        }
        
        __device__ void findBestSplit(
       	const float *baggedxstart, const int *baggedclassstart, int mdim, int nclass, int *bagstart,
       	int totsamples, int k, int ndstart, int ndend, int *ndendl,
       	int *msplit, float *gini_score, float *best_split, int *best_split_index, bool *isTerminal,
       	int mtry, int idx, int maxTreeSize, int *classpop, float* classweights,
       	curandState_t *randstate,
       	int *wlstart, int *wrstart, int *dimtempstart, int *tempbagstart)
        {
       	//Compute initial values of numerator and denominator of Gini
       	float gini_n = 0.0;
       	float gini_d = 0.0;
       	float gini_rightn, gini_rightd, gini_leftn, gini_leftd;
       	int ctreestart = k * nclass + nclass * idx * maxTreeSize;
       	int i;
       	for (i = 0; i < nclass; ++i)
       	{
      		gini_n += classpop[i + ctreestart] * classpop[i + ctreestart];
      		gini_d += classpop[i + ctreestart];
       	}
       	float gini_crit0 = gini_n / gini_d;
        
       	//start main loop through variables to find best split
       	float gini_critmax = -1.0e25;
       	float crit;
       	int trynum, featurei;
       	int maxfeature = mdim;
        
       	for (i = 0; i < mdim; ++i)
       	{
      		dimtempstart[i] = i;
       	}
        
       	*msplit = -1;
        
       	//for (trynum = 0; trynum < 1; ++trynum)
       	for (trynum = 0; trynum < mtry && trynum < mdim; ++trynum)
       	{
      		//Choose a random feature
      		i = curand(randstate) % maxfeature;
      		featurei = dimtempstart[i];
      		dimtempstart[i] = dimtempstart[maxfeature-1];
      		dimtempstart[maxfeature-1] = featurei;
      		--maxfeature;
        
      		//Sort according to this feature
      		sortbagbyx(baggedxstart, totsamples, mdim, featurei, bagstart, ndstart, ndend, tempbagstart);
        
      		//Split on numerical predictor featurei
      		gini_rightn = gini_n;
      		gini_rightd = gini_d;
      		gini_leftn = 0;
      		gini_leftd = 0;
      		for (i = 0; i < nclass; ++i)
      		{
     			wrstart[i] = classpop[i + ctreestart];
     			wlstart[i] = 0;
      		}
      		int splitpoint;
      		int splitxi;
      		float split_weight, thisx, nextx;
      		int split_class;
      		int ntie = 1;
      		//Loop through all possible split points
      		for (splitpoint = ndstart; splitpoint <= ndend-1; ++splitpoint)
      		{
     			//Get split details
     			splitxi = bagstart[splitpoint];
     			//Determine class based on index and nsamples vector
     			split_class = baggedclassstart[splitxi]-1;
     			split_weight = classweights[split_class];
     			//Update neumerator and demominator
     			gini_leftn += split_weight * (2 * wlstart[split_class] + split_weight);
     			gini_rightn += split_weight * (-2 * wrstart[split_class] + split_weight);
     			gini_leftd += split_weight;
     			gini_rightd -= split_weight;
     			wlstart[split_class] += split_weight;
     			wrstart[split_class] -= split_weight;
        
     			//Check if the next value is the same (no point splitting)
     			thisx = baggedxstart[splitxi + totsamples * featurei];
     			nextx = baggedxstart[bagstart[splitpoint+1] + totsamples * featurei];
     			if (thisx != nextx)
     			{
        				//Check if either node is empty (or very small to allow for float errors)
        				if (gini_rightd > 1.0e-5 && gini_leftd > 1.0e-5)
        				{
       					//Check the split
       					crit = (gini_leftn / gini_leftd) + (gini_rightn / gini_rightd);
       					if (crit > gini_critmax)
       					{
      						*best_split = (thisx + nextx) / 2;
      						*best_split_index = splitpoint;
      						gini_critmax = crit;
      						*msplit = featurei;
      						*ndendl = splitpoint;
      						ntie = 1;
       					}
       					else if (crit == gini_critmax)
       					{
      						++ntie;
      						//Break ties at random
      						if ((curand(randstate) % ntie) == 0)
      						{
     							*best_split = (thisx + nextx) / 2;
     							*best_split_index = splitpoint;
     							gini_critmax = crit;
     							*msplit = featurei;
     							*ndendl = splitpoint;
      						}
       					}
        				}
     			}
      		} // end splitpoint for
       	} // end trynum for
        
       	if (gini_critmax < -1.0e10 || *msplit == -1)
       	{
      		//We could not find a suitable split - mark as a terminal node
      		*isTerminal = true;
       	}
       	else if (*msplit != featurei)
       	{
      		//Resort for msplit (if necessary)
      		sortbagbyx(baggedxstart, totsamples, mdim, *msplit, bagstart, ndstart, ndend, tempbagstart);
       	}
       	*gini_score = gini_critmax - gini_crit0;
        
        }
        
        extern "C" __global__ void trainKernel(
       	const float *x, int n, int mdim, int nclass,
       	const int *classes, const int *classindex,
       	const int *nsamples, const int *samplefrom,
       	int maxnsamples, 
       	unsigned long long seed, unsigned long long sequencestart,
       	int ntree, int maxTreeSize, int mtry, int nodeStopSize,
       	int *treemap, int *nodestatus, float *xbestsplit, 
       	int *bestvar, int *nodeclass, int *ndbigtree,
       	int *nodestart, int *nodepop,
       	int *classpop, float *classweights,
       	int *weight_left, int *weight_right,
       	int *dimtemp, int *bagspace, int *tempbag, float *baggedx, int *baggedclass)
        {
        // Optional arguments for debug (place after xbestsplit): int *nbestsplit, float *bestgini,
       	int idx = threadIdx.x + blockDim.x * blockIdx.x;
        
       	//Make sure we don't overrun
       	if (idx < ntree) {

                /*
      		//Init random number generators (one for each thread)
      		curandState_t state;
      		curand_init(seed, sequencestart + idx, 0, &state);
        
      		int i,j,k,cioffset,bioffset;
        
      		int totsamples = 0;
      		for (i = 0; i < nclass; ++i){
     			totsamples += nsamples[i];
      		}
        
      		//Choose random samples for all classes
      		int *bagstart = bagspace + idx * nclass * maxnsamples;
      		int *tempbagstart = tempbag + idx * nclass * maxnsamples;
      		float *baggedxstart = baggedx + idx * mdim * totsamples;
      		int *baggedclassstart = baggedclass + idx * totsamples;
      		//TODO: offset weightleft, weightright and dimtemp !
      		sampledata(nclass, nsamples, samplefrom, maxnsamples, bagstart, &state);
        
      		//Remove gaps and index into x (instead of into class)
      		k = 0;
      		cioffset = 0;
      		bioffset = 0;
      		for (i = 0; i < nclass; ++i){
     			for (j = 0; j < nsamples[i]; ++j) {
        				//Move memory into local block?
        				int xindex = classindex[bagstart[j + i * maxnsamples] + cioffset];
        				int dimindex;
        				for (dimindex = 0; dimindex < mdim; ++dimindex){
       					baggedxstart[j + bioffset + totsamples * dimindex] = x[xindex + n * dimindex];
        				}
        				baggedclassstart[j + bioffset] = classes[xindex];
        				bagstart[k] = j + bioffset;
        				++k;
     			}
     			cioffset += samplefrom[i];
     			bioffset += nsamples[i];
     			classpop[i + idx * nclass * maxTreeSize] = nsamples[i];
      		}
        
      		//Wipe other values
      		for (;k < nclass * maxnsamples; ++k) {
     			bagstart[k] = -1;
      		}
        
      		int ndstart, ndend, ndendl;
      		int msplit, best_split_index;
      		float best_split, gini_score;
        
      		//Repeat findbestsplit until the tree is complete
      		int ncur = 0;
      		int treeoffset1 = idx * maxTreeSize;
      		int treeOffset2 = idx * 2 * maxTreeSize;
      		nodestart[treeoffset1] = 0;
      		nodepop[treeoffset1] = totsamples;
      		nodestatus[treeoffset1] = NODE_TOSPLIT;
        
      		for (k = 0; k < maxTreeSize-2; ++k) {
     			//Check for end of tree
     			if (k > ncur || ncur >= maxTreeSize - 2) break;
     			//Skip nodes we don't need to split
     			if (nodestatus[treeoffset1+k] != NODE_TOSPLIT) continue;
        
     			// initialize for next call to findbestsplit
     			ndstart = nodestart[treeoffset1 + k];
     			ndend = ndstart + nodepop[treeoffset1 + k] - 1;
     			bool isTerminal = false;
     			gini_score = 0.0;
     			best_split_index = -1;
        
     			findBestSplit(baggedxstart, baggedclassstart, mdim, nclass, bagstart, totsamples, k, ndstart, ndend, &ndendl,
        				&msplit, &gini_score, &best_split, &best_split_index, &isTerminal, mtry, idx, maxTreeSize, classpop, classweights, 
        				&state, weight_left + nclass * idx, weight_right + nclass * idx, dimtemp + mdim * idx, tempbagstart);
        
     			if (isTerminal) {
        				// Node is terminal: Mark it as such and move on to the next.
        				nodestatus[k] = NODE_TERMINAL;
        				//bestvar[treeoffset1 + k] = 0;
        				//xbestsplit[treeoffset1 + k] = 0;
        				continue;
     			}
        
     			// this is a split node - prepare for next round
     			bestvar[treeoffset1 + k] = msplit + 1;
     			//bestgini[treeoffset1 + k] = gini_score;
     			xbestsplit[treeoffset1 + k] = best_split;
     			//nbestsplit[treeoffset1 + k] = best_split_index;
     			nodestatus[treeoffset1 + k] = NODE_INTERIOR;
     			//varUsed[msplit - 1] = 1;
     			//tgini[msplit - 1] += decsplit;
        
     			int leftk = ncur + 1;
     			int rightk = ncur + 2;
     			nodepop[treeoffset1 + leftk] = ndendl - ndstart + 1;
     			nodepop[treeoffset1 + rightk] = ndend - ndendl;
     			nodestart[treeoffset1 + leftk] = ndstart;
     			nodestart[treeoffset1 + rightk] = ndendl + 1;
        
     			// Check for terminal node conditions
     			nodestatus[treeoffset1 + leftk] = NODE_TOSPLIT;
     			if (nodepop[treeoffset1 + leftk] <= nodeStopSize) {
        				nodestatus[treeoffset1 + leftk] = NODE_TERMINAL;
     			}
        
     			nodestatus[treeoffset1 + rightk] = NODE_TOSPLIT;
     			if (nodepop[treeoffset1 + rightk] <= nodeStopSize) {
        				nodestatus[treeoffset1 + rightk] = NODE_TERMINAL;
     			}
        
     			//Calculate class populations
     			int nodeclass = 0;
     			int ctreestart_left = leftk * nclass + idx * nclass * maxTreeSize;
     			int ctreestart_right = rightk * nclass + idx * nclass * maxTreeSize;
     			for (i = ndstart; i <= ndendl; ++i) {
        				nodeclass = baggedclassstart[bagstart[i]]-1;
        				classpop[nodeclass + ctreestart_left] += classweights[nodeclass];
     			}
     			for (i = ndendl+1; i <= ndend; ++i) {
        				nodeclass = baggedclassstart[bagstart[i]]-1;
        				classpop[nodeclass + ctreestart_right] += classweights[nodeclass];
     			}
        
     			for(i = 0; i < nclass; ++i)
     			{
        				if (classpop[i + ctreestart_left] == nodepop[treeoffset1 + leftk])
        				{
       					nodestatus[treeoffset1 + leftk] = NODE_TERMINAL;
        				}
        				if (classpop[i + ctreestart_right] == nodepop[treeoffset1 + rightk])
        				{
       					nodestatus[treeoffset1 + rightk] = NODE_TERMINAL;
        				}
     			}
        
     			//Update treemap offset (indexed from 1 rather than 0)
     			treemap[treeOffset2 + k*2] = ncur + 2;
     			treemap[treeOffset2 + 1 + k*2] = ncur + 3;
     			ncur += 2;
        
      		}
        
      		//Tidy up
      		//TODO: Check results - should not be necessary to go up to maxTreeSize
      		ndbigtree[idx] = ncur+1;
      		//ndbigtree[idx] = maxTreeSize;
      		for(k = maxTreeSize-1; k >= 0; --k)
      		{
     			//if (nodestatus[treeoffset1 + k] == 0)
     			//	--ndbigtree[idx];
     			if (nodestatus[treeoffset1 + k] == NODE_TOSPLIT)
        				nodestatus[treeoffset1 + k] = NODE_TERMINAL;
      		}
        
      		//Calculate prediction for terminal nodes
      		for (k = 0; k < maxTreeSize; ++k)
      		{
     			treeoffset1 = idx * maxTreeSize;
     			if (nodestatus[treeoffset1 + k] == NODE_TERMINAL)
     			{
        				int toppop = 0;
        				int ntie = 1;
        				for (i = 0; i < nclass; ++i)
        				{
       					int ctreeoffset = k * nclass + idx * nclass * maxTreeSize;
       					if (classpop[i + ctreeoffset] > toppop)
       					{
      						nodeclass[treeoffset1 + k] = i+1;
      						toppop = classpop[i + ctreeoffset];
       					}
       					//Break ties at random
       					if (classpop[i + ctreeoffset] == toppop)
       					{
      						++ntie;
      						if ((curand(&state) % ntie) == 0)
      						{
     							nodeclass[treeoffset1 + k] = i+1;
     							toppop = classpop[i + ctreeoffset];
      						}
       					}
        				}
     			}
      		}
      		*/
        
      		ndbigtree[idx] = idx;
        
       	}
        
        }
        """
        
    def make_trees(self, training_x, training_y, num_trees, test_file):
        time.sleep(3)
        
        test_file = test_file
        print training_y, "training_y"
        gpu_train = nvcc.SourceModule(self.gpu_randomforest_train_source, no_extern_c=True).get_function('trainKernel')
        st_f = time.time()
        for classi in range(self.nclass):
            print 'Class {0}: {1} training pixels.'.format(classi, np.sum(training_y == classi + 1))
            
        # Train on GPU
        ntree = num_trees
        self.ntree = num_trees
        self.mtry = np.int32(np.floor(np.sqrt(training_x.shape[0])))
        #nsamples = np.ones((1,nclass), dtype=np.int32) * (training_x.shape[1] / nclass)
        self.nsamples = np.ones((1,self.nclass), dtype=np.int32) * 10
        self.classweights = np.ones((1,self.nclass), dtype=np.float32)
            
        # Sanity check
        assert(training_x.shape[1] == training_y.shape[0])
        
        # Random number seeds
        seed = np.int64(time.time())
        sequencestart = np.int64(43)
        
        samplefrom = np.zeros((self.nclass), dtype=np.int32)
        maxTreeSize = np.int32(2 * np.sum(self.nsamples) + 1)
        nodeStopSize = np.int32(1)
        
        for classi in range(self.nclass):
            samplefrom[classi] = np.sum(training_y == (classi + 1))
        
        maxnsamples = np.max(self.nsamples)
        classindex = -1 * np.ones((np.max(samplefrom) * self.nclass), dtype=np.int32)
        
        cioffset = 0
        for classi in range(self.nclass):
            classindex[cioffset:cioffset + samplefrom[classi]] = np.nonzero(training_y == (classi + 1))[0]
            cioffset = cioffset + samplefrom[classi]
        
        bagmem = -1 * np.ones((ntree, maxnsamples * self.nclass), dtype=np.int32)
        d_bagspace = gpuarray.to_gpu(bagmem)
        d_tempbag = gpuarray.to_gpu(bagmem)
        bagmem = None
        
        print cu.mem_get_info(), '0'
        test_file.write("Code Point 0")
        d_treemap = gpuarray.zeros((long(ntree * 2), long(maxTreeSize)), np.int32)
        d_nodestatus = gpuarray.zeros((long(ntree), long(maxTreeSize)), np.int32)
        d_xbestsplit = gpuarray.zeros((long(ntree), long(maxTreeSize)), np.float32)
        #d_nbestsplit = gpuarray.zeros((long(ntree), long(maxTreeSize)), np.int32)
        #d_bestgini = gpuarray.zeros((long(ntree), long(maxTreeSize)), np.float32)
        d_bestvar = gpuarray.zeros((long(ntree), long(maxTreeSize)), np.int32)
        d_nodeclass = gpuarray.zeros((long(ntree), long(maxTreeSize)), np.int32)
        d_ndbigtree = gpuarray.zeros((long(ntree), 1), np.int32)
        d_nodestart = gpuarray.zeros((long(ntree), long(maxTreeSize)), np.int32)
        d_nodepop = gpuarray.zeros((long(ntree), long(maxTreeSize)), np.int32)
        d_classpop = gpuarray.zeros((long(ntree), long(maxTreeSize*self.nclass)), np.int32)
        d_classweights = gpuarray.to_gpu(self.classweights)
        d_weight_left = gpuarray.zeros((long(ntree), long(self.nclass)), np.int32)
        d_weight_right = gpuarray.zeros((long(ntree), long(self.nclass)), np.int32)
        d_dimtemp = gpuarray.zeros((long(ntree), long(training_x.shape[0])), np.int32)
        
        test_file.write("Code Point 1")
        print cu.mem_get_info(), '1'
        print cu.mem_get_info(), '1.1'
        
        d_baggedx = gpuarray.zeros((long(np.sum(self.nsamples)*training_x.shape[0]), long(ntree)), np.float32)
        d_baggedclass = gpuarray.zeros((long(ntree), long(np.sum(self.nsamples))), np.int32)
        
        print cu.mem_get_info(), '2'
        test_file.write("code Point 2")

        import pycuda.driver

        d_hack = pycuda.driver.mem_alloc(32)                

        print cu.mem_get_info(), '2.1'
        test_file.write("code Point 2.1")

        hack = np.array([0, 1, 2, 3, 4, 5, 6, 7], dtype=np.int32)
        pycuda.driver.memcpy_htod(d_hack, hack)

        print cu.mem_get_info(), '3'
        test_file.write("code Point 3")
                                                                
        d_training_x = pycuda.driver.mem_alloc(training_x.nbytes)                

        print cu.mem_get_info(), '4'
        test_file.write("code Point 4: " + str(training_x.nbytes) + "       ")

        pycuda.driver.memcpy_htod(d_training_x, training_x.copy())

        print cu.mem_get_info(), '5'
        test_file.write("code Point 5")
        
        d_training_x = gpuarray.to_gpu(training_x.copy())
        
        print cu.mem_get_info(), '6'
        test_file.write("code Point 6")
        
        d_training_y = gpuarray.to_gpu(training_y.copy())
        
        print cu.mem_get_info(), '7'
        test_file.write("code Point 7")
        d_classindex = gpuarray.to_gpu(classindex)
        d_nsamples = gpuarray.to_gpu(self.nsamples)
        d_samplefrom = gpuarray.to_gpu(samplefrom)
        
        print cu.mem_get_info(), '8'
        test_file.write("code Point 8")
                    
        block = (32, 1, 1)
        grid = (int((ntree + 1) / block[0]) - 1, 1)
        
        test_file.write('gridsize={0}'.format(grid[0]))
        
        gpu_train(d_training_x, np.int32(training_x.shape[1]), np.int32(training_x.shape[0]), np.int32(self.nclass),
        d_training_y, d_classindex, d_nsamples, d_samplefrom,
        np.int32(maxnsamples), seed, sequencestart, np.int32(ntree), np.int32(maxTreeSize), np.int32(self.mtry), np.int32(nodeStopSize),
        d_treemap, d_nodestatus, d_xbestsplit,
        d_bestvar, d_nodeclass, d_ndbigtree,
        d_nodestart, d_nodepop,
        d_classpop, d_classweights,
        d_weight_left, d_weight_right,
        d_dimtemp, d_bagspace, d_tempbag, d_baggedx, d_baggedclass, 
        block=block, grid=grid)
        
        test_file.write("code Point 9")
        
        treemap = d_treemap.get()
        nodestatus = d_nodestatus.get()
        xbestsplit = d_xbestsplit.get()
        bestvar = d_bestvar.get()
        nodeclass = d_nodeclass.get()
        ndbigtree = d_ndbigtree.get()
        
        test_file.write("code Point 10")
        
        print "forest making took", time.time()-st_f
        return treemap, nodestatus, xbestsplit, nodeclass, ndbigtree
        
        
    #num_trees is PER ITERATION    
    def make_forest(self, training_x, training_y, num_trees, iterations):
        
        test_file = open(r"C:\Users\DanielMiron\rhoana\ClassifyMembranes\debug.txt", "w")
        
        training_y = training_y+np.ones(np.shape(training_y))
        self.treemap = []
        self.nodestatus = []
        self.xbestsplit = []
        self.nodeclass = []
        self.ndbigtree = []
        for i in range(iterations):
            test_file.write("start of iteration")
            
            treemap_t, nodestatus_t, xbestsplit_t, nodeclass_t, ndbigtree_t = self.make_trees(training_x, training_y, num_trees, test_file)
            
            test_file.write("code Point 11")
            
            self.treemap.append(treemap_t)
            self.nodestatus.append(nodestatus_t)
            self.xbestsplit.append(xbestsplit_t)
            self.nodeclass.append(nodeclass_t)
            self.ndbigtree.append(ndbigtree_t)
            
            test_file.write("code Point 12")
        self.treemap = np.vstack(self.treemap)
        self.nodestatus = np.vstack(self.nodestatus)
        self.xbestsplit = np.vstack(self.xbestsplit)
        self.nodeclass = np.vstack(self.nodeclass)
        self.ndbigtree = np.vstack(self.ndbigtree)
        
    def save_forest(self, filename):
        # Save results
        out_hdf5 = h5py.File(filename, 'w')
        out_hdf5['/forest/treemap'] = self.treemap
        out_hdf5['/forest/nodestatus'] = self.nodestatus
        out_hdf5['/forest/xbestsplit'] = self.xbestsplit
        out_hdf5['/forest/bestvar'] = self.bestvar
        out_hdf5['/forest/nodeclass'] = self.nodeclass
        out_hdf5['/forest/ndbigtree'] = self.ndbigtree
            
        out_hdf5['/forest/nrnodes'] = self.maxTreeSize
        out_hdf5['/forest/ntree'] = self.ntree
        out_hdf5['/forest/nclass'] = self.nclass
        out_hdf5['/forest/classweights'] = self.classweights
        out_hdf5['/forest/mtry'] = self.mtry
            
        out_hdf5.close()
        return