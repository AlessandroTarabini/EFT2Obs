# Auto_detect.sh

The script is meant to run automatically the ```auto_detect_operators.py``` step, which determines the interesting that are relevant for the process. The script does the following steps:

* Create another folder in the ```cards``` folder
* Change the ```proc_card```:
    * NP=0 --> NP=2
    * [noborn=QCD] --> [virt=QCD]
    * change the model from the restricted one to the original SMEFT@NLO
* Setting up the process
* Running ```auto_detect_operators```

At the moment, we only print out the relevant operators through the terminal (``` --noReweightCard --noConfigJson```)

```
sh auto_detect.sh ggF-SMEFTatNLO-tree
sh auto_detect.sh ggF-SMEFTatNLO-loop
sh auto_detect.sh ggF_SMEFTatNLO_tree_loop_2
sh auto_detect.sh ggF_SMEFTatNLO_tree_loop_4
```

# Generating gridpacks

```
./scripts/setup_process.sh ggF_SMEFTatNLO_tree

python scripts/make_config.py -p ggF_SMEFTatNLO_tree -o cards/ggF_SMEFTatNLO_tree/config_SMEFTatNLO_ggH.json --pars DIM6:2,4,7,8 DIM62f:4,5,19,24 DIM64f4l:7 --def-val 0.01 --def-sm 0 --def-gen 1E-8 --set-inactive DIM6:1=1.000000e+03

python scripts/make_reweight_card.py cards/ggF_SMEFTatNLO_tree/config_SMEFTatNLO_ggH.json cards/ggF_SMEFTatNLO_tree/reweight_card.dat --prepend 'change process p p > h NP=2 QED=1 QCD=0' 'change process p p > h j NP=2 QED=1 QCD=1 --add' 'change process p p > h j j NP=2 QED=1 QCD=2 --add'

python scripts/make_param_card.py -p ggF_SMEFTatNLO_tree -c cards/ggF_SMEFTatNLO_tree/config_SMEFTatNLO_ggH.json -o cards/ggF_SMEFTatNLO_tree/param_card.dat

mkdir jobs_tree

python scripts/launch_gridpack.py ggF_SMEFTatNLO_tree -c 8 --job-mode condor --task-name gp-ggF_SMEFTatNLO_tree --dir jobs_tree --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8'
```

```
./scripts/setup_process.sh ggF_SMEFTatNLO_loop

python scripts/make_config.py -p ggF_SMEFTatNLO_loop -o cards/ggF_SMEFTatNLO_loop/config_SMEFTatNLO_ggH_no_cpg.json --pars DIM6:2,4,8 DIM62F:4,5,19,24 DIM64F4L:7 --def-val 0.01 --def-sm 0.0 --def-gen 1E-8 --set-inactive DIM6:1=1.000000e+03

python scripts/make_reweight_card.py cards/ggF_SMEFTatNLO_loop/config_SMEFTatNLO_ggH_no_cpg.json cards/ggF_SMEFTatNLO_loop/reweight_card.dat --prepend 'change process p p > h NP=2 QED=1 QCD=2 [virt=QCD]' 'change process p p > h j NP=2 QED=1 QCD=3 [virt=QCD] --add' 'change process p p > h j j NP=2 QED=1 QCD=4 [virt=QCD] --add'

python scripts/make_param_card.py -p ggF_SMEFTatNLO_loop -c cards/ggF_SMEFTatNLO_loop/config_SMEFTatNLO_ggH_no_cpg.json -o cards/ggF_SMEFTatNLO_loop/param_card.dat

mkdir jobs_loop

python scripts/launch_gridpack.py ggF_SMEFTatNLO_loop -c 8 --job-mode condor --task-name gp-ggF_SMEFTatNLO_loop --dir jobs_loop --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8'
```

```
./scripts/setup_process.sh ggF_SMEFTatNLO_tree_loop_2

python scripts/make_config.py -p ggF_SMEFTatNLO_tree_loop_2 -o cards/ggF_SMEFTatNLO_tree_loop_2/config_SMEFTatNLO_ggH.json --pars DIM6:2,4,7,8 DIM62f:4,5,19,24 DIM64f4l:7 --def-val 0.01 --def-sm 0 --def-gen 1E-8 --set-inactive DIM6:1=1.000000e+03

python scripts/make_reweight_card.py cards/ggF_SMEFTatNLO_tree_loop_2/config_SMEFTatNLO_ggH.json cards/ggF_SMEFTatNLO_tree_loop_2/reweight_card.dat --prepend 'change process p p > h NP=2 QCD=0 QED=1 QCD^2==2 NP^2==2 [virt=QCD]' 'change process p p > h j NP=2 QCD=1 QED=1 QCD^2==4 NP^2==2 [virt=QCD] --add' 'change process p p > h j j NP=2 QCD=2 QED=1 QCD^2==6 NP^2==2 [virt=QCD] --add'

python scripts/make_param_card.py -p ggF_SMEFTatNLO_tree_loop_2 -c cards/ggF_SMEFTatNLO_tree_loop_2/config_SMEFTatNLO_ggH.json -o cards/ggF_SMEFTatNLO_tree_loop_2/param_card.dat

mkdir jobs_tree_loop_2

python scripts/launch_gridpack.py ggF_SMEFTatNLO_tree_loop_2 -c 8 --job-mode condor --task-name gp-ggF_SMEFTatNLO_tree_loop_2 --dir jobs_tree_loop_2 --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8'
```

