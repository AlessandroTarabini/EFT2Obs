## Quick script to produce the first step for all params, avoiding the generation of the various cards 

./scripts/setup_process.sh ggF_SMEFTatNLO_tree
mkdir jobs_tree
python scripts/launch_gridpack.py ggF_SMEFTatNLO_tree -c 8 --job-mode condor --task-name gp-ggF_SMEFTatNLO_tree --dir jobs_tree --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8'

./scripts/setup_process.sh ggF_SMEFTatNLO_loop
mkdir jobs_loop
python scripts/launch_gridpack.py ggF_SMEFTatNLO_loop -c 8 --job-mode condor --task-name gp-ggF_SMEFTatNLO_loop --dir jobs_loop --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8'

./scripts/setup_process.sh ggF_SMEFTatNLO_tree_loop_2
mkdir jobs_tree_loop_2
python scripts/launch_gridpack.py ggF_SMEFTatNLO_tree_loop_2 -c 8 --job-mode condor --task-name gp-ggF_SMEFTatNLO_tree_loop_2 --dir jobs_tree_loop_2 --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8'

./scripts/setup_process.sh ggF_SMEFTatNLO_tree_loop_4
mkdir jobs_tree_loop_4
python scripts/launch_gridpack.py ggF_SMEFTatNLO_tree_loop_4 -c 8 --job-mode condor --task-name gp-ggF_SMEFTatNLO_tree_loop_4 --dir jobs_tree_loop_4 --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8'