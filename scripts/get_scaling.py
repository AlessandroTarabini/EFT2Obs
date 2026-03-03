#!/usr/bin/env python3

from __future__ import print_function
from builtins import range
from array import array
import numpy as np
import math
import json
import argparse

import yoda
from eftscaling import EFT2ObsHist, EFTScaling

parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default="Rivet.yoda")
parser.add_argument('--output', '-o', default=None)
parser.add_argument('--config', '-c', default="Rivet.yoda")
parser.add_argument('--hist', default='/HiggsTemplateCrossSectionsStage1/HTXS_stage1_pTjet30')
parser.add_argument('--exclude-rel', default=None, type=float, help="Exclude terms with magnitude below this value relative to largest")
parser.add_argument('--exclude-abs', default=1e-16, type=float, help="Exclude terms with magnitude below this value")
parser.add_argument('--rebin', default=None, help="Comma separated list of new bin edges")
parser.add_argument('--save', default='json', help="Comma separated list of output formats (json, txt, latex)")
parser.add_argument('--save-raw', action='store_true', help="Save the raw histogram information as JSON, for further processing")
parser.add_argument('--legacy', action='store_true', help="Use the legacy format for json ouput (if requested)")
parser.add_argument('--translate-tex', default=None, help="json file to translate parameter names to latex")
parser.add_argument('--translate-txt', default=None, help="json file to translate parameter names in the text file")
parser.add_argument('--bin-labels', default=None, help="json file to translate bin labels")
parser.add_argument('--nlo', action='store_true', help="Set if weights came from NLO reweighting")
parser.add_argument('--filter-params', default=None, help="Specify a subset of parameters to include")
parser.add_argument('--remove-empty-bins', action='store_true', help="Remove bins with zero entries")
parser.add_argument('--print-style', default="perBin", choices=["perBin", "perTerm"], help="Specify the format for printing to the screen")
parser.add_argument('--color-above', default=None, type=float, help="When using --print-style perTerm, highlight relative uncertainties above this threshold")

parser.add_argument('--skip-print', action='store_true', help="Skip printing to screen")
parser.add_argument('--skip-lin-terms', action='store_true', help="Skip linear terms")
parser.add_argument('--skip-square-terms', action='store_true', help="Skip square terms")
parser.add_argument('--skip-cross-terms', action='store_true', help="Skip cross terms")

args = parser.parse_args()
import xml.etree.ElementTree as ET

def correctWeights(w):
    # number of WCs
    N = int( -(3/2) + np.sqrt(9/4 - 2*(1-len(w[0]))) )
    for ip in range(N):
        s0 = w[:, 0]
        s1 = w[:, ip * 2 + 1]
        s2 = w[:, ip * 2 + 2]
        
        s1 -= s0
        s2 -= s0
        
        Ai = 4.0 * s1 - s2
        Bii = s2 - Ai
        
        w[:, ip * 2 + 1] = Ai
        w[:, ip * 2 + 2] = Bii
    
    crossed_offset = 2*N + 1
    c_counter = 0
    for ix in range(N):
        for iy in range(ix + 1, N):
            s = w[:, crossed_offset + c_counter]
            sm = w[:, 0]
            sx = w[:, ix * 2 + 1]
            sy = w[:, iy * 2 + 1]
            sxx = w[:, ix * 2 + 2]
            syy = w[:, iy * 2 + 2]
            
            s -= (sm + sx + sy + sxx + syy)
            w[:, crossed_offset + c_counter] = s

            c_counter += 1
            
    assert crossed_offset + c_counter == len(w[0]) 
    
    return w

def extract_lhe_weights(file_path):
    w_list = []
    
    with open(file_path, 'r') as file:
        inside_event = False
        event_data = ""
        
        for line in file:
            if "<event>" in line:
                inside_event = True
                event_data = line
            elif "</event>" in line:
                event_data += line
                inside_event = False
                
                # Parse the event XML
                root = ET.fromstring("<root>" + event_data + "</root>")
                w = [float(wgt.text) for wgt in root.findall(".//wgt")]
                w_list.append(w)
            elif inside_event:
                event_data += line
    
    return np.array(w_list) / len(w_list)

def extract_direct_weights(file_path):
    with open(file_path, 'r') as file:
        results = json.load(file)
        
    N = len(results)
    num = [results[f"rw{i:04d}"][0] for i in range(N)]
    uncert = [results[f"rw{i:04d}"][1] for i in range(N)]
    
    return np.array([num])

def initTerms(params):
    points = list()
    points.append(list('1'))
    for i in range(len(params)):
        points.append([params[i]])
        points.append([params[i], params[i]])
    for ix in range(0, len(params)):
        for iy in range(ix + 1, len(params)):
            points.append([params[ix], params[iy]])
    return points

def PrintEntry(label, val, err):
    print('%-20s | %12.4f | %12.4f | %12.4f' % (label, val, err, abs(err / val)))

with open(args.config) as jsonfile:
    cfg = json.load(jsonfile)
pars = cfg['parameters']
defs = cfg['parameter_defaults']

if args.output is None:
    auto_name = args.hist
    if auto_name.startswith('/'):
        auto_name = auto_name[1:]
    args.output = auto_name.replace('/', '_')

save_formats = args.save.split(',')

translate_tex = {}
if args.translate_tex is not None:
    with open(args.translate_tex) as jsonfile:
        translate_tex = json.load(jsonfile)

translate_txt = {}
if args.translate_txt is not None:
    with open(args.translate_txt) as jsonfile:
        translate_txt = json.load(jsonfile)

