// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/VisibleFinalState.hh"
#include "Rivet/Tools/RivetYODA.hh"

namespace Rivet {

  /// @brief H->yy analysis at 13.6 TeV with 2022 dataset
  class CMS_2025_I2915441 : public Analysis {
   public:
    /// Constructor
    RIVET_DEFAULT_ANALYSIS_CTOR(CMS_2025_I2915441);

    void init() {
      //---All particle final state
      FinalState fs;
      declare(fs, "FS");

      //---Visible final state (no neutrinos)
      VisibleFinalState vfs(fs);
      declare(vfs, "VFS");

      //---Photons
      FinalState fs_photons(Cuts::abspid == PID::PHOTON);
      declare(fs_photons, "FS_PHOTONS");

      //---Leptons
      FinalState fs_leptons(Cuts::abspid == PID::ELECTRON || Cuts::abspid == PID::MUON);
      declare(fs_leptons, "FS_LEPTONS");

      //---Jets
      FastJets fs_jets(fs, FastJets::ANTIKT, 0.4);
      declare(fs_jets, "JETS");

      //---Histograms 
      // Run2 binning
      // book(_h_pt_h, "pt_h",{0,5,10,15,20,25,30,35,45,60,80,100,120,140,170,200,250,350,450,10000}); 
      // book(_h_rapidity_h, "rapidity_h", {0,0.15,0.3,0.6,0.9,2.5});
      // book(_h_njets_eta2p5, "njets_eta2p5", {0,1,2,3,100});
      // book(_h_jet_pt_lead, "jet_pt_lead", {0,30,75,120,200,13000});
      // book(_h_cos_theta_star, "cos_theta_star", {0.,0.07,0.15,0.22,0.35,0.45, 0.55, 0.75, 1.0});
      // 2022 binning 
      book(_h_pt_h, "PTH",{0,15,30,45,80,120,200,350,13000}); 
      book(_h_rapidity_h, "rapidity", {0,0.15,0.3,0.6,0.9,2.5});
      book(_h_njets_eta4p7, "NJ", {0,1,2,3,100});
      book(_h_jet_pt_lead, "PTJ0", {0,30,75,120,200,13000});
      book(_h_dphi_jj, "DPhiJ0J1", {-5, -3.1415926536, -2.09439510239, -1.0471975512, 0, 1.0471975512, 2.09439510239, 3.1415926536});
      book(_h_cos_theta_star, "cos_theta_star", {0.,0.07,0.15,0.22,0.35,0.45, 0.55, 0.75, 1.0});
      book(_h_sigma, "h_sigma", 1, 0, 2); // This is to get the cross section without fiducial cuts
    }

    // cos theta star angle in the Collins Soper frame
    double getCosThetaStar_CS(const FourMomentum& h1, const FourMomentum& h2) {
      FourMomentum hh = h1 + h2;
      LorentzTransform boost = LorentzTransform::mkFrameTransformFromBeta(hh.betaVec());
      FourMomentum h1_boosted = boost.transform(h1);
      return abs(cos(h1_boosted.theta()));
    }

    double deltaphi_jj(const FourMomentum& h1, const FourMomentum& h2) {
      //Direction of the two jets - vectors in the lab frame
      Vector3 j1dir(h1.x(), h1.y(), h1.z());
      Vector3 j2dir(h2.x(), h2.y(), h2.z());
      //Transverse component in the xy plane
      Vector3 jt1(h1.x(), h1.y(), 0);
      Vector3 jt2(h2.x(), h2.y(), 0);
      //Unit vectors of the transverse components
      Vector3 jt1_norm   = jt1 * (1/jt1.mod());
      Vector3 jt2_norm   = jt2 * (1/jt2.mod());
      //Unit vector of the z axis
      Vector3 z(0,0,1);
      //Cross product between transverse components
      double cross      = jt1_norm.cross(jt2_norm).dot(z);
      double cross_norm = cross * (1 / abs(cross));
      //Dot product between transverse components
      double dot         = jt1_norm.dot(jt2_norm);
      //Difference between the direction of the two jets
      double diff       = (j1dir - j2dir).dot(z);
      double diff_norm  = diff * (1 / abs(diff));
      return acos(dot) * diff_norm * cross_norm;
    }