```
./scripts/setup_process.sh ggF_SMEFTatNLO_tree_loop_4

python scripts/make_config.py -p ggF_SMEFTatNLO_tree_loop_4 -o cards/ggF_SMEFTatNLO_tree_loop_4/config_SMEFTatNLO_ggH.json --pars DIM6:2,4,7,8 DIM62f:4,5,19,24 DIM64f4l:7 --def-val 0.01 --def-sm 0 --def-gen 1E-8 --set-inactive DIM6:1=1.000000e+03

python scripts/make_reweight_card.py cards/ggF_SMEFTatNLO_tree_loop_4/config_SMEFTatNLO_ggH.json cards/ggF_SMEFTatNLO_tree_loop_4/reweight_card.dat --prepend 'change process p p > h NP=2 QCD=0 QED=1 QCD^2==2 NP^2==4 [virt=QCD]' 'change process p p > h j NP=2 QCD=1 QED=1 QCD^2==4 NP^2==4 [virt=QCD] --add' 'change process p p > h j j NP=2 QCD=2 QED=1 QCD^2==6 NP^2==4 [virt=QCD] --add'

python scripts/make_param_card.py -p ggF_SMEFTatNLO_tree_loop_4 -c cards/ggF_SMEFTatNLO_tree_loop_4/config_SMEFTatNLO_ggH.json -o cards/ggF_SMEFTatNLO_tree_loop_4/param_card.dat

mkdir jobs_tree_loop_4

python scripts/launch_gridpack.py ggF_SMEFTatNLO_tree_loop_4 -c 8 --job-mode condor --task-name gp-ggF_SMEFTatNLO_tree_loop_4 --dir jobs_tree_loop_4 --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8'
```

# Launch Jobs

```
python scripts/launch_jobs.py --gridpack gridpack_ggF_SMEFTatNLO_loop.tar.gz -j 200 -s 1 -e 2500 -p CMS_2025_I2915441 -o test-ggF-SMEFTatNLO-loop --sub-opts '+MaxRuntime = 18000' --task-name test-ggF-SMEFTatNLO-loop --dir jobs_evts_loop --job-mode condor --env "HIGGSPRODMODE=GGF"

python scripts/launch_jobs.py --gridpack gridpack_ggF_SMEFTatNLO_tree.tar.gz -j 200 -s 1 -e 2500 -p CMS_2025_I2915441 -o test-ggF-SMEFTatNLO-tree --sub-opts '+MaxRuntime = 18000' --task-name test-ggF-SMEFTatNLO-tree --dir jobs_evts_tree --job-mode condor --env "HIGGSPRODMODE=GGF"

python scripts/launch_jobs.py --gridpack gridpack_ggF_SMEFTatNLO_tree_loop_2.tar.gz -j 200 -s 1 -e 2500 -p CMS_2025_I2915441 -o test-ggF-SMEFTatNLO-tree-loop-2 --sub-opts '+MaxRuntime = 18000' --task-name test-ggF-SMEFTatNLO-tree-loop-2 --dir jobs_evts_tree_loop_2 --job-mode condor --env "HIGGSPRODMODE=GGF"

python scripts/launch_jobs.py --gridpack gridpack_ggF_SMEFTatNLO_tree_loop_4.tar.gz -j 200 -s 1 -e 2500 -p CMS_2025_I2915441 -o test-ggF-SMEFTatNLO-tree-loop-4 --sub-opts '+MaxRuntime = 18000' --task-name test-ggF-SMEFTatNLO-tree-loop-4 --dir jobs_evts_tree_loop_4 --job-mode condor --env "HIGGSPRODMODE=GGF"
```

# Extracting parameterisations

Once the events are generated, the various YODA files are merged together and the scaling equation are extracted.

```
yodamerge -o merged_yoda/ggF-SMEFTatNLO-loop.yoda test-ggF-SMEFTatNLO-loop/*

yodamerge -o merged_yoda/ggF-SMEFTatNLO-tree.yoda test-ggF-SMEFTatNLO-tree/*

yodamerge -o merged_yoda/ggF-SMEFTatNLO-tree-loop-2.yoda test-ggF-SMEFTatNLO-tree-loop-2/*

yodamerge -o merged_yoda/ggF-SMEFTatNLO-tree-loop-4.yoda test-ggF-SMEFTatNLO-tree-loop-4/*
```

```
mkdir params
cd params

python ../scripts/get_scaling.py -c ../cards/ggF_SMEFTatNLO_loop/config_SMEFTatNLO_ggH_no_cpg.json -i ../merged_yoda/ggF-SMEFTatNLO-loop.yoda --hist "/CMS_2025_I2915441/pt_h" -o loop_CMS_2025_I2915441_pt_h --bin-labels ../bin_labels.json

python ../scripts/get_scaling.py -c ../cards/ggF_SMEFTatNLO_tree/config_SMEFTatNLO_ggH.json -i ../merged_yoda/ggF-SMEFTatNLO-tree.yoda --hist "/CMS_2025_I2915441/pt_h" -o tree_CMS_2025_I2915441_pt_h --bin-labels ../bin_labels.json

python ../scripts/get_scaling.py -c ../cards/ggF_SMEFTatNLO_tree_loop_2/config_SMEFTatNLO_ggH.json -i ../merged_yoda/ggF-SMEFTatNLO-tree-loop-2.yoda --hist "/CMS_2025_I2915441/pt_h" -o tree-loop-2_CMS_2025_I2915441_pt_h --bin-labels ../bin_labels.json

python ../scripts/get_scaling.py -c ../cards/ggF_SMEFTatNLO_tree_loop_4/config_SMEFTatNLO_ggH.json -i ../merged_yoda/ggF-SMEFTatNLO-tree-loop-4.yoda --hist "/CMS_2025_I2915441/pt_h" -o tree-loop-4_CMS_2025_I2915441_pt_h --bin-labels ../bin_labels.json
```