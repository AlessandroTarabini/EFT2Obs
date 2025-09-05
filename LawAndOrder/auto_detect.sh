process=$1

cd ../cards
cp -r ${process} ${process}_operators
cd ${process}_operators

sed -i 's/NP=0/NP=2/g' proc_card.dat
sed -i 's/noborn=QCD/virt=QCD/g' proc_card.dat

# Change the model to SMEFTatNLO
sed -i '1s/.*/import model SMEFTatNLO/' proc_card.dat
sed -i '$s/.*/output '"$1"'_operators/' proc_card.dat

cd ../..

./scripts/setup_process.sh ${process}_operators

python ./scripts/auto_detect_operators.py -p ${process}_operators --noValidation --def-val 1.0 --noReweightCard --noConfigJson -b DIM6,DIM62F,DIM64F2L,DIM64F4L,DIM64F

rm -r cards/${process}_operators 
rm -r MG5_aMC_v2_9_16/${process}_operators 