    void analyze(const Event& event) {

      _h_sigma->fill(1.); // To be filled before any fiducial cut

      Particles photons = apply<FinalState>(event, "FS_PHOTONS").particlesByPt();

      if (photons.size() < 2) vetoEvent;

      //---Isolate photons with ET_sum in cone
      //---Implementing logic for NanoAOD: https://github.com/bonanomi/cmssw/blob/69e3a519595c0d44d39dc8dc2f2ec562365ec90c/PhysicsTools/NanoAOD/plugins/GenPartIsoProducer.cc#L125-L153
      Particles isolated_photons;
      Particles vfs = apply<FinalState>(event, "VFS").particlesByPt();
      for (const Particle& photon : photons) {
        if (photon.pT() < 10 * GeV) continue; // Cut applied on gen-level photons in NanoAOD
        double mom_in_cone = 0;
        for (const Particle& particle : vfs) {
          if (deltaR(photon, particle) < 0.3 && deltaR(photon, particle) > 0.001) {
            mom_in_cone += particle.pT();
          }
        }
        if (mom_in_cone < 10 * GeV) isolated_photons.push_back(photon);
      }

      if (isolated_photons.size() < 2) vetoEvent;

      //---kinematic photon selection
      FourMomentum mom_PP = isolated_photons[0].mom() + isolated_photons[1].mom();
      if (
        sqrt(isolated_photons[0].pT() * isolated_photons[1].pT()) < mom_PP.mass() / 3. 
          || isolated_photons[1].pT() < mom_PP.mass() / 4. 
          || (isolated_photons[0].abseta() > 2.5 || (isolated_photons[0].abseta() < 1.566 && isolated_photons[0].abseta() > 1.442))
          || (isolated_photons[1].abseta() > 2.5 || (isolated_photons[1].abseta() < 1.566 && isolated_photons[1].abseta() > 1.442)))
        vetoEvent;

      _h_pt_h->fill(mom_PP.pt() / GeV);
      _h_rapidity_h->fill(abs(mom_PP.rapidity()));
      _h_cos_theta_star->fill(getCosThetaStar_CS(isolated_photons[0].mom(), isolated_photons[1].mom()));

      //---jets
      // auto jets_eta2p5 = apply<FastJets>(event, "JETS").jetsByPt(Cuts::abseta < 2.5 && Cuts::pt > 30 * GeV);
      auto jets_eta4p7 = apply<FastJets>(event, "JETS").jetsByPt(Cuts::abseta < 4.7 && Cuts::pt > 30 * GeV);

      //--- Isolate leptons for lepton cleaning
      //--- Implementing the logic for NanoAOD: https://github.com/bonanomi/cmssw/blob/69e3a519595c0d44d39dc8dc2f2ec562365ec90c/PhysicsTools/NanoAOD/plugins/GenPartIsoProducer.cc
      //--- Identify FSR photons, to be removed in the computation of the lepton isolation
      Particles leptons = apply<FinalState>(event, "FS_LEPTONS").particlesByPt();
      Particles isolated_leptons;
      for (const Particle& lep : leptons) {
          if (lep.abspid() == PID::ELECTRON && (abs(lep.eta())>2.5 || lep.pT() < 15 * GeV)) continue; // Kinematic cuts applied to electrons
          if (lep.abspid() == PID::MUON && (abs(lep.eta())>2.4 || lep.pT() < 10 * GeV)) continue; // Kinematic cuts applied to muons
          FourMomentum mom_lep = lep.mom();
          double mom_in_cone = 0;
          for (const Particle& part : vfs) {
            if (part.abspid() == PID::PHOTON && deltaR(lep,part) < 0.3 && part.hasParentWith(Cuts::pid == PID::ELECTRON || Cuts::pid == PID::MUON) ) {
              mom_lep += part.mom();
            }else{
              if (deltaR(mom_lep, part) < 0.3 && deltaR(mom_lep, part) > 0.001 && lep.pid()!=PID::ELECTRON && lep.pid()!=PID::MUON) mom_in_cone += part.pT();
            }
          }
          if (mom_in_cone / mom_lep.pT() < 0.2) isolated_leptons.push_back(lep);
      }

      // idiscardIfAnyDeltaRLess(jets_eta2p5, isolated_photons, 0.4);
      // idiscardIfAnyDeltaRLess(jets_eta2p5, isolated_leptons, 0.4);
      idiscardIfAnyDeltaRLess(jets_eta4p7, isolated_photons, 0.4);
      idiscardIfAnyDeltaRLess(jets_eta4p7, isolated_leptons, 0.4);

      // _h_njets_eta2p5->fill(jets_eta2p5.size());
      _h_njets_eta4p7->fill(jets_eta4p7.size());

      if (jets_eta4p7.size() > 0) {
        _h_jet_pt_lead->fill(jets_eta4p7[0].pt() / GeV);
      }else{
        _h_jet_pt_lead->fill(0); // For the underflow bin Njet = 0
      }

      if (jets_eta4p7.size() > 1) {
        _h_dphi_jj->fill(deltaphi_jj(jets_eta4p7[0], jets_eta4p7[1]));
      }else{
        _h_dphi_jj->fill(-4); // For the underflow 
      }

    }

    void finalize() {
      scale(_h_pt_h, crossSection() / femtobarn * BR / sumOfWeights());
      scale(_h_rapidity_h, crossSection() / femtobarn * BR / sumOfWeights());
      scale(_h_njets_eta4p7, crossSection() / femtobarn * BR / sumOfWeights());
      scale(_h_jet_pt_lead, crossSection() / femtobarn * BR / sumOfWeights());
      scale(_h_dphi_jj, crossSection() / femtobarn * BR / sumOfWeights());
      scale(_h_cos_theta_star, crossSection() / femtobarn * BR / sumOfWeights());
      scale(_h_sigma, crossSection() / femtobarn * BR / sumOfWeights());
    }

   private:

    Histo1DPtr _h_pt_h;
    Histo1DPtr _h_rapidity_h;
    Histo1DPtr _h_njets_eta4p7;
    Histo1DPtr _h_jet_pt_lead;
    Histo1DPtr _h_dphi_jj;
    Histo1DPtr _h_cos_theta_star;
    Histo1DPtr _h_sigma;
    const double BR = 0.00227;
  };

  RIVET_DECLARE_PLUGIN(CMS_2025_I2915441);

}  // namespace Rivet