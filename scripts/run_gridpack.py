from __future__ import print_function
import argparse
import subprocess
import os
import sys
import shutil

parser = argparse.ArgumentParser()

parser.add_argument('--gridpack', default='.')
parser.add_argument('--launch-dir', default='.')
parser.add_argument('--madgraph-dir', default='./MG5_aMC_v2_6_7/')
parser.add_argument('-e', '--events', default=5000, type=int, help="Number of events to generate")
parser.add_argument('-s', '--seed', type=int, default=1, help="Random number seed")
parser.add_argument('-p', '--plugins', type=str, default='', help="Comma separated list of rivet plugins to run")
parser.add_argument('-o', '--outdir', type=str, default='.', help="Output directory for yoda files")
parser.add_argument('--save-lhe', type=str, default=None, help="Local directory to save the LHE file")
parser.add_argument('--load-lhe', type=str, default=None, help="Load LHE file from this local directory, skip running MG")
parser.add_argument('--save-hepmc', type=str, default=None, help="Local directory to save the hepmc file")
parser.add_argument('--load-hepmc', type=str, default=None, help="Load hepmc file from this local directory, skip running MG")
parser.add_argument('--rivet-ignore-beams', action='store_true', help="Pass the --ignore-beams argument when running rivet, useful for simulating decay-only processes")
parser.add_argument('--no-cleanup', action='store_true', help="Do not delete working directory at the end")
parser.add_argument('--to-step', default='rivet', choices=['lhe', 'shower', 'rivet'], help="Terminate after this step")
parser.add_argument('--nlo', action='store_true', help="Run on an NLO gridpack")

args = parser.parse_args()

if args.load_hepmc is not None and (args.load_lhe is not None or args.save_lhe is not None):
    raise RuntimeError('Cannot set --load-hepmc and --load-lhe/--save-lhe at the same time')


def ResolvePath(pathname, relbase):
    if os.path.isabs(pathname):
        return pathname
    else:
        return os.path.abspath(os.path.join(relbase, pathname))


def MaybeMakeDir(pathname):
    if not os.path.isdir(pathname) and not os.path.isfile(pathname):
        print('>> Creating directory %s' % pathname)
        subprocess.check_call(['mkdir', '-p', pathname])


def EnsurePythonInPath():
    """Ensure 'python' is available in PATH for rivet scripts that require it.
    Creates a symlink from python3 to python if needed.
    Returns (new_path, cleanup_dir) where cleanup_dir is None if no cleanup needed."""
    # Check if python is already available
    if shutil.which('python') is not None:
        return (os.environ.get('PATH', ''), None)
    
    # python not found, check for python3
    python3_path = shutil.which('python3')
    if python3_path is None:
        raise RuntimeError('Neither python nor python3 found in PATH')
    
    # Create a temporary directory for the symlink
    tmpdir = os.environ.get('TMPDIR', '/tmp')
    python_link_dir = os.path.join(tmpdir, 'python_link_%i' % os.getpid())
    os.makedirs(python_link_dir, exist_ok=True)
    python_link_path = os.path.join(python_link_dir, 'python')
    
    # Create symlink
    if not os.path.exists(python_link_path):
        os.symlink(python3_path, python_link_path)
        print('>> Created python symlink: %s -> %s' % (python_link_path, python3_path))
    
    # Prepend to PATH
    new_path = python_link_dir + os.pathsep + os.environ.get('PATH', '')
    return (new_path, python_link_dir)


# Path we're running from
iwd = os.getcwd()
# Path we launched from (different from iwd if this is running in a batch job)
launch_dir = os.path.abspath(args.launch_dir)

madgraph_dir = os.path.abspath(args.madgraph_dir)

outdir = ResolvePath(args.outdir, args.launch_dir)
MaybeMakeDir(outdir)

gridpack = ResolvePath(args.gridpack, args.launch_dir)
print('>> Writing yoda output to %s' % outdir)

events = args.events
seed = args.seed
plugins = args.plugins
save_lhe = args.save_lhe
load_lhe = args.load_lhe
save_hepmc = args.save_hepmc
load_hepmc = args.load_hepmc
if save_lhe is not None:
    save_lhe = ResolvePath(save_lhe, args.launch_dir)
    MaybeMakeDir(save_lhe)
    print('>> Saving LHE output to %s' % save_lhe)