bin_labels = list()
if args.bin_labels is not None:
    with open(args.bin_labels) as jsonfile:
        bin_labels = json.load(jsonfile)[args.hist]

hname = args.hist

n_pars = len(pars)
n_hists = int(1 + n_pars * 2 + (n_pars * n_pars - n_pars) / 2)

filter = list()
if args.filter_params is not None:
    filter = args.filter_params.split(',')

for p in pars:
    for k in defs:
        if k not in p:
            p[k] = defs[k]


# Generate a list of constants that need to be divided out of each entry
eftconstants = [1.] # for the SM
for ip in range(len(pars)):
    eftconstants.append(pars[ip]['val'])
    eftconstants.append(pars[ip]['val'] * pars[ip]['val'])
for ix in range(0, len(pars)):
    for iy in range(ix + 1, len(pars)):
        eftconstants.append(pars[ix]['val'] * pars[iy]['val'])

if ".yoda" in args.input:
    hists = []
    aos = yoda.read(args.input, asdict=True)

    for i in range(n_hists):
        if args.nlo:
            hists.append(aos['%s[rw%.4i_nlo]' % (hname, i)])
        else:
            hists.append(aos['%s[rw%.4i]' % (hname, i)])

    # print hists
    is2D = isinstance(hists[0], yoda.Histo2D)

    if args.rebin is not None and not is2D:
        rebin = [float(X) for X in args.rebin.split(',')]
        for h in hists:
            h.rebinTo(rebin)

    nbins = hists[0].numBins()

    if is2D:
        edges = [[list(hists[0].bins()[ib].xEdges()), list(hists[0].bins()[ib].yEdges())] for ib in range(nbins)]
            # areas = list(hists[0].volumes())
        areas = [hists[0].bins()[ib].volume() for ib in range(nbins)]
    else:
        edges = [list(hists[0].bins()[ib].xEdges()) for ib in range(nbins)]
        areas = list(hists[0].areas())
            # print (areas,  [hists[0].bins[ib].sumW for ib in range(nbins)])
            
    assert(len(eftconstants) == len(hists))
    for ip, hist in enumerate(hists):
        hist.scaleW(1. / eftconstants[ip])
        
    e2ohist = EFT2ObsHist(
        terms=initTerms([X['name'] for X in pars]),
        sumW=[[hist.bins()[ib].sumW() for ib in range(nbins)] for hist in hists],
        sumW2=[[hist.bins()[ib].sumW2() for ib in range(nbins)] for hist in hists],
        numEntries=[[hist.bins()[ib].numEntries() for ib in range(nbins)] for hist in hists],
        bin_edges=edges,
        bin_labels=bin_labels)

elif ".lhe" in args.input or ".json " in args.input:
    event_weights = extract_lhe_weights(args.input) if ".lhe" in args.input else extract_direct_weights(args.input) 
    event_weights = correctWeights(event_weights)
    event_weights /= np.array(eftconstants)

    e2ohist = EFT2ObsHist(
        terms=initTerms([X['name'] for X in pars]),
        sumW=event_weights.sum(axis=0).reshape(-1, 1),
        sumW2=(event_weights**2).sum(axis=0).reshape(-1, 1),
        numEntries=[[len(event_weights)]],
        bin_edges=[[-1, 1]],
        bin_labels=["inclusive"]
    )

if args.remove_empty_bins:
    e2ohist.removeEmptyBins()

if not args.skip_print:
    e2ohist.printToScreen(style=args.print_style, colorAbove=args.color_above)
e2oscaling = EFTScaling.fromEFT2ObsHist(e2ohist, filter=filter, 
                                        lin_terms=not args.skip_lin_terms,
                                        square_terms=not args.skip_square_terms,
                                        cross_terms=not args.skip_cross_terms)

if args.exclude_rel is not None:
    print('>> Excluding terms with relative uncertainty below %s' % args.exclude_rel)
    e2oscaling.excludeRel(args.exclude_rel)
if args.exclude_abs is not None:
    print('>> Excluding terms with absolute uncertainty below %s' % args.exclude_abs)
    e2oscaling.excludeAbs(args.exclude_abs)

if args.save_raw:
    print('>> Saving EFT2ObsHist as %s_raw.json' % args.output)
    e2ohist.writeToJSON('%s_raw.json' % args.output)

if 'json' in save_formats:
    print('>> Saving histogram parametrisation to %s.json' % args.output)
    e2oscaling.writeToJSON('%s.json' % args.output, legacy=args.legacy, indent=2)

if 'common_json' in save_formats:
    print('>> Saving histogram parametrisation to %s.common.json' % args.output)
    e2oscaling.writeToCommonJSON('%s.common.json' % args.output, indent=1, decimals=4)

if 'CMS_json' in save_formats:
    print('>> Saving histogram parametrisation to %s.CMS.json' % args.output)
    e2oscaling.writeToCMSJSON('%s.CMS.json' % args.output, indent=1)

if 'yaml' in save_formats:
    print('>> Saving histogram parametrisation to %s.yaml' % args.output)
    e2oscaling.writeToYAML('%s.yaml' % args.output)

if 'txt' in save_formats:
    print('>> Saving histogram parametrisation to %s.txt' % args.output)
    e2oscaling.writeToTxt('%s.txt' % args.output, translate_txt)

if 'tex' in save_formats:
    print('>> Saving histogram parametrisation to %s.tex' % args.output)
    e2oscaling.writeToTex('%s.tex' % args.output, translate_tex)
