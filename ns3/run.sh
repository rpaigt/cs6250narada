#/bin/bash

#copies the necessary files over to ns3 scratch folder and run ns3 simulation
#and returns output into run.log


#do not modify this
NSPATH="../../ns-allinone-3.16/ns-3.16/"
SCRATCHPATH=$NSPATH"/scratch/"

#files to be copied over, modify this accordingly
FILES="sim.py ../routing2.py"

#this checks if you have already extracted and compiled ns-3.16 into ../..
if [ ! -d $NSPATH ]; then
    echo "Please ensure that $NSPATH folder exists."
    echo "Extract and compile ns-3.16 into $NSPATH first."
    exit 1
fi

#copy files over
for i in $FILES; do
    cp -v $i $SCRATCHPATH
done

#run simulation
cd $NSPATH
export NS_LOG=
if [ $1 == "-v" ]; then
    export NS_LOG="*=level_all|prefix_func|prefix_time"
fi
    
#logging variable, modify this accordingly
./waf --pyrun scratch/sim.py