if load_lhe is not None:
    load_lhe = ResolvePath(load_lhe, args.launch_dir)
    print('>> Loading LHE input from %s' % load_lhe)
if save_hepmc is not None:
    save_hepmc = ResolvePath(save_hepmc, args.launch_dir)
    MaybeMakeDir(save_hepmc)
    print('>> Saving HepMC output to %s' % save_hepmc)
if load_hepmc is not None:
    load_hepmc = ResolvePath(load_hepmc, args.launch_dir)
    print('>> Loading HepMC input from %s' % load_hepmc)
ignore_beams = args.rivet_ignore_beams

# Check if TMPDIR is set
if 'TMPDIR' not in os.environ:
    tmpdir = subprocess.check_output(['mktemp', '-d']).strip().decode()
    print('>> No TMPDIR was set, created %s' % tmpdir)
else:
    tmpdir = os.environ['TMPDIR']
    print('>> TMPDIR is set to %s' % tmpdir)

gridpack_dir = tmpdir+'/gridpack_run_%i' % seed

if os.path.isdir(gridpack_dir):
    subprocess.check_call(['rm', '-r', gridpack_dir])

finished = False

# Can skip untarring the gridpack if we're going to read straight from existing hepMC
if load_hepmc is None:
    os.mkdir(gridpack_dir)
    print('>> Untarring gridpack %s into %s' % (gridpack, gridpack_dir))
    subprocess.check_call(['tar', '-xf', gridpack, '-C', '%s/' % gridpack_dir])

    # sys.exit(0)
    os.chdir(gridpack_dir)
    gp_dir = os.getcwd()

    if not args.nlo:
        subprocess.check_call(['mkdir', '-p', 'madevent/Events/GridRun'])

    if load_lhe is None:
        subprocess.check_call(['./run.sh', '%i' % events, '%i' % seed])
        if not args.nlo:
            subprocess.check_call(['mv', 'events.lhe.gz', 'madevent/Events/GridRun/unweighted_events.lhe.gz'])
            os.chdir('madevent')
            subprocess.check_call('echo "0" | ./bin/madevent --debug reweight GridRun', shell=True)
            os.chdir(gp_dir)
            if(os.path.isfile("madspin_card.dat")):
                subprocess.check_call(['cp', 'madevent/Events/GridRun/unweighted_events.lhe.gz', './events_%i.lhe.gz' % (seed)])
                subprocess.check_call(['gunzip', './events_%i.lhe.gz' % (seed)])
                initrwgtlines = []
                isReweightBlock = False
                with open("events_%i.lhe"%(seed), "r") as origfile: #Need to keep track of the initrwgt header because running madspin removes it
                    for line in origfile:
                        if "initrwgt" in line:
                            isReweightBlock=True
                        if "/initrwgt" in line:
                            isReweightBlock=False
                        if isReweightBlock or "/initrwgt" in line:
                            initrwgtlines.append(line)
                origfile.close()
                msrunfile = open("madspinrun.dat","w")
                msrunfile.write('import events_%i.lhe\n'%(seed))
                msseed = seed+100000000 
                msrunfile.write('echo "set seed %i"\n'%(msseed))
                madspcard = open("madspin_card.dat","r")
                mslines = madspcard.readlines()
                madspcard.close()
                for line in mslines:
                     msrunfile.write(line)
                msrunfile.close()
                subprocess.check_call(['%s/MadSpin/madspin' %(madgraph_dir), 'madspinrun.dat' ]) #Run madspin
                subprocess.check_call(['gunzip','./events_%i_decayed.lhe.gz' %(seed)])
                infile = open("events_%i_decayed.lhe"%(seed), "r")
                outfile = open("events_%i_decayed_updated.lhe"%(seed),"w")
                for line in infile: #Now we need to put the initrwgt info back in the header
                    if "/header" in line:
                        for initrwline in initrwgtlines:
                            outfile.write(initrwline)
                    outfile.write(line)
                infile.close()
                outfile.close()
                subprocess.check_call(['gzip','./events_%i_decayed_updated.lhe'%(seed)])
                subprocess.check_call(['mv', './events_%i_decayed_updated.lhe.gz'%(seed), 'madevent/Events/GridRun/unweighted_events.lhe.gz']) #Move the decayed events back into the usual location 
    else:
        if args.nlo:
            subprocess.check_call(['cp', '%s/events_%i.lhe.gz' % (load_lhe, seed), 'madevent/Events/GridRun/unweighted_events.lhe.gz'])
        else:
            subprocess.check_call(['cp', '%s/events_%i.lhe.gz' % (load_lhe, seed), 'Events/GridRun/events.lhe.gz'])

    if save_lhe is not None:
        subprocess.check_call(['mkdir', '-p', save_lhe])
        if args.nlo:
            subprocess.check_call(['cp', 'Events/GridRun/events.lhe.gz', '%s/events_%i.lhe.gz' % (save_lhe, seed)])
        else:
            subprocess.check_call(['cp', 'madevent/Events/GridRun/unweighted_events.lhe.gz', '%s/events_%i.lhe.gz' % (save_lhe, seed)])

    if args.to_step == 'lhe':
        finished = True

    # For NLO we have already run the shower
    if not finished:
        if args.nlo:
            subprocess.check_call(['cp', 'Events/GridRun/events_PYTHIA8_0.hepmc.gz', '%s/events_%i.hepmc.gz' % (tmpdir, seed)])
            subprocess.check_call(['gunzip', '%s/events_%i.hepmc.gz' % (tmpdir, seed)])
        else:
            os.chdir('madevent')
            lines = ['pythia8']
            if save_hepmc is None:
                lines.append('set HEPMCoutput:file fifo@%s/events_%i.hepmc' % (tmpdir, seed))
            else:
                lines.append('set HEPMCoutput:file %s/events_%i.hepmc' % (tmpdir, seed))
            with open('mgrunscript', "w") as text_file:
                text_file.write('\n'.join(lines))
            subprocess.check_call('./bin/madevent --debug shower GridRun < mgrunscript', shell=True)

    if args.to_step == 'shower':
        finished = True
else:
    subprocess.check_call(['cp', '%s/events_%i.hepmc.gz' % (load_hepmc, seed), '%s/events_%i.hepmc.gz' % (tmpdir, seed)])
    subprocess.check_call(['gunzip', '%s/events_%i.hepmc.gz' % (tmpdir, seed)])


os.chdir(iwd)

if not finished:
    # Ensure python is available in PATH for rivet scripts
    rivet_env = os.environ.copy()
    rivet_path, python_cleanup_dir = EnsurePythonInPath()
    rivet_env['PATH'] = rivet_path
    
    try:
        rivet_args = ['rivet', '--analysis=%s' % plugins, '%s/events_%i.hepmc' % (tmpdir, seed), '-o', '%s/Rivet_%i.yoda' % (outdir, seed)]
        if ignore_beams:
            rivet_args.append('--ignore-beams')
        subprocess.check_call(rivet_args, env=rivet_env)
    finally:
        # Clean up the python symlink directory if it was created
        if python_cleanup_dir is not None and os.path.exists(python_cleanup_dir):
            try:
                os.remove(os.path.join(python_cleanup_dir, 'python'))
                os.rmdir(python_cleanup_dir)
                print('>> Cleaned up python symlink directory: %s' % python_cleanup_dir)
            except OSError as e:
                print('>> Warning: Failed to clean up python symlink directory %s: %s' % (python_cleanup_dir, e))

if save_hepmc is not None:
    subprocess.check_call(['mkdir', '-p', save_hepmc])
    subprocess.check_call(['gzip', '%s/events_%i.hepmc' % (tmpdir, seed)])
    subprocess.check_call(['cp', '%s/events_%i.hepmc.gz' % (tmpdir, seed), '%s/events_%i.hepmc.gz' % (save_hepmc, seed)])
    os.remove('%s/events_%i.hepmc.gz' % (tmpdir, seed))
else:
    if not args.to_step == 'lhe': #if stopped at lhe, there would be no hepmc to delete
        os.remove('%s/events_%i.hepmc' % (tmpdir, seed))

if not args.no_cleanup and load_hepmc is None:
    subprocess.check_call(['rm', '-rf', gridpack_dir])